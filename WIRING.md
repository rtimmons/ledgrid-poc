# SPI Wiring Guide: Raspberry Pi to SCORPIO

## Connection Table

| Signal | Raspberry Pi GPIO | **RPi Physical Pin** | SCORPIO GPIO | SCORPIO Board Label | Notes |
|--------|------------------|---------------------|--------------|---------------------|-------|
| **SCLK** | **GPIO 11** | **🔴 Pin 23** | **GPIO 14** | **SCK** | **CLOCK - Most common issue!** |
| **MOSI** | **GPIO 10** | **🔴 Pin 19** | **GPIO 12** | *(no label)* | **Data from Pi to SCORPIO** |
| CS/CE0 | GPIO 8 | **Pin 24** | GPIO 13 | *(no label)* | Chip Select (active LOW) |
| MISO | GPIO 9 | Pin 21 | GPIO 15 | **MO** | Data from SCORPIO to Pi (optional) |
| GND | GND | Pin 6, 9, 14, 20, 25, 30, 34, or 39 | GND | **GND** | **CRITICAL: Common ground** |

### Quick Reference - Raspberry Pi Physical Pins:
```
        3.3V [ 1] [ 2] 5V
       GPIO2 [ 3] [ 4] 5V
       GPIO3 [ 5] [ 6] GND      ← Any GND works
       GPIO4 [ 7] [ 8] GPIO14
         GND [ 9] [10] GPIO15
      GPIO17 [11] [12] GPIO18
      GPIO27 [13] [14] GND
      GPIO22 [15] [16] GPIO23
        3.3V [17] [18] GPIO24
🔴 GPIO10 MOSI [19] [20] GND
      GPIO9 MISO [21] [22] GPIO25
🔴 GPIO11 SCLK [23] [24] GPIO8 CE0  ← Use this for CS
         GND [25] [26] GPIO7 CE1
```

**Note about board labels:** The SCORPIO silkscreen labels (MO, MI, SCK) are for **master mode**. Since we're using the board as a **slave**, the pin assignments differ. The table above shows the correct pins for slave mode.

**IMPORTANT:** RP2040 SPI1 requires all pins from the same GPIO set:
- **Set A:** GPIO 8-11 (alternate configuration)
- **Set B:** GPIO 12-15 (current configuration - CS=13, MOSI=12, SCK=14, MISO=15)

## Physical Setup

1. **Power the SCORPIO** - Connect USB cable to SCORPIO for power and debugging
2. **Connect SPI wires** - Use female-to-female jumper wires
3. **Connect GND** - Mandatory for signal reference
4. **Verify connections** - Double-check each wire before powering on

## Verification Steps

### On Raspberry Pi:
```bash
# 1. Check SPI is enabled
ls -l /dev/spidev*
# Should see: /dev/spidev0.0 and /dev/spidev0.1

# 2. Enable SPI if not found
sudo raspi-config
# Interface Options -> SPI -> Enable -> Reboot

# 3. Test SPI master
python3 -c "import spidev; spi=spidev.SpiDev(); spi.open(0,0); print('SPI OK')"

# 4. Run LED controller
python3 led_controller_spi.py rainbow
```

### On SCORPIO (via Serial Monitor):
You should see:
```
*** CRITICAL: Verify this wiring! ***
  Raspberry Pi -> SCORPIO (SPI1 Set B: GPIO 12-15)
  GPIO 8 (CE0)   -> GPIO 13 (CS)
  GPIO 10 (MOSI) -> GPIO 12 (MOSI) <-- DATA IN
  GPIO 9 (MISO)  -> GPIO 15 (MISO)
  GPIO 11 (SCLK) -> GPIO 14 (SCK)
  GND -> GND
```

## Troubleshooting

### Problem: "SCK never toggled! Check SCK wire (GPIO 14)" (MOST COMMON)
**This is the most common wiring issue!**

The SCORPIO detects CS assertions but never sees clock pulses:
```
[CS] Asserted - transaction start
[CS] Released after 1ms - SCK toggles: 0 - NO DATA in FIFO!
  → SCK never toggled! Check SCK wire (GPIO 14)
```

**Solution:**
1. **Verify physical connection:**
   - Raspberry Pi **Physical Pin 23** → SCORPIO **GPIO 14** (labeled "SCK")
   - This is Pin 23 on the Pi (bottom row, 12th pin from the left)
   - Double-check you're counting correctly on the Pi header
   
2. **Test with verification script:**
   ```bash
   python3 verify_pi_wiring.py
   ```
   This will toggle each pin so you can verify with a multimeter

3. **Common mistakes:**
   - Using Pin 22 instead of Pin 23 (easy to miscount)
   - Wire connected to wrong header pin
   - Loose connection
   - SCORPIO side connected to wrong GPIO

### Problem: CS detected but no data after SCK toggles
```
[CS] Released after Xms - SCK toggles: 64 - NO DATA in FIFO!
  → SCK toggled but no data received
```

**Solution:**
- **Most likely:** MOSI (GPIO 10 → GPIO 12) not connected
- **Check:** Raspberry Pi **Physical Pin 19** → SCORPIO **GPIO 12** (unlabeled)
- **Verify:** Use multimeter in continuity mode
- **Note:** GPIO 12 is between the labeled "SCK" and "CS" pins on SCORPIO

### Problem: No CS activity detected
```
[DEBUG] SPI SR: 0x3 | RNE=0 | BSY=0 | CS=HIGH
(CS never goes LOW)
```

**Solution:**
- **Most likely:** CS (GPIO 8 → GPIO 13) not connected
- **Check:** Raspberry Pi **Physical Pin 24** → SCORPIO **GPIO 13** (unlabeled)

### Problem: Device not detected or erratic behavior
- **Most likely:** No common ground
- **Fix:** Connect any GND pin from Pi to GND on SCORPIO
- **Critical:** GND MUST be connected for any signals to work

## Notes on SCORPIO GPIO Pins and Board Labels

The SCORPIO board uses specific pins for different functions:
- **GPIO 16-23**: NeoPixel LED outputs (DO NOT USE for SPI)
- **GPIO 12-15**: SPI1 Set B pins (current slave configuration)
  - GPIO 12: **MOSI** (SPI1 RX - receives data from Pi) - *unlabeled on board*
  - GPIO 13: **CS** (SPI1 CSn - Chip Select) - *unlabeled on board*
  - GPIO 14: **SCK** (SPI1 SCK - Clock) - *labeled "SCK" on board* ✓
  - GPIO 15: **MISO** (SPI1 TX - sends data to Pi) - *labeled "MO" on board* ✓
- **GPIO 8-11**: SPI1 Set A pins (alternate - not used)
  - GPIO 8 is labeled "MI" on board, but cannot be used with GPIO 14 SCK
- **GPIO 2-3**: I2C (not used in this project)

**CRITICAL:** 
1. All SPI pins must be from the same set (either 8-11 OR 12-15). Mixing sets will not work!
2. Board labels (MO, MI, SCK) are for **master mode**. In **slave mode**, pin functions differ.
3. The "MI" label at GPIO 8 cannot be used when SCK is at GPIO 14 (they're from different pin sets).

## Multi-SCORPIO Setup (Future)

To control multiple SCORPIO boards:
- Use different CS pins for each board (CE0, CE1, or manual GPIO pins)
- All MOSI, MISO, SCLK, and GND are shared
- Each SCORPIO gets its own CS line

Example for 2 boards:
```
Pi GPIO 8 (CE0) → SCORPIO #1 GPIO 13
Pi GPIO 7 (CE1) → SCORPIO #2 GPIO 13
Pi GPIO 10 (MOSI) → Both SCORPIO GPIO 12 (shared)
Pi GPIO 11 (SCLK) → Both SCORPIO GPIO 14 (shared)
Pi GPIO 9 (MISO) → Both SCORPIO GPIO 15 (shared)
Pi GND → Both SCORPIO GND (shared)
```


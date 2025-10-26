# LED Grid - Adafruit Feather RP2040 SCORPIO

An I2C-controlled LED system using the Adafruit Feather RP2040 SCORPIO board with 8-channel parallel NeoPixel control.

## System Architecture

- **SCORPIO Board**: Acts as I2C slave, receives commands and drives 8 LED strips (GPIO 16-23)
- **Controller (Python)**: Acts as I2C master, sends pixel data and commands

## Hardware

- **Board**: Adafruit Feather RP2040 SCORPIO
- **Features**: 8 parallel NeoPixel outputs driven by PIO (Programmable I/O)
- **I2C**: Wire1 peripheral (i2c1)
  - SDA: GPIO 2
  - SCL: GPIO 3
- **I2C Address**: 0x42

### Wiring (SCORPIO to Raspberry Pi)
| SCORPIO | Raspberry Pi |
|---------|--------------|
| GPIO 2 (SDA) | GPIO 2 (Pin 3, SDA) |
| GPIO 3 (SCL) | GPIO 3 (Pin 5, SCL) |
| GND | GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39) |

**Important:** I2C requires pull-up resistors (typically 4.7kΩ) on both SDA and SCL lines. The Raspberry Pi usually has built-in pull-ups, but if communication fails, add external 4.7kΩ resistors from SDA/SCL to 3.3V.

## Firmware Setup

1. Install [PlatformIO](https://platformio.org/)
2. Build and upload the firmware:
   ```bash
   pio run --target upload
   ```
3. Monitor the serial output:
   ```bash
   pio device monitor
   ```

## Python Controller Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make the script executable:
   ```bash
   chmod +x led_controller.py
   ```

## Usage

### Rainbow Animation
```bash
python led_controller.py rainbow
```

With custom speed:
```bash
python led_controller.py rainbow --speed 2.0
```

For a specific duration:
```bash
python led_controller.py rainbow --duration 60
```

### Solid Color
Set all LEDs to a specific RGB color:
```bash
python led_controller.py solid 255 0 0  # Red
python led_controller.py solid 0 255 0  # Green
python led_controller.py solid 0 0 255  # Blue
```

### Test Strips
Test each strip individually with different colors:
```bash
python led_controller.py test
```

### Clear All LEDs
```bash
python led_controller.py clear
```

### Set Brightness
Add `--brightness` to any command:
```bash
python led_controller.py rainbow --brightness 100
```

## I2C Protocol

The firmware supports the following commands:

| Command | Byte | Description | Data Format |
|---------|------|-------------|-------------|
| SET_PIXEL | 0x01 | Set single pixel | `[cmd][pixelH][pixelL][R][G][B]` |
| SET_BRIGHTNESS | 0x02 | Set brightness | `[cmd][brightness]` |
| SHOW | 0x03 | Update display | `[cmd]` |
| CLEAR | 0x04 | Clear all pixels | `[cmd]` |
| SET_RANGE | 0x05 | Set multiple pixels | `[cmd][startH][startL][count][R][G][B]...` |

## Configuration

### Firmware (`src/main.cpp`)
- `I2C_ADDRESS`: I2C slave address (default: 0x42)
- `I2C_SDA_PIN`: SDA pin (default: GPIO 2)
- `I2C_SCL_PIN`: SCL pin (default: GPIO 3)
- `USE_WIRE1`: Define to use Wire1 peripheral (required for GPIO 2/3)
- `NUM_LED`: LEDs per strip (default: 30)

### Python (`led_controller.py`)
- `I2C_BUS`: I2C bus number (default: 1 for Raspberry Pi)
- `I2C_ADDRESS`: Must match firmware (default: 0x42)
- `NUM_LED_PER_STRIP`: Must match firmware (default: 30)

## The SCORPIO Board

The SCORPIO board uses the RP2040's PIO hardware to drive 8 NeoPixel strips simultaneously without blocking the CPU. The GPIO pins 16-23 are dedicated NeoPixel outputs.

## Troubleshooting

### Check I2C Connection

Run the I2C scanner to detect devices:
```bash
python3 i2c_scan.py
```

This will show all I2C devices on the bus. You should see device `0x42`.

### Common Issues

**"No I2C devices found"**
1. Make sure the SCORPIO board firmware is uploaded and running
2. Check the serial monitor output: `pio device monitor`
3. Verify I2C wiring:
   - SCORPIO GPIO 2 (SDA) → Raspberry Pi GPIO 2 (Pin 3)
   - SCORPIO GPIO 3 (SCL) → Raspberry Pi GPIO 3 (Pin 5)
   - Common GND connection
4. Check for pull-up resistors (4.7kΩ on SDA and SCL to 3.3V)

**"Permission denied"**
- Run with sudo: `sudo python3 led_controller.py rainbow`
- Or add user to i2c group: `sudo usermod -a -G i2c $USER` (logout/login required)

**"I2C bus not found"**
- Enable I2C on Raspberry Pi: `sudo raspi-config` → Interface Options → I2C
- Check available buses: `ls /dev/i2c-*`
- Try different bus number: `python3 led_controller.py rainbow --bus 0`

**"Input/output error"**
- Device not responding - check if firmware is running
- Monitor SCORPIO serial output to see if it's receiving commands
- Verify I2C address matches in both firmware and Python script


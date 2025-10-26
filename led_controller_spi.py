#!/usr/bin/env python3
"""
LED Grid Controller - SPI version
Controls multiple SCORPIO boards via SPI
"""

import time
import colorsys
import argparse
import spidev

# LED Configuration  
NUM_LED_PER_STRIP = 30
NUM_STRIPS = 8
TOTAL_LEDS = NUM_LED_PER_STRIP * NUM_STRIPS

# SPI Configuration
SPI_BUS = 0  # SPI bus number (0 = /dev/spidev0.X)
SPI_DEVICE = 1  # CS device (0 = CE0)
SPI_SPEED = 1000000  # 1 MHz

# Command definitions
CMD_SET_PIXEL = 0x01
CMD_SET_BRIGHTNESS = 0x02
CMD_SHOW = 0x03
CMD_CLEAR = 0x04
CMD_SET_RANGE = 0x05
CMD_PING = 0xFF


class LEDController:
    """Control LED strips via SPI"""
    
    def __init__(self, bus=SPI_BUS, device=SPI_DEVICE, speed=SPI_SPEED):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = speed
        self.spi.mode = 0  # SPI Mode 0 (CPOL=0, CPHA=0)
        
        print(f"SPI Controller initialized")
        print(f"  Bus: {bus}, Device: {device}")
        print(f"  Speed: {speed/1000000:.1f} MHz")
        print(f"  Device: /dev/spidev{bus}.{device}")
        
        # Test ping
        try:
            self.spi.xfer([CMD_PING])
            time.sleep(0.01)
            print("✓ SPI connection OK\n")
        except Exception as e:
            print(f"Warning: SPI test failed: {e}\n")
    
    def set_pixel(self, pixel, r, g, b):
        """Set a single pixel color"""
        if pixel >= TOTAL_LEDS:
            return
        
        data = [
            CMD_SET_PIXEL,
            (pixel >> 8) & 0xFF,
            pixel & 0xFF,
            int(r) & 0xFF,
            int(g) & 0xFF,
            int(b) & 0xFF
        ]
        self.spi.xfer(data)
    
    def set_brightness(self, brightness):
        """Set global brightness (0-255)"""
        data = [CMD_SET_BRIGHTNESS, int(brightness) & 0xFF]
        self.spi.xfer(data)
    
    def show(self):
        """Update the LED display"""
        self.spi.xfer([CMD_SHOW])
    
    def clear(self):
        """Clear all LEDs"""
        self.spi.xfer([CMD_CLEAR])
    
    def set_range(self, start_pixel, colors):
        """
        Set a range of pixels efficiently
        colors: list of (r, g, b) tuples
        """
        count = min(len(colors), 160)  # Limit to avoid buffer overflow
        
        data = [
            CMD_SET_RANGE,
            (start_pixel >> 8) & 0xFF,
            start_pixel & 0xFF,
            count
        ]
        
        # Add RGB data
        for i in range(count):
            r, g, b = colors[i]
            data.extend([int(r) & 0xFF, int(g) & 0xFF, int(b) & 0xFF])
        
        self.spi.xfer(data)
    
    def close(self):
        """Close SPI connection"""
        self.spi.close()


def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB (0-255)"""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def rainbow_animation(controller, duration=None, speed=1.0):
    """Rainbow cycle animation"""
    print("Starting rainbow animation...")
    print("Press Ctrl+C to stop\n")
    
    hue_offset = 0
    start_time = time.time()
    frame_count = 0
    
    try:
        while True:
            if duration and (time.time() - start_time) > duration:
                break
            
            # Calculate colors for all pixels
            for pixel in range(TOTAL_LEDS):
                hue = (hue_offset + (pixel / TOTAL_LEDS)) % 1.0
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                controller.set_pixel(pixel, r, g, b)
            
            controller.show()
            
            hue_offset += 0.01 * speed
            if hue_offset >= 1.0:
                hue_offset -= 1.0
            
            frame_count += 1
            
            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"FPS: {fps:.1f} | Frames: {frame_count}")
            
            time.sleep(0.02)
    
    except KeyboardInterrupt:
        print("\nAnimation stopped")


def solid_color(controller, r, g, b):
    """Set all LEDs to a solid color"""
    print(f"Setting all LEDs to RGB({r}, {g}, {b})")
    for pixel in range(TOTAL_LEDS):
        controller.set_pixel(pixel, r, g, b)
    controller.show()


def test_strips(controller):
    """Test each strip individually"""
    print("Testing each strip individually...")
    
    colors = [
        (255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
        (0, 255, 255), (0, 0, 255), (127, 0, 255), (255, 0, 255),
    ]
    
    for strip in range(NUM_STRIPS):
        print(f"Testing strip {strip}...")
        r, g, b = colors[strip]
        
        for pixel in range(NUM_LED_PER_STRIP):
            pixel_index = strip * NUM_LED_PER_STRIP + pixel
            controller.set_pixel(pixel_index, r, g, b)
        
        controller.show()
        time.sleep(0.5)
    
    print("Test complete!")


def main():
    parser = argparse.ArgumentParser(description='LED Grid Controller (SPI)')
    parser.add_argument('--bus', type=int, default=SPI_BUS,
                        help=f'SPI bus number (default: {SPI_BUS})')
    parser.add_argument('--device', type=int, default=SPI_DEVICE,
                        help=f'SPI device/CS number (default: {SPI_DEVICE})')
    parser.add_argument('--speed', type=int, default=SPI_SPEED,
                        help=f'SPI speed in Hz (default: {SPI_SPEED})')
    parser.add_argument('--brightness', type=int, default=50,
                        help='LED brightness 0-255 (default: 50)')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    rainbow_parser = subparsers.add_parser('rainbow', help='Rainbow animation')
    rainbow_parser.add_argument('--speed', type=float, default=1.0, dest='anim_speed')
    rainbow_parser.add_argument('--duration', type=float, default=None)
    
    solid_parser = subparsers.add_parser('solid', help='Solid color')
    solid_parser.add_argument('r', type=int, help='Red (0-255)')
    solid_parser.add_argument('g', type=int, help='Green (0-255)')
    solid_parser.add_argument('b', type=int, help='Blue (0-255)')
    
    subparsers.add_parser('test', help='Test each strip')
    subparsers.add_parser('clear', help='Clear all LEDs')
    
    args = parser.parse_args()
    
    controller = None
    try:
        controller = LEDController(bus=args.bus, device=args.device, speed=args.speed)
        
        controller.set_brightness(args.brightness)
        print(f"Brightness set to {args.brightness}\n")
        
        if args.command == 'rainbow':
            rainbow_animation(controller, duration=args.duration, speed=args.anim_speed)
        elif args.command == 'solid':
            solid_color(controller, args.r, args.g, args.b)
        elif args.command == 'test':
            test_strips(controller)
        elif args.command == 'clear':
            controller.clear()
            print("All LEDs cleared")
        else:
            rainbow_animation(controller)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if controller:
            controller.close()
            print("\nSPI connection closed")


if __name__ == '__main__':
    main()


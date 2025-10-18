import serial
import time
import os
import sys

try:
    from crsf_parser import CRSFParser
except ImportError:
    print("Error: crsf-parser library not found!")
    print("Please install it with: pip install crsf-parser")
    sys.exit(1)

class EdgeTXMonitor:
    def __init__(self, port='COM3', baudrate=400000):
        self.port = port
        self.baudrate = baudrate
        self.channels = [1500] * 16  # Initialize channels at center
        self.frame_count = 0
        
        # Create parser with callback function
        self.parser = CRSFParser(self.handle_frame)
        
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.01)
            print(f"✓ Opened {port} at {baudrate} baud")
        except serial.SerialException as e:
            print(f"✗ Error opening {port}: {e}")
            sys.exit(1)
    
    def handle_frame(self, frame):
        """Callback function to handle parsed CRSF frames"""
        # Check if this is an RC channels frame
        if hasattr(frame, 'channels'):
            self.frame_count += 1
            
            # Convert CRSF values to microseconds
            for i in range(min(16, len(frame.channels))):
                crsf_value = frame.channels[i]
                # CRSF range: 172-1811 maps to 988-2012 µs
                us_value = int(988 + (crsf_value * 1024 / 1984))
                self.channels[i] = us_value
    
    def create_bar(self, value, width=40):
        """Create ASCII bar for channel value (988-2012 µs)"""
        normalized = (value - 988) / (2012 - 988)
        normalized = max(0, min(1, normalized))  # Clamp to 0-1
        filled = int(normalized * width)
        bar = '█' * filled + '░' * (width - filled)
        return bar
    
    def value_to_percent(self, value):
        """Convert microseconds to percentage"""
        return int(((value - 1500) / 512) * 100)
    
    def clear_screen(self):
        """Clear terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display(self):
        """Display channel data"""
        self.clear_screen()
        
        print("=" * 80)
        print("EdgeTX CRSF Channel Monitor (using crsf-parser)")
        print("=" * 80)
        print(f"Port: {self.port} @ {self.baudrate} baud")
        print(f"Frames received: {self.frame_count}")
        print("=" * 80)
        print()
        
        if self.frame_count == 0:
            print("⚠ Waiting for CRSF data...")
            print()
            print("Setup checklist:")
            print("  1. ✓ External ELRS module connected")
            print("  2. ✓ Model Setup > External RF > Mode: CRSF")
            print("  3. ✓ USB Mode: CLI")
            print("  4. □ Run: serialpassthrough rfmod 0 400000")
            print()
            print("If you haven't enabled passthrough yet:")
            print("  - Open another terminal")
            print("  - Run: python cli_tester.py")
            print("  - Type: serialpassthrough rfmod 0 400000")
            print("  - Then run this monitor")
            return
        
        channel_names = [
            "Aileron ", "Elevator", "Throttle", "Rudder  ",
            "CH5     ", "CH6     ", "CH7     ", "CH8     ",
            "CH9     ", "CH10    ", "CH11    ", "CH12    ",
            "CH13    ", "CH14    ", "CH15    ", "CH16    "
        ]
        
        for i in range(16):
            value = self.channels[i]
            percent = self.value_to_percent(value)
            bar = self.create_bar(value)
            
            print(f"CH{i+1:02d} [{channel_names[i]}] [{bar}] {percent:4d}% ({value}µs)")
        
        print()
        print("Press Ctrl+C to exit | Move sticks to see updates")
    
    def run(self):
        """Main monitoring loop"""
        last_display = time.time()
        
        print("Starting CRSF monitor with crsf-parser library...")
        print("Waiting for data...")
        print()
        
        try:
            while True:
                # Read available data
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    
                    # Feed data to parser byte by byte
                    # The parser will call our handle_frame callback when a complete frame is received
                    for byte in data:
                        self.parser.parse_byte(byte)
                
                # Update display at 10Hz
                if time.time() - last_display > 0.1:
                    self.display()
                    last_display = time.time()
                    
        except KeyboardInterrupt:
            print("\n\nMonitor stopped.")
            self.ser.close()
            print("Connection closed.")

def main():
    print()
    print("=" * 80)
    print("EdgeTX CRSF Channel Monitor")
    print("=" * 80)
    print()
    
    # Check if passthrough is likely active
    print("IMPORTANT: Make sure you've enabled serial passthrough first!")
    print()
    print("To enable passthrough:")
    print("  1. Set USB Mode to CLI")
    print("  2. Connect to TX12")
    print("  3. Run: serialpassthrough rfmod 0 400000")
    print()
    
    response = input("Have you enabled passthrough? (y/n): ").strip().lower()
    
    if response != 'y':
        print()
        print("Please enable passthrough first, then run this monitor again.")
        sys.exit(0)
    
    print()
    print("Starting monitor...")
    print()
    
    # Try different common baudrates
    baudrates = [400000, 420000, 115200]
    
    for baud in baudrates:
        print(f"Trying {baud} baud...")
        try:
            monitor = EdgeTXMonitor('COM3', baud)
            monitor.run()
            break
        except Exception as e:
            print(f"Failed at {baud}: {e}")
            continue

if __name__ == "__main__":
    main()
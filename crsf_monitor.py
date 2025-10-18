import serial
import time
import sys
import os

class CRSFMonitor:
    # CRSF Constants
    CRSF_SYNC_BYTE = 0xC8
    CRSF_FRAMETYPE_RC_CHANNELS = 0x16
    
    def __init__(self, port='COM3', baudrate=921600):
        self.port = port
        self.baudrate = baudrate
        self.channels = [1500] * 16  # Initialize 16 channels at center
        self.frame_count = 0
        self.error_count = 0
        
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.01)
            print(f"✓ Opened {port} at {baudrate} baud")
        except serial.SerialException as e:
            print(f"✗ Error opening {port}: {e}")
            sys.exit(1)
    
    def crc8_dvb_s2(self, data):
        """Calculate CRC8 for CRSF protocol"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0xD5
                else:
                    crc = crc << 1
        return crc & 0xFF
    
    def parse_rc_channels(self, payload):
        """Parse 16 channels from CRSF RC channels packet"""
        if len(payload) < 22:
            return False
        
        # CRSF uses 11-bit values packed into bytes
        # 16 channels * 11 bits = 176 bits = 22 bytes
        channels = []
        bit_index = 0
        
        for i in range(16):
            value = 0
            for bit in range(11):
                byte_index = bit_index // 8
                bit_offset = bit_index % 8
                if byte_index < len(payload):
                    if payload[byte_index] & (1 << bit_offset):
                        value |= (1 << bit)
                bit_index += 1
            
            # Convert 11-bit value (0-2047) to microseconds (988-2012)
            # CRSF range: 172-1811 maps to 988-2012 µs
            us_value = int(988 + (value * 1024 / 2047))
            channels.append(us_value)
        
        self.channels = channels
        return True
    
    def read_frame(self):
        """Read and parse a CRSF frame"""
        # Look for sync byte
        sync = self.ser.read(1)
        if len(sync) == 0:
            return False
        
        if sync[0] != self.CRSF_SYNC_BYTE:
            return False
        
        # Read frame length
        length_byte = self.ser.read(1)
        if len(length_byte) == 0:
            return False
        
        frame_length = length_byte[0]
        
        # Sanity check
        if frame_length > 64 or frame_length < 2:
            self.error_count += 1
            return False
        
        # Read rest of frame (type + payload + crc)
        frame_data = self.ser.read(frame_length)
        if len(frame_data) < frame_length:
            return False
        
        # Extract frame type, payload, and CRC
        frame_type = frame_data[0]
        payload = frame_data[1:-1]
        received_crc = frame_data[-1]
        
        # Verify CRC
        crc_data = bytes([frame_length]) + bytes([frame_type]) + payload
        calculated_crc = self.crc8_dvb_s2(crc_data)
        
        if calculated_crc != received_crc:
            self.error_count += 1
            return False
        
        # Parse RC channels packet
        if frame_type == self.CRSF_FRAMETYPE_RC_CHANNELS:
            if self.parse_rc_channels(payload):
                self.frame_count += 1
                return True
        
        return False
    
    def create_bar(self, value, width=40):
        """Create ASCII bar for channel value (988-2012 µs)"""
        normalized = (value - 988) / (2012 - 988)
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
        print("EdgeTX CRSF Channel Monitor")
        print("=" * 80)
        print(f"Port: {self.port} @ {self.baudrate} baud")
        print(f"Frames: {self.frame_count} | Errors: {self.error_count}")
        print("=" * 80)
        print()
        
        if self.frame_count == 0:
            print("⚠ Waiting for CRSF data...")
            print()
            print("Configuration check:")
            print("  1. Internal RF set to CRSF? ✓ (you mentioned this is set)")
            print("  2. Try setting AUX1 to 'Telem Mirror'")
            print("  3. Move sticks to generate data")
            print()
            print("If no data appears:")
            print("  - EdgeTX may not output CRSF on USB in your configuration")
            print("  - We may need to use External RF instead of Internal RF")
            print("  - Or switch back to USB Joystick mode")
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
        print("Press Ctrl+C to exit")
    
    def run(self):
        """Main monitoring loop"""
        last_display = time.time()
        
        try:
            print("Starting CRSF monitor...")
            print("Move your sticks to generate channel data...")
            print()
            
            while True:
                # Try to read frames
                self.read_frame()
                
                # Update display at 10Hz
                if time.time() - last_display > 0.1:
                    self.display()
                    last_display = time.time()
                    
        except KeyboardInterrupt:
            print("\n\nMonitor stopped.")
            self.ser.close()

def main():
    # Try different configurations
    configs = [
        ('COM3', 921600),   # Your reported baudrate
        ('COM3', 400000),   # Standard CRSF
        ('COM3', 420000),   # Alternative CRSF
    ]
    
    print("=" * 80)
    print("CRSF Channel Monitor - Testing configurations")
    print("=" * 80)
    print()
    
    for port, baud in configs:
        print(f"Trying {port} @ {baud} baud...")
        try:
            ser = serial.Serial(port, baud, timeout=1)
            
            # Quick test for data
            time.sleep(0.5)
            if ser.in_waiting > 0:
                print(f"  ✓ Data detected at {baud}!")
                ser.close()
                print()
                print(f"Starting monitor with {port} @ {baud}...")
                print()
                time.sleep(1)
                
                monitor = CRSFMonitor(port, baud)
                monitor.run()
                return
            else:
                print(f"  ✗ No data at {baud}")
                ser.close()
        except:
            print(f"  ✗ Cannot open at {baud}")
    
    print()
    print("=" * 80)
    print("No CRSF data found at any baudrate.")
    print()
    print("Starting monitor anyway at 921600 baud...")
    print("(Will wait for data to appear)")
    print("=" * 80)
    print()
    time.sleep(2)
    
    monitor = CRSFMonitor('COM3', 921600)
    monitor.run()

if __name__ == "__main__":
    main()
import serial
import time
import os
import sys

class MixedProtocolMonitor:
    """Monitor that handles multiple RC protocols"""
    
    # Protocol sync bytes
    CRSF_SYNC = 0xC8
    SBUS_SYNC = 0x0F
    FRSKY_SYNC = 0x7E
    
    def __init__(self, port='COM4', baudrate=None):
        self.port = port
        self.baudrate = baudrate
        self.channels = [1500] * 16
        self.frame_count = 0
        self.protocol_detected = None
        self.buffer = bytearray()
        
        if baudrate is None:
            # Auto-detect
            self.baudrate = self.auto_detect_baudrate()
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.01)
            print(f"✓ Opened {self.port} at {self.baudrate} baud")
        except serial.SerialException as e:
            print(f"✗ Error: {e}")
            sys.exit(1)
    
    def auto_detect_baudrate(self):
        """Find baudrate with data"""
        baudrates = [4800, 9600, 19200, 57600, 100000, 115200, 400000, 420000]
        
        print("Auto-detecting baudrate...")
        for baud in baudrates:
            try:
                ser = serial.Serial(self.port, baud, timeout=0.5)
                time.sleep(0.5)
                if ser.in_waiting > 0:
                    print(f"✓ Found data at {baud} baud")
                    ser.close()
                    return baud
                ser.close()
            except:
                pass
        
        print("Using default: 100000 baud (S.Bus standard)")
        return 100000
    
    def parse_sbus(self, data):
        """Parse S.Bus frame (25 bytes)"""
        if len(data) < 25:
            return False
        
        if data[0] != 0x0F:  # S.Bus start byte
            return False
        
        # S.Bus packs 16 channels into 11-bit values (22 bytes)
        channels = []
        bit_offset = 8  # Skip start byte
        
        for i in range(16):
            value = 0
            for bit in range(11):
                byte_idx = (bit_offset + bit) // 8
                bit_idx = (bit_offset + bit) % 8
                if byte_idx < len(data) and data[byte_idx] & (1 << bit_idx):
                    value |= (1 << bit)
            
            bit_offset += 11
            # Convert S.Bus (0-2047) to microseconds (988-2012)
            us = int(988 + (value * 1024 / 2047))
            channels.append(us)
        
        self.channels = channels
        self.protocol_detected = "S.Bus"
        return True
    
    def parse_crsf(self, data):
        """Parse CRSF frame"""
        if len(data) < 4:
            return False
        
        if data[0] != self.CRSF_SYNC:
            return False
        
        frame_len = data[1]
        
        if len(data) < frame_len + 2:
            return False
        
        frame_type = data[2]
        
        # RC Channels packet (0x16)
        if frame_type == 0x16 and frame_len >= 24:
            payload = data[3:3+22]
            
            # Parse 16 channels (11-bit each, packed)
            channels = []
            bit_index = 0
            
            for i in range(16):
                value = 0
                for bit in range(11):
                    byte_idx = bit_index // 8
                    bit_offset = bit_index % 8
                    if byte_idx < len(payload) and payload[byte_idx] & (1 << bit_offset):
                        value |= (1 << bit)
                    bit_index += 1
                
                # Convert to microseconds
                us = int(988 + (value * 1024 / 2047))
                channels.append(us)
            
            self.channels = channels
            self.protocol_detected = "CRSF"
            return True
        
        return False
    
    def process_data(self):
        """Process incoming data and try to parse frames"""
        if self.ser.in_waiting > 0:
            new_data = self.ser.read(self.ser.in_waiting)
            self.buffer.extend(new_data)
            
            # Try to find and parse frames
            while len(self.buffer) >= 25:
                                # Try CRSF (starts with 0xC8)
                if self.buffer[0] == self.CRSF_SYNC and len(self.buffer) >= 4:
                    frame_len = self.buffer[1]
                    if len(self.buffer) >= frame_len + 2:
                        if self.parse_crsf(self.buffer[:frame_len + 2]):
                            self.frame_count += 1
                            self.buffer = self.buffer[frame_len + 2:]
                            continue
             
                # Try S.Bus (starts with 0x0F, 25 bytes)
                if self.buffer[0] == 0x0F and len(self.buffer) >= 25:
                    if self.parse_sbus(self.buffer[:25]):
                        self.frame_count += 1
                        self.buffer = self.buffer[25:]
                        continue   
                # No valid frame found, remove first byte
                self.buffer.pop(0)
    
    def create_bar(self, value, width=40):
        """Create ASCII bar"""
        normalized = (value - 988) / (2012 - 988)
        normalized = max(0, min(1, normalized))
        filled = int(normalized * width)
        return '█' * filled + '░' * (width - filled)
    
    def value_to_percent(self, value):
        """Convert to percentage"""
        return int(((value - 1500) / 512) * 100)
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display(self):
        """Display channels"""
        self.clear_screen()
        
        print("=" * 80)
        print("EdgeTX Channel Monitor - Multi-Protocol")
        print("=" * 80)
        print(f"Port: {self.port} @ {self.baudrate} baud")
        print(f"Protocol: {self.protocol_detected or 'Detecting...'}")
        print(f"Frames: {self.frame_count}")
        print("=" * 80)
        print()
        
        if self.frame_count == 0:
            print("⚠ Waiting for channel data...")
            print("Move your sticks to generate frames!")
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
        """Main loop"""
        last_display = time.time()
        
        print("Starting monitor...")
        print("Waiting for data...")
        print()
        
        try:
            while True:
                self.process_data()
                
                if time.time() - last_display > 0.1:
                    self.display()
                    last_display = time.time()
        
        except KeyboardInterrupt:
            print("\n\nStopped.")
            self.ser.close()

def main():
    print()
    print("=" * 80)
    print("MULTI-PROTOCOL CHANNEL MONITOR")
    print("=" * 80)
    print()
    port = 'COM4'  # Change to your port
    print()
    monitor = MixedProtocolMonitor(port)
    monitor.run()

if __name__ == "__main__":
    main()
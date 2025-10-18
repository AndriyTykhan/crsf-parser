import serial
import serial.tools.list_ports
import time
import sys

def list_com_ports():
    """List all available COM ports"""
    ports = serial.tools.list_ports.comports()
    print("=" * 60)
    print("Available COM Ports:")
    print("=" * 60)
    for port in ports:
        print(f"  {port.device} - {port.description}")
    print()

def try_baudrate(port, baudrate, duration=3):
    """Try a specific baudrate and return if data was received"""
    try:
        ser = serial.Serial(port, baudrate, timeout=0.1)
        print(f"  Trying {baudrate} baud... ", end='', flush=True)
        
        start_time = time.time()
        bytes_received = 0
        
        while time.time() - start_time < duration:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                bytes_received += len(data)
        
        ser.close()
        
        if bytes_received > 0:
            print(f"✓ FOUND DATA! ({bytes_received} bytes)")
            return True
        else:
            print("✗ No data")
            return False
            
    except serial.SerialException as e:
        print(f"✗ Error: {e}")
        return False

def sniff_serial_data(port, baudrate, timeout=2):
    """
    Sniff data from serial port and display in multiple formats
    """
    print("=" * 60)
    print(f"Serial Data Sniffer - Monitoring {port} @ {baudrate} baud")
    print("=" * 60)
    print("Move your sticks and switches to generate channel data!")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f"✓ Successfully opened {port}")
        print()
        
        bytes_received = 0
        last_data_time = time.time()
        no_data_warning_shown = False
        
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                bytes_received += len(data)
                last_data_time = time.time()
                no_data_warning_shown = False
                
                # Display in multiple formats
                print(f"[{time.strftime('%H:%M:%S')}] Received {len(data)} bytes:")
                
                # Hex format (first 32 bytes)
                hex_str = ' '.join([f'{b:02X}' for b in data[:32]])
                if len(data) > 32:
                    hex_str += " ..."
                print(f"  HEX: {hex_str}")
                
                # Check for CRSF sync byte (0xC8)
                if 0xC8 in data:
                    print(f"  ✓ CRSF sync byte detected (0xC8)!")
                
                # ASCII format (printable characters only)
                ascii_str = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data[:32]])
                if len(data) > 32:
                    ascii_str += "..."
                print(f"  ASCII: {ascii_str}")
                
                print(f"  Total bytes: {bytes_received}")
                print()
            
            # Check if no data for a while
            if time.time() - last_data_time > 5 and bytes_received == 0 and not no_data_warning_shown:
                print("⚠ No data received yet.")
                print()
                print("EdgeTX Configuration Needed:")
                print("  1. Go to MODEL SETUP on your TX12")
                print("  2. Set External RF Mode to 'CRSF' or 'OFF' with CRSF")
                print("  3. Or try setting Internal RF to a CRSF-compatible mode")
                print()
                print("Still waiting for data...")
                print()
                no_data_warning_shown = True
                last_data_time = time.time()
            
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nSniffer stopped.")
        print(f"Total bytes received: {bytes_received}")
        ser.close()

def auto_detect_baudrate(port):
    """Try common baudrates to find which one has data"""
    print("=" * 60)
    print("Auto-detecting baudrate...")
    print("=" * 60)
    
    # Common baudrates for RC protocols
    baudrates = [
        400000,  # CRSF standard - YOUR MODULE SETTING
        921600,  # High speed - TX12 setting
        420000,  # CRSF alternative
        115200,  # Common serial
        57600,   # Lower speed
        19200,   # Very low speed
    ]
    
    for baudrate in baudrates:
        if try_baudrate(port, baudrate):
            return baudrate
    
    print()
    print("✗ No data found at any common baudrate.")
    print()
    return None

def main():
    print()
    list_com_ports()
    
    port = 'COM3'
    
    print("Would you like to:")
    print("  1. Auto-detect baudrate (recommended)")
    print("  2. Use specific baudrate")
    print()
    
    # Auto-detect first
    print("Starting auto-detection...")
    print()
    detected_baud = auto_detect_baudrate(port)
    
    if detected_baud:
        print()
        print(f"✓ Data detected at {detected_baud} baud!")
        print()
        input("Press Enter to start monitoring with this baudrate...")
        sniff_serial_data(port, detected_baud)
    else:
        print()
        print("Trying default 400000 baud (CRSF standard)...")
        print()
        sniff_serial_data(port, 400000)

if __name__ == "__main__":
    main()
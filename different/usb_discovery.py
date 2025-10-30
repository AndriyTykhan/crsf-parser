import serial.tools.list_ports
import sys

def discover_usb_devices():
    """Discover all USB serial devices connected to the computer"""
    print("=" * 70)
    print("USB Device Discovery Tool")
    print("=" * 70)
    print()
    print("Scanning for USB devices...")
    print()
    
    # Get all COM ports
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("✗ No COM ports found!")
        print()
        print("Troubleshooting:")
        print("  1. Make sure your TX12 is connected via USB")
        print("  2. Check if TX12 is powered on")
        print("  3. Try a different USB cable")
        print("  4. Check Windows Device Manager")
        return []
    
    print(f"Found {len(ports)} COM port(s):")
    print()
    
    device_list = []
    
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port.device}")
        print(f"   Description: {port.description}")
        print(f"   Manufacturer: {port.manufacturer if port.manufacturer else 'Unknown'}")
        print(f"   Hardware ID: {port.hwid}")
        
        # Check if it's likely a TX12 or similar device
        is_radio = False
        keywords = ['CH340', 'CP210', 'FTDI', 'USB Serial', 'STM32', 'Virtual COM']
        
        description_lower = port.description.lower()
        for keyword in keywords:
            if keyword.lower() in description_lower:
                is_radio = True
                break
        
        if is_radio:
            print(f"   *** Likely RC Radio/Controller ***")
        
        print()
        
        device_list.append({
            'port': port.device,
            'description': port.description,
            'manufacturer': port.manufacturer,
            'hwid': port.hwid,
            'likely_radio': is_radio
        })
    
    print("=" * 70)
    
    return device_list

def test_device_communication(port_name):
    """Test if device responds at different baudrates"""
    import serial
    import time
    
    print()
    print("=" * 70)
    print(f"Testing communication on {port_name}")
    print("=" * 70)
    print()
    
    # Common baudrates for RC equipment
    baudrates = [
        9600,     # Very common
        19200,    # Common
        38400,    # Common
        57600,    # Common
        115200,   # Very common (CLI, debugging)
        400000,   # CRSF standard
        420000,   # CRSF alternative
        921600,   # High speed
    ]
    
    for baud in baudrates:
        print(f"Testing {baud:6d} baud... ", end='', flush=True)
        
        try:
            ser = serial.Serial(port_name, baud, timeout=1)
            time.sleep(0.5)  # Wait for device to respond
            
            # Check if any data is waiting
            bytes_available = ser.in_waiting

            print(f"✓ DATA FOUND! ({ser})")

            
            if bytes_available > 0:
                data = ser.read(bytes_available)
                # print(f"✓ DATA FOUND! ({bytes_available} bytes)")
                
                # Show sample of data
                hex_sample = ' '.join([f'{b:02X}' for b in data[:16]])
                print(f"     Sample: {hex_sample}")
            else:
                # Try sending a simple command (like newline) to wake it up
                ser.write(b'\r\n')
                time.sleep(0.3)
                
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    print(f"✓ RESPONSIVE! ({len(data)} bytes after prompt)")
                else:
                    print("✗ No response")
            
            ser.close()
            
        except Exception as e:
            print(f"✗ Error: {str(e)[:30]}")
    
    print()
    print("=" * 70)

def main():
    print()
    
    # Discover devices
    devices = discover_usb_devices()
    
    if not devices:
        print("\nNo devices found. Please connect your TX12 and try again.")
        return
    
    # Find likely radio devices
    radio_devices = [d for d in devices if d['likely_radio']]
    
    if radio_devices:
        print("\nMost likely device(s) for your TX12:")
        for d in radio_devices:
            print(f"  → {d['port']} - {d['description']}")
    
    print()
    print("=" * 70)
    print()
    
    # Ask user which port to test
    if len(devices) == 1:
        port_to_test = devices[0]['port']
        print(f"Only one device found: {port_to_test}")
        print()
        response = input("Test this port? (y/n): ").strip().lower()
        
        if response == 'y':
            test_device_communication(port_to_test)
    else:
        print("Which port would you like to test?")
        for i, d in enumerate(devices, 1):
            print(f"  {i}. {d['port']}")
        
        print()
        try:
            choice = int(input("Enter number (or 0 to skip): "))
            
            if choice > 0 and choice <= len(devices):
                port_to_test = devices[choice - 1]['port']
                test_device_communication(port_to_test)
        except:
            print("Invalid choice. Exiting.")
    
    print()
    print("Discovery complete!")
    print()

if __name__ == "__main__":
    main()
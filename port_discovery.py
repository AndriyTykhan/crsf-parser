import serial
import time
import sys

def test_command(ser, command, delay=0.5):
    """Send command and get response"""
    ser.reset_input_buffer()
    ser.write(f"{command}\r\n".encode())
    time.sleep(delay)
    
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.05)
    
    return response.strip()

def main():
    port = 'COM3'
    baudrate = 115200
    
    print("=" * 70)
    print("EdgeTX Serial Port Type Discovery")
    print("=" * 70)
    print()
    
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"✓ Connected to {port}")
        time.sleep(1)
        ser.reset_input_buffer()
        
        print()
        print("First, let's check the command usage...")
        print("=" * 70)
        
        # Try command alone to see usage
        print("\nTrying 'serialpassthrough' without parameters:")
        response = test_command(ser, "serialpassthrough", 1)
        print(response)
        print()
        
        if "usage" in response.lower() or "syntax" in response.lower():
            print("✓ Found usage information above!")
            print()
        
        print()
        print("Testing serialpassthrough with different port types...")
        print("=" * 70)
        print()
        
        # Common port type names in EdgeTX
        port_types = [
            'aux1', 'aux2', 
            'main', 'sport', 
            'vcp', 'telemetry',
            'ext', 'external',
            'module', 'radio',
            'smartport', 'fport',
            'sbus', 'ibus',
            'serial1', 'serial2',
            'uart1', 'uart2', 'uart3',
            'usart1', 'usart2', 'usart3'
        ]
        
        successful_types = []
        
        for ptype in port_types:
            cmd = f"serialpassthrough {ptype} 0 400000"
            print(f"Testing: {ptype:15s} ", end='', flush=True)
            
            response = test_command(ser, cmd, 0.3)
            
            # Check if error message contains "invalid port type"
            if "invalid port type" in response.lower():
                print("✗ Invalid")
            elif "error" in response.lower():
                print(f"✗ Error: {response[:50]}")
            elif len(response) == 0:
                print("✓ ACCEPTED! (no error - passthrough likely active)")
                successful_types.append(ptype)
                # Reset connection
                ser.close()
                time.sleep(1)
                ser = serial.Serial(port, baudrate, timeout=1)
                time.sleep(0.5)
            else:
                print(f"? Response: {response[:50]}")
                if "invalid" not in response.lower():
                    successful_types.append(ptype)
        
        print()
        print("=" * 70)
        
        if successful_types:
            print("✓ Found working port type(s):")
            for ptype in successful_types:
                print(f"  - {ptype}")
            print()
            print("To enable passthrough, use:")
            print(f"  serialpassthrough {successful_types[0]} 0 400000")
        else:
            print("✗ No valid port types found")
            print()
            print("Let's try getting more info...")
            print()
            
            # Try to get help
            print("Trying 'serialpassthrough' alone (might show usage):")
            response = test_command(ser, "serialpassthrough", 1)
            print(response)
            print()
            
            # Try set command
            print("Checking 'set' command for serial port info:")
            response = test_command(ser, "set", 1)
            print(response)
        
        print()
        print("=" * 70)
        ser.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
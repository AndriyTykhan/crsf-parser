import serial
import time
import sys

def send_cli_command(ser, command):
    """Send a command to CLI and read response"""
    print(f"\nSending: {command}")
    ser.write(f"{command}\r\n".encode())
    time.sleep(0.5)
    
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        time.sleep(0.1)
    
    if response:
        print(f"Response:\n{response}")
    else:
        print("(no response)")
    
    return response

def main():
    port = 'COM4'
    baudrate = 115200  # Common CLI baudrate
    
    print("=" * 70)
    print("EdgeTX CLI Passthrough Tester")
    print("=" * 70)
    print()
    print("Make sure:")
    print("  1. USB Mode is set to CLI")
    print("  2. TX12 is connected via USB")
    print("=" * 70)
    print()
    
    try:
        print(f"Opening {port} at {baudrate} baud...")
        ser = serial.Serial(port, baudrate, timeout=1)
        print("✓ Connected")
        time.sleep(1)
        
        # Clear any existing data
        ser.reset_input_buffer()
        
        print()
        print("Testing CLI commands...")
        print("=" * 70)
        
        # Try common commands
        commands = [
            "",  # Empty line to wake up CLI
            "help",
            "serial",
            "passthrough",
            "crsf",
            "status",
            "tasks",
            "version"
        ]
        
        for cmd in commands:
            send_cli_command(ser, cmd)
        
        print()
        print("=" * 70)
        print("FOUND: serialpassthrough command!")
        print("=" * 70)
        print()
        print("Let's get more info about this command...")
        
        # Get help for serialpassthrough
        send_cli_command(ser, "help serialpassthrough")
        
        print()
        print("=" * 70)
        print("Now let's try to enable CRSF passthrough...")
        print("=" * 70)
        
        # Common passthrough configurations for CRSF/ELRS
        passthrough_configs = [
            "serialpassthrough 0 0 400000",  # Port 0, 400k baud (CRSF)
            "serialpassthrough 1 0 400000",  # Port 1, 400k baud
            "serialpassthrough 0 1 400000",  # Port 0, subport 1
            "serialpassthrough uart 0 400000",  # UART type
            "serialpassthrough usb 0 400000",  # USB type
        ]
        
        print()
        print("Trying different passthrough configurations...")
        print("(If one works, the CLI will stop responding - that's good!)")
        print()
        
        for config in passthrough_configs:
            print(f"\nTrying: {config}")
            ser.write(f"{config}\r\n".encode())
            time.sleep(1)
            
            # Check for response
            response = ""
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                print(f"Response: {response}")
            else:
                print("(no response - passthrough might be active!)")
                print()
                print("✓ If passthrough is now active:")
                print("  1. Exit this script (Ctrl+C)")
                print("  2. Run: python crsf_monitor.py")
                print("  3. You should see channel data!")
                print()
                print("To exit passthrough mode: Unplug USB or reboot TX12")
                print()
                input("Press Enter to continue testing other configs...")
        
        print()
        print("=" * 70)
        print("CLI Test Complete")
        print("=" * 70)
        print()
        print("Look for any 'passthrough' or 'serial' commands in the help output above.")
        print()
        
        # Interactive mode
        print("Entering interactive mode. Type commands or 'quit' to exit:")
        print("-" * 70)
        
        while True:
            try:
                cmd = input("CLI> ").strip()
                
                if cmd.lower() in ['quit', 'exit', 'q']:
                    break
                
                if cmd:
                    send_cli_command(ser, cmd)
                    
            except KeyboardInterrupt:
                break
        
        ser.close()
        print("\nClosed connection.")
        
    except serial.SerialException as e:
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure USB Mode is set to CLI")
        print("  2. Try unplugging and replugging USB")
        print("  3. Check Device Manager for the correct COM port")
        sys.exit(1)

if __name__ == "__main__":
    main()
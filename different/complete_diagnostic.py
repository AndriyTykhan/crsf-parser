import serial
import time
import sys

def test_raw_data(port='COM3', baudrate=400000, duration=5):
    """Test if ANY data is coming through at all"""
    print("=" * 70)
    print(f"Step 1: Testing for RAW data at {baudrate} baud")
    print("=" * 70)
    
    try:
        ser = serial.Serial(port, baudrate, timeout=0.1)
        print(f"✓ Opened {port}")
        print(f"Listening for {duration} seconds...")
        print("Move your sticks now!")
        print()
        
        start_time = time.time()
        total_bytes = 0
        data_chunks = []
        
        while time.time() - start_time < duration:
            if ser.in_waiting > 0:
                chunk = ser.read(ser.in_waiting)
                total_bytes += len(chunk)
                data_chunks.append(chunk)
                
                # Show first few bytes
                if len(data_chunks) <= 3:
                    hex_str = ' '.join([f'{b:02X}' for b in chunk[:20]])
                    print(f"  Received {len(chunk)} bytes: {hex_str}...")
            
            time.sleep(0.01)
        
        ser.close()
        
        print()
        print(f"Total bytes received: {total_bytes}")
        
        if total_bytes == 0:
            print("✗ NO DATA RECEIVED")
            return False, None
        else:
            print("✓ DATA IS FLOWING!")
            
            # Check for CRSF sync byte
            all_data = b''.join(data_chunks)
            if 0xC8 in all_data:
                print("✓ Found CRSF sync byte (0xC8)!")
            else:
                print("⚠ No CRSF sync byte found - might be wrong protocol")
            
            return True, all_data
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, None

def test_multiple_baudrates(port='COM3'):
    """Test multiple baudrates to find the right one"""
    print()
    print("=" * 70)
    print("Step 2: Testing multiple baudrates")
    print("=" * 70)
    
    baudrates = [400000, 420000, 115200, 921600, 57600]
    
    for baud in baudrates:
        print(f"\nTesting {baud} baud... ", end='', flush=True)
        
        try:
            ser = serial.Serial(port, baud, timeout=0.5)
            time.sleep(1)  # Wait a bit
            
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"✓ FOUND DATA! ({len(data)} bytes)")
                
                # Show sample
                hex_str = ' '.join([f'{b:02X}' for b in data[:16]])
                print(f"  Sample: {hex_str}")
                ser.close()
                return baud
            else:
                print("✗ No data")
            
            ser.close()
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return None

def check_passthrough_status():
    """Check if passthrough is likely active"""
    print()
    print("=" * 70)
    print("Step 3: Passthrough Status Check")
    print("=" * 70)
    
    print()
    print("When passthrough is ACTIVE:")
    print("  - CLI commands won't work")
    print("  - Serial port streams CRSF data")
    print("  - Moving sticks generates data")
    print()
    print("When passthrough is NOT active:")
    print("  - CLI responds to commands")
    print("  - No CRSF data flows")
    print()
    
    response = input("Can you still type CLI commands on your TX12? (y/n): ").strip().lower()
    
    if response == 'y':
        print()
        print("⚠ Passthrough is NOT active!")
        print()
        print("You need to run: serialpassthrough rfmod 0 400000")
        return False
    else:
        print()
        print("✓ Passthrough seems to be active")
        return True

def main():
    print()
    print("=" * 70)
    print("COMPLETE CRSF DIAGNOSTIC TOOL")
    print("=" * 70)
    print()
    print("This will help us figure out why no data is being received.")
    print()
    
    # Step 0: Check basic setup
    print("Current Setup Check:")
    print("  1. TX12 connected via USB?")
    print("  2. External ELRS module plugged in and powered?")
    print("  3. Model Setup > External RF > Mode: CRSF?")
    print("  4. USB Mode: CLI?")
    print()
    
    response = input("Is all of the above confirmed? (y/n): ").strip().lower()
    if response != 'y':
        print("\nPlease verify your setup and run again.")
        return
    
    print()
    
    # Check if passthrough is active
    if not check_passthrough_status():
        print()
        print("=" * 70)
        print("ACTION REQUIRED:")
        print("=" * 70)
        print()
        print("1. Keep this program running")
        print("2. Open another terminal/command prompt")
        print("3. Run: python cli_tester.py")
        print("4. Type: serialpassthrough rfmod 0 400000")
        print("5. Come back to this window")
        print()
        input("Press Enter once you've enabled passthrough...")
    
    print()
    
    # Test for raw data at 400k
    has_data, raw_data = test_raw_data('COM3', 400000, 5)
    
    if not has_data:
        # Try other baudrates
        working_baud = test_multiple_baudrates('COM3')
        
        if working_baud:
            print()
            print(f"✓ Found working baudrate: {working_baud}")
            print(f"Try running monitor with: {working_baud} baud")
        else:
            print()
            print("=" * 70)
            print("DIAGNOSIS: NO DATA AT ANY BAUDRATE")
            print("=" * 70)
            print()
            print("Possible issues:")
            print("  1. Passthrough not actually active")
            print("  2. Wrong port (not COM3)")
            print("  3. CRSF not configured to output data")
            print("  4. Module not communicating with TX12")
            print()
            print("Troubleshooting:")
            print("  - Verify the 26Hz status still shows in Model Setup")
            print("  - Try unplugging and replugging the ELRS module")
            print("  - Reboot TX12 and try passthrough again")
            print("  - Check Windows Device Manager for COM port number")
    else:
        print()
        print("=" * 70)
        print("DIAGNOSIS: DATA IS FLOWING!")
        print("=" * 70)
        print()
        print("The issue might be with parsing, not data reception.")
        print("Let's try the monitor now with better debugging.")
    
    print()
    print("=" * 70)
    print("Diagnostic complete")
    print("=" * 70)

if __name__ == "__main__":
    main()
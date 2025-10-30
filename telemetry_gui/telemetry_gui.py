#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import serial
import threading
import time
import argparse
from collections import deque

# Import from your original script (assuming it's named python_parser.py)
# If your file has a different name, change this import
from python_parser import (
    PacketsTypes, crsf_validate_frame, signed_byte,
    channelsCrsfToChannelsPacket
)

class TelemetryGUI:
    def __init__(self, root, serial_port, baud_rate, tx_enabled):
        self.root = root
        self.root.title("ELRS Telemetry Monitor")
        self.root.geometry("800x600")
        
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.tx_enabled = tx_enabled
        
        # Telemetry data storage
        self.data = {
            'attitude': {'pitch': 0, 'roll': 0, 'yaw': 0},
            'flight_mode': 'UNKNOWN',
            'link_stats': {'rssi1': 0, 'rssi2': 0, 'lq': 0, 'mode': 0},
            'battery': {'voltage': 0, 'current': 0, 'mah': 0, 'percent': 0},
            'gps': {'lat': 0, 'lon': 0, 'speed': 0, 'heading': 0, 'altitude': 0, 'sats': 0},
            'vario': {'vspeed': 0}
        }
        
        self.rssi_history = deque(maxlen=100)
        self.lq_history = deque(maxlen=100)
        
        self.running = True
        self.setup_ui()
        
        # Start serial reading thread
        self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.serial_thread.start()
        
        # Start UI update loop
        self.update_ui()
        
    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Flight Mode (top, spanning both columns)
        mode_frame = ttk.LabelFrame(main_frame, text="Flight Mode", padding="10")
        mode_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.flight_mode_label = ttk.Label(mode_frame, text="UNKNOWN", font=("Arial", 24, "bold"))
        self.flight_mode_label.pack()
        
        # Left Column - Attitude
        attitude_frame = ttk.LabelFrame(main_frame, text="Attitude", padding="10")
        attitude_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        ttk.Label(attitude_frame, text="Pitch:").grid(row=0, column=0, sticky=tk.W)
        self.pitch_label = ttk.Label(attitude_frame, text="0.00 rad", font=("Arial", 12))
        self.pitch_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(attitude_frame, text="Roll:").grid(row=1, column=0, sticky=tk.W)
        self.roll_label = ttk.Label(attitude_frame, text="0.00 rad", font=("Arial", 12))
        self.roll_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(attitude_frame, text="Yaw:").grid(row=2, column=0, sticky=tk.W)
        self.yaw_label = ttk.Label(attitude_frame, text="0.00 rad", font=("Arial", 12))
        self.yaw_label.grid(row=2, column=1, sticky=tk.W)
        
        # Right Column - Battery
        battery_frame = ttk.LabelFrame(main_frame, text="Battery", padding="10")
        battery_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        ttk.Label(battery_frame, text="Voltage:").grid(row=0, column=0, sticky=tk.W)
        self.voltage_label = ttk.Label(battery_frame, text="0.00 V", font=("Arial", 12))
        self.voltage_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(battery_frame, text="Current:").grid(row=1, column=0, sticky=tk.W)
        self.current_label = ttk.Label(battery_frame, text="0.0 A", font=("Arial", 12))
        self.current_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(battery_frame, text="Capacity:").grid(row=2, column=0, sticky=tk.W)
        self.capacity_label = ttk.Label(battery_frame, text="0 mAh", font=("Arial", 12))
        self.capacity_label.grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(battery_frame, text="Remaining:").grid(row=3, column=0, sticky=tk.W)
        self.percent_label = ttk.Label(battery_frame, text="0 %", font=("Arial", 12))
        self.percent_label.grid(row=3, column=1, sticky=tk.W)
        
        # Link Statistics
        link_frame = ttk.LabelFrame(main_frame, text="Link Statistics", padding="10")
        link_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        link_frame.columnconfigure(1, weight=1)
        link_frame.columnconfigure(3, weight=1)
        
        ttk.Label(link_frame, text="RSSI:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.rssi_label = ttk.Label(link_frame, text="0 dBm", font=("Arial", 12))
        self.rssi_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(link_frame, text="Link Quality:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.lq_label = ttk.Label(link_frame, text="0", font=("Arial", 12))
        self.lq_label.grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(link_frame, text="Mode:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.mode_label = ttk.Label(link_frame, text="0", font=("Arial", 12))
        self.mode_label.grid(row=1, column=1, sticky=tk.W)
        
        # GPS
        gps_frame = ttk.LabelFrame(main_frame, text="GPS", padding="10")
        gps_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        gps_frame.columnconfigure(1, weight=1)
        gps_frame.columnconfigure(3, weight=1)
        
        ttk.Label(gps_frame, text="Latitude:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.lat_label = ttk.Label(gps_frame, text="0.0000000", font=("Arial", 10))
        self.lat_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(gps_frame, text="Longitude:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.lon_label = ttk.Label(gps_frame, text="0.0000000", font=("Arial", 10))
        self.lon_label.grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(gps_frame, text="Speed:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.speed_label = ttk.Label(gps_frame, text="0.0 m/s", font=("Arial", 10))
        self.speed_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(gps_frame, text="Altitude:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.alt_label = ttk.Label(gps_frame, text="0 m", font=("Arial", 10))
        self.alt_label.grid(row=1, column=3, sticky=tk.W)
        
        ttk.Label(gps_frame, text="Satellites:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.sats_label = ttk.Label(gps_frame, text="0", font=("Arial", 10))
        self.sats_label.grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(gps_frame, text="Heading:").grid(row=2, column=2, sticky=tk.W, padx=5)
        self.heading_label = ttk.Label(gps_frame, text="0.0°", font=("Arial", 10))
        self.heading_label.grid(row=2, column=3, sticky=tk.W)
        
        # Vario
        vario_frame = ttk.LabelFrame(main_frame, text="Variometer", padding="10")
        vario_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(vario_frame, text="Vertical Speed:").grid(row=0, column=0, sticky=tk.W)
        self.vspeed_label = ttk.Label(vario_frame, text="0.0 m/s", font=("Arial", 12))
        self.vspeed_label.grid(row=0, column=1, sticky=tk.W)
        
    def handle_packet(self, ptype, data):
        """Process CRSF packets and update data dictionary"""
        if ptype == PacketsTypes.LINK_STATISTICS:
            rssi1 = signed_byte(data[3])
            rssi2 = signed_byte(data[4])
            lq = data[5]
            mode = data[8]
            self.data['link_stats'] = {
                'rssi1': rssi1, 'rssi2': rssi2, 'lq': lq, 'mode': mode
            }
            self.rssi_history.append(rssi1)
            self.lq_history.append(lq)
            
        elif ptype == PacketsTypes.ATTITUDE:
            pitch = int.from_bytes(data[3:5], byteorder='big', signed=True) / 10000.0
            roll = int.from_bytes(data[5:7], byteorder='big', signed=True) / 10000.0
            yaw = int.from_bytes(data[7:9], byteorder='big', signed=True) / 10000.0
            self.data['attitude'] = {'pitch': pitch, 'roll': roll, 'yaw': yaw}
            
        elif ptype == PacketsTypes.FLIGHT_MODE:
            packet = ''.join(map(chr, data[3:-2])).split('\x00')[0].strip()
            self.data['flight_mode'] = packet
            
        elif ptype == PacketsTypes.BATTERY_SENSOR:
            vbat = int.from_bytes(data[3:5], byteorder='big', signed=True) / 10.0
            curr = int.from_bytes(data[5:7], byteorder='big', signed=True) / 10.0
            mah = data[7] << 16 | data[8] << 7 | data[9]
            pct = data[10]
            self.data['battery'] = {
                'voltage': vbat, 'current': curr, 'mah': mah, 'percent': pct
            }
            
        elif ptype == PacketsTypes.GPS:
            lat = int.from_bytes(data[3:7], byteorder='big', signed=True) / 1e7
            lon = int.from_bytes(data[7:11], byteorder='big', signed=True) / 1e7
            gspd = int.from_bytes(data[11:13], byteorder='big', signed=True) / 36.0
            hdg = int.from_bytes(data[13:15], byteorder='big', signed=True) / 100.0
            alt = int.from_bytes(data[15:17], byteorder='big', signed=True) - 1000
            sats = data[17]
            self.data['gps'] = {
                'lat': lat, 'lon': lon, 'speed': gspd,
                'heading': hdg, 'altitude': alt, 'sats': sats
            }
            
        elif ptype == PacketsTypes.VARIO:
            vspd = int.from_bytes(data[3:5], byteorder='big', signed=True) / 10.0
            self.data['vario'] = {'vspeed': vspd}
    
    def read_serial(self):
        """Background thread for reading serial data"""
        try:
            with serial.Serial(self.serial_port, self.baud_rate, timeout=2) as ser:
                input_buffer = bytearray()
                while self.running:
                    if ser.in_waiting > 0:
                        input_buffer.extend(ser.read(ser.in_waiting))
                    else:
                        if self.tx_enabled:
                            ser.write(channelsCrsfToChannelsPacket([992 for ch in range(16)]))
                        time.sleep(0.020)
                    
                    while len(input_buffer) > 2:
                        expected_len = input_buffer[1] + 2
                        if expected_len > 64 or expected_len < 4:
                            input_buffer = bytearray()
                        elif len(input_buffer) >= expected_len:
                            single = input_buffer[:expected_len]
                            input_buffer = input_buffer[expected_len:]
                            
                            if crsf_validate_frame(single):
                                self.handle_packet(single[2], single)
                        else:
                            break
        except Exception as e:
            print(f"Serial error: {e}")
    
    def update_ui(self):
        """Update UI with current telemetry data"""
        # Attitude
        att = self.data['attitude']
        self.pitch_label.config(text=f"{att['pitch']:0.2f} rad")
        self.roll_label.config(text=f"{att['roll']:0.2f} rad")
        self.yaw_label.config(text=f"{att['yaw']:0.2f} rad")
        
        # Battery
        bat = self.data['battery']
        self.voltage_label.config(text=f"{bat['voltage']:0.2f} V")
        self.current_label.config(text=f"{bat['current']:0.1f} A")
        self.capacity_label.config(text=f"{bat['mah']} mAh")
        self.percent_label.config(text=f"{bat['percent']} %")
        
        # Link Stats
        link = self.data['link_stats']
        self.rssi_label.config(text=f"{link['rssi1']} dBm")
        self.lq_label.config(text=f"{link['lq']}")
        self.mode_label.config(text=f"{link['mode']}")
        
        # Flight Mode
        self.flight_mode_label.config(text=self.data['flight_mode'])
        
        # GPS
        gps = self.data['gps']
        self.lat_label.config(text=f"{gps['lat']:.7f}")
        self.lon_label.config(text=f"{gps['lon']:.7f}")
        self.speed_label.config(text=f"{gps['speed']:.1f} m/s")
        self.alt_label.config(text=f"{gps['altitude']} m")
        self.sats_label.config(text=f"{gps['sats']}")
        self.heading_label.config(text=f"{gps['heading']:.1f}°")
        
        # Vario
        self.vspeed_label.config(text=f"{self.data['vario']['vspeed']:.1f} m/s")
        
        # Schedule next update
        self.root.after(50, self.update_ui)  # Update every 50ms
    
    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', '--port', default='COM4', required=False)
    parser.add_argument('-b', '--baud', default=921600, required=False)
    parser.add_argument('-t', '--tx', required=False, default=False, action='store_true',
                        help='Enable sending CHANNELS_PACKED every 20ms (all channels 1500us)')
    args = parser.parse_args()
    
    root = tk.Tk()
    app = TelemetryGUI(root, args.port, args.baud, args.tx)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
import pygame
import sys
import os
import time

class EdgeTXMonitor:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        # Check for joysticks
        if pygame.joystick.get_count() == 0:
            print("Error: No joystick detected!")
            sys.exit(1)
        
        # Initialize the first joystick (TX12)
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        
        self.num_axes = self.joystick.get_numaxes()
        self.num_buttons = self.joystick.get_numbuttons()
        
        # Channel names (you can customize these)
        self.channel_names = [
            "CH1 (Ail)", "CH2 (Ele)", "CH3 (Thr)", "CH4 (Rud)",
            "CH5", "CH6", "CH7", "CH8",
            "CH9", "CH10", "CH11", "CH12",
            "CH13", "CH14", "CH15", "CH16"
        ]
        
        self.running = True
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def create_bar(self, value, width=40):
        """Create an ASCII bar graph for a channel value
        value ranges from -1.0 to 1.0"""
        # Normalize to 0-1 range
        normalized = (value + 1.0) / 2.0
        filled = int(normalized * width)
        bar = '█' * filled + '░' * (width - filled)
        return bar
    
    def value_to_percent(self, value):
        """Convert -1.0 to 1.0 range to -100% to 100%"""
        return int(value * 100)
    
    def value_to_microseconds(self, value):
        """Convert -1.0 to 1.0 range to microseconds (1000-2000)"""
        return int(1500 + (value * 500))
    
    def display_header(self):
        """Display the monitor header"""
        print("=" * 80)
        print(f"EdgeTX Channel Monitor - {self.joystick.get_name()}")
        print("=" * 80)
        print(f"Monitoring {min(self.num_axes, 16)} channels | Press Ctrl+C to exit")
        print("=" * 80)
        print()
    
    def display_channels(self):
        """Display all channel values with bars"""
        pygame.event.pump()  # Process pygame events
        
        channels_to_show = min(self.num_axes, 16)
        
        for i in range(channels_to_show):
            value = self.joystick.get_axis(i)
            percent = self.value_to_percent(value)
            microseconds = self.value_to_microseconds(value)
            bar = self.create_bar(value)
            
            # Format: CH01 [Name      ] [Bar] -100% (1000µs)
            print(f"CH{i+1:02d} [{self.channel_names[i]:10s}] [{bar}] {percent:4d}% ({microseconds}µs)")
        
        print()
        print("Values update at ~10Hz | Move your sticks and switches!")
    
    def run(self):
        """Main monitoring loop"""
        try:
            while self.running:
                self.clear_screen()
                self.display_header()
                self.display_channels()
                time.sleep(0.1)  # 10Hz update rate
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
        finally:
            pygame.quit()
            print("Channel monitor closed.")

def main():
    monitor = EdgeTXMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
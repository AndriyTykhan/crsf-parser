import pygame
import sys

# Initialize pygame and joystick
pygame.init()
pygame.joystick.init()

# Check for connected joysticks
joystick_count = pygame.joystick.get_count()

print("=" * 60)
print("EdgeTX Controller Detection")
print("=" * 60)
print(f"\nFound {joystick_count} joystick(s) connected\n")

if joystick_count == 0:
    print("No joysticks detected!")
    print("\nTroubleshooting:")
    print("1. Make sure your TX12 is connected via USB")
    print("2. Check if it's powered on")
    print("3. In Windows, check Device Manager for game controllers")
    print("4. You may need to enable USB Joystick mode in EdgeTX")
    sys.exit(1)

# List all detected joysticks
for i in range(joystick_count):
    joystick = pygame.joystick.Joystick(i)
    joystick.init()
    
    print(f"Joystick {i}:")
    print(f"  Name: {joystick.get_name()}")
    print(f"  Number of Axes: {joystick.get_numaxes()}")
    print(f"  Number of Buttons: {joystick.get_numbuttons()}")
    print(f"  Number of Hats: {joystick.get_numhats()}")
    print()

print("=" * 60)
print("\nIf you see your TX12 listed above, you're ready to run")
print("the full channel monitor!")
print("=" * 60)

pygame.quit()
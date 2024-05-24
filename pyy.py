import pyautogui

# Wait a few seconds to give you time to move your mouse to the desired position
print("Move your mouse to the desired position within 5 seconds...")
pyautogui.sleep(15)

# Get the current position of the mouse cursor
x, y = pyautogui.position()
print(f"Current mouse position: ({x}, {y})")

import keyboard
import time
import sys

def on_hotkey():
    print("\n[SUCCESS] Hotkey 'alt+shift+g' detected!")

def main():
    print("--- ShiftLang Hotkey Debugger ---")
    print("This script checks if the 'keyboard' library can detect your hotkey.")
    print("1. Press 'alt+shift+g' to test the specific hotkey.")
    print("2. Press 'esc' to exit.")
    print("--------------------------------------------------")
    print("Waiting for input...")

    # Register the specific hotkey
    try:
        keyboard.add_hotkey('alt+shift+g', on_hotkey)
    except Exception as e:
        print(f"[ERROR] Failed to register hotkey: {e}")
        return

    # Also inspect all events to see if keys are being read at all
    # hooks can sometimes block or be blocked, so we'll just print what we see briefly
    # actually, hook might be too noisy. Let's just wait.
    
    try:
        keyboard.wait('esc')
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()
        print("\nExiting.")

if __name__ == "__main__":
    main()

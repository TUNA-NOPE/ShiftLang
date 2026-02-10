import sys
import time
import traceback

def run_diagnostics():
    print("--- ShiftLang Diagnostic Tool ---")
    
    # 1. Dependency Check
    print("\n[1] Checking dependencies...")
    try:
        import keyboard
        import pyperclip
        from deep_translator import GoogleTranslator
        print("  [PASS] All required libraries import successfully.")
    except ImportError as e:
        print(f"  [FAIL] Missing dependency: {e}")
        print("  Try running: pip install -r requirements.txt")
        return

    # 2. Translation API Check
    print("\n[2] Testing Translation API (English -> Hebrew)...")
    try:
        translator = GoogleTranslator(source='english', target='hebrew')
        result = translator.translate("Hello World")
        print(f"  Result: {result}")
        if result:
            print("  [PASS] Translation API works.")
        else:
            print("  [FAIL] Translation returned empty string.")
    except Exception as e:
        print(f"  [FAIL] Translation error: {e}")
        traceback.print_exc()

    # 3. Clipboard Check (Basic)
    print("\n[3] Testing Basic Clipboard...")
    try:
        test_text = f"Debug_Test_{int(time.time())}"
        print(f"  Copying: {test_text}")
        pyperclip.copy(test_text)
        time.sleep(0.5)
        pasted = pyperclip.paste()
        print(f"  Pasted: {pasted}")
        
        if pasted.strip() == test_text:
            print("  [PASS] Clipboard read/write works.")
        else:
            print("  [FAIL] Clipboard mismatch.")
            print(f"         Expected: '{test_text}'")
            print(f"         Got:      '{pasted}'")
    except Exception as e:
        print(f"  [FAIL] Clipboard error: {e}")
        traceback.print_exc()

    # 4. Hotkey Registration Check
    print("\n[4] Testing Hotkey Registration...")
    try:
        # Just verify we can register a hook without crashing
        # We won't block/wait, just register and unregister
        # This checks for permission issues on some OSs
        keyboard.add_hotkey('ctrl+shift+0', lambda: None)
        keyboard.remove_hotkey('ctrl+shift+0')
        print("  [PASS] Hotkey registration API seems functional (no crash).")
    except Exception as e:
        print(f"  [FAIL] Hotkey registration error: {e}")
        print("         Do you have sufficient permissions? (Try running as Administrator/Sudo)")
        traceback.print_exc()

    print("\n--- Diagnostic Complete ---")

if __name__ == "__main__":
    run_diagnostics()

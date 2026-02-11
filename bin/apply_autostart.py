import install
import sys

def apply():
    print("Applying autostart configuration...")
    # install.py has setup_autostart() which uses OS_NAME
    if install.setup_autostart():
        print("Autostart configured successfully.")
    else:
        print("Failed to configure autostart.")

if __name__ == "__main__":
    apply()

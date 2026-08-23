import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("  SAGAR TOUR AND TRAVEL - WEB APPLICATION LAUNCHER")
    print("  WhatsApp / Booking Contact: 7901864610")
    print("=" * 60)
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_py = os.path.join(app_dir, "app.py")
    
    print("\nStarting Flask server on http://127.0.0.1:5000 ...")
    print("Public Website: http://127.0.0.1:5000/")
    print("Admin Panel:    http://127.0.0.1:5000/admin (Default Passcode: sagar123)\n")
    
    python_exe = sys.executable
    subprocess.run([python_exe, app_py])

if __name__ == "__main__":
    main()

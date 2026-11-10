"""Double-click this file to open Filmlux Studio in your browser.

(Same as running:  python studio.py app)
Keep the black window open while you use the app; close it, or press Ctrl+C, to stop.
"""
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "engine"))

try:
    from vstudio.app import serve
    serve()
except SystemExit:
    pass
except Exception:
    traceback.print_exc()
    print("\nFilmlux Studio could not start. Run  python studio.py check  in this folder to see what is missing"
          "\n(usually: pip install -r requirements.txt).")
    input("\nPress Enter to close this window...")

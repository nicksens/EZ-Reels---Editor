"""
Easy Reels - Direct Batch Mode Launcher
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    print("🚀 Easy Reels - Batch Processing Mode")
    print("=" * 40)
    
    try:
        from easy_reels.gui.batch_main_window import BatchEasyReelsApp
        app = BatchEasyReelsApp()
        app.mainloop()
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

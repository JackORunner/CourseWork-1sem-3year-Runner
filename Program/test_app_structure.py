import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

def test_imports():
    print("Testing Imports...")
    try:
        from main import main
        from views.library_view import LibraryView
        from views.study_view import StudyView
        from views.settings_view import SettingsView
        print("Imports Successful.")
    except ImportError as e:
        print(f"Import Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error during imports: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_imports()

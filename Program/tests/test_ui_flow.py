
import sys
import os
import flet as ft
from unittest.mock import MagicMock, patch
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from views.library_view import LibraryView
from views.study_view import StudyView
from views.settings_view import SettingsView
import ai_engine
import database

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_library_view_logic():
    print("\n--- Testing LibraryView Logic ---")
    page = MagicMock(spec=ft.Page)
    page.client_storage = MagicMock()
    page.client_storage.get.return_value = "fake_key"

    # Mock DB
    with patch('views.library_view.Database') as MockDB:
        mock_db_instance = MockDB.return_value
        mock_db_instance.get_materials.return_value = [{'id': 1, 'subject': 'Hist', 'topic_name': 'Test', 'content': 'foo'}]
        mock_db_instance.get_subjects.return_value = ['Hist']
        
        # Init View
        try:
            lib = LibraryView(page)
            lib.did_mount()
            print("✓ LibraryView initialized and mounted")
        except Exception as e:
            print(f"FAILED: LibraryView Init: {e}")
            return

        # Open Dialog
        try:
            lib.open_add_dialog(None)
            dialog = lib.add_dialog
            print("✓ Add Dialog Opened")
        except Exception as e:
            print(f"FAILED: Open Add Dialog: {e}")
            return

        # Test Save Validation (Empty)
        try:
            dialog.save(None)
            if dialog.subject_field.error_text == "Required":
                print("✓ Validation Logic Triggered Correctly")
            else:
                print(f"FAILED: Validation Logic (Expected error text, got {dialog.subject_field.error_text})")
        except Exception as e:
            print(f"FAILED: Save Empty: {e}")

        # Test Save Success
        try:
            dialog.subject_field.value = "Math"
            dialog.topic_field.value = "Algebra"
            dialog.content_field.value = "1+1=2"
            dialog.save(None)
            mock_db_instance.add_material.assert_called()
            print("✓ Save Logic Validated")
        except Exception as e:
            print(f"FAILED: Save Success: {e}")

        # Test AI Generate Button (Logic only)
        try:
             # Set values
            dialog.ai_subject_field.value = "Science"
            dialog.ai_topic_field.value = "Atoms"
            
            # Mock AI
            lib.ai.generate_lesson = MagicMock(return_value="Generated Content")
            
            dialog.generate_content(None)
            
            if dialog.content_field.value == "Generated Content":
                 print("✓ AI Generation Integration Logic Validated")
            else:
                 print(f"FAILED: AI Generation (Expected 'Generated Content', got '{dialog.content_field.value}')")

        except Exception as e:
            print(f"FAILED: AI Gen Logic: {e}")


def test_study_view_logic():
    print("\n--- Testing StudyView Logic ---")
    page = MagicMock(spec=ft.Page)
    page.client_storage.get.return_value = "fake_key"
    
    # Mock DB and AI
    with patch('views.study_view.Database') as MockDB:
        mock_db_instance = MockDB.return_value
        mock_db_instance.get_materials.return_value = [{'id': 1, 'subject': 'Hist', 'topic_name': 'Test', 'content': 'This is a test content.'}]
        
        try:
            study = StudyView(page, material_id=1)
            study.did_mount()
            print("✓ StudyView initialized and mounted")
        except Exception as e:
            print(f"FAILED: StudyView Init: {e}")
            return
            
        # Test Mode Select -> Read
        try:
            # Simulate click on Standard Mode
            e = MagicMock()
            e.control.data = "Standard"
            study.set_mode(e)
            study.go_to_read(e)
            
            if study.step == 2:
                 print("✓ Transition to Read Step (Step 2)")
            else:
                 print(f"FAILED: Transition to Read (Step {study.step})")
        except Exception as e:
            print(f"FAILED: Go To Read: {e}")
            return

        # Test Read -> Recall
        try:
            study.go_to_recall(None)
            if study.step == 3:
                print("✓ Transition to Recall Step (Step 3)")
            else:
                print(f"FAILED: Transition to Recall (Step {study.step})")
        except Exception as e:
            print(f"FAILED: Go To Recall: {e}")
            return

        # Test Submit Logic
        try:
            study.recall_input = MagicMock()
            study.recall_input.value = "This is a test content."
            
            study.ai.analyze_recall = MagicMock(return_value={'score': 100, 'summary_feedback': 'Good', 'missing_key_facts': []})
            
            study.submit_recall(None)
            
            if study.step == 4:
                print("✓ Transition to Feedback Step (Step 4)")
            else:
                print(f"FAILED: Transition to Feedback (Step {study.step})")
                
            mock_db_instance.save_session.assert_called()
            print("✓ Session Saved to DB")
            
        except Exception as e:
             print(f"FAILED: Submit Recall: {e}")


def test_settings_view_logic():
    print("\n--- Testing SettingsView Logic ---")
    page = MagicMock(spec=ft.Page)
    page.client_storage = MagicMock()
    page.client_storage.get.return_value = None

    try:
        settings = SettingsView(page)
        settings.did_mount()
        print("✓ SettingsView initialized")
    except Exception as e:
        print(f"FAILED: Init Settings: {e}")
        return

    try:
        settings.api_key_field.value = "new_key"
        settings.save_api_key(None)
        page.client_storage.set.assert_called_with("google_api_key", "new_key")
        print("✓ Save API Key Logic Validated")
    except Exception as e:
        print(f"FAILED: Save API Key: {e}")

if __name__ == "__main__":
    test_library_view_logic()
    test_study_view_logic()
    test_settings_view_logic()

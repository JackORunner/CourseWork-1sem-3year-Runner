import os
import json
from database import Database
from ai_engine import AIEngine

def test_database():
    print("Testing Database...")
    if os.path.exists("test_mindrecall.db"):
        os.remove("test_mindrecall.db")
    
    db = Database("test_mindrecall.db")
    
    # Test Add Material
    mat_id = db.add_material("History", "French Rev", "Liberty, Equality, Fraternity.")
    print(f"Added Material ID: {mat_id}")
    
    # Test Get Materials
    materials = db.get_materials()
    assert len(materials) == 1
    assert materials[0]["subject"] == "History"
    print("Get Materials: PASS")
    
    # Test Get Subjects
    subjects = db.get_subjects()
    assert "History" in subjects
    print("Get Subjects: PASS")

    # Test Save Session
    feedback = {"score": 90, "summary": "Good job"}
    db.save_session(mat_id, "Liberty Equality Fraternity", 90, feedback, "Standard")
    
    # Test Get Sessions
    sessions = db.get_sessions(mat_id)
    assert len(sessions) == 1
    assert sessions[0]["ai_score"] == 90
    assert sessions[0]["ai_feedback"]["score"] == 90
    print("Session Management: PASS")
    
    db.get_connection().close()
    if os.path.exists("test_mindrecall.db"):
        os.remove("test_mindrecall.db")
    print("Database Tests Completed Successfully.\n")

def test_ai_engine():
    print("Testing AI Engine (Offline checks)...")
    try:
        engine = AIEngine() 
        # calls without key should raise error or handle gracefully
        try:
             res = engine.generate_lesson("Math", "Pi")
             print(f"Generate Lesson (No Key): {res}") # Should be error message
        except ValueError as e:
             print(f"Generate Lesson (No Key): caught expected error -> {e}")

        try:
            res = engine.analyze_recall("Original", "Attempt")
            if isinstance(res, dict) and "score" in res:
                 print(f"Analyze Recall (No Key): Unexpected success? {res}")
            else:
                 # It might return a dict with error info if handled internally
                 print(f"Analyze Recall (No Key): {res}")
        except ValueError as e:
             print(f"Analyze Recall (No Key): caught expected error -> {e}")

        print("AI Engine Offline Tests Completed.\n")

    except Exception as e:
        print(f"AI Engine Test Failed: {e}")

if __name__ == "__main__":
    test_database()
    test_ai_engine()

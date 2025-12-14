import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

import os

# Ensure DB is created in the same directory as this script, not CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "mindrecall.db")

class Database:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Initializes the database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Materials Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                topic_name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Sessions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id INTEGER,
                user_input TEXT,
                ai_score INTEGER,
                ai_feedback TEXT, -- Stored as JSON string
                mode TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (material_id) REFERENCES materials (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_material(self, subject: str, topic_name: str, content: str) -> int:
        """Adds a new study material to the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO materials (subject, topic_name, content) VALUES (?, ?, ?)",
            (subject, topic_name, content)
        )
        material_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return material_id

    def update_material(self, material_id: int, subject: str, topic_name: str, content: str) -> None:
        """Updates an existing study material."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE materials
            SET subject = ?, topic_name = ?, content = ?
            WHERE id = ?
            """,
            (subject, topic_name, content, material_id),
        )
        conn.commit()
        conn.close()

    def delete_material(self, material_id: int) -> None:
        """Deletes a material by its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))
        conn.commit()
        conn.close()

    def get_materials(self, subject_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves materials, optionally filtered by subject."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if subject_filter:
            cursor.execute(
                "SELECT id, subject, topic_name, content, created_at FROM materials WHERE subject = ?",
                (subject_filter,)
            )
        else:
            cursor.execute("SELECT id, subject, topic_name, content, created_at FROM materials")
            
        rows = cursor.fetchall()
        conn.close()
        
        materials = []
        for row in rows:
            materials.append({
                "id": row[0],
                "subject": row[1],
                "topic_name": row[2],
                "content": row[3],
                "created_at": row[4]
            })
        return materials

    def get_subjects(self) -> List[str]:
        """Retrieves a list of all unique subjects."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT subject FROM materials ORDER BY subject")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def save_session(self, material_id: int, user_input: str, ai_score: int, ai_feedback: Dict, mode: str):
        """Saves a study session result."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Ensure feedback is stored as a JSON string
        feedback_json = json.dumps(ai_feedback)
        
        cursor.execute(
            """INSERT INTO sessions 
               (material_id, user_input, ai_score, ai_feedback, mode) 
               VALUES (?, ?, ?, ?, ?)""",
            (material_id, user_input, ai_score, feedback_json, mode)
        )
        conn.commit()
        conn.close()

    def get_sessions(self, material_id: int) -> List[Dict[str, Any]]:
        """Retrieves session history for a specific material."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, user_input, ai_score, ai_feedback, mode, timestamp 
               FROM sessions WHERE material_id = ? ORDER BY timestamp DESC""",
            (material_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            sessions.append({
                "id": row[0],
                "user_input": row[1],
                "ai_score": row[2],
                "ai_feedback": json.loads(row[3]),
                "mode": row[4],
                "timestamp": row[5]
            })
        return sessions

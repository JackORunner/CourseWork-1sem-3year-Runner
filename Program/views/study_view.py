import os
import sys
import flet as ft
import time
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from Program.database import Database
from Program.ai_engine import AIEngine, DEFAULT_READ_INSTRUCTION, DEFAULT_RECALL_INSTRUCTION


class StudyView(ft.Container):
    def __init__(self, page: ft.Page, material_id: int):
        super().__init__()
        self.page: ft.Page = page
        self.material_id = material_id
        self.db = Database()
        self.ai = AIEngine()
        self.expand = True
        self.padding = 20

        self.material: Dict[str, Any] | None = self._get_material(material_id)
        self.error_view = not bool(self.material)

        self.step = 1  # 1: Setup, 2: Read, 3: Recall, 4: Feedback
        self.mode = "Standard"  # or "Mastery"
        self.start_time = 0
        self.analysis_result: Dict[str, Any] = {}

    def _safe_update(self):
        try:
            self.update()
        except AssertionError:
            # Control not yet attached to page; ignore update in that case
            return

    def _show_error(self, message: str):
        page = getattr(self, "page", None)
        if page is None:
            return
        try:
            page.snack_bar = ft.SnackBar(ft.Text(message))
            page.snack_bar.open = True
            page.update()
        except Exception:
            return

    def _get_material(self, mid):
        all_mats = self.db.get_materials()
        for m in all_mats:
            if str(m.get("id")) == str(mid):
                m["instruction_read"] = m.get("instruction_read") or DEFAULT_READ_INSTRUCTION
                m["instruction_recall"] = m.get("instruction_recall") or DEFAULT_RECALL_INSTRUCTION
                return m
        return None

    def did_mount(self):
        page = getattr(self, "page", None)
        if not page:
            return
        key = page.client_storage.get("google_api_key")
        if key:
            self.ai.set_api_key(key)
        self.render_step()

    def set_mode(self, e):
        self.mode = e.control.data
        self.render_step()

    def go_to_read(self, e):
        self.step = 2
        self.start_time = time.time()
        self.render_step()

    def go_to_recall(self, e):
        self.step = 3
        self.render_step()

    def submit_recall(self, e):
        if not self.material:
            self._show_error("Material not found.")
            return
        # Отримуємо текст користувача (безпечно, якщо поле ще не ініціалізоване)
        user_text = (getattr(self, "recall_input", None) or ft.TextField()).value
        user_text = (user_text or "").strip()
        
        if not user_text:
            return

        # Переходимо на крок завантаження
        self.step = 4
        self.render_loading()

        try:
            # Викликаємо AI аналіз
            analysis = self.ai.analyze_recall(
                self.material["content"],
                user_text,
                # Передаємо інструкцію для ВІДТВОРЕННЯ (Recall)
                recall_instruction=self.material.get("instruction_recall", DEFAULT_RECALL_INSTRUCTION),
                # Передаємо інструкцію для ЗАПАМ'ЯТОВАННЯ (Read)"
                memorization_instruction=self.material.get("instruction_read", DEFAULT_READ_INSTRUCTION)
            )
            
            self.analysis_result = analysis or {}
            
            # Зберігаємо сесію в базу даних
            self.db.save_session(
                self.material["id"],
                user_text,
                self.analysis_result.get("score", 0),
                self.analysis_result,
                self.mode,
            )
            
            # Оновлюємо екран, щоб показати результати
            self.render_step()
            
        except Exception as err:
            # Якщо сталася помилка, показуємо повідомлення і повертаємо на крок введення
            self._show_error(f"Error analyzing: {err}")
            self.step = 3
            self.render_step()

    def retry_mastery(self, e):
        self.step = 2
        self.render_step()

    def text_peek(self, e):
        self.step = 2
        self.render_step()

    def finish_session(self, e):
        page = getattr(self, "page", None)
        if page:
            page.go("/library")

    def go_back(self, e):
        page = getattr(self, "page", None)
        if page:
            page.go("/library")

    def render_loading(self):
        self.content = ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center)
        self._safe_update()

    def set_mode_standard(self, e):
        self.mode = "Standard"
        self.go_to_read(e)

    def set_mode_mastery(self, e):
        self.mode = "Mastery"
        self.go_to_read(e)

    def render_step(self):
        if self.error_view or not self.material:
            self.content = ft.Text("Material not found.")
            self._safe_update()
            return

        page = getattr(self, "page", None)
        if not page:
            return

        controls = []

        if self.step == 1:
            controls = [
                ft.Text(f"Study Session: {self.material['topic_name']}", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"Subject: {self.material['subject']}"),
                ft.Divider(),
                ft.Text("Select Mode:"),
                ft.Row(
                    [
                        ft.ElevatedButton("Standard Mode", on_click=self.set_mode_standard),
                        ft.ElevatedButton("Mastery Mode", on_click=self.set_mode_mastery),
                    ]
                ),
                ft.Text("Standard: Get feedback and save.", size=12, italic=True),
                ft.Text("Mastery: Must score > 80% to pass.", size=12, italic=True),
            ]

        elif self.step == 2:
            bg_color = ft.Colors.GREY_200 if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_900
            text_color = ft.Colors.BLACK if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.WHITE

            controls = [
                ft.Text("Read and Memorize", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    self.material.get("instruction_read", DEFAULT_READ_INSTRUCTION),
                    italic=True,
                    size=13,
                    color=ft.Colors.GREY_600,
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Text(self.material["content"], size=16, color=text_color),
                    padding=20,
                    bgcolor=bg_color,
                    border_radius=10,
                    expand=True,
                ),
                ft.Container(height=20),
                ft.ElevatedButton("I'm Ready (Hide Text)", icon=ft.Icons.VISIBILITY_OFF, on_click=self.go_to_recall),
            ]

        elif self.step == 3:
            self.recall_input = ft.TextField(
                label="Reconstruct the text here...",
                multiline=True,
                min_lines=10,
                expand=True,
                autofocus=True,
            )
            controls = [
                ft.Text("Active Recall", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    self.material.get("instruction_recall", DEFAULT_RECALL_INSTRUCTION),
                    italic=True,
                    size=13,
                    color=ft.Colors.GREY_600,
                ),
                ft.Container(height=10),
                self.recall_input,
                ft.Container(height=10),
                ft.ElevatedButton("Submit Analysis", icon=ft.Icons.CHECK, on_click=self.submit_recall),
            ]

        elif self.step == 4:
            score = self.analysis_result.get("score", 0)
            summary = self.analysis_result.get("summary_feedback", "No feedback provided.")
            missing = self.analysis_result.get("missing_key_facts", [])
            raw = self.analysis_result.get("_raw")

            score_color = ft.Colors.GREEN if score >= 80 else ft.Colors.ORANGE
            if score < 50:
                score_color = ft.Colors.RED

            feedback_content = [
                ft.Row(
                    [
                        ft.Text(f"Score: {score}/100", size=30, weight=ft.FontWeight.BOLD, color=score_color),
                        ft.Icon(ft.Icons.THUMB_UP if score >= 80 else ft.Icons.THUMB_DOWN),
                    ]
                ),
                ft.Text(summary, size=16),
                ft.Divider(),
                ft.Text("Missing Key Facts:", weight=ft.FontWeight.BOLD),
            ]

            for fact in missing:
                feedback_content.append(ft.Text(f"• {fact}"))

            if raw:
                feedback_content.append(ft.Divider())
                feedback_content.append(ft.Text("Raw AI output (debug):", weight=ft.FontWeight.BOLD, size=12))
                feedback_content.append(ft.Text(raw, size=12, selectable=True))

            actions = [ft.ElevatedButton("Finish", on_click=self.finish_session)]

            if self.mode == "Mastery" and score < 80:
                actions = [
                    ft.ElevatedButton("Retry (Peek Text)", on_click=self.text_peek),
                    ft.TextButton("Give Up / Finish", on_click=self.finish_session),
                ]

            controls = feedback_content + [ft.Container(height=20), ft.Row(actions)]

        header = ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Back", on_click=self.go_back),
            ft.Text("Back to Library", weight=ft.FontWeight.BOLD),
        ])

        self.content = ft.Column([header] + controls, scroll=ft.ScrollMode.AUTO, expand=True)
        self._safe_update()



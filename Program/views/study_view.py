import flet as ft
import time
import threading
from database import Database
from ai_engine import AIEngine
import asyncio

class StudyView(ft.Container):
    def __init__(self, page: ft.Page, material_id: int):
        super().__init__()
        self.page = page
        self.material_id = material_id
        self.db = Database()
        self.ai = AIEngine()
        self.expand = True
        self.padding = 20
        
        # Load Material
        self.material = self._get_material(material_id)
        
        if not self.material:
            self.error_view = True
        else:
            self.error_view = False

        # State
        self.step = 1 # 1: Setup, 2: Read, 3: Recall, 4: Feedback
        self.mode = "Standard" # or "Mastery"
        self.start_time = 0
        
        # UI Elements
        # self.content will be set by render_step


    def _get_material(self, mid):
        # Helper to find material by ID (simplistic since get_materials returns list)
        # Ideally DB should have get_material_by_id
        all_mats = self.db.get_materials()
        for m in all_mats:
            if str(m['id']) == str(mid):
                return m
        return None

    def did_mount(self):
        key = self.page.client_storage.get("google_api_key")
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
        user_text = self.recall_input.value
        if not user_text:
            return

        self.step = 4
        self.render_loading()
        
        # Run analysis asynchronously to not block UI
        # Flet is threading based, but let's just do a simple blocking call for now wrapped or quick
        # Ideally use threading or asyncio if Flet supports async handlers fully here
        # For simplicity in this sync wrapper:
        self.process_analysis(user_text)

    def process_analysis(self, user_text):
        try:
            analysis = self.ai.analyze_recall(self.material['content'], user_text)
            self.db.save_session(
                self.material['id'], 
                user_text, 
                analysis.get('score', 0), 
                analysis, 
                self.mode
            )
            self.analysis_result = analysis
            self.render_step() # Updates to step 4 view
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error analyzing: {e}"))
            self.page.snack_bar.open = True
            self.page.update()
            self.step = 3 # Go back so they can try again or save manual?
            self.render_step()

    def retry_mastery(self, e):
        # Mastery Mode retry: Show original text briefly then back to recall
        self.step = 2 # Reuse Read view but maybe with a timer?
        self.render_step()

    def text_peek(self, e):
        """Allows a quick peek at the text in Mastery mode retry, or just going back to read."""
        self.step = 2
        self.render_step()

    def finish_session(self, e):
        self.page.go("/library")

    def go_back(self, e):
        """Return to library from StudyView."""
        self.page.go("/library")

    def render_loading(self):
        self.content = ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center)
        self.update()

    def set_mode_standard(self, e):
        self.mode = "Standard"
        self.go_to_read(e)

    def set_mode_mastery(self, e):
        self.mode = "Mastery"
        self.go_to_read(e)

    def render_step(self):
        if self.error_view:
            self.content = ft.Text("Material not found.")
            self.update()
            return

        controls = []
        
        # STEP 1: SETUP
        if self.step == 1:
            controls = [
                ft.Text(f"Study Session: {self.material['topic_name']}", size=24, weight="bold"),
                ft.Text(f"Subject: {self.material['subject']}"),
                ft.Divider(),
                ft.Text("Select Mode:"),
                ft.Row([
                    ft.ElevatedButton("Standard Mode", on_click=self.set_mode_standard), 
                    ft.ElevatedButton("Mastery Mode", on_click=self.set_mode_mastery)
                ]),
                ft.Text("Standard: Get feedback and save.", size=12, italic=True),
                ft.Text("Mastery: Must score > 80% to pass.", size=12, italic=True),
            ]

        # STEP 2: READING
        elif self.step == 2:
            # Determine background color based on theme
            bg_color = ft.Colors.GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_900
            text_color = ft.Colors.BLACK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.WHITE
            
            controls = [
                ft.Text("Read and Memorize", size=20, weight="bold"),
                ft.Divider(),
                ft.Container(
                    content=ft.Text(self.material['content'], size=16, color=text_color),
                    padding=20,
                    bgcolor=bg_color,
                    border_radius=10,
                    expand=True # Try to fill space
                ),
                ft.Container(height=20),
                ft.ElevatedButton("I'm Ready (Hide Text)", icon=ft.Icons.VISIBILITY_OFF, on_click=self.go_to_recall)
            ]

        # STEP 3: RECALL
        elif self.step == 3:
            self.recall_input = ft.TextField(
                label="Reconstruct the text here...",
                multiline=True,
                min_lines=10,
                expand=True,
                autofocus=True
            )
            controls = [
                ft.Text("Active Recall", size=20, weight="bold"),
                ft.Text("Type everything you remember.", italic=True),
                ft.Container(height=10),
                self.recall_input,
                ft.Container(height=10),
                ft.ElevatedButton("Submit Analysis", icon=ft.Icons.CHECK, on_click=self.submit_recall)
            ]

        # STEP 4: FEEDBACK
        elif self.step == 4:
            score = self.analysis_result.get('score', 0)
            summary = self.analysis_result.get('summary_feedback', 'No feedback provided.')
            missing = self.analysis_result.get('missing_key_facts', [])
            
            score_color = ft.Colors.GREEN if score >= 80 else ft.Colors.ORANGE
            if score < 50: score_color = ft.Colors.RED

            feedback_content = [
                ft.Row([
                    ft.Text(f"Score: {score}/100", size=30, weight="bold", color=score_color),
                    ft.Icon(ft.Icons.THUMB_UP if score >= 80 else ft.Icons.THUMB_DOWN)
                ]),
                ft.Text(summary, size=16),
                ft.Divider(),
                ft.Text("Missing Key Facts:", weight="bold"),
            ]
            
            for fact in missing:
                feedback_content.append(ft.Text(f"• {fact}"))

            actions = [ft.ElevatedButton("Finish", on_click=self.finish_session)]
            
            if self.mode == "Mastery" and score < 80:
                actions = [
                    ft.ElevatedButton("Retry (Peek Text)", on_click=self.text_peek),
                    ft.TextButton("Give Up / Finish", on_click=self.finish_session)
                ]

            controls = feedback_content + [ft.Container(height=20), ft.Row(actions)]

        # Always show a back button at the top
        header = ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Back", on_click=self.go_back),
            ft.Text("Back to Library", weight="bold"),
        ])

        self.content = ft.Column([header] + controls, scroll=ft.ScrollMode.AUTO, expand=True)
        self.update()



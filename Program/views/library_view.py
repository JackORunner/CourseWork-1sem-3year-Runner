import flet as ft
from database import Database
from ai_engine import AIEngine
import datetime


class LibraryView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.expand = True
        self.padding = 20
        self.pg: ft.Page = page
        self.db = Database()
        self.ai = AIEngine()

        self.materials_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.subject_filter = ft.Dropdown(
            label="Filter by Subject",
            options=[ft.dropdown.Option("All")],
            value="All",
            on_change=self.filter_materials,
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Library", size=30, weight=ft.FontWeight.BOLD),
                        ft.FloatingActionButton(
                            icon=ft.Icons.ADD,
                            text="Add Material",
                            on_click=self.open_add_dialog,
                        ),
                    ],
                ),
                ft.Divider(),
                self.subject_filter,
                ft.Container(height=10),
                self.materials_list,
            ],
        )

        self.check_api_key()

    def check_api_key(self):
        api_key = self.pg.client_storage.get("google_api_key")
        if isinstance(api_key, str) and hasattr(self.ai, "set_api_key"):
            self.ai.set_api_key(api_key)

    def did_mount(self):
        self.load_materials()
        self.load_subjects()

    def load_subjects(self):
        subjects = self.db.get_subjects()
        options = [ft.dropdown.Option("All")] + [ft.dropdown.Option(s) for s in subjects]
        self.subject_filter.options = options
        self.update()

    def load_materials(self, subject=None):
        self.materials_list.controls.clear()
        filter_subj = subject if subject != "All" else None
        materials = self.db.get_materials(filter_subj)

        if not materials:
            self.materials_list.controls.append(
                ft.Text("No materials found. Add some to get started!", italic=True)
            )
        else:
            for mat in materials:
                self.materials_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=10,
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.Icons.BOOK),
                                        title=ft.Text(mat["topic_name"], weight=ft.FontWeight.BOLD),
                                        subtitle=ft.Text(
                                            f"{mat['subject']} • {len(mat['content'].split())} words"
                                        ),
                                        trailing=ft.IconButton(
                                            icon=ft.Icons.PLAY_ARROW,
                                            tooltip="Start Study Session",
                                            on_click=lambda e, m=mat: self.start_study(m),
                                        ),
                                    )
                                ]
                            ),
                        )
                    )
                )
        self.update()

    def filter_materials(self, e):
        self.load_materials(self.subject_filter.value)

    def start_study(self, material):
        self.pg.go(f"/study?id={material['id']}")

    def open_add_dialog(self, e):
        self.add_dialog = AddMaterialDialog(self.pg, self.on_material_added)
        self.pg.open(self.add_dialog)
        self.pg.update()

    def on_material_added(self):
        self.load_materials()
        self.load_subjects()
        self.pg.snack_bar = ft.SnackBar(ft.Text("Material added successfully!"))  # type: ignore[attr-defined]
        self.pg.snack_bar.open = True  # type: ignore[attr-defined]
        self.pg.update()


class AddMaterialDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, on_success):
        super().__init__()
        self.pg: ft.Page = page
        self.on_success = on_success
        self.db = Database()
        self.ai = AIEngine(api_key=self.pg.client_storage.get("google_api_key"))

        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Manual Paste", icon=ft.Icons.EDIT),
                ft.Tab(text="AI Generate", icon=ft.Icons.AUTO_AWESOME),
            ],
            expand=True,
            on_change=self.handle_tab_change,
        )

        self.subject_field = ft.TextField(label="Subject (e.g., History)")
        self.topic_field = ft.TextField(label="Topic (e.g., French Revolution)")
        self.content_field = ft.TextField(
            label="Content",
            multiline=True,
            min_lines=5,
            max_lines=10,
            expand=True,
        )

        self.ai_subject_field = ft.TextField(label="Subject")
        self.ai_topic_field = ft.TextField(label="Topic")
        self.ai_loading = ft.ProgressRing(visible=False)

        self.manual_content = ft.Column(
            [self.subject_field, self.topic_field, self.content_field],
            scroll=ft.ScrollMode.AUTO,
            height=300,
        )

        self.ai_content = ft.Column(
            [
                ft.Text("Enter a subject and topic, and AI will generate a lesson for you."),
                self.ai_subject_field,
                self.ai_topic_field,
                ft.ElevatedButton("Generate Content", on_click=self.generate_content),
                self.ai_loading,
            ],
            scroll=ft.ScrollMode.AUTO,
            height=300,
        )

        self.content = ft.Container(
            width=500,
            height=400,
            content=ft.Column(
                [
                    self.tabs,
                    ft.Container(
                        content=self.manual_content, expand=True, visible=True, key="manual_container"
                    ),
                    ft.Container(
                        content=self.ai_content, expand=True, visible=False, key="ai_container"
                    ),
                ]
            ),
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close),
            ft.ElevatedButton("Save", on_click=self.save),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def handle_tab_change(self, e):
        is_manual = self.tabs.selected_index == 0
        container = self.content
        if isinstance(container, ft.Container) and isinstance(container.content, ft.Column):
            cols = container.content.controls
            if len(cols) >= 3:
                cols[1].visible = is_manual
                cols[2].visible = not is_manual
        self.pg.update()

    def generate_content(self, e):
        if not self.ai_subject_field.value or not self.ai_topic_field.value:
            self.ai_subject_field.error_text = "Required" if not self.ai_subject_field.value else None
            self.ai_topic_field.error_text = "Required" if not self.ai_topic_field.value else None
            self.pg.update()
            return

        self.ai_loading.visible = True
        self.pg.update()

        try:
            api_key = self.pg.client_storage.get("google_api_key")
            if isinstance(api_key, str) and hasattr(self.ai, "set_api_key"):
                self.ai.set_api_key(api_key)

            text = self.ai.generate_lesson(self.ai_subject_field.value, self.ai_topic_field.value)

            self.subject_field.value = self.ai_subject_field.value
            self.topic_field.value = self.ai_topic_field.value
            self.content_field.value = text

            self.tabs.selected_index = 0
            self.handle_tab_change(None)

        except Exception as ex:
            self.content_field.value = f"Error: {ex}"

        self.ai_loading.visible = False
        self.pg.update()

    def save(self, e):
        if self.subject_field.value and self.topic_field.value and self.content_field.value:
            self.db.add_material(
                self.subject_field.value,
                self.topic_field.value,
                self.content_field.value,
            )
            self.pg.close(self)
            self.on_success()
        else:
            self.subject_field.error_text = "Required" if not self.subject_field.value else None
            self.topic_field.error_text = "Required" if not self.topic_field.value else None
            self.content_field.error_text = "Required" if not self.content_field.value else None
            self.pg.update()

    def close(self, e):
        self.pg.close(self)
        self.pg.update()

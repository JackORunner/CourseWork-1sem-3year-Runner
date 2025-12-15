import os
import sys
import flet as ft
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from Program.database import Database
from Program.ai_engine import AIEngine, DEFAULT_READ_INSTRUCTION, DEFAULT_RECALL_INSTRUCTION


class LibraryView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.expand = True
        self.padding = 20
        self.pg: ft.Page = page
        self.db = Database()
        self.ai = AIEngine()
        self._delete_dialog: ft.AlertDialog | None = None
        self._pending_delete_id: int | None = None

        self.materials_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.search_field = ft.TextField(
            label="Search topics...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            on_change=self.filter_materials
        )
        
        self.subject_filter = ft.Dropdown(
            label="Filter by Subject",
            options=[ft.dropdown.Option("All")],
            value="All",
            width=200,
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
                ft.Row(
                    controls=[
                        self.search_field,
                        self.subject_filter,
                    ]
                ),
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

    def load_materials(self, subject: str | None = None, search_query: str | None = "") -> None:
        self.materials_list.controls.clear()
        
        # Get all materials first (or filter by subject if DB supports it efficiently)
        # Since DB.get_materials handles subject filtering:
        filter_subj = subject if subject != "All" else None
        materials = self.db.get_materials(filter_subj)

        # Apply search filter in memory
        if search_query:
            query = search_query.lower()
            materials = [
                m for m in materials 
                if query in m["topic_name"].lower() or query in m["content"].lower()
            ]

        if not materials:
            self.materials_list.controls.append(
                ft.Text("No materials found.", italic=True)
            )
        else:
            for mat in materials:
                self.materials_list.controls.append(
                    ft.Card(
                        expand=True,
                        content=ft.Container(
                            padding=10,
                            expand=True,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(
                                        spacing=10,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        expand=True,
                                        controls=[
                                            ft.Icon(ft.Icons.BOOK),
                                            ft.Column(
                                                spacing=2,
                                                expand=True,
                                                controls=[
                                                    ft.Container(
                                                        expand=True,
                                                        content=ft.Text(
                                                            mat["topic_name"],
                                                            weight=ft.FontWeight.BOLD,
                                                            overflow=ft.TextOverflow.ELLIPSIS,
                                                            max_lines=1,
                                                        ),
                                                    ),
                                                    ft.Container(
                                                        expand=True,
                                                        content=ft.Text(
                                                            f"{mat['subject']} • {len(mat['content'].split())} words",
                                                            color=ft.Colors.GREY_600,
                                                            size=12,
                                                            overflow=ft.TextOverflow.ELLIPSIS,
                                                            max_lines=1,
                                                        ),
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=4,
                                        alignment=ft.MainAxisAlignment.END,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.EDIT,
                                                tooltip="Edit",
                                                icon_size=20,
                                                style=ft.ButtonStyle(padding=0),
                                                on_click=lambda e, m=mat: self.open_edit_dialog(m),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.PLAY_ARROW,
                                                tooltip="Start Study Session",
                                                icon_size=22,
                                                style=ft.ButtonStyle(padding=0),
                                                on_click=lambda e, m=mat: self.start_study(m),
                                            ),
                                            ft.IconButton(
                                                icon=ft.Icons.DELETE,
                                                tooltip="Delete",
                                                icon_size=22,
                                                style=ft.ButtonStyle(padding=0),
                                                on_click=lambda e, m=mat: self.open_delete_dialog(m),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    )
                )
        self.update()

    def filter_materials(self, e):
        subject_val = self.subject_filter.value or "All"
        search_val = self.search_field.value or ""
        self.load_materials(
            subject=subject_val,
            search_query=search_val,
        )

    def start_study(self, material):
        self.pg.go(f"/study?id={material['id']}")

    def open_edit_dialog(self, material):
        self.edit_dialog = AddMaterialDialog(self.pg, self.on_material_updated, material)
        self.pg.open(self.edit_dialog)
        self.pg.update()

    def open_add_dialog(self, e):
        self.add_dialog = AddMaterialDialog(self.pg, self.on_material_added)
        self.pg.open(self.add_dialog)
        self.pg.update()

    def open_delete_dialog(self, material):
        self._pending_delete_id = material.get("id")
        self._delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete material"),
            content=ft.Text(f"Delete \"{material.get('topic_name')}\"? This cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=self._cancel_delete),
                ft.ElevatedButton(
                    "Delete",
                    bgcolor=ft.Colors.RED,
                    on_click=self.confirm_delete
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.pg.open(self._delete_dialog)
        self.pg.update()

    def _cancel_delete(self, e):
        if self._delete_dialog:
            self.pg.close(self._delete_dialog)
            self._delete_dialog = None
        self._pending_delete_id = None
        self.pg.update()

    def confirm_delete(self, e):
        if self._pending_delete_id is not None:
            self.db.delete_material(self._pending_delete_id)
        if self._delete_dialog:
            self.pg.close(self._delete_dialog)
            self._delete_dialog = None
        self._pending_delete_id = None
        self.on_material_deleted()

    def on_material_added(self):
        self.load_materials()
        self.load_subjects()
        self.pg.snack_bar = ft.SnackBar(ft.Text("Material added successfully!"))  # type: ignore[attr-defined]
        self.pg.snack_bar.open = True  # type: ignore[attr-defined]
        self.pg.update()

    def on_material_updated(self):
        self.load_materials()
        self.load_subjects()
        self.pg.snack_bar = ft.SnackBar(ft.Text("Material updated."))  # type: ignore[attr-defined]
        self.pg.snack_bar.open = True  # type: ignore[attr-defined]
        self.pg.update()

    def on_material_deleted(self):
        self.load_materials()
        self.load_subjects()
        self.pg.snack_bar = ft.SnackBar(ft.Text("Material deleted."))  # type: ignore[attr-defined]
        self.pg.snack_bar.open = True  # type: ignore[attr-defined]
        self.pg.update()


class AddMaterialDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, on_success, material=None):
        super().__init__()
        self.pg: ft.Page = page
        self.on_success = on_success
        self.db = Database()
        self.ai = AIEngine(api_key=self.pg.client_storage.get("google_api_key"))
        self.material = material
        self.is_edit = material is not None

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

        self.read_instruction_field = ft.TextField(
            label="Memorization instructions (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            hint_text=DEFAULT_READ_INSTRUCTION,
        )

        self.recall_instruction_field = ft.TextField(
            label="Recall instructions (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            hint_text=DEFAULT_RECALL_INSTRUCTION,
        )

        # Pre-fill for edit mode
        if self.is_edit and self.material:
            self.subject_field.value = self.material.get("subject", "")
            self.topic_field.value = self.material.get("topic_name", "")
            self.content_field.value = self.material.get("content", "")
            self.read_instruction_field.value = self.material.get("instruction_read", "")
            self.recall_instruction_field.value = self.material.get("instruction_recall", "")

        self.ai_subject_field = ft.TextField(label="Subject")
        self.ai_topic_field = ft.TextField(label="Topic")
        self.ai_loading = ft.ProgressRing(visible=False)

        self.manual_content = ft.Column(
            [
                self.subject_field,
                self.topic_field,
                self.content_field,
                self.read_instruction_field,
                self.recall_instruction_field,
            ],
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

        action_label = "Update" if self.is_edit else "Save"
        self.actions = [
            ft.TextButton("Cancel", on_click=self.close),
            ft.ElevatedButton(action_label, on_click=self.save),
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

            # Reset custom instructions to defaults if empty when generating
            if not self.read_instruction_field.value:
                self.read_instruction_field.value = DEFAULT_READ_INSTRUCTION
            if not self.recall_instruction_field.value:
                self.recall_instruction_field.value = DEFAULT_RECALL_INSTRUCTION

            self.tabs.selected_index = 0
            self.handle_tab_change(None)

        except Exception as ex:
            self.content_field.value = f"Error: {ex}"

        self.ai_loading.visible = False
        self.pg.update()

    def save(self, e):
        if self.subject_field.value and self.topic_field.value and self.content_field.value:
            # Fallback to defaults if empty
            instr_read = self.read_instruction_field.value.strip() if self.read_instruction_field.value else ""
            instr_recall = self.recall_instruction_field.value.strip() if self.recall_instruction_field.value else ""
            if not instr_read:
                instr_read = DEFAULT_READ_INSTRUCTION
            if not instr_recall:
                instr_recall = DEFAULT_RECALL_INSTRUCTION

            if self.is_edit and self.material:
                self.db.update_material(
                    self.material.get("id"),
                    self.subject_field.value,
                    self.topic_field.value,
                    self.content_field.value,
                    instr_read,
                    instr_recall,
                )
            else:
                self.db.add_material(
                    self.subject_field.value,
                    self.topic_field.value,
                    self.content_field.value,
                    instr_read,
                    instr_recall,
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

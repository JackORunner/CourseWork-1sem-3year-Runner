import flet as ft

class SettingsView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.api_key_field = ft.TextField(
            label="Google Gemini API Key",
            password=True,
            can_reveal_password=True,
            width=400
        )
        self.controls = [
            ft.Container(
                padding=20,
                content=ft.Column(
                    controls=[
                        ft.Text("Settings", size=30, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Text("Configure your AI settings below.", size=16),
                        ft.Container(height=20),
                        self.api_key_field,
                        ft.ElevatedButton(
                            text="Save API Key",
                            icon=ft.Icons.SAVE,
                            on_click=self.save_api_key
                        ),
                        ft.Container(height=20),
                        ft.Text(
                            "Note: Your API Key is stored locally on this device.",
                            size=12,
                            italic=True,
                            color=ft.Colors.GREY_500
                        )
                    ]
                )
            )
        ]

    def did_mount(self):
        # Load existing key if present
        saved_key = self.page.client_storage.get("google_api_key")
        if saved_key:
            self.api_key_field.value = saved_key
            self.update()

    def save_api_key(self, e):
        if self.api_key_field.value:
            self.page.client_storage.set("google_api_key", self.api_key_field.value)
            self.page.snack_bar = ft.SnackBar(ft.Text("API Key saved successfully!"))
            self.page.snack_bar.open = True
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Please enter a valid API Key."))
            self.page.snack_bar.open = True
            self.page.update()

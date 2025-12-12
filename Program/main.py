import flet as ft
from views.library_view import LibraryView
from views.settings_view import SettingsView
from views.study_view import StudyView

def main(page: ft.Page):
    page.title = "MindRecall"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    
    # State for simple routing
    # Routes: /library, /settings, /study?id=X
    
    def route_change(route):
        page.views.clear()
        
        # Base UI Structure (Nav + Content)
        # We wrap content in a view
        
        troute = ft.TemplateRoute(page.route)
        
        # Determine current view index for Nav Highlight
        sel_index = 0
        if troute.match("/library"): sel_index = 0
        elif troute.match("/settings"): sel_index = 1
        
        # Create Navigation Controls
        rail = ft.NavigationRail(
            selected_index=sel_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.LIBRARY_BOOKS, selected_icon=ft.Icons.LIBRARY_BOOKS_OUTLINED, label="Library"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SETTINGS, selected_icon=ft.Icons.SETTINGS_OUTLINED, label="Settings"
                ),
            ],
            on_change=lambda e: nav_change(e.control.selected_index)
        )

        bar = ft.NavigationBar(
            selected_index=sel_index,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.LIBRARY_BOOKS, label="Library"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
            ],
            on_change=lambda e: nav_change(e.control.selected_index)
        )

        # Helper to handle nav clicks
        def nav_change(index):
            if index == 0: page.go("/library")
            elif index == 1: page.go("/settings")

        # Content Logic
        my_content = ft.Container(expand=True)
        
        if troute.match("/library") or page.route == "/":
            my_content.content = LibraryView(page)
            
        elif troute.match("/settings"):
            my_content.content = SettingsView(page)
            
        elif page.route.startswith("/study"):
            # Extract ID from query param manually since Flet routing is simple
            # route format: /study?id=123
            try:
                # simple parse
                query = page.route.split("?")[1]
                param = query.split("=")[1]
                my_content.content = StudyView(page, material_id=int(param))
                # Hide Nav in Study mode? Or keep it? keeping it is safer for generic nav
            except:
                my_content.content = ft.Text("Invalid Study Session ID")

        # Responsive Layout
        # If width > 600, use Rail (Desktop). Else use Bar (Mobile).
        # Note: Flet page.width might update dynamic. simpler to just check once or use ResponsiveRow.
        # For a truly responsive shell, we usually listen to resize. 
        # But 'page.views.append' builds a View object. 
        
        view_controls = []
        
        # We will use a Row for Desktop (Rail | Content)
        # And a Column for Mobile (Content | Bar) or just View with proper AppBar/NavBar
        
        # Let's use the View's built-in properties for simple responsive nav triggers?
        # Actually Flet Views work best with AppBar/NavDrawer/NavBar params.
        
        if page.width > 600:
             # Desktop Layout
             page.views.append(
                ft.View(
                    route,
                    [
                        ft.Row(
                            [
                                rail,
                                ft.VerticalDivider(width=1),
                                my_content
                            ],
                            expand=True,
                        )
                    ]
                )
            )
        else:
            # Mobile Layout
            page.views.append(
                ft.View(
                    route,
                    [my_content],
                    navigation_bar=bar # Native bottom bar
                )
            )
            
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Default Route
    page.go("/library")

if __name__ == "__main__":
    ft.app(target=main)

import os
import sys

# Make sure the app's project folders are on sys.path inside the APK runtime
_current_dir = os.path.abspath(os.path.dirname(__file__))
_parent_dir = os.path.abspath(os.path.join(_current_dir, ".."))
for p in (_current_dir, _parent_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

# Debug output (appears in adb logcat). Remove after debugging.
try:
    print("DEBUG: main __file__=", __file__)
    print("DEBUG: sys.path=", sys.path)
    print("DEBUG: files in current_dir=", os.listdir(_current_dir))
    print("DEBUG: views exists=", os.path.isdir(os.path.join(_current_dir, "views")))
except Exception as _e:
    print("DEBUG: error printing debug info:", _e)

# Normalize Windows-style bundled filenames (e.g. 'views\\file.py')
# Some packagers store files with backslashes in the filename instead of
# creating real directories. Detect those and move them into a proper
# `views/` directory so imports like `from views.library_view import ...`
# work inside the APK runtime.
try:
    _moved_any = False
    for fn in os.listdir(_current_dir):
        if fn.startswith("views\\") or fn.startswith("views/"):
            # split on whichever separator is present in the filename
            if "\\" in fn:
                parts = fn.split("\\", 1)
            else:
                parts = fn.split("/", 1)
            subpath = parts[1] if len(parts) > 1 else parts[0]
            dest_dir = os.path.join(_current_dir, "views")
            os.makedirs(dest_dir, exist_ok=True)
            src = os.path.join(_current_dir, fn)
            dest = os.path.join(dest_dir, subpath)
            try:
                if not os.path.exists(dest):
                    os.rename(src, dest)
                _moved_any = True
            except Exception:
                try:
                    # fallback: copy then remove
                    with open(src, "rb") as r, open(dest, "wb") as w:
                        w.write(r.read())
                    os.remove(src)
                    _moved_any = True
                except Exception:
                    pass

    # fix incorrectly named init file (init.py -> __init__.py)
    init_wrong = os.path.join(_current_dir, "views", "init.py")
    init_right = os.path.join(_current_dir, "views", "__init__.py")
    if os.path.exists(init_wrong) and not os.path.exists(init_right):
        try:
            os.rename(init_wrong, init_right)
            _moved_any = True
        except Exception:
            try:
                with open(init_wrong, "rb") as r, open(init_right, "wb") as w:
                    w.write(r.read())
                os.remove(init_wrong)
                _moved_any = True
            except Exception:
                pass

    if _moved_any:
        try:
            print("DEBUG: normalized bundled view files into real views/ dir")
        except Exception:
            pass
except Exception as _e:
    print("DEBUG: error normalizing bundled paths:", _e)
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
            except Exception as e:
                print(f"Error loading StudyView: {e}")
                my_content.content = ft.Text(f"Error loading Study Session: {e}")

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
    print("Starting MindRecall Application...")
    try:
        ft.app(target=main)
    except Exception as e:
        print(f"Error starting app: {e}")
        input("Press Enter to exit...")

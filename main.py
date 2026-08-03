# main.py
# Entry point for "Daftar" (دفتر) - installment sales manager for shop
# owners. Wires the database, theme and all screens together.

from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from theme import APP_TITLE
from database import Database
from utils.fonts import find_arabic_font

from screens.home_screen import HomeScreen
from screens.customers_screen import CustomersScreen
from screens.add_customer_screen import AddCustomerScreen
from screens.customer_detail_screen import CustomerDetailScreen
from screens.installments_screen import InstallmentsScreen
from screens.reports_screen import ReportsScreen
from screens.settings_screen import SettingsScreen
from screens.friends_screen import FriendsScreen
from screens.add_friend_transaction_screen import AddFriendTransactionScreen
from screens.friend_transaction_detail_screen import FriendTransactionDetailScreen


def _register_arabic_font():
    """Register an Arabic-capable font as the app's default font family
    ("Roboto" is the internal name KivyMD's widgets use, so we override
    that). Uses the bundled Tajawal font if present in assets/fonts/,
    otherwise automatically falls back to a system font that supports
    Arabic glyphs (Tahoma / Segoe UI on Windows, etc. - see utils/fonts.py).
    This is what fixes Arabic text showing as empty boxes (□□□)."""
    try:
        regular = find_arabic_font(bold=False)
        bold = find_arabic_font(bold=True)
        if regular:
            LabelBase.register(
                name="Roboto",
                fn_regular=regular,
                fn_bold=bold or regular,
            )
        else:
            print(
                "[Daftar] WARNING: no Arabic-capable font found. "
                "Arabic text may show as boxes. Add a font to assets/fonts/."
            )
    except Exception as e:
        print(f"[Daftar] Error registering Arabic font: {e}")


class DaftarApp(MDApp):
    def build(self):
        self.title = APP_TITLE
        _register_arabic_font()

        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Purple"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.accent_palette = "DeepPurple"

        # Window defaults for a comfortable desktop experience
        Window.size = (420, 780)
        Window.minimum_width, Window.minimum_height = (360, 640)

        self.db = Database()
        self.db.refresh_late_statuses()

        sm = MDScreenManager()
        sm.app_db = self.db
        sm.app_ref = self

        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(CustomersScreen(name="customers"))
        sm.add_widget(AddCustomerScreen(name="add_customer"))
        sm.add_widget(CustomerDetailScreen(name="customer_detail"))
        sm.add_widget(InstallmentsScreen(name="installments"))
        sm.add_widget(ReportsScreen(name="reports"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(FriendsScreen(name="friends"))
        sm.add_widget(AddFriendTransactionScreen(name="add_friend_transaction"))
        sm.add_widget(FriendTransactionDetailScreen(name="friend_transaction_detail"))

        self.sm = sm
        return sm

    def on_start(self):
        # IMPORTANT: the first screen added to ScreenManager already
        # becomes "current" automatically. Assigning sm.current = "home"
        # again is therefore a no-op (same value), so on_pre_enter is
        # NEVER fired for the home screen on startup - it only fires on
        # actual screen *changes*. Without this explicit call, the stat
        # cards and nav buttons never get built and the home screen
        # renders empty. We build its content here once the widget tree
        # is fully mounted, and on every future visit on_pre_enter takes
        # over normally.
        try:
            home = self.sm.get_screen("home")
            home.refresh_stats()
            if not home._nav_built:
                home._build_nav()
                home._nav_built = True
        except Exception as e:
            print(f"[Daftar] Error initializing home screen: {e}")

    def on_stop(self):
        if hasattr(self, "db"):
            self.db.close()


if __name__ == "__main__":
    DaftarApp().run()

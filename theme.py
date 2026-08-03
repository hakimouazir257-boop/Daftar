# theme.py
# Central place for the "Daftar" (دفتر) app color palette, typography and
# reusable style constants. Keeping everything here makes it trivial to
# re-skin the whole application (e.g. add more theme variants) later.

from kivy.utils import get_color_from_hex

# ---------------------------------------------------------------------------
# Brand colors (as given in the design spec)
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "#4B1D8F"        # Dark purple
COLOR_PRIMARY_LIGHT = "#6D3FD3"  # Secondary purple
COLOR_SECONDARY = "#6D3FD3"
COLOR_BACKGROUND = "#F5F5F7"
COLOR_BACKGROUND_DARK = "#121212"
COLOR_SURFACE_DARK = "#1E1E1E"
COLOR_TEXT = "#222222"
COLOR_TEXT_DARK = "#EDEDED"
COLOR_SUCCESS = "#2ECC71"
COLOR_WARNING = "#F4B400"
COLOR_ERROR = "#E74C3C"
COLOR_MUTED = "#8A8A8E"

# Gradient pair used for headers / hero cards
GRADIENT_START = COLOR_PRIMARY
GRADIENT_END = COLOR_PRIMARY_LIGHT

# ---------------------------------------------------------------------------
# Customer rating badges -> (label, color)
# ---------------------------------------------------------------------------
RATING_EXCELLENT = "excellent"
RATING_GOOD = "good"
RATING_AVERAGE = "average"
RATING_BAD = "bad"

RATING_META = {
    RATING_EXCELLENT: {"label": "عميل ممتاز", "icon": "🟢", "color": COLOR_SUCCESS},
    RATING_GOOD: {"label": "عميل جيد", "icon": "🟡", "color": COLOR_WARNING},
    RATING_AVERAGE: {"label": "عميل متوسط", "icon": "🟠", "color": "#E67E22"},
    RATING_BAD: {"label": "عميل متعثر", "icon": "🔴", "color": COLOR_ERROR},
}

INSTALLMENT_STATUS_META = {
    "paid": {"label": "مدفوع", "color": COLOR_SUCCESS},
    "unpaid": {"label": "غير مدفوع", "color": COLOR_MUTED},
    "late": {"label": "متأخر", "color": COLOR_ERROR},
}


def hex_rgba(hex_code: str, alpha: float = 1.0):
    """Return an rgba() tuple usable directly in kv / python widgets."""
    r, g, b, a = get_color_from_hex(hex_code)
    return r, g, b, alpha if alpha != 1.0 else a


# Font settings -------------------------------------------------------------
# NOTE: Place a proper Arabic-shaping-friendly font (e.g. Cairo, Tajawal)
# inside assets/fonts and update the paths below. Kivy does not reshape
# Arabic glyphs automatically for on-screen Labels, so for best results a
# font that already looks acceptable without reshaping (or an app-level
# reshaping helper, see services/arabic_text.py) should be used.
FONT_REGULAR = "assets/fonts/Tajawal-Regular.ttf"
FONT_BOLD = "assets/fonts/Tajawal-Bold.ttf"

APP_TITLE = "دفتر"

"""
terminal.mk colour palette
---------------------------------
Kept in one place so the CLI (ANSI truecolor) and the future GUI (Tk/HTML
colours) both draw from the exact same source of truth.
"""

# Hex palette as supplied by terminal.mk
TEXT = "#9fb3ca"        # whitish accent / primary text
BG = "#2e3b4e"          # dark accent / page background
ACCENT_WINE = "#a52a53"    # maroon accent (Download All / warnings)
ACCENT_TEAL = "#26a69a"    # teal accent (Export / success / links)
ACCENT_ORANGE = "#ff8c00"  # orange accent (Filter / highlights)

# A few extra tones derived from the CF.css stylesheet, useful for panels
# and borders in both the CLI and the GUI.
BG_SECONDARY = "#344357"
BG_PANEL = "#3b4e6e"
TEXT_MUTED = "#a0b5d3"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


class Ansi:
    """24-bit ANSI truecolor helpers, with a graceful no-color fallback."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def fg(self, hex_color: str, text: str) -> str:
        if not self.enabled:
            return text
        r, g, b = _hex_to_rgb(hex_color)
        return f"\x1b[38;2;{r};{g};{b}m{text}\x1b[0m"

    def bold(self, text: str) -> str:
        if not self.enabled:
            return text
        return f"\x1b[1m{text}\x1b[0m"

    def dim(self, text: str) -> str:
        if not self.enabled:
            return text
        return f"\x1b[2m{text}\x1b[0m"

    # convenience wrappers matching the palette's semantic roles
    def text(self, s: str) -> str:
        return self.fg(TEXT, s)

    def muted(self, s: str) -> str:
        return self.fg(TEXT_MUTED, s)

    def teal(self, s: str) -> str:
        return self.fg(ACCENT_TEAL, s)

    def orange(self, s: str) -> str:
        return self.fg(ACCENT_ORANGE, s)

    def wine(self, s: str) -> str:
        return self.fg(ACCENT_WINE, s)

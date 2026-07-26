# -*- coding: utf-8 -*-
"""Оформлення застосунку.

Палітра взята з логотипа «Освітнього простору №8»: темно-синій, помаранчевий,
зелений. Стиль діловий: без прикрас, з опорою на типографіку документа.
"""
import os
import tkinter as tk
from tkinter import font as tkfont

# ---- основа ----
BG = "#EEF1F5"            # тло робочої області
BG_DARK = "#E3E8EF"       # смуги згори й знизу
CARD = "#FFFFFF"
CARD_EDGE = "#D5DCE5"
HAIRLINE = "#E6EAF0"

# ---- фірмові кольори (з логотипа) ----
NAVY = "#15356B"
NAVY_DARK = "#0E2A57"
ORANGE = "#F39200"
GREEN = "#2E9E5B"

# ---- текст ----
INK = "#1C2733"
INK_SOFT = "#5B6B7C"
INK_MUTED = "#8A97A5"
INK_RED = "#B3261E"
INK_GREEN = "#1E7A45"
ON_NAVY = "#FFFFFF"

# ---- підказка ----
HINT_BG = "#EDF2F9"
HINT_EDGE = "#C7D6E8"
HINT_INK = "#274067"

# сумісність зі старими назвами
PAPER = BG
PAPER_DARK = BG_DARK
STICKER = HINT_BG
STICKER_EDGE = HINT_EDGE
STICKER_INK = HINT_INK

# ---- акценти розділів (приглушені, ділові) ----
TAB_COLORS = {
    "green":  ("#E4F0E9", "#1E7A45"),
    "blue":   ("#E3EAF4", NAVY),
    "orange": ("#FBEBD6", "#A96400"),
    "red":    ("#F6E4E3", "#98322B"),
    "purple": ("#E8E6F1", "#4B3F73"),
    "teal":   ("#E0EDEC", "#1F5F5B"),
    "brown":  ("#EDE7DE", "#6B5433"),
}

_fonts = {}
_images = {}


def resources_dir():
    import sys
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "resources")


def image(name):
    """PhotoImage із кешем (Tk знищує картинку без посилання)."""
    if name not in _images:
        path = os.path.join(resources_dir(), name)
        if not os.path.exists(path):
            return None
        try:
            _images[name] = tk.PhotoImage(file=path)
        except tk.TclError:
            return None
    return _images[name]


def init_fonts(root, scale=1.0):
    have = set(tkfont.families(root))
    serif = next((f for f in ("Georgia", "Cambria", "Times New Roman", "Segoe UI")
                  if f in have), "TkDefaultFont")
    body = next((f for f in ("Segoe UI", "Tahoma", "Verdana") if f in have), "TkDefaultFont")

    def s(px):
        return max(9, int(round(px * scale)))

    _fonts.clear()
    _fonts.update({
        "hand_xl": (serif, s(21), "bold"),      # заголовок екрана
        "hand_l":  (serif, s(15), "bold"),      # назва програми
        "hand_m":  (serif, s(13), "bold"),      # підзаголовок
        "body":    (body, s(11)),
        "body_b":  (body, s(11), "bold"),
        "body_l":  (body, s(12)),
        "small":   (body, s(10)),
        "input":   (body, s(12)),
    })
    return _fonts


def f(name):
    return _fonts.get(name, ("TkDefaultFont", 11))


class Sheet(tk.Canvas):
    """Робоча область зі скролом. Віджети кладуться через add()."""

    PAD_LEFT = 34

    def __init__(self, master, **kw):
        super().__init__(master, bg=BG, highlightthickness=0, **kw)
        self._items = []      # [window_id, widget, pad_x, stretch, pad_y, fixed_h]
        self._total = 0
        self.bind("<Configure>", self._on_resize)

    # ---- побудова ----
    def add(self, widget, pad_x=None, pad_y=10, stretch=True, height=None):
        pad_x = self.PAD_LEFT if pad_x is None else pad_x
        wid = self.create_window(pad_x, 0, anchor="nw", window=widget)
        self._items.append([wid, widget, pad_x, stretch, pad_y, height])
        return widget

    def gap(self, px=14):
        self._items.append([None, None, 0, False, px, 0])

    def finish(self):
        self._apply_widths()
        self.update_idletasks()
        self._layout()
        self.after_idle(self._relayout)

    def _relayout(self):
        if not self.winfo_exists():
            return
        self._apply_widths()
        self.update_idletasks()
        self._layout()

    def _apply_widths(self):
        w = self.winfo_width() or self.winfo_reqwidth()
        for wid, _widget, pad_x, stretch, _pad_y, _fixed in self._items:
            if wid is not None and stretch:
                self.itemconfigure(wid, width=max(280, w - pad_x - self.PAD_LEFT))

    def _layout(self):
        y = 22
        for wid, widget, _pad_x, _stretch, pad_y, fixed in self._items:
            y += pad_y
            if wid is None:
                continue
            self.coords(wid, self.coords(wid)[0], y)
            y += fixed if fixed else widget.winfo_reqheight()
        self._total = y + 36
        self.configure(scrollregion=(0, 0, 10, self._total))

    def _on_resize(self, _evt=None):
        if self._items:
            self._apply_widths()
            self._layout()

    # ---- скрол ----
    def scrollable(self):
        try:
            first, last = self.yview()
        except tk.TclError:
            return False
        return (last - first) < 0.999

    def wheel(self, delta):
        if self.scrollable():
            self.yview_scroll(-1 * (delta // 120), "units")

    def clear(self):
        self.delete("all")
        self._items.clear()


# ---------- елементи ----------

def title(master, text, color=NAVY):
    return tk.Label(master, text=text, font=f("hand_xl"), fg=color, bg=BG,
                    anchor="w", justify="left", wraplength=980)


def subtitle(master, text, color=INK_SOFT):
    return tk.Label(master, text=text, font=f("hand_m"), fg=color, bg=BG,
                    anchor="w", justify="left", wraplength=980)


def paragraph(master, text, color=INK, font_key="body_l"):
    return tk.Label(master, text=text, font=f(font_key), fg=color, bg=BG,
                    anchor="w", justify="left", wraplength=980)


class Sticker(tk.Frame):
    """Блок підказки: світло-синій, зі смугою ліворуч. Без «наліпок»."""

    def __init__(self, master, heading, text, width=520):
        super().__init__(master, bg=HINT_EDGE, padx=1, pady=1)
        tk.Frame(self, bg=NAVY, width=4).pack(side="left", fill="y")
        inner = tk.Frame(self, bg=HINT_BG, padx=14, pady=11)
        inner.pack(side="left", fill="both", expand=True)
        if heading:
            tk.Label(inner, text=heading.upper(), font=f("small"), bg=HINT_BG,
                     fg=INK_MUTED, anchor="w", justify="left").pack(fill="x")
        tk.Label(inner, text=text, font=f("body"), bg=HINT_BG, fg=HINT_INK,
                 anchor="w", justify="left", wraplength=width).pack(fill="x", pady=(3, 0))


class Card(tk.Frame):
    def __init__(self, master, accent=None, **kw):
        super().__init__(master, bg=CARD_EDGE, padx=1, pady=1, **kw)
        if accent:
            tk.Frame(self, bg=accent, width=4).pack(side="left", fill="y")
        self.body = tk.Frame(self, bg=CARD, padx=16, pady=14)
        self.body.pack(side="left", fill="both", expand=True)


def button(master, text, command, kind="primary"):
    palette = {
        "primary":   (NAVY, ON_NAVY, NAVY_DARK),
        "secondary": ("#FFFFFF", NAVY, "#F0F3F8"),
        "danger":    (INK_RED, "#FFFFFF", "#8E1E17"),
        "ghost":     (BG_DARK, INK_SOFT, "#D3DAE3"),
    }[kind]
    b = tk.Button(master, text=text, command=command, font=f("body_b"),
                  bg=palette[0], fg=palette[1], activebackground=palette[2],
                  activeforeground=palette[1], relief="flat", padx=20, pady=9,
                  cursor="hand2", borderwidth=0,
                  highlightthickness=1 if kind == "secondary" else 0,
                  highlightbackground=CARD_EDGE)
    return b


def text_area(master, height=7):
    return tk.Text(master, height=height, font=f("input"), fg=INK, bg=CARD,
                   relief="flat", wrap="word", padx=10, pady=8,
                   insertbackground=NAVY, selectbackground="#CBDBF0",
                   highlightthickness=1, highlightbackground=CARD_EDGE,
                   highlightcolor=NAVY, undo=True, spacing1=1, spacing3=3)


def entry(master, width=40):
    return tk.Entry(master, font=f("input"), fg=INK, bg=CARD, relief="flat",
                    width=width, insertbackground=NAVY,
                    highlightthickness=1, highlightbackground=CARD_EDGE,
                    highlightcolor=NAVY)

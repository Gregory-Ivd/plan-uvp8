# -*- coding: utf-8 -*-
"""Екрани: заставка, інструкція, шапка документа, розділ плану."""
import tkinter as tk
from tkinter import ttk

import theme
from theme import (CARD, INK, INK_RED, INK_SOFT, PAPER, TAB_COLORS, Card, Sheet,
                   Sticker, f, paragraph, subtitle, title)


class BaseScreen(tk.Frame):
    """Аркуш зі скролом. Нащадки заповнюють self.sheet у build()."""

    def __init__(self, app):
        super().__init__(app.body, bg=PAPER)
        self.app = app
        self.doc = app.doc
        self.sheet = Sheet(self)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.sheet.yview)
        self.sheet.configure(yscrollcommand=bar.set)
        self.sheet.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.build()
        self.sheet.finish()

    def relayout(self):
        """Викликається, коли віджет змінив висоту (наприклад, розгорнули приклад)."""
        self.sheet._relayout()

    def build(self):
        raise NotImplementedError

    def collect(self):
        """Зберегти введене в модель. Викликається перед переходом."""

    def next_label(self):
        return "Далі  ›"

    def can_leave(self):
        return True


# --------------------------------------------------------------------------- #

class WelcomeScreen(BaseScreen):

    def build(self):
        tpl = self.doc.tpl
        self.sheet.add(title(self.sheet, tpl.get("app_title", "Мій план")), pad_y=40)
        self.sheet.add(subtitle(self.sheet, tpl["doc_title"]))
        self.sheet.gap(18)

        card = Card(self.sheet, accent=TAB_COLORS["blue"][1])
        tk.Label(card.body, text="Ця програма допоможе скласти власний план", font=f("hand_m"),
                 bg=CARD, fg=INK, anchor="w", justify="left").pack(fill="x")
        tk.Label(card.body, font=f("body_l"), bg=CARD, fg=INK_SOFT, anchor="w",
                 justify="left", wraplength=760, text=(
                     "Спочатку — коротка інструкція: що це за документ і на чому він "
                     "ґрунтується.\nПотім ви заповните шапку і 13 розділів. У кожному "
                     "розділі буде підказка й живий приклад.\nНаприкінці програма "
                     "перевірить типові помилки, покаже чернетку і збереже готовий "
                     "документ у Word і PDF — його можна одразу роздрукувати.")
                 ).pack(fill="x", pady=(8, 0))
        self.sheet.add(card)
        self.sheet.gap(20)

        made = tpl.get("made_by", "")
        if made:
            box = tk.Frame(self.sheet, bg=theme.HINT_EDGE, padx=1, pady=1)
            tk.Frame(box, bg=theme.NAVY, width=4).pack(side="left", fill="y")
            inner = tk.Frame(box, bg=theme.HINT_BG, padx=16, pady=14)
            inner.pack(side="left", fill="both", expand=True)
            logo = theme.image("logo.png")
            if logo:
                tk.Label(inner, image=logo, bg=theme.HINT_BG).pack(side="left",
                                                                  padx=(0, 16))
            texts = tk.Frame(inner, bg=theme.HINT_BG)
            texts.pack(side="left", fill="both", expand=True)
            tk.Label(texts, text="ХТО ЗРОБИВ ЦЮ ПРОГРАМУ", font=f("small"),
                     bg=theme.HINT_BG, fg=theme.INK_MUTED, anchor="w").pack(fill="x")
            tk.Label(texts, text=made, font=f("body_l"), bg=theme.HINT_BG,
                     fg=theme.HINT_INK, anchor="w", justify="left",
                     wraplength=520).pack(fill="x", pady=(4, 0))
            self.sheet.add(box, stretch=False)
        self.sheet.gap(10)

    def next_label(self):
        return "Почати  ›"


# --------------------------------------------------------------------------- #

class InstructionScreen(BaseScreen):

    def build(self):
        self.sheet.add(title(self.sheet, "Коротка інструкція"), pad_y=26)
        self.sheet.gap(6)
        palette = ["blue", "green", "red", "orange", "purple"]
        for i, blk in enumerate(self.doc.tpl["instruction"]["blocks"]):
            accent = TAB_COLORS[palette[i % len(palette)]][1]
            card = Card(self.sheet, accent=accent)
            tk.Label(card.body, text=blk["heading"], font=f("hand_m"), bg=CARD, fg=accent,
                     anchor="w", justify="left").pack(fill="x")
            tk.Label(card.body, text=blk["text"], font=f("body_l"), bg=CARD, fg=INK,
                     anchor="w", justify="left", wraplength=780).pack(fill="x", pady=(6, 0))
            self.sheet.add(card)
            self.sheet.gap(6)


# --------------------------------------------------------------------------- #

class HeaderScreen(BaseScreen):

    def build(self):
        self.sheet.add(title(self.sheet, "Шапка документа"), pad_y=26)
        self.sheet.add(paragraph(self.sheet,
                                 "Так, як пишеться на паперовому бланку.", font_key="body_l"))
        self.sheet.gap(10)

        self.entries = {}
        card = Card(self.sheet, accent=TAB_COLORS["blue"][1])
        for fld in self.doc.tpl.get("header_fields", []):
            row = tk.Frame(card.body, bg=CARD)
            row.pack(fill="x", pady=6)
            star = " *" if fld.get("required") else ""
            tk.Label(row, text=fld["label"] + star, font=f("body_b"), bg=CARD, fg=INK,
                     anchor="w", width=34).pack(side="left")
            ent = theme.entry(row, width=fld.get("width", 40))
            ent.insert(0, self.doc.header.get(fld["id"], ""))
            ent.pack(side="left", ipady=4)
            self.entries[fld["id"]] = ent
            if fld.get("hint"):
                tk.Label(card.body, text=fld["hint"], font=f("small"), bg=CARD,
                         fg=INK_SOFT, anchor="w").pack(fill="x", padx=(0, 0))
        self.sheet.add(card)
        self.sheet.gap(18)

        need = self.doc.tpl.get("need_field", {})
        self.sheet.add(subtitle(self.sheet, need.get("label", "Криміногенна потреба")))
        self.sheet.gap(4)
        self.sheet.add(Sticker(self.sheet, None, need.get("hint", ""), width=760))
        self.sheet.gap(8)
        card2 = Card(self.sheet)
        self.need_text = theme.text_area(card2.body, height=6)
        self.need_text.insert("1.0", self.doc.need)
        self.need_text.pack(fill="both", expand=True)
        self.sheet.add(card2)
        self.sheet.gap(8)
        if need.get("example"):
            self.sheet.add(ExampleBox(self.sheet, need["example"], self.relayout))

    def collect(self):
        for key, ent in self.entries.items():
            self.doc.header[key] = ent.get().strip()
        self.doc.need = self.need_text.get("1.0", "end").strip()


# --------------------------------------------------------------------------- #

class ExampleBox(tk.Frame):
    """Приклад, згорнутий за замовчуванням."""

    def __init__(self, master, text, on_toggle=None):
        super().__init__(master, bg=PAPER)
        self.shown = False
        self.on_toggle = on_toggle
        self.btn = tk.Button(self, text="▸  Показати приклад", command=self.toggle,
                             font=f("body_b"), bg=PAPER, fg=theme.NAVY, relief="flat",
                             cursor="hand2", anchor="w", borderwidth=0,
                             activebackground=PAPER, activeforeground=INK)
        self.btn.pack(fill="x")
        self.lbl = tk.Label(self, text=text, font=f("body"), bg="#F7F9FC", fg=INK_SOFT,
                            anchor="w", justify="left", wraplength=740, padx=14, pady=12,
                            highlightthickness=1, highlightbackground=theme.HAIRLINE)

    def toggle(self):
        self.shown = not self.shown
        if self.shown:
            self.lbl.pack(fill="x", pady=(6, 0))
            self.btn.configure(text="▾  Сховати приклад")
        else:
            self.lbl.pack_forget()
            self.btn.configure(text="▸  Показати приклад")
        if self.on_toggle:
            self.on_toggle()


# --------------------------------------------------------------------------- #

class SectionScreen(BaseScreen):

    def __init__(self, app, spec):
        self.spec = spec
        super().__init__(app)

    def build(self):
        spec = self.spec
        data = self.doc.sections[spec["id"]]
        bg_col, ink_col = TAB_COLORS.get(spec.get("color", "blue"), TAB_COLORS["blue"])

        tab = tk.Frame(self.sheet, bg=bg_col, padx=14, pady=6)
        tk.Label(tab, text=f"Розділ {spec['number']} із {len(self.doc.tpl['sections'])}",
                 font=f("body_b"), bg=bg_col, fg=ink_col).pack()
        self.sheet.add(tab, pad_y=22, stretch=False)
        self.sheet.gap(4)
        self.sheet.add(title(self.sheet, spec["title"], color=ink_col))
        self.sheet.gap(10)

        if spec.get("hint"):
            self.sheet.add(Sticker(self.sheet, "Що тут писати", spec["hint"], width=760))
            self.sheet.gap(10)

        # --- проміжні цілі ---
        card = Card(self.sheet, accent=ink_col)
        tk.Label(card.body, text="Проміжні цілі", font=f("body_b"), bg=CARD, fg=INK,
                 anchor="w").pack(fill="x")
        self.goals = theme.text_area(card.body, height=7)
        self.goals.insert("1.0", data["goals"])
        self.goals.pack(fill="both", expand=True, pady=(6, 0))
        self.counter = tk.Label(card.body, text="", font=f("small"), bg=CARD,
                                fg=INK_SOFT, anchor="e")
        self.counter.pack(fill="x")
        self.goals.bind("<KeyRelease>", self._count)
        self.sheet.add(card)
        self.sheet.gap(6)
        if spec.get("example"):
            self.sheet.add(ExampleBox(self.sheet, spec["example"], self.relayout))
            self.sheet.gap(4)
        if spec.get("avoid"):
            avoid = "\n".join("•  " + a for a in spec["avoid"])
            self.sheet.add(tk.Label(self.sheet, text="Чого краще уникати:\n" + avoid,
                                    font=f("body"), bg=PAPER, fg=INK_RED, anchor="w",
                                    justify="left", wraplength=760))
        self.sheet.gap(14)

        # --- термін ---
        card2 = Card(self.sheet, accent=ink_col)
        tk.Label(card2.body, text="Термін виконання", font=f("body_b"), bg=CARD, fg=INK,
                 anchor="w").pack(fill="x")
        self.term = ttk.Combobox(card2.body, values=spec.get("terms", []),
                                 font=f("input"), width=52)
        self.term.set(data["term"])
        self.term.pack(anchor="w", pady=(6, 0))
        tk.Label(card2.body, text="Можна вибрати зі списку або написати свій.",
                 font=f("small"), bg=CARD, fg=INK_SOFT, anchor="w").pack(fill="x", pady=(4, 0))
        self.sheet.add(card2)
        self.sheet.gap(14)

        # --- перепони ---
        card3 = Card(self.sheet, accent=ink_col)
        tk.Label(card3.body, text="Перепони та їх можливе вирішення", font=f("body_b"),
                 bg=CARD, fg=INK, anchor="w").pack(fill="x")
        if spec.get("obstacles_hint"):
            tk.Label(card3.body, text=spec["obstacles_hint"], font=f("small"), bg=CARD,
                     fg=INK_SOFT, anchor="w", justify="left",
                     wraplength=740).pack(fill="x", pady=(2, 0))
        self.obst = theme.text_area(card3.body, height=6)
        self.obst.insert("1.0", data["obstacles"])
        self.obst.pack(fill="both", expand=True, pady=(6, 0))
        self.sheet.add(card3)
        self.sheet.gap(10)

        self.skip_var = tk.BooleanVar(value=data["skipped"])
        chk = tk.Checkbutton(self.sheet, text="Цей розділ мене не стосується",
                             variable=self.skip_var, font=f("body"), bg=PAPER, fg=INK_SOFT,
                             activebackground=PAPER, selectcolor=CARD, anchor="w",
                             cursor="hand2")
        self.sheet.add(chk, stretch=False)
        self._count()

    def _count(self, _evt=None):
        n = len(self.goals.get("1.0", "end").strip())
        need = self.spec.get("min_chars", 0)
        if need and n < need:
            self.counter.configure(text=f"{n} знаків — бажано хоча б {need}", fg=INK_RED)
        else:
            self.counter.configure(text=f"{n} знаків", fg=INK_SOFT)

    def collect(self):
        self.doc.sections[self.spec["id"]] = {
            "goals": self.goals.get("1.0", "end").strip(),
            "term": self.term.get().strip(),
            "obstacles": self.obst.get("1.0", "end").strip(),
            "skipped": bool(self.skip_var.get()),
        }

# -*- coding: utf-8 -*-
"""Завершальні екрани: перевірка, чернетка, вивантаження."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

import render_docx
import render_pdf
import template
import theme
import validation
from screens import BaseScreen
from theme import (CARD, INK, INK_GREEN, INK_RED, INK_SOFT, PAPER, TAB_COLORS, Card,
                   Sticker, f, paragraph, title)

LEVEL_STYLE = {
    validation.BLOCK: ("Треба виправити", INK_RED),
    validation.WARN:  ("Варто подумати", "#8A5A1E"),
    validation.HINT:  ("Дрібниця", INK_SOFT),
}


class ReviewScreen(BaseScreen):

    def build(self):
        self.sheet.add(title(self.sheet, "Перевірка"), pad_y=26)
        issues = validation.check(self.doc)
        counts = validation.summary(issues)
        done, total = self.doc.progress()

        if not issues:
            self.sheet.add(paragraph(self.sheet,
                                     f"Заповнено {done} із {total} розділів. "
                                     "Зауважень немає — можна дивитись чернетку.",
                                     color=INK_GREEN))
            return

        self.sheet.add(paragraph(self.sheet, (
            f"Заповнено {done} із {total} розділів. "
            f"Знайдено: {counts[validation.BLOCK]} треба виправити, "
            f"{counts[validation.WARN]} варто подумати, {counts[validation.HINT]} дрібниць.")))
        self.sheet.gap(6)
        self.sheet.add(Sticker(self.sheet, None,
                               "Виправити обов'язково потрібно лише червоні пункти. "
                               "Решта — поради: ви маєте право написати по-своєму.",
                               width=760))
        self.sheet.gap(12)

        order = {validation.BLOCK: 0, validation.WARN: 1, validation.HINT: 2}
        for issue in sorted(issues, key=lambda i: order[i.level]):
            label, colour = LEVEL_STYLE[issue.level]
            card = Card(self.sheet, accent=colour)
            top = tk.Frame(card.body, bg=CARD)
            top.pack(fill="x")
            tk.Label(top, text=f"{label} · {issue.where}", font=f("body_b"), bg=CARD,
                     fg=colour, anchor="w").pack(side="left")
            if issue.fix:
                tk.Button(top, text="Виправити", font=f("small"), bg=CARD, fg=INK,
                          relief="flat", cursor="hand2", borderwidth=0,
                          activebackground=CARD,
                          command=lambda i=issue: self._apply_fix(i)).pack(side="right")
            elif issue.sid:
                tk.Button(top, text="Перейти", font=f("small"), bg=CARD, fg=INK,
                          relief="flat", cursor="hand2", borderwidth=0,
                          activebackground=CARD,
                          command=lambda i=issue: self.app.goto_section(i.sid)).pack(side="right")
            tk.Label(card.body, text=issue.text, font=f("body"), bg=CARD, fg=INK,
                     anchor="w", justify="left", wraplength=740).pack(fill="x", pady=(4, 0))
            self.sheet.add(card)
            self.sheet.gap(4)

    def _apply_fix(self, issue):
        bad, good = issue.fix
        data = self.doc.sections[issue.sid]
        for key in ("goals", "term", "obstacles"):
            data[key] = validation.apply_russism_fix(data[key], bad, good)
        self.app.rebuild_current()

    def can_leave(self):
        blocking = [i for i in validation.check(self.doc) if i.level == validation.BLOCK]
        if blocking:
            messagebox.showwarning(
                "Ще не все заповнено",
                "Спершу виправте червоні пункти:\n\n"
                + "\n".join(f"• {i.where}: {i.text}" for i in blocking[:6]))
            return False
        return True

    def next_label(self):
        return "Дивитись чернетку  ›"


# --------------------------------------------------------------------------- #

class PreviewScreen(BaseScreen):

    def build(self):
        self.sheet.add(title(self.sheet, "Чернетка"), pad_y=26)
        self.sheet.add(paragraph(self.sheet,
                                 "Це весь текст майбутнього документа. Прочитайте вголос — "
                                 "так найкраще видно незграбні місця."))
        self.sheet.gap(10)
        card = Card(self.sheet)
        txt = tk.Text(card.body, font=("Consolas", 10), bg=CARD, fg=INK, relief="flat",
                      wrap="word", height=30, padx=10, pady=8)
        txt.insert("1.0", as_text(self.doc))
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True)
        self.sheet.add(card, height=520)

    def next_label(self):
        return "До вивантаження  ›"


def as_text(doc):
    tpl = doc.tpl
    out = [tpl["doc_title"].upper(), ""]
    out.append(f"Засудженого {doc.title_line()}")
    date_from, date_to = doc.period()
    out.append(f"на період з {date_from or '___'} по {date_to or '___'}")
    out.append("")
    out.append((tpl.get("need_field") or {}).get("label", "Криміногенна потреба").upper())
    out.append(doc.need.strip() or "(не заповнено)")
    out.append("")
    for group, caption in (("during", "НАМІРИ ТА ПЛАНИ ПІД ЧАС ВІДБУВАННЯ ПОКАРАННЯ"),
                           ("after", "НАМІРИ ТА ПЛАНИ ПІСЛЯ ЗВІЛЬНЕННЯ")):
        specs = [s for s in tpl["sections"] if s["group"] == group]
        if not specs:
            continue
        out += ["=" * 70, caption, "=" * 70, ""]
        for spec in specs:
            data = doc.sections[spec["id"]]
            if data["skipped"] and not data["goals"].strip():
                continue
            out.append(f"{spec['number']}. {spec['title']}")
            out.append(f"   Проміжні цілі: {data['goals'].strip() or '(порожньо)'}")
            out.append(f"   Термін: {data['term'].strip() or '(порожньо)'}")
            out.append(f"   Перепони: {data['obstacles'].strip() or '(порожньо)'}")
            out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #

class ExportScreen(BaseScreen):

    def build(self):
        self.sheet.add(title(self.sheet, "Готово"), pad_y=26)
        self.sheet.add(paragraph(self.sheet,
                                 "Оберіть, у якому вигляді зберегти документ. "
                                 "Файли лягають у теку «export» поруч із програмою."))
        self.sheet.gap(14)

        card = Card(self.sheet, accent=TAB_COLORS["green"][1])
        row = tk.Frame(card.body, bg=CARD)
        row.pack(fill="x")
        theme.button(row, "Зберегти Word (.docx)", self.save_docx).pack(side="left", padx=(0, 10))
        theme.button(row, "Зберегти PDF", self.save_pdf, "secondary").pack(side="left", padx=(0, 10))
        theme.button(row, "Друк", self.print_doc, "secondary").pack(side="left")
        self.status = tk.Label(card.body, text="", font=f("body"), bg=CARD, fg=INK_GREEN,
                               anchor="w", justify="left", wraplength=740)
        self.status.pack(fill="x", pady=(12, 0))
        self.sheet.add(card)
        self.sheet.gap(16)

        self.sheet.add(Sticker(self.sheet, "Що далі",
                               "Роздрукуйте документ і підпишіть його від руки. Другий підпис "
                               "ставить начальник відділення СПС. Рамку «Висновки щодо "
                               "результатів реалізації» заповнюють у кінці періоду — вона має "
                               "лишитися порожньою.", width=760))
        self.sheet.gap(14)
        theme_row = tk.Frame(self.sheet, bg=PAPER)
        theme.button(theme_row, "Відкрити теку з файлами", self.open_folder,
                     "ghost").pack(side="left")
        theme.button(theme_row, "Почати новий план", self.app.start_over,
                     "ghost").pack(side="left", padx=10)
        self.sheet.add(theme_row, stretch=False)

    # ---- дії ----
    def _target(self, ext):
        name = f"{self.doc.safe_filename()} — індивідуальний план{ext}"
        return os.path.join(template.export_dir(), name)

    def save_docx(self):
        try:
            path = render_docx.build(self.doc, self._target(".docx"))
        except Exception as exc:                                    # noqa: BLE001
            messagebox.showerror("Не вдалося зберегти", str(exc))
            return None
        self.status.configure(text=f"Збережено:\n{path}", fg=INK_GREEN)
        template.clear_draft()
        return path

    def save_pdf(self):
        try:
            path = render_pdf.build(self.doc, self._target(".pdf"))
        except Exception as exc:                                    # noqa: BLE001
            messagebox.showerror("Не вдалося зберегти PDF", str(exc))
            return None
        self.status.configure(text=f"Збережено:\n{path}", fg=INK_GREEN)
        template.clear_draft()
        return path

    def print_doc(self):
        path = self.save_docx()
        if not path:
            return
        try:
            os.startfile(path, "print")                              # noqa: S606
            self.status.configure(text="Відправлено на принтер, що встановлений "
                                       "за замовчуванням.", fg=INK_GREEN)
            return
        except OSError:
            pass
        pdf = self.save_pdf()
        if pdf:
            try:
                os.startfile(pdf)                                    # noqa: S606
                self.status.configure(
                    text="Word на цьому комп'ютері не знайдено. Відкрито PDF — "
                         "натисніть Ctrl+P, щоб надрукувати.", fg=INK_RED)
            except OSError:
                messagebox.showinfo("Друк", f"Відкрийте файл вручну:\n{pdf}")

    def open_folder(self):
        path = template.export_dir()
        try:
            if sys.platform == "win32":
                os.startfile(path)                                   # noqa: S606
            else:
                subprocess.Popen(["xdg-open", path])                 # noqa: S607
        except OSError as exc:
            messagebox.showinfo("Тека з файлами", f"{path}\n\n{exc}")

    def next_label(self):
        return ""

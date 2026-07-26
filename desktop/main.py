# -*- coding: utf-8 -*-
"""«Мій план» — застосунок для заповнення індивідуального плану
виправлення та ресоціалізації.

Продукт навчання та роботи учасників «Освітнього простору №8».
"""
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import admin
import document
import finish
import screens
import template
import theme
from theme import INK, INK_SOFT, PAPER, PAPER_DARK, f

AUTOSAVE_MS = 30_000
SCALES = (1.15, 1.35, 1.55)


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        try:
            self.tpl = template.load_template()
        except Exception as exc:                                    # noqa: BLE001
            messagebox.showerror("Помилка шаблону",
                                 f"Не вдалося прочитати шаблон документа.\n\n{exc}")
            self.destroy()
            sys.exit(1)

        self.doc = document.PlanDocument(self.tpl)
        self._scale_idx = 0
        theme.init_fonts(self, SCALES[self._scale_idx])

        self.title(self.tpl.get("app_title", "Мій план"))
        self.minsize(940, 640)
        self.configure(bg=PAPER)
        self._centre(1120, 820)
        ico = os.path.join(theme.resources_dir(), "app.ico")
        if os.path.exists(ico):
            try:
                self.iconbitmap(ico)
            except tk.TclError:
                pass

        self._build_chrome()
        self._build_steps()
        self.current = None
        self.index = 0

        self._offer_draft()
        self.show(0)
        self._bind_scrolling()
        self.after(AUTOSAVE_MS, self._autosave)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------- прокручування ----------------
    def _bind_scrolling(self):
        self.bind_all("<MouseWheel>", self._on_wheel)
        for key, amount in (("<Prior>", -5), ("<Next>", 5),
                            ("<Home>", None), ("<End>", None)):
            self.bind_all(key, lambda e, a=amount: self._scroll_key(a))

    def _sheet(self):
        return getattr(self.current, "sheet", None)

    def _on_wheel(self, evt):
        # Якщо курсор над полем вводу, яке саме має що прокручувати, не заважаємо йому.
        try:
            under = self.winfo_containing(evt.x_root, evt.y_root)
        except tk.TclError:
            under = None
        if isinstance(under, tk.Text):
            first, last = under.yview()
            if (last - first) < 0.999:
                return
        sheet = self._sheet()
        if sheet is not None:
            sheet.wheel(evt.delta)

    def _scroll_key(self, amount):
        sheet = self._sheet()
        if sheet is None or not sheet.scrollable():
            return
        if amount is None:
            sheet.yview_moveto(0.0)
        else:
            sheet.yview_scroll(amount, "units")

    def _centre(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(w, sw - 80), min(h, sh - 120)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 20)}")

    # ---------------- каркас вікна ----------------
    def _build_chrome(self):
        # ---- верхня смуга ----
        top = tk.Frame(self, bg=theme.NAVY, padx=18, pady=11)
        top.pack(side="top", fill="x")
        logo = theme.image("logo_small.png")
        if logo:
            tk.Label(top, image=logo, bg=theme.NAVY).pack(side="left", padx=(0, 12))
        tk.Label(top, text=self.tpl.get("app_title", "Мій план"), font=f("hand_l"),
                 bg=theme.NAVY, fg=theme.ON_NAVY).pack(side="left")
        self.progress = tk.Label(top, text="", font=f("body_b"), bg=theme.NAVY,
                                 fg="#B9C7DD")
        self.progress.pack(side="left", padx=26)

        theme.button(top, "Редактор шаблону", self.open_admin, "ghost").pack(side="right")
        theme.button(top, "Аа", self.cycle_scale, "ghost").pack(side="right", padx=8)

        # ---- нижня смуга: пакуємо ДО робочої області, інакше її витісняє за край ----
        bottom = tk.Frame(self, bg=PAPER_DARK, padx=18, pady=12)
        bottom.pack(side="bottom", fill="x")
        tk.Frame(bottom, bg=theme.CARD_EDGE, height=1).place(x=0, y=0, relwidth=1)
        self.btn_back = theme.button(bottom, "‹  Назад", self.back, "secondary")
        self.btn_back.pack(side="left")
        self.btn_next = theme.button(bottom, "Далі  ›", self.next)
        self.btn_next.pack(side="right")
        self.hint = tk.Label(bottom, text="", font=f("small"), bg=PAPER_DARK, fg=INK_SOFT)
        self.hint.pack(side="right", padx=16)

        self.body = tk.Frame(self, bg=PAPER)
        self.body.pack(side="top", fill="both", expand=True)

    def _build_steps(self):
        self.steps = ["welcome", "instruction", "header"]
        self.steps += [s["id"] for s in self.tpl["sections"]]
        self.steps += ["review", "preview", "export"]

    # ---------------- навігація ----------------
    def _make_screen(self, key):
        if key == "welcome":
            return screens.WelcomeScreen(self)
        if key == "instruction":
            return screens.InstructionScreen(self)
        if key == "header":
            return screens.HeaderScreen(self)
        if key == "review":
            return finish.ReviewScreen(self)
        if key == "preview":
            return finish.PreviewScreen(self)
        if key == "export":
            return finish.ExportScreen(self)
        spec = next(s for s in self.tpl["sections"] if s["id"] == key)
        return screens.SectionScreen(self, spec)

    def show(self, index):
        index = max(0, min(index, len(self.steps) - 1))
        if self.current is not None:
            self.current.collect()
            self.current.destroy()
        self.index = index
        self.current = self._make_screen(self.steps[index])
        self.current.pack(fill="both", expand=True)
        self._refresh_chrome()

    def rebuild_current(self):
        key = self.steps[self.index]
        if self.current is not None:
            self.current.destroy()
        self.current = self._make_screen(key)
        self.current.pack(fill="both", expand=True)
        self._refresh_chrome()

    def _refresh_chrome(self):
        done, total = self.doc.progress()
        self.progress.configure(text=f"Заповнено {done} із {total} розділів")
        label = self.current.next_label()
        if label:
            self.btn_next.configure(text=label, state="normal")
        else:
            self.btn_next.configure(text="Завершити", state="normal")
        self.btn_back.configure(state="normal" if self.index > 0 else "disabled")
        key = self.steps[self.index]
        if key in ("welcome", "instruction", "header", "review", "preview", "export"):
            self.hint.configure(text="")
        else:
            self.hint.configure(text="Порожній розділ можна пропустити галочкою внизу")

    def next(self):
        if self.steps[self.index] == "export":
            self._on_close()
            return
        self.current.collect()
        if not self.current.can_leave():
            return
        self.show(self.index + 1)

    def back(self):
        self.show(self.index - 1)

    def goto_section(self, sid):
        if sid in self.steps:
            self.show(self.steps.index(sid))

    # ---------------- сервіс ----------------
    def cycle_scale(self):
        self._scale_idx = (self._scale_idx + 1) % len(SCALES)
        theme.init_fonts(self, SCALES[self._scale_idx])
        self.current.collect()
        self._rebuild_all()

    def _rebuild_all(self):
        for child in self.winfo_children():
            child.destroy()
        self._build_chrome()
        self.current = None
        self.show(self.index)

    def open_admin(self):
        if admin.authorise(self):
            admin.AdminWindow(self)

    def reload_template(self):
        try:
            self.tpl = template.load_template()
        except Exception as exc:                                    # noqa: BLE001
            messagebox.showerror("Помилка шаблону", str(exc))
            return
        saved = self.doc.to_dict()
        self.doc = document.PlanDocument(self.tpl)
        self.doc.load_dict(saved)
        self._build_steps()
        self.index = min(self.index, len(self.steps) - 1)
        self._rebuild_all()

    def start_over(self):
        if not messagebox.askyesno("Почати новий план",
                                   "Усе введене буде стерто. Продовжити?"):
            return
        template.clear_draft()
        self.doc = document.PlanDocument(self.tpl)
        self.current = None
        self._rebuild_all_from(0)

    def _rebuild_all_from(self, index):
        self.index = index
        for child in self.winfo_children():
            child.destroy()
        self._build_chrome()
        self.current = None
        self.show(index)

    # ---------------- чернетка ----------------
    def _offer_draft(self):
        data = template.load_draft()
        if not data:
            return
        if messagebox.askyesno(
                "Знайдено незавершену чернетку",
                "Минулого разу програму закрили, не зберігши документ.\n\n"
                "Продовжити з того місця?"):
            self.doc.load_dict(data)
        else:
            template.clear_draft()

    def _autosave(self):
        try:
            if self.current is not None:
                self.current.collect()
            if self.doc.pib() or any(v["goals"] for v in self.doc.sections.values()):
                template.save_draft(self.doc.to_dict())
        finally:
            self.after(AUTOSAVE_MS, self._autosave)

    def _on_close(self):
        if self.current is not None:
            self.current.collect()
        has_data = self.doc.pib() or any(v["goals"] for v in self.doc.sections.values())
        if has_data:
            answer = messagebox.askyesnocancel(
                "Вихід",
                "Зберегти чернетку, щоб продовжити пізніше?\n\n"
                "Так — зберегти й вийти.\nНі — вийти й нічого не лишати.")
            if answer is None:
                return
            if answer:
                template.save_draft(self.doc.to_dict())
            else:
                template.clear_draft()
        self.destroy()


def main():
    app = App()
    # Стиль створюємо тільки після головного вікна, інакше ttk відкриє друге, порожнє.
    try:
        ttk.Style(app).theme_use("clam")
    except tk.TclError:
        pass
    app.mainloop()


if __name__ == "__main__":
    main()

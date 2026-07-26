# -*- coding: utf-8 -*-
"""Редактор шаблону для адміністрації. Захист паролем — від випадкової правки."""
import copy
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import template
import theme
from theme import CARD, CARD_EDGE, INK, INK_SOFT, PAPER, PAPER_DARK, f


def authorise(parent):
    """Перший вхід — задати пароль. Далі — перевірити."""
    if not template.has_password():
        messagebox.showinfo(
            "Редактор шаблону",
            "Цей режим призначений для адміністрації установи.\n\n"
            "Зараз ви задасте пароль. Він захищає шаблон від випадкових змін, "
            "а не від злому — не зберігайте в ньому нічого важливого.")
        first = simpledialog.askstring("Новий пароль", "Придумайте пароль:",
                                       show="•", parent=parent)
        if not first:
            return False
        again = simpledialog.askstring("Новий пароль", "Повторіть пароль:",
                                       show="•", parent=parent)
        if first != again:
            messagebox.showerror("Пароль", "Паролі не збігаються.")
            return False
        template.set_password(first)
        return True

    entered = simpledialog.askstring("Редактор шаблону", "Пароль:", show="•", parent=parent)
    if entered is None:
        return False
    if not template.check_password(entered):
        messagebox.showerror("Пароль", "Пароль неправильний.")
        return False
    return True


class AdminWindow(tk.Toplevel):

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.tpl = copy.deepcopy(app.tpl)
        self.current_sid = None

        self.title("Редактор шаблону документа")
        self.geometry("1080x720")
        self.configure(bg=PAPER)
        self.transient(app)
        self.grab_set()

        self._build()
        self._fill_list()
        if self.tpl["sections"]:
            self._select(self.tpl["sections"][0]["id"])

    # ---------------- каркас ----------------
    def _build(self):
        top = tk.Frame(self, bg=PAPER_DARK, padx=14, pady=10)
        top.pack(fill="x")
        tk.Label(top, text="Редактор шаблону", font=f("hand_l"), bg=PAPER_DARK,
                 fg=INK).pack(side="left")
        tk.Label(top, text="Зміни застосуються після натискання «Зберегти»",
                 font=f("small"), bg=PAPER_DARK, fg=INK_SOFT).pack(side="left", padx=16)
        theme.button(top, "Зберегти", self.save).pack(side="right")
        theme.button(top, "Скасувати", self.destroy, "secondary").pack(side="right", padx=8)

        main = tk.Frame(self, bg=PAPER)
        main.pack(fill="both", expand=True, padx=14, pady=12)

        # ---- ліворуч: загальне + список розділів ----
        left = tk.Frame(main, bg=PAPER, width=330)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="Загальні тексти", font=f("body_b"), bg=PAPER, fg=INK,
                 anchor="w").pack(fill="x")
        self.general = {}
        for key, label in (("doc_title", "Назва документа"),
                           ("app_title", "Назва програми")):
            tk.Label(left, text=label, font=f("small"), bg=PAPER, fg=INK_SOFT,
                     anchor="w").pack(fill="x", pady=(6, 0))
            ent = theme.entry(left, width=34)
            ent.insert(0, self.tpl.get(key, ""))
            ent.pack(fill="x", ipady=3)
            self.general[key] = ent
        theme.button(left, "Редагувати інструкцію", self.edit_instruction,
                     "secondary").pack(fill="x", pady=8)

        tk.Label(left, text="Розділи", font=f("body_b"), bg=PAPER, fg=INK,
                 anchor="w").pack(fill="x", pady=(12, 4))
        self.listbox = tk.Listbox(left, font=f("body"), bg=CARD, fg=INK, relief="flat",
                                  highlightthickness=1, highlightbackground=CARD_EDGE,
                                  activestyle="none", selectbackground="#CFE0F5",
                                  selectforeground=INK)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_pick)

        btns = tk.Frame(left, bg=PAPER)
        btns.pack(fill="x", pady=8)
        for text, cmd in (("Додати", self.add_section), ("Вилучити", self.remove_section),
                          ("↑", lambda: self.move(-1)), ("↓", lambda: self.move(1))):
            theme.button(btns, text, cmd, "secondary").pack(side="left", padx=(0, 5))

        io = tk.Frame(left, bg=PAPER)
        io.pack(fill="x")
        theme.button(io, "Експорт", self.export, "ghost").pack(side="left")
        theme.button(io, "Імпорт", self.do_import, "ghost").pack(side="left", padx=6)
        theme.button(io, "Скинути", self.reset, "ghost").pack(side="left")

        # ---- праворуч: форма розділу ----
        right = tk.Frame(main, bg=PAPER, padx=16)
        right.pack(side="left", fill="both", expand=True)
        self.fields = {}

        self._entry_row(right, "title", "Назва розділу")
        row = tk.Frame(right, bg=PAPER)
        row.pack(fill="x", pady=(8, 0))
        tk.Label(row, text="Блок", font=f("small"), bg=PAPER, fg=INK_SOFT,
                 width=12, anchor="w").pack(side="left")
        self.group = ttk.Combobox(row, values=["during", "after"], width=12, state="readonly")
        self.group.pack(side="left")
        tk.Label(row, text="Колір", font=f("small"), bg=PAPER, fg=INK_SOFT,
                 width=8, anchor="e").pack(side="left", padx=(14, 4))
        self.colour = ttk.Combobox(row, values=list(theme.TAB_COLORS), width=10,
                                   state="readonly")
        self.colour.pack(side="left")
        tk.Label(row, text="Мін. знаків", font=f("small"), bg=PAPER, fg=INK_SOFT,
                 anchor="e").pack(side="left", padx=(14, 4))
        self.min_chars = theme.entry(row, width=6)
        self.min_chars.pack(side="left", ipady=2)
        self.obst_req = tk.BooleanVar()
        tk.Checkbutton(row, text="перепони обов'язкові", variable=self.obst_req,
                       font=f("small"), bg=PAPER, fg=INK_SOFT, activebackground=PAPER,
                       selectcolor=CARD).pack(side="left", padx=12)

        self._text_row(right, "hint", "Підказка «Що тут писати»", 4)
        self._text_row(right, "obstacles_hint", "Підказка до перепон", 3)
        self._text_row(right, "example", "Приклад", 5)
        self._text_row(right, "avoid", "Чого уникати (по рядку на пункт)", 3)
        self._text_row(right, "terms", "Типові терміни (по рядку)", 3)

    def _entry_row(self, master, key, label):
        tk.Label(master, text=label, font=f("small"), bg=PAPER, fg=INK_SOFT,
                 anchor="w").pack(fill="x", pady=(8, 2))
        ent = theme.entry(master, width=70)
        ent.pack(fill="x", ipady=4)
        self.fields[key] = ent

    def _text_row(self, master, key, label, height):
        tk.Label(master, text=label, font=f("small"), bg=PAPER, fg=INK_SOFT,
                 anchor="w").pack(fill="x", pady=(10, 2))
        txt = theme.text_area(master, height=height)
        txt.pack(fill="x")
        self.fields[key] = txt

    # ---------------- дані ----------------
    def _fill_list(self):
        self.listbox.delete(0, "end")
        for s in self.tpl["sections"]:
            mark = "▸" if s["group"] == "during" else "◂"
            self.listbox.insert("end", f" {mark} {s['number']}. {s['title'][:44]}")

    def _spec(self, sid):
        return next(s for s in self.tpl["sections"] if s["id"] == sid)

    def _on_pick(self, _evt=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._store()
        self._select(self.tpl["sections"][sel[0]]["id"])

    def _select(self, sid):
        self.current_sid = sid
        spec = self._spec(sid)
        self.fields["title"].delete(0, "end")
        self.fields["title"].insert(0, spec.get("title", ""))
        self.group.set(spec.get("group", "during"))
        self.colour.set(spec.get("color", "blue"))
        self.min_chars.delete(0, "end")
        self.min_chars.insert(0, str(spec.get("min_chars", 0)))
        self.obst_req.set(bool(spec.get("obstacles_required", False)))
        for key in ("hint", "obstacles_hint", "example"):
            self.fields[key].delete("1.0", "end")
            self.fields[key].insert("1.0", spec.get(key, ""))
        for key in ("avoid", "terms"):
            self.fields[key].delete("1.0", "end")
            self.fields[key].insert("1.0", "\n".join(spec.get(key, [])))
        idx = [s["id"] for s in self.tpl["sections"]].index(sid)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx)

    def _store(self):
        if not self.current_sid:
            return
        spec = self._spec(self.current_sid)
        spec["title"] = self.fields["title"].get().strip()
        spec["group"] = self.group.get() or "during"
        spec["color"] = self.colour.get() or "blue"
        try:
            spec["min_chars"] = int(self.min_chars.get() or 0)
        except ValueError:
            spec["min_chars"] = 0
        spec["obstacles_required"] = bool(self.obst_req.get())
        for key in ("hint", "obstacles_hint", "example"):
            spec[key] = self.fields[key].get("1.0", "end").strip()
        for key in ("avoid", "terms"):
            lines = [ln.strip() for ln in self.fields[key].get("1.0", "end").splitlines()]
            spec[key] = [ln for ln in lines if ln]

    def _renumber(self):
        for i, s in enumerate(self.tpl["sections"], start=1):
            s["number"] = i

    # ---------------- дії ----------------
    def add_section(self):
        self._store()
        new_id = f"s{len(self.tpl['sections']) + 1}"
        while any(s["id"] == new_id for s in self.tpl["sections"]):
            new_id += "x"
        self.tpl["sections"].append({
            "id": new_id, "number": len(self.tpl["sections"]) + 1, "group": "during",
            "color": "blue", "title": "Новий розділ", "hint": "", "example": "",
            "avoid": [], "terms": [], "min_chars": 0, "obstacles_required": False,
            "obstacles_hint": "",
        })
        self._renumber()
        self._fill_list()
        self._select(new_id)

    def remove_section(self):
        if not self.current_sid or len(self.tpl["sections"]) <= 1:
            return
        spec = self._spec(self.current_sid)
        if not messagebox.askyesno("Вилучити розділ",
                                   f"Вилучити «{spec['title']}» із шаблону?", parent=self):
            return
        self.tpl["sections"].remove(spec)
        self._renumber()
        self._fill_list()
        self.current_sid = None
        self._select(self.tpl["sections"][0]["id"])

    def move(self, delta):
        if not self.current_sid:
            return
        self._store()
        ids = [s["id"] for s in self.tpl["sections"]]
        i = ids.index(self.current_sid)
        j = i + delta
        if not 0 <= j < len(ids):
            return
        secs = self.tpl["sections"]
        secs[i], secs[j] = secs[j], secs[i]
        self._renumber()
        self._fill_list()
        self._select(self.current_sid)

    def edit_instruction(self):
        InstructionEditor(self, self.tpl)

    def export(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".json",
                                            initialfile="template.json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        self._store()
        self._apply_general()
        try:
            template._validate(self.tpl)
            with open(path, "w", encoding="utf-8") as fh:
                import json
                json.dump(self.tpl, fh, ensure_ascii=False, indent=2)
        except Exception as exc:                                    # noqa: BLE001
            messagebox.showerror("Експорт", str(exc), parent=self)
            return
        messagebox.showinfo("Експорт", f"Шаблон збережено:\n{path}", parent=self)

    def do_import(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            import json
            with open(path, encoding="utf-8") as fh:
                tpl = json.load(fh)
            template._validate(tpl)
        except Exception as exc:                                    # noqa: BLE001
            messagebox.showerror("Імпорт", f"Файл не підходить:\n{exc}", parent=self)
            return
        self.tpl = tpl
        self._fill_list()
        self.current_sid = None
        self._select(self.tpl["sections"][0]["id"])

    def reset(self):
        if not messagebox.askyesno("Скинути шаблон",
                                   "Повернути заводський шаблон? Усі зміни буде втрачено.",
                                   parent=self):
            return
        template.reset_template()
        self.app.reload_template()
        self.destroy()

    def _apply_general(self):
        for key, ent in self.general.items():
            val = ent.get().strip()
            if val:
                self.tpl[key] = val

    def save(self):
        self._store()
        self._apply_general()
        try:
            template.save_template(self.tpl)
        except Exception as exc:                                    # noqa: BLE001
            messagebox.showerror("Збереження", str(exc), parent=self)
            return
        self.app.reload_template()
        messagebox.showinfo("Збережено", "Шаблон оновлено.", parent=self)
        self.destroy()


class InstructionEditor(tk.Toplevel):
    """Правка текстів інструкції."""

    def __init__(self, parent, tpl):
        super().__init__(parent)
        self.tpl = tpl
        self.title("Інструкція для засудженого")
        self.geometry("820x640")
        self.configure(bg=PAPER)
        self.transient(parent)
        self.grab_set()

        bar = tk.Frame(self, bg=PAPER_DARK, padx=12, pady=8)
        bar.pack(fill="x")
        tk.Label(bar, text="Блоки інструкції", font=f("hand_m"), bg=PAPER_DARK,
                 fg=INK).pack(side="left")
        theme.button(bar, "Прийняти", self.apply_changes).pack(side="right")
        theme.button(bar, "Додати блок", self.add_block, "secondary").pack(side="right", padx=8)

        wrap = tk.Frame(self, bg=PAPER)
        wrap.pack(fill="both", expand=True, padx=12, pady=10)
        canvas = tk.Canvas(wrap, bg=PAPER, highlightthickness=0)
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=PAPER)
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.rows = []
        for blk in self.tpl.setdefault("instruction", {}).setdefault("blocks", []):
            self._row(blk)

    def _row(self, blk):
        frame = tk.Frame(self.inner, bg=PAPER, pady=8)
        frame.pack(fill="x")
        head = theme.entry(frame, width=60)
        head.insert(0, blk.get("heading", ""))
        head.pack(fill="x", ipady=4)
        body = theme.text_area(frame, height=6)
        body.insert("1.0", blk.get("text", ""))
        body.pack(fill="x", pady=(6, 0))
        theme.button(frame, "Вилучити блок",
                     lambda: self._drop(frame), "ghost").pack(anchor="e")
        self.rows.append((frame, head, body))

    def _drop(self, frame):
        self.rows = [r for r in self.rows if r[0] is not frame]
        frame.destroy()

    def add_block(self):
        self._row({"heading": "Новий блок", "text": ""})

    def apply_changes(self):
        blocks = []
        for _frame, head, body in self.rows:
            heading = head.get().strip()
            text = body.get("1.0", "end").strip()
            if heading or text:
                blocks.append({"heading": heading, "text": text})
        self.tpl["instruction"]["blocks"] = blocks
        self.destroy()

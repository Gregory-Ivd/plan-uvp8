# -*- coding: utf-8 -*-
"""Стан заповненого плану."""


class PlanDocument:
    """Зберігає введені значення й віддає їх рендерерам."""

    def __init__(self, template):
        self.tpl = template
        self.header = {fld["id"]: "" for fld in template.get("header_fields", [])}
        self.need = ""
        self.sections = {
            s["id"]: {"goals": "", "term": "", "obstacles": "", "skipped": False}
            for s in template["sections"]
        }

    # ---- серіалізація для чернетки ----
    def to_dict(self):
        return {"header": self.header, "need": self.need, "sections": self.sections}

    def load_dict(self, data):
        if not isinstance(data, dict):
            return
        for key, val in (data.get("header") or {}).items():
            if key in self.header:
                self.header[key] = val
        self.need = data.get("need", "") or ""
        for sid, val in (data.get("sections") or {}).items():
            if sid in self.sections and isinstance(val, dict):
                self.sections[sid].update({
                    "goals": val.get("goals", ""),
                    "term": val.get("term", ""),
                    "obstacles": val.get("obstacles", ""),
                    "skipped": bool(val.get("skipped", False)),
                })

    # ---- зручні вибірки ----
    def section_spec(self, sid):
        return next(s for s in self.tpl["sections"] if s["id"] == sid)

    def specs(self, group=None):
        return [s for s in self.tpl["sections"] if group is None or s["group"] == group]

    def is_filled(self, sid):
        d = self.sections[sid]
        return d["skipped"] or bool(d["goals"].strip())

    def progress(self):
        total = len(self.sections)
        done = sum(1 for sid in self.sections if self.is_filled(sid))
        return done, total

    def pib(self):
        return (self.header.get("pib") or "").strip()

    def title_line(self):
        pib = self.pib()
        birth = (self.header.get("birth") or "").strip()
        if pib and birth:
            return f"{pib}, {birth} року народження"
        return pib or "___________________________"

    def period(self):
        return ((self.header.get("date_from") or "").strip(),
                (self.header.get("date_to") or "").strip())

    def safe_filename(self):
        pib = self.pib() or "Без імені"
        short = " ".join(pib.split()[:3])
        bad = '<>:"/\\|?*'
        for ch in bad:
            short = short.replace(ch, "")
        return short.strip() or "План"

# -*- coding: utf-8 -*-
"""Перевірка заповненого плану. Блокує лише порожні обов'язкові поля."""
import re

BLOCK, WARN, HINT = "block", "warn", "hint"

# Русизми та кальки, що найчастіше трапляються в таких документах.
RUSSISMS = [
    ("на протязі всього", "протягом усього"),
    ("на протязі", "протягом"),
    ("у продовж", "протягом"),
    ("на рахунок того", "щодо того"),
    ("прийняти участь", "взяти участь"),
    ("приймати участь", "брати участь"),
    ("поступив до", "вступив до"),
    ("поступити до", "вступити до"),
    ("зайняти перше місце", "посісти перше місце"),
    ("відноситись до", "ставитися до"),
    ("відношення до", "ставлення до"),
    ("міроприємств", "заходів"),
    ("міроприємства", "заходи"),
    ("на протязі часу", "протягом часу"),
    ("у якості", "як"),
    ("згідно закону", "згідно із законом"),
    ("не дивлячись на", "попри"),
    ("співпадає", "збігається"),
    ("в залежності від", "залежно від"),
    ("по мірі того", "у міру того"),
    ("даний час", "цей час"),
    ("виключно з", "лише з"),
    ("на сьогоднішній день", "сьогодні"),
]

# Початок фрази, що описує процес, а не результат.
PROCESS_STARTS = (
    "брати участь", "приймати участь", "проводити", "відвідувати",
    "займатися", "виконувати", "здійснювати", "продовжувати",
)

RESULT_MARKERS = (
    "маю", "мав", "досяг", "опанував", "здобув", "закінчив", "склав",
    "отримав", "не маю", "планую", "хочу", "зобов", "стану", "оформлю",
    "результат", "щоб", "аби",
)

NO_OBSTACLE = ("не має", "немає", "нема", "відсутні", "відсутня", "-", "—", "нет")


class Issue:
    def __init__(self, level, where, text, fix=None, sid=None):
        self.level = level
        self.where = where
        self.text = text
        self.fix = fix          # (пошук, заміна) для автозаміни
        self.sid = sid

    def __repr__(self):
        return f"<Issue {self.level} {self.where}>"


def find_russisms(text):
    out = []
    low = text.lower()
    for bad, good in sorted(RUSSISMS, key=lambda p: -len(p[0])):
        # довші збіги мають пріоритет: «на протязі всього» не має дублюватись «на протязі»
        if bad in low and not any(bad in found for found, _ in out):
            out.append((bad, good))
    return out


def apply_russism_fix(text, bad, good):
    """Заміна без урахування регістру, з поверненням великої літери на початку."""
    def repl(m):
        src = m.group(0)
        return good.capitalize() if src[:1].isupper() else good
    return re.sub(re.escape(bad), repl, text, flags=re.IGNORECASE)


def check(doc):
    issues = []

    # ---- шапка ----
    for fld in doc.tpl.get("header_fields", []):
        if fld.get("required") and not (doc.header.get(fld["id"]) or "").strip():
            issues.append(Issue(BLOCK, "Шапка документа",
                                f"Не заповнено поле «{fld['label']}»."))
    if not doc.need.strip():
        issues.append(Issue(WARN, "Криміногенна потреба",
                            "Блок «Криміногенна потреба» порожній. Це короткий зміст "
                            "усього плану — комісія читає його першим."))

    # ---- розділи ----
    for spec in doc.tpl["sections"]:
        sid = spec["id"]
        data = doc.sections[sid]
        where = f"Розділ {spec['number']}"
        goals = data["goals"].strip()
        obst = data["obstacles"].strip()

        if data["skipped"]:
            continue

        if not goals:
            issues.append(Issue(BLOCK, where,
                                "Не заповнено «Проміжні цілі». Якщо розділ вас не "
                                "стосується — позначте його як такий, що не застосовується.",
                                sid=sid))
            continue

        min_chars = spec.get("min_chars", 0)
        if min_chars and len(goals) < min_chars:
            issues.append(Issue(WARN, where,
                                f"Відповідь коротка ({len(goals)} знаків). Для цього розділу "
                                f"варто хоча б {min_chars}: додайте імена, назви, дати.",
                                sid=sid))

        if not data["term"].strip():
            issues.append(Issue(WARN, where,
                                "Не вказано «Термін виконання». Ціль без строку читається "
                                "як намір без плану.", sid=sid))

        low_goal = goals.lower()
        if low_goal.startswith(PROCESS_STARTS) and not any(m in low_goal for m in RESULT_MARKERS):
            issues.append(Issue(HINT, where,
                                "Ціль сформульована як процес. Допишіть, якого результату "
                                "хочете досягти: не «брати участь», а «опанував / маю / не маю».",
                                sid=sid))

        if spec.get("obstacles_required"):
            if not obst:
                issues.append(Issue(WARN, where,
                                    "Не заповнено «Перепони та їх можливе вирішення».", sid=sid))
            elif obst.lower().strip(" .") in NO_OBSTACLE:
                issues.append(Issue(WARN, where,
                                    "У перепонах стоїть «Не має». Для цього розділу перепона "
                                    "зазвичай очевидна, і порожня клітинка читається як відписка. "
                                    "Напишіть, що заважає — і як ви це обходите.", sid=sid))

        for field_name, text in (("Проміжні цілі", goals),
                                 ("Термін виконання", data["term"]),
                                 ("Перепони", obst)):
            for bad, good in find_russisms(text):
                issues.append(Issue(HINT, where,
                                    f"У полі «{field_name}»: «{bad}» → «{good}».",
                                    fix=(bad, good), sid=sid))

    return issues


def summary(issues):
    return {
        BLOCK: sum(1 for i in issues if i.level == BLOCK),
        WARN: sum(1 for i in issues if i.level == WARN),
        HINT: sum(1 for i in issues if i.level == HINT),
    }

# -*- coding: utf-8 -*-
"""Шаблон документа: завантаження, збереження, шляхи, пароль адміністратора."""
import base64
import hashlib
import json
import os
import shutil
import sys

APP_DIRNAME = "plan-app"


def base_dir():
    """Тека, де лежить .exe (або скрипт) — сюди пишемо все, що змінюється."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundled_dir():
    """Тека з ресурсами всередині збірки."""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def data_path(*parts):
    return os.path.join(base_dir(), *parts)


def export_dir():
    d = data_path("export")
    os.makedirs(d, exist_ok=True)
    return d


TEMPLATE_FILE = "template.json"
CONFIG_FILE = "config.json"
DRAFT_FILE = "~draft.json"


def _default_template_path():
    for cand in (os.path.join(bundled_dir(), "resources", TEMPLATE_FILE),
                 os.path.join(base_dir(), "resources", TEMPLATE_FILE)):
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError("Не знайдено resources/template.json")


def load_template():
    """Спершу шукає редагований шаблон поруч із .exe, інакше бере вбудований."""
    user = data_path(TEMPLATE_FILE)
    path = user if os.path.exists(user) else _default_template_path()
    with open(path, encoding="utf-8") as fh:
        tpl = json.load(fh)
    _validate(tpl)
    return tpl


def save_template(tpl):
    _validate(tpl)
    with open(data_path(TEMPLATE_FILE), "w", encoding="utf-8") as fh:
        json.dump(tpl, fh, ensure_ascii=False, indent=2)


def reset_template():
    """Повертає шаблон до заводського стану."""
    user = data_path(TEMPLATE_FILE)
    if os.path.exists(user):
        os.remove(user)


def export_template(dest):
    shutil.copyfile(data_path(TEMPLATE_FILE) if os.path.exists(data_path(TEMPLATE_FILE))
                    else _default_template_path(), dest)


def import_template(src):
    with open(src, encoding="utf-8") as fh:
        tpl = json.load(fh)
    save_template(tpl)
    return tpl


def _validate(tpl):
    if not isinstance(tpl, dict):
        raise ValueError("Шаблон має бути об'єктом JSON")
    for key in ("doc_title", "sections"):
        if key not in tpl:
            raise ValueError(f"У шаблоні бракує поля «{key}»")
    if not tpl["sections"]:
        raise ValueError("У шаблоні немає жодного розділу")
    seen = set()
    for s in tpl["sections"]:
        for key in ("id", "number", "title", "group"):
            if key not in s:
                raise ValueError(f"У розділі бракує поля «{key}»: {s.get('title', s)}")
        if s["id"] in seen:
            raise ValueError(f"Повторюваний id розділу: {s['id']}")
        seen.add(s["id"])
        if s["group"] not in ("during", "after"):
            raise ValueError(f"group має бути during або after, а не {s['group']}")
    return True


# ---------------- конфіг і пароль ----------------

def load_config():
    path = data_path(CONFIG_FILE)
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            pass
    return {}


def save_config(cfg):
    with open(data_path(CONFIG_FILE), "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)


def _hash(password, salt):
    return base64.b64encode(
        hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    ).decode("ascii")


def has_password():
    return bool(load_config().get("admin_hash"))


def set_password(password):
    salt = os.urandom(16)
    cfg = load_config()
    cfg["admin_salt"] = base64.b64encode(salt).decode("ascii")
    cfg["admin_hash"] = _hash(password, salt)
    save_config(cfg)


def check_password(password):
    cfg = load_config()
    if not cfg.get("admin_hash"):
        return False
    salt = base64.b64decode(cfg["admin_salt"])
    return _hash(password, salt) == cfg["admin_hash"]


# ---------------- чернетка ----------------

def draft_path():
    return data_path(DRAFT_FILE)


def save_draft(values):
    try:
        with open(draft_path(), "w", encoding="utf-8") as fh:
            json.dump(values, fh, ensure_ascii=False, indent=1)
    except OSError:
        pass


def load_draft():
    path = draft_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def clear_draft():
    try:
        if os.path.exists(draft_path()):
            os.remove(draft_path())
    except OSError:
        pass

"""Optional feature modules (Habits, Reading, Faith, ...).

Every module is a subclass of ``Module`` registered in ``MODULE_REGISTRY``.
Code that builds navigation or Today cards loops over the registry and calls
the same methods on each module, so adding a module never needs an
``if key == "..."`` branch (polymorphism + registry pattern).

v1.3 ships the framework only; the registry is empty until v1.5.
"""
from abc import ABC, abstractmethod

MODULE_REGISTRY = {}


class Module(ABC):
    key = ""
    title = ""
    description = ""
    keep_in_exam_mode = False

    @abstractmethod
    def today_card(self, user, today):
        """Return a JSON-serialisable card for Today, or None."""

    def nav_item(self):
        return {"key": self.key, "title": self.title, "url": f"/{self.key}/"}

    def describe(self, enabled):
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "enabled": enabled,
        }


def register(cls):
    """Class decorator: instantiate and add a module to the registry."""
    if not cls.key:
        raise ValueError("A module needs a non-empty key.")
    MODULE_REGISTRY[cls.key] = cls()
    return cls


def enabled_modules(enabled_keys):
    return [MODULE_REGISTRY[key] for key in enabled_keys if key in MODULE_REGISTRY]


def build_module_cards(enabled_keys, user, today, exam_mode=False):
    cards = []
    for module in enabled_modules(enabled_keys):
        if exam_mode and not module.keep_in_exam_mode:
            continue
        card = module.today_card(user, today)
        if card is not None:
            cards.append({"key": module.key, "title": module.title, "card": card})
    return cards

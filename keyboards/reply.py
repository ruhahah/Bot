from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from i18n import TEXTS


def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXTS["btn_question"][lang])],
            [KeyboardButton(text=TEXTS["btn_lesson"][lang])],
            [KeyboardButton(text=TEXTS["btn_history"][lang]),
             KeyboardButton(text=TEXTS["btn_faq"][lang])],
            [KeyboardButton(text=TEXTS["btn_profile"][lang])],
            [KeyboardButton(text=TEXTS["btn_change_lang"][lang])],
        ],
        resize_keyboard=True,
    )


ADM_BTN_KEYS = [
    "adm_btn_stats", "adm_btn_students", "adm_btn_bookings",
    "adm_btn_unanswered", "adm_btn_questions", "adm_btn_slots",
    "adm_btn_broadcast", "adm_btn_ban", "adm_btn_lang", "adm_btn_cancel",
]


def _adm(key: str, lang: str) -> str:
    return TEXTS[key].get(lang, TEXTS[key]["ru"])


def admin_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_adm("adm_btn_stats", lang)),
             KeyboardButton(text=_adm("adm_btn_students", lang))],
            [KeyboardButton(text=_adm("adm_btn_bookings", lang)),
             KeyboardButton(text=_adm("adm_btn_unanswered", lang))],
            [KeyboardButton(text=_adm("adm_btn_questions", lang)),
             KeyboardButton(text=_adm("adm_btn_slots", lang))],
            [KeyboardButton(text=_adm("adm_btn_broadcast", lang)),
             KeyboardButton(text=_adm("adm_btn_ban", lang))],
            [KeyboardButton(text=_adm("adm_btn_lang", lang))],
        ],
        resize_keyboard=True,
    )


def admin_cancel_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_adm("adm_btn_cancel", lang))]],
        resize_keyboard=True,
    )


def all_adm_texts(key: str) -> set[str]:
    return set(TEXTS[key].values())


def cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXTS["btn_cancel"][lang])]],
        resize_keyboard=True,
    )

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from callbacks import CancelBookingFactory, DayCallbackFactory, FaqCallbackFactory, LangCallbackFactory, TimeCallbackFactory
from i18n import FAQ_DATA, TEXTS, WEEKDAYS, day_name

BACK_TO_DAYS = "back_to_days"
NEW_BOOKING = "new_booking"
MY_BOOKINGS = "my_bookings"
EDIT_PROFILE = "edit_profile"


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data=LangCallbackFactory(lang="kk").pack())],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data=LangCallbackFactory(lang="ru").pack())],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data=LangCallbackFactory(lang="en").pack())],
        ]
    )


def lesson_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS["btn_new_booking"][lang], callback_data=NEW_BOOKING)],
            [InlineKeyboardButton(text=TEXTS["btn_my_bookings"][lang], callback_data=MY_BOOKINGS)],
        ]
    )


def my_bookings_keyboard(bookings: list[dict], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for b in bookings:
        builder.row(
            InlineKeyboardButton(
                text=f"{TEXTS['btn_cancel_booking'][lang]}  {b['day_name']} {b['time']}",
                callback_data=CancelBookingFactory(booking_id=b["id"]).pack(),
            )
        )
    return builder.as_markup()


def profile_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS["btn_edit_profile"][lang], callback_data=EDIT_PROFILE)],
        ]
    )


def build_days_keyboard(available_days: list[str], lang: str) -> InlineKeyboardMarkup:
    ordered = [k for k in WEEKDAYS if k in available_days]
    builder = InlineKeyboardBuilder()
    for key in ordered:
        builder.button(text=day_name(key, lang), callback_data=DayCallbackFactory(day=key))
    builder.adjust(2)
    return builder.as_markup()


def build_time_slots_keyboard(day_key: str, available_times: list[str], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in available_times:
        builder.button(text=slot, callback_data=TimeCallbackFactory(day=day_key, time=slot))
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text=TEXTS["back"][lang], callback_data=BACK_TO_DAYS))
    return builder.as_markup()


def faq_keyboard(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, item in enumerate(FAQ_DATA):
        q_text = item["q"].get(lang, item["q"]["ru"])
        builder.row(InlineKeyboardButton(
            text=q_text,
            callback_data=FaqCallbackFactory(idx=i).pack(),
        ))
    return builder.as_markup()

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db
from callbacks import AnswerQuestionFactory, CancelBookingFactory, DayCallbackFactory, FaqCallbackFactory, LangCallbackFactory, TimeCallbackFactory
from config import load_config
from i18n import FAQ_DATA, all_texts, day_name as i18n_day_name, get_lang, set_lang, t
from keyboards.inline import (
    BACK_TO_DAYS, EDIT_PROFILE, MY_BOOKINGS, NEW_BOOKING,
    build_days_keyboard, build_time_slots_keyboard,
    faq_keyboard, lang_keyboard, lesson_menu_keyboard,
    my_bookings_keyboard, profile_keyboard,
)
from keyboards.reply import cancel_keyboard, main_keyboard
from states import LessonFSM, ProfileFSM, QuestionFSM

logger = logging.getLogger(__name__)
router = Router()

# Кэш forwarded_map (message_id -> student_id). Загружается из БД при старте.
forwarded_map: dict[int, int] = {}

cfg = load_config()

# Часовой пояс UTC+5 (Казахстан)
TZ = timezone(timedelta(hours=5))


# ─── /start + выбор языка ─────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        await message.answer("🚫 You are banned.")
        return
    await message.answer(
        "Выберите язык / Тілді таңдаңыз / Choose language:",
        reply_markup=lang_keyboard(),
    )


@router.callback_query(LangCallbackFactory.filter())
async def cb_lang_selected(callback: CallbackQuery, callback_data: LangCallbackFactory) -> None:
    lang = callback_data.lang
    uid = callback.from_user.id
    await set_lang(uid, lang)
    await callback.message.edit_text(t(uid, "greeting"))
    await callback.message.answer(
        t(uid, "main_menu"),
        reply_markup=main_keyboard(lang),
    )
    await callback.answer()


# ─── Смена языка ──────────────────────────────────────────────────────────────

@router.message(F.text.in_(all_texts("btn_change_lang")))
async def handle_change_lang(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        await message.answer("🚫 You are banned.")
        return
    await message.answer(
        "Выберите язык / Тілді таңдаңыз / Choose language:",
        reply_markup=lang_keyboard(),
    )


# ─── Задать вопрос преподавателю (FSM) ────────────────────────────────────────

@router.message(F.text.in_(all_texts("btn_question")))
async def handle_question(message: Message, state: FSMContext) -> None:
    if await db.is_banned(message.from_user.id):
        await message.answer("🚫 You are banned.")
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    await state.set_state(QuestionFSM.waiting_for_question)
    await message.answer(
        t(uid, "ask_question_prompt"),
        reply_markup=cancel_keyboard(lang),
    )


@router.message(QuestionFSM.waiting_for_question, F.text.in_(all_texts("btn_cancel")))
async def cancel_question(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = get_lang(uid)
    await state.clear()
    await message.answer(t(uid, "cancelled"), reply_markup=main_keyboard(lang))


@router.message(QuestionFSM.waiting_for_question, F.text | F.photo)
async def receive_question(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()

    uid = message.from_user.id
    lang = get_lang(uid)
    user = message.from_user
    adm_lang = get_lang(cfg.admin_id)
    username = f"@{user.username}" if user.username else t(cfg.admin_id, "no_username")
    caption = t(cfg.admin_id, "adm_new_question",
                name=user.full_name, username=username, uid=str(user.id))

    if message.photo:
        sent = await bot.send_photo(
            chat_id=cfg.admin_id,
            photo=message.photo[-1].file_id,
            caption=caption + (f"\n\n{message.caption}" if message.caption else ""),
        )
    else:
        sent = await bot.send_message(
            chat_id=cfg.admin_id,
            text=f"{caption}\n\n{message.text}",
        )

    forwarded_map[sent.message_id] = user.id
    await db.save_forwarded(sent.message_id, user.id)

    q_text = message.caption or message.text or "[фото]"
    created_at = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    q_id = await db.save_question(uid, q_text, sent.message_id, created_at)

    answer_builder = InlineKeyboardBuilder()
    answer_builder.row(InlineKeyboardButton(
        text=t(cfg.admin_id, "adm_btn_answer"),
        callback_data=AnswerQuestionFactory(question_id=q_id).pack(),
    ))
    await bot.send_message(
        chat_id=cfg.admin_id,
        text=t(cfg.admin_id, "adm_click_answer"),
        reply_markup=answer_builder.as_markup(),
    )

    logger.info("Вопрос от %s (%s) переслан админу", user.full_name, user.id)

    await message.answer(t(uid, "question_sent"), reply_markup=main_keyboard(lang))


@router.message(QuestionFSM.waiting_for_question)
async def wrong_content(message: Message) -> None:
    await message.answer(t(message.from_user.id, "wrong_content"))


# ─── Профиль ученика ──────────────────────────────────────────────────────

@router.message(F.text.in_(all_texts("btn_profile")))
async def handle_profile(message: Message, state: FSMContext) -> None:
    if await db.is_banned(message.from_user.id):
        await message.answer("🚫 You are banned.")
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    profile = await db.get_profile(uid)
    if profile:
        await message.answer(
            t(uid, "profile_info", name=profile["name"], grade=profile["grade"]),
            reply_markup=profile_keyboard(lang),
        )
    else:
        await message.answer(t(uid, "profile_empty"))
        await state.set_state(ProfileFSM.waiting_for_name)
        await message.answer(
            t(uid, "profile_enter_name"),
            reply_markup=cancel_keyboard(lang),
        )


@router.callback_query(F.data == EDIT_PROFILE)
async def cb_edit_profile(callback: CallbackQuery, state: FSMContext) -> None:
    uid = callback.from_user.id
    lang = get_lang(uid)
    await state.set_state(ProfileFSM.waiting_for_name)
    await callback.message.edit_text(t(uid, "profile_enter_name"), reply_markup=None)
    await callback.message.answer(
        t(uid, "profile_enter_name"),
        reply_markup=cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(ProfileFSM.waiting_for_name, F.text.in_(all_texts("btn_cancel")))
@router.message(ProfileFSM.waiting_for_grade, F.text.in_(all_texts("btn_cancel")))
async def cancel_profile(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = get_lang(uid)
    await state.clear()
    await message.answer(t(uid, "cancelled"), reply_markup=main_keyboard(lang))


@router.message(ProfileFSM.waiting_for_name, F.text)
async def profile_got_name(message: Message, state: FSMContext) -> None:
    await state.update_data(profile_name=message.text.strip())
    await state.set_state(ProfileFSM.waiting_for_grade)
    await message.answer(t(message.from_user.id, "profile_enter_grade"))


@router.message(ProfileFSM.waiting_for_grade, F.text)
async def profile_got_grade(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = get_lang(uid)
    data = await state.get_data()
    await state.clear()
    name = data["profile_name"]
    grade = message.text.strip()
    await db.save_profile(uid, name, grade)
    await message.answer(t(uid, "profile_saved"), reply_markup=main_keyboard(lang))


# ─── Записаться на доп. урок ─────────────────────────────────────────────

DAY_KEY_TO_WEEKDAY = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4}

# booking_id -> asyncio.Task (напоминания)
_reminder_tasks: dict[int, asyncio.Task] = {}


def _today() -> str:
    """Текущая дата по UTC+5 в формате YYYY-MM-DD."""
    return datetime.now(TZ).strftime("%Y-%m-%d")


def _next_weekday_dt(weekday: int, hour: int, minute: int) -> datetime:
    """Ближайшая дата для заданного дня недели и времени."""
    now = datetime.now(TZ)
    days_ahead = weekday - now.weekday()
    if days_ahead < 0:
        days_ahead += 7
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
    if target <= now:
        target += timedelta(weeks=1)
    return target


async def _reminder_coro(bot: Bot, uid: int, booking: dict, delay: float) -> None:
    """Ждёт delay секунд, затем отправляет напоминание."""
    await asyncio.sleep(delay)
    try:
        await bot.send_message(
            chat_id=uid,
            text=t(uid, "lesson_reminder",
                   day=booking["day_name"], time=booking["time"], topic=booking["topic"]),
        )
        logger.info("Напоминание отправлено %s", uid)
    except Exception as e:
        logger.error("Ошибка отправки напоминания %s: %s", uid, e)


def schedule_reminder(bot: Bot, uid: int, booking_id: int, booking: dict) -> None:
    """Планирует напоминание за 22 часа до урока."""
    wday = DAY_KEY_TO_WEEKDAY.get(booking.get("day_key", ""))
    if wday is None:
        return
    hour, minute = map(int, booking["time"].split(":"))
    lesson_dt = _next_weekday_dt(wday, hour, minute)
    reminder_dt = lesson_dt - timedelta(hours=22)
    delay = (reminder_dt - datetime.now(TZ)).total_seconds()
    if delay > 0:
        task = asyncio.create_task(_reminder_coro(bot, uid, booking, delay))
        _reminder_tasks[booking_id] = task


async def restore_reminders(bot: Bot) -> None:
    """Восстановить напоминания из БД после перезапуска."""
    bookings = await db.get_all_bookings(today=_today())
    for b in bookings:
        schedule_reminder(bot, b["user_id"], b["id"], b)
    logger.info("Восстановлено напоминаний: %d", len(_reminder_tasks))


@router.message(F.text.in_(all_texts("btn_lesson")))
async def handle_lesson(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        await message.answer("🚫 You are banned.")
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    await message.answer(t(uid, "lesson_menu"), reply_markup=lesson_menu_keyboard(lang))


@router.callback_query(F.data == NEW_BOOKING)
async def cb_new_booking(callback: CallbackQuery, state: FSMContext) -> None:
    uid = callback.from_user.id
    lang = get_lang(uid)
    profile = await db.get_profile(uid)
    if profile:
        await state.update_data(student_name=profile["name"])
        await state.set_state(LessonFSM.waiting_for_topic)
        await callback.message.edit_text(t(uid, "enter_topic"), reply_markup=None)
        await callback.message.answer(t(uid, "enter_topic"), reply_markup=cancel_keyboard(lang))
    else:
        await state.set_state(LessonFSM.waiting_for_name)
        await callback.message.edit_text(t(uid, "enter_name"), reply_markup=None)
        await callback.message.answer(t(uid, "enter_name"), reply_markup=cancel_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == MY_BOOKINGS)
async def cb_my_bookings(callback: CallbackQuery) -> None:
    uid = callback.from_user.id
    lang = get_lang(uid)
    bookings = await db.get_user_bookings(uid, today=_today())
    if not bookings:
        await callback.message.edit_text(t(uid, "no_bookings"))
        await callback.answer()
        return
    lines = [t(uid, "my_bookings_title")]
    for i, b in enumerate(bookings, start=1):
        lines.append(t(uid, "booking_line", n=str(i), day=b["day_name"], time=b["time"], topic=b["topic"]))
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=my_bookings_keyboard(bookings, lang),
    )
    await callback.answer()


@router.callback_query(CancelBookingFactory.filter())
async def cb_cancel_booking(callback: CallbackQuery, callback_data: CancelBookingFactory, bot: Bot) -> None:
    uid = callback.from_user.id
    lang = get_lang(uid)
    booking_id = callback_data.booking_id
    removed = await db.delete_booking(booking_id)
    if removed:
        task = _reminder_tasks.pop(booking_id, None)
        if task and not task.done():
            task.cancel()
        user = callback.from_user
        username = f"@{user.username}" if user.username else t(cfg.admin_id, "no_username")
        await bot.send_message(
            chat_id=cfg.admin_id,
            text=t(cfg.admin_id, "adm_booking_cancel_notify",
                   name=removed['student_name'], username=username,
                   topic=removed['topic'], day=removed['day_name'],
                   time=removed['time']),
        )
    bookings = await db.get_user_bookings(uid, today=_today())
    if bookings:
        lines = [t(uid, "my_bookings_title")]
        for i, b in enumerate(bookings, start=1):
            lines.append(t(uid, "booking_line", n=str(i), day=b["day_name"], time=b["time"], topic=b["topic"]))
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=my_bookings_keyboard(bookings, lang),
        )
    else:
        await callback.message.edit_text(t(uid, "booking_cancelled"))
    await callback.answer()


@router.message(LessonFSM.waiting_for_name, F.text.in_(all_texts("btn_cancel")))
@router.message(LessonFSM.waiting_for_topic, F.text.in_(all_texts("btn_cancel")))
async def cancel_lesson(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = get_lang(uid)
    await state.clear()
    await message.answer(t(uid, "cancelled"), reply_markup=main_keyboard(lang))


@router.message(LessonFSM.waiting_for_name, F.text)
async def lesson_got_name(message: Message, state: FSMContext) -> None:
    await state.update_data(student_name=message.text.strip())
    await state.set_state(LessonFSM.waiting_for_topic)
    await message.answer(t(message.from_user.id, "enter_topic"))


@router.message(LessonFSM.waiting_for_topic, F.text)
async def lesson_got_topic(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = get_lang(uid)
    await state.update_data(topic=message.text.strip())
    await state.set_state(LessonFSM.choosing_day)
    available_days = await db.get_days_with_available_slots(today=_today())
    if not available_days:
        await state.clear()
        await message.answer(t(uid, "no_available_days"), reply_markup=main_keyboard(lang))
        return
    await message.answer(t(uid, "choose_day"), reply_markup=build_days_keyboard(available_days, lang))


@router.callback_query(LessonFSM.choosing_day, DayCallbackFactory.filter())
async def cb_day_selected(callback: CallbackQuery, callback_data: DayCallbackFactory, state: FSMContext) -> None:
    uid = callback.from_user.id
    lang = get_lang(uid)
    day_key = callback_data.day
    dn = i18n_day_name(day_key, lang)
    available_times = await db.get_available_slots(day_key, today=_today())
    if not available_times:
        await callback.answer(t(uid, "no_available_times"), show_alert=True)
        return
    await state.update_data(day_key=day_key, day_name=dn)
    await state.set_state(LessonFSM.choosing_time)
    await callback.message.edit_text(
        t(uid, "available_time", day=dn),
        reply_markup=build_time_slots_keyboard(day_key, available_times, lang),
    )
    await callback.answer()


@router.callback_query(LessonFSM.choosing_time, F.data == BACK_TO_DAYS)
async def cb_back_to_days(callback: CallbackQuery, state: FSMContext) -> None:
    uid = callback.from_user.id
    lang = get_lang(uid)
    await state.set_state(LessonFSM.choosing_day)
    available_days = await db.get_days_with_available_slots(today=_today())
    if not available_days:
        await state.clear()
        await callback.message.edit_text(t(uid, "no_available_days"))
        await callback.answer()
        return
    await callback.message.edit_text(
        t(uid, "choose_day"),
        reply_markup=build_days_keyboard(available_days, lang),
    )
    await callback.answer()


@router.callback_query(LessonFSM.choosing_time, TimeCallbackFactory.filter())
async def cb_time_selected(callback: CallbackQuery, callback_data: TimeCallbackFactory, state: FSMContext, bot: Bot) -> None:
    day_key = callback_data.day
    time = callback_data.time

    if await db.is_slot_taken(day_key, time, today=_today()):
        uid = callback.from_user.id
        await callback.answer(t(uid, "slot_already_taken"), show_alert=True)
        return

    data = await state.get_data()
    await state.clear()

    uid = callback.from_user.id
    lang = get_lang(uid)
    dn = data["day_name"]
    student_name = data["student_name"]
    topic = data["topic"]
    user = callback.from_user
    username = f"@{user.username}" if user.username else t(cfg.admin_id, "no_username")

    wday = DAY_KEY_TO_WEEKDAY.get(day_key)
    h, m = map(int, time.split(":"))
    lesson_dt = _next_weekday_dt(wday, h, m)
    lesson_date = lesson_dt.strftime("%Y-%m-%d")

    booking_id = await db.add_booking(uid, student_name, topic, day_key, dn, time,
                                      lesson_date=lesson_date)
    booking = {"student_name": student_name, "topic": topic,
               "day_name": dn, "day_key": day_key, "time": time,
               "lesson_date": lesson_date}
    schedule_reminder(bot, uid, booking_id, booking)

    await callback.message.edit_text(
        t(uid, "booking_confirmed", day=dn, time=time),
        reply_markup=None,
    )

    await bot.send_message(
        chat_id=cfg.admin_id,
        text=t(cfg.admin_id, "adm_new_booking",
               name=student_name, username=username,
               topic=topic, day=dn, time=time),
    )
    logger.info("Заявка на доп. урок от %s: %s %s", student_name, dn, time)

    await callback.message.answer(t(uid, "main_menu"), reply_markup=main_keyboard(lang))
    await callback.answer()


# ─── История вопросов ─────────────────────────────────────────────────────

@router.message(F.text.in_(all_texts("btn_history")))
async def handle_history(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        await message.answer("🚫 You are banned.")
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    questions = await db.get_user_questions(uid, limit=10)
    if not questions:
        await message.answer(t(uid, "history_empty"))
        return
    lines = [t(uid, "history_title")]
    for q in questions:
        lines.append(t(uid, "history_q", text=q["question_text"]))
        if q["answer_text"]:
            lines.append(t(uid, "history_a", text=q["answer_text"]))
        else:
            lines.append(t(uid, "history_no_answer"))
        lines.append("")
    await message.answer("\n".join(lines).strip())


# ─── FAQ ──────────────────────────────────────────────────────────────────

@router.message(F.text.in_(all_texts("btn_faq")))
async def handle_faq(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        await message.answer("🚫 You are banned.")
        return
    uid = message.from_user.id
    lang = get_lang(uid)
    await message.answer(t(uid, "faq_title"), reply_markup=faq_keyboard(lang))


@router.callback_query(FaqCallbackFactory.filter())
async def cb_faq_answer(callback: CallbackQuery, callback_data: FaqCallbackFactory) -> None:
    uid = callback.from_user.id
    lang = get_lang(uid)
    idx = callback_data.idx
    if 0 <= idx < len(FAQ_DATA):
        item = FAQ_DATA[idx]
        q_text = item["q"].get(lang, item["q"]["ru"])
        a_text = item["a"].get(lang, item["a"]["ru"])
        await callback.message.edit_text(f"❓ {q_text}\n\n{a_text}")
    await callback.answer()


# ─── Ежедневная утренняя рассылка ─────────────────────────────────────────

async def _daily_digest_loop(bot: Bot) -> None:
    """Каждый день в 08:00 UTC+5 рассылает уведомления об уроках."""
    while True:
        now = datetime.now(TZ)
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        delay = (target - now).total_seconds()
        await asyncio.sleep(delay)

        today_str = datetime.now(TZ).strftime("%Y-%m-%d")
        bookings = await db.get_bookings_for_date(today_str)
        for b in bookings:
            try:
                await bot.send_message(
                    chat_id=b["user_id"],
                    text=t(b["user_id"], "daily_digest",
                           time=b["time"], topic=b["topic"]),
                )
            except Exception as e:
                logger.error("Ошибка утренней рассылки %s: %s", b["user_id"], e)
        if bookings:
            logger.info("Утренняя рассылка: %d уведомлений", len(bookings))


def start_daily_digest(bot: Bot) -> None:
    """Запустить фоновую задачу ежедневной рассылки."""
    asyncio.create_task(_daily_digest_loop(bot))

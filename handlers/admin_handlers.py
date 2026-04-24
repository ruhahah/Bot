import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db
from config import load_config
from callbacks import AdminCancelBookingFactory, AnswerQuestionFactory, BanCallbackFactory, LangCallbackFactory
from handlers.user_handlers import forwarded_map
from i18n import TEXTS, WEEKDAYS, day_name, get_lang, set_lang, t
from keyboards.inline import lang_keyboard
from keyboards.reply import (
    admin_cancel_keyboard, admin_keyboard, all_adm_texts,
)
from states import AdminCancelFSM, AnswerQuestionFSM, BanFSM, BroadcastFSM

logger = logging.getLogger(__name__)
router = Router()

cfg = load_config()
TZ = timezone(timedelta(hours=5))

ADMIN_DAY_ALIASES: dict[str, str] = {
    # Russian
    "пн": "mon", "пон": "mon", "понедельник": "mon",
    "вт": "tue", "вторник": "tue",
    "ср": "wed", "среда": "wed",
    "чт": "thu", "четверг": "thu",
    "пт": "fri", "пятница": "fri",
    # English
    "mon": "mon", "monday": "mon", "mnd": "mon", "mn": "mon",
    "tue": "tue", "tuesday": "tue", "tu": "tue",
    "wed": "wed", "wednesday": "wed", "wd": "wed",
    "thu": "thu", "thursday": "thu", "th": "thu",
    "fri": "fri", "friday": "fri", "fr": "fri",
    # Kazakh
    "дс": "mon", "дүйсенбі": "mon", "дүй": "mon",
    "сей": "tue", "сейсенбі": "tue", "сс": "tue",
    "сәр": "wed", "сәрсенбі": "wed",
    "бей": "thu", "бейсенбі": "thu", "бс": "thu",
    "жұ": "fri", "жұма": "fri", "жм": "fri",
}

DAY_ORDER = list(WEEKDAYS.keys())

IS_ADMIN = F.chat.id == cfg.admin_id
IS_ADMIN_CB = F.message.chat.id == cfg.admin_id

CANCEL_WORDS: set[str] = {"отмена", "cancel", "/cancel"} | all_adm_texts("adm_btn_cancel")


def _lang(uid: int) -> str:
    return get_lang(uid)


def _today() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


# ─── /admin — главное меню ────────────────────────────────────────────────────

@router.message(Command("admin"), IS_ADMIN)
async def cmd_admin(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    await message.answer(
        t(uid, "adm_panel_title"),
        parse_mode="HTML",
        reply_markup=admin_keyboard(lang),
    )


# ─── /start для админа ───────────────────────────────────────────────────────

@router.message(Command("start"), IS_ADMIN)
async def admin_start(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    await message.answer(
        t(uid, "adm_welcome"),
        parse_mode="HTML",
        reply_markup=admin_keyboard(lang),
    )


# ─── Язык ─────────────────────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_lang")), IS_ADMIN)
async def admin_change_lang(message: Message) -> None:
    await message.answer(
        "Выберите язык / Тілді таңдаңыз / Choose language:",
        reply_markup=lang_keyboard(),
    )


@router.callback_query(LangCallbackFactory.filter(), IS_ADMIN_CB)
async def admin_lang_selected(callback: CallbackQuery,
                              callback_data: LangCallbackFactory) -> None:
    lang = callback_data.lang
    uid = callback.from_user.id
    await set_lang(uid, lang)
    name = {"ru": "🇷🇺 Русский", "kk": "🇰🇿 Қазақша", "en": "🇬🇧 English"}.get(lang, lang)
    await callback.message.edit_text(t(uid, "adm_lang_changed", name=name))
    await callback.message.answer(
        t(uid, "adm_panel_title"),
        parse_mode="HTML",
        reply_markup=admin_keyboard(lang),
    )
    await callback.answer()


# ─── Статистика ───────────────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_stats")), IS_ADMIN)
@router.message(Command("stats"), IS_ADMIN)
async def cmd_stats(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    s = await db.get_stats(today=_today())
    await message.answer(
        t(uid, "adm_stats",
          total_users=str(s["total_users"]), profiles=str(s["profiles"]),
          active_bookings=str(s["active_bookings"]),
          total_questions=str(s["total_questions"]),
          unanswered=str(s["unanswered"]),
          total_slots=str(s["total_slots"])),
        parse_mode="HTML",
        reply_markup=admin_keyboard(lang),
    )


# ─── Список учеников ─────────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_students")), IS_ADMIN)
@router.message(Command("students"), IS_ADMIN)
async def cmd_students(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    students = await db.get_all_students()
    if not students:
        await message.answer(t(uid, "adm_no_students"),
                             reply_markup=admin_keyboard(lang))
        return
    lines = [t(uid, "adm_students_title")]
    for i, s in enumerate(students, 1):
        lang_flag = {"ru": "🇷🇺", "kk": "🇰🇿", "en": "🇬🇧"}.get(s["lang"] or "ru", "")
        lines.append(
            f"{i}. {s['name']} ({s['grade']}) {lang_flag}\n"
            f"   ID: <code>{s['user_id']}</code>"
        )
    await message.answer("\n".join(lines), parse_mode="HTML",
                         reply_markup=admin_keyboard(lang))


# ─── Активные записи ─────────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_bookings")), IS_ADMIN)
@router.message(Command("bookings"), IS_ADMIN)
async def cmd_bookings(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    bookings = await db.get_all_bookings(today=_today())
    if not bookings:
        await message.answer(t(uid, "adm_no_bookings"),
                             reply_markup=admin_keyboard(lang))
        return
    lines = [t(uid, "adm_bookings_title")]
    builder = InlineKeyboardBuilder()
    cancel_label = TEXTS["adm_btn_cancel_booking"].get(lang, "❌")
    for i, b in enumerate(bookings, 1):
        lines.append(
            f"{i}. {b['day_name']} {b['time']} ({b['lesson_date']})\n"
            f"   {b['student_name']} — {b['topic']}"
        )
        builder.row(InlineKeyboardButton(
            text=f"{cancel_label} #{i} — {b['student_name']}",
            callback_data=AdminCancelBookingFactory(booking_id=b["id"]).pack(),
        ))
    await message.answer("\n".join(lines), parse_mode="HTML",
                         reply_markup=builder.as_markup())


@router.callback_query(AdminCancelBookingFactory.filter(), IS_ADMIN_CB)
async def cb_admin_cancel(callback: CallbackQuery,
                          callback_data: AdminCancelBookingFactory,
                          state: FSMContext) -> None:
    uid = callback.from_user.id
    lang = _lang(uid)
    await state.update_data(admin_cancel_booking_id=callback_data.booking_id)
    await state.set_state(AdminCancelFSM.waiting_for_reason)
    await callback.message.answer(
        t(uid, "adm_cancel_reason"),
        reply_markup=admin_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(AdminCancelFSM.waiting_for_reason, IS_ADMIN, F.text)
async def fsm_admin_cancel_reason(message: Message, state: FSMContext, bot: Bot) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    reason = message.text.strip()
    if reason in CANCEL_WORDS or reason.lower() in CANCEL_WORDS:
        await state.clear()
        await message.answer(t(uid, "adm_cancelled"), reply_markup=admin_keyboard(lang))
        return
    data = await state.get_data()
    await state.clear()
    booking_id = data.get("admin_cancel_booking_id")
    if not booking_id:
        await message.answer("Error", reply_markup=admin_keyboard(lang))
        return
    booking = await db.delete_booking(booking_id)
    if not booking:
        await message.answer("Not found", reply_markup=admin_keyboard(lang))
        return
    try:
        await bot.send_message(
            chat_id=booking["user_id"],
            text=t(booking["user_id"], "booking_cancelled_by_admin",
                   day=booking["day_name"], time=booking["time"],
                   topic=booking["topic"], reason=reason),
        )
    except Exception as e:
        logger.error("Не удалось уведомить ученика %s: %s", booking["user_id"], e)
    await message.answer(
        t(uid, "adm_booking_deleted",
          name=booking["student_name"], day=booking["day_name"],
          time=booking["time"], reason=reason),
        reply_markup=admin_keyboard(lang),
    )
    logger.info("Админ отменил запись #%s, причина: %s", booking_id, reason)


# ─── Неотвеченные вопросы ────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_unanswered")), IS_ADMIN)
@router.message(Command("unanswered"), IS_ADMIN)
async def cmd_unanswered(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    questions = await _get_unanswered()
    if not questions:
        await message.answer(t(uid, "adm_all_answered"),
                             reply_markup=admin_keyboard(lang))
        return
    lines = [t(uid, "adm_unanswered_title")]
    builder = InlineKeyboardBuilder()
    answer_label = TEXTS["adm_btn_answer"].get(lang, "✏️")
    for i, q in enumerate(questions, 1):
        name = q.get("student_name") or f"ID {q['user_id']}"
        lines.append(
            f"{i}. <b>{name}</b> [{q['created_at']}]\n"
            f"   {q['question_text'][:100]}"
        )
        builder.row(InlineKeyboardButton(
            text=f"{answer_label} #{i} — {name}",
            callback_data=AnswerQuestionFactory(question_id=q["id"]).pack(),
        ))
    await message.answer("\n".join(lines), parse_mode="HTML",
                         reply_markup=builder.as_markup())


async def _get_unanswered() -> list[dict]:
    import aiosqlite
    async with aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT q.id, q.user_id, q.question_text, q.created_at, "
            "COALESCE(sp.name, '') AS student_name "
            "FROM questions q "
            "LEFT JOIN student_profiles sp ON q.user_id = sp.user_id "
            "WHERE q.answer_text = '' ORDER BY q.id DESC LIMIT 20"
        )
        return [dict(row) for row in await cursor.fetchall()]


# ─── Все вопросы ──────────────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_questions")), IS_ADMIN)
@router.message(Command("questions"), IS_ADMIN)
async def cmd_questions(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    questions = await db.get_all_questions(limit=30)
    if not questions:
        await message.answer(t(uid, "adm_no_questions"),
                             reply_markup=admin_keyboard(lang))
        return
    lines = [t(uid, "adm_questions_title")]
    builder = InlineKeyboardBuilder()
    answer_label = TEXTS["adm_btn_answer"].get(lang, "✏️")
    for i, q in enumerate(questions, 1):
        name = q["student_name"] or f"ID {q['user_id']}"
        status = "✅" if q["answer_text"] else "⏳"
        lines.append(
            f"{i}. {status} <b>{name}</b> [{q['created_at']}]\n"
            f"   ❓ {q['question_text'][:80]}"
        )
        if q["answer_text"]:
            lines.append(f"   💬 {q['answer_text'][:80]}")
        else:
            builder.row(InlineKeyboardButton(
                text=f"{answer_label} #{i} — {name}",
                callback_data=AnswerQuestionFactory(question_id=q["id"]).pack(),
            ))
        lines.append("")
    markup = builder.as_markup() if builder.buttons else None
    await message.answer("\n".join(lines).strip(), parse_mode="HTML",
                         reply_markup=markup or admin_keyboard(lang))


# ─── Слоты ────────────────────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_slots")), IS_ADMIN)
@router.message(Command("slots"), IS_ADMIN)
async def cmd_slots(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    all_slots = await db.get_all_slots()
    if not all_slots:
        await message.answer(t(uid, "adm_no_slots"),
                             reply_markup=admin_keyboard(lang))
        return
    lines = [t(uid, "adm_slots_title")]
    for dk in DAY_ORDER:
        if dk in all_slots:
            dn = day_name(dk, lang)
            times = ", ".join(all_slots[dk])
            lines.append(f"  {dn}: {times}")
    await message.answer("\n".join(lines), parse_mode="HTML",
                         reply_markup=admin_keyboard(lang))


# ─── Команды /addslot /delslot ───────────────────────────────────────────────

@router.message(Command("addslot"), IS_ADMIN)
async def cmd_add_slot(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Формат: /addslot <день> <время>\n"
            "Пример: /addslot пн 15:30",
            reply_markup=admin_keyboard(lang),
        )
        return
    day_alias = parts[1].lower()
    time_str = parts[2].strip()
    day_key = ADMIN_DAY_ALIASES.get(day_alias)
    if not day_key:
        await message.answer(f"Неизвестный день: {parts[1]}",
                             reply_markup=admin_keyboard(lang))
        return
    if ":" not in time_str:
        await message.answer("Время в формате ЧЧ:ММ", reply_markup=admin_keyboard(lang))
        return
    ok = await db.add_time_slot(day_key, time_str)
    dn = day_name(day_key, lang)
    text = f"✅ {dn} {time_str}" if ok else f"⚠️ {dn} {time_str}"
    await message.answer(text, reply_markup=admin_keyboard(lang))


@router.message(Command("delslot"), IS_ADMIN)
async def cmd_del_slot(message: Message) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Формат: /delslot <день> <время>\n"
            "Пример: /delslot пн 15:30",
            reply_markup=admin_keyboard(lang),
        )
        return
    day_alias = parts[1].lower()
    time_str = parts[2].strip()
    day_key = ADMIN_DAY_ALIASES.get(day_alias)
    if not day_key:
        await message.answer(f"Неизвестный день: {parts[1]}",
                             reply_markup=admin_keyboard(lang))
        return
    ok = await db.remove_time_slot(day_key, time_str)
    dn = day_name(day_key, lang)
    text = f"🗑 {dn} {time_str}" if ok else f"⚠️ {dn} {time_str}"
    await message.answer(text, reply_markup=admin_keyboard(lang))


# ─── Рассылка ─────────────────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_broadcast")), IS_ADMIN)
@router.message(Command("broadcast"), IS_ADMIN)
async def cmd_broadcast(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    await state.set_state(BroadcastFSM.waiting_for_message)
    await message.answer(
        t(uid, "adm_broadcast_prompt"),
        reply_markup=admin_cancel_keyboard(lang),
    )


@router.message(BroadcastFSM.waiting_for_message, IS_ADMIN, F.text.in_(CANCEL_WORDS))
async def cancel_broadcast(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    await state.clear()
    await message.answer(t(uid, "adm_broadcast_cancelled"),
                         reply_markup=admin_keyboard(lang))


@router.message(BroadcastFSM.waiting_for_message, IS_ADMIN, F.text | F.photo)
async def do_broadcast(message: Message, state: FSMContext, bot: Bot) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    await state.clear()
    user_ids = await db.broadcast_users()
    sent, failed = 0, 0
    for target_uid in user_ids:
        target_lang = get_lang(target_uid)
        header = {
            "ru": "📣 <b>Сообщение от преподавателя:</b>\n\n",
            "kk": "📣 <b>Мұғалімнен хабарлама:</b>\n\n",
            "en": "📣 <b>Message from the teacher:</b>\n\n",
        }.get(target_lang, "📣 <b>Сообщение от преподавателя:</b>\n\n")
        try:
            if message.photo:
                raw_caption = message.caption or ""
                await bot.send_photo(
                    chat_id=target_uid,
                    photo=message.photo[-1].file_id,
                    caption=header + raw_caption,
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=target_uid,
                    text=header + message.text,
                    parse_mode="HTML",
                )
            sent += 1
        except Exception:
            failed += 1
    await message.answer(
        t(uid, "adm_broadcast_done", sent=str(sent), failed=str(failed)),
        reply_markup=admin_keyboard(lang),
    )
    logger.info("Рассылка: %d доставлено, %d ошибок", sent, failed)


# ─── Ответ на вопрос через inline-кнопку ─────────────────────────────────────

@router.callback_query(AnswerQuestionFactory.filter(), IS_ADMIN_CB)
async def cb_answer_question(callback: CallbackQuery,
                             callback_data: AnswerQuestionFactory,
                             state: FSMContext) -> None:
    uid = callback.from_user.id
    lang = _lang(uid)
    q = await db.get_question_by_id(callback_data.question_id)
    if not q:
        await callback.answer("Not found", show_alert=True)
        return
    if q["answer_text"]:
        await callback.answer("Already answered", show_alert=True)
        return
    await state.update_data(answer_question_id=q["id"],
                            answer_user_id=q["user_id"])
    await state.set_state(AnswerQuestionFSM.waiting_for_answer)
    await callback.message.answer(
        t(uid, "adm_answer_prompt", q=q["question_text"][:200]),
        parse_mode="HTML",
        reply_markup=admin_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(AnswerQuestionFSM.waiting_for_answer, IS_ADMIN, F.text)
async def fsm_answer_question(message: Message, state: FSMContext, bot: Bot) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    text = message.text.strip()
    if text in CANCEL_WORDS or text.lower() in CANCEL_WORDS:
        await state.clear()
        await message.answer(t(uid, "adm_cancelled"),
                             reply_markup=admin_keyboard(lang))
        return
    data = await state.get_data()
    await state.clear()
    question_id = data.get("answer_question_id")
    user_id = data.get("answer_user_id")
    if not question_id or not user_id:
        await message.answer("Error", reply_markup=admin_keyboard(lang))
        return
    await db.save_answer_by_id(question_id, text)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=t(user_id, "teacher_reply", text=text),
        )
    except Exception as e:
        logger.error("Не удалось отправить ответ ученику %s: %s", user_id, e)
    await message.answer(t(uid, "adm_answer_sent"),
                         reply_markup=admin_keyboard(lang))
    logger.info("Админ ответил на вопрос #%s для ученика %s", question_id, user_id)


# ─── Бан пользователей ───────────────────────────────────────────────────────

@router.message(F.text.in_(all_adm_texts("adm_btn_ban")), IS_ADMIN)
async def cmd_ban(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    banned = await db.get_all_banned()
    if not banned:
        await message.answer(t(uid, "adm_no_banned"), reply_markup=admin_keyboard(lang))
    else:
        lines = [t(uid, "adm_ban_list_title")]
        builder = InlineKeyboardBuilder()
        unban_label = TEXTS["adm_btn_unban"].get(lang, "✅")
        for i, b in enumerate(banned, 1):
            name = b["name"] or f"ID {b['user_id']}"
            lines.append(
                f"{i}. {name} ({b['grade'] or '?'}) — {b['user_id']}\n"
                f"   📅 {b['banned_at']}\n"
                f"   📝 {b['reason'] or '—'}"
            )
            builder.row(InlineKeyboardButton(
                text=f"{unban_label} #{i} — {name}",
                callback_data=BanCallbackFactory(user_id=b["user_id"], action="unban").pack(),
            ))
        await message.answer("\n".join(lines), reply_markup=builder.as_markup())
    await message.answer(t(uid, "adm_ban_prompt"), reply_markup=admin_cancel_keyboard(lang))
    await state.set_state(BanFSM.waiting_for_user_id)


@router.message(BanFSM.waiting_for_user_id, IS_ADMIN, F.text.in_(CANCEL_WORDS))
async def cancel_ban(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    await state.clear()
    await message.answer(t(uid, "adm_ban_cancelled"), reply_markup=admin_keyboard(lang))


@router.message(BanFSM.waiting_for_user_id, IS_ADMIN, F.text)
async def ban_got_user_id(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("Error: invalid ID", reply_markup=admin_keyboard(lang))
        await state.clear()
        return
    await state.update_data(ban_target_id=target_id)
    await state.set_state(BanFSM.waiting_for_reason)
    await message.answer(t(uid, "adm_ban_reason"), reply_markup=admin_cancel_keyboard(lang))


@router.message(BanFSM.waiting_for_reason, IS_ADMIN, F.text.in_(CANCEL_WORDS))
async def cancel_ban_reason(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    await state.clear()
    await message.answer(t(uid, "adm_ban_cancelled"), reply_markup=admin_keyboard(lang))


@router.message(BanFSM.waiting_for_reason, IS_ADMIN, F.text)
async def ban_got_reason(message: Message, state: FSMContext) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    reason = message.text.strip()
    data = await state.get_data()
    await state.clear()
    target_id = data.get("ban_target_id")
    if target_id:
        await db.add_ban(target_id, reason)
        await message.answer(t(uid, "adm_user_banned"), reply_markup=admin_keyboard(lang))
    else:
        await message.answer("Error", reply_markup=admin_keyboard(lang))


@router.callback_query(BanCallbackFactory.filter(), IS_ADMIN_CB)
async def cb_ban_action(callback: CallbackQuery,
                        callback_data: BanCallbackFactory) -> None:
    uid = callback.from_user.id
    lang = _lang(uid)
    action = callback_data.action
    target_id = callback_data.user_id

    if action == "unban":
        await db.remove_ban(target_id)
        await callback.message.edit_text(t(uid, "adm_user_unbanned"))
        await callback.answer()
    elif action == "confirm":
        await callback.message.edit_text(t(uid, "adm_ban_reason"))
        await callback.answer()
    await callback.answer()


# ─── Ответ ученику (reply) ───────────────────────────────────────────────────

@router.message(F.reply_to_message, IS_ADMIN)
async def admin_reply(message: Message, bot: Bot) -> None:
    uid = message.from_user.id
    lang = _lang(uid)
    student_id = forwarded_map.get(message.reply_to_message.message_id)
    if student_id is None:
        student_id = await db.get_student_by_message(message.reply_to_message.message_id)
    if not student_id:
        await message.answer("—")
        return

    if message.photo:
        await bot.send_photo(
            chat_id=student_id,
            photo=message.photo[-1].file_id,
            caption=t(student_id, "teacher_reply", text=message.caption or ""),
        )
    else:
        await bot.send_message(
            chat_id=student_id,
            text=t(student_id, "teacher_reply", text=message.text),
        )
    answer_text = message.caption or message.text or ""
    await db.save_answer(message.reply_to_message.message_id, answer_text)
    await message.answer(t(uid, "adm_answer_sent"))

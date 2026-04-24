"""
SQLite-хранилище бота.
Таблицы: user_langs, bookings, forwarded_map, time_slots.
"""

import aiosqlite

DB_PATH = "bot.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS user_langs (
                user_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL DEFAULT 'ru'
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                day_key TEXT NOT NULL,
                day_name TEXT NOT NULL,
                time TEXT NOT NULL,
                lesson_date TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS forwarded_map (
                message_id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_key TEXT NOT NULL,
                time TEXT NOT NULL,
                UNIQUE(day_key, time)
            );
            CREATE TABLE IF NOT EXISTS student_profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                grade TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL DEFAULT '',
                fwd_message_id INTEGER,
                created_at TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                banned_at TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL DEFAULT ''
            );
        """)
        await db.commit()
        # Миграция: добавить lesson_date если нет
        try:
            await db.execute(
                "ALTER TABLE bookings ADD COLUMN lesson_date TEXT NOT NULL DEFAULT ''"
            )
            await db.commit()
        except Exception:
            pass


# ── Languages ─────────────────────────────────────────────────────────────────

async def get_all_langs() -> dict[int, str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id, lang FROM user_langs")
        return {row[0]: row[1] for row in await cursor.fetchall()}


async def save_lang(user_id: int, lang: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_langs (user_id, lang) VALUES (?, ?)",
            (user_id, lang),
        )
        await db.commit()


# ── Forwarded map ─────────────────────────────────────────────────────────────

async def get_all_forwarded() -> dict[int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT message_id, student_id FROM forwarded_map")
        return {row[0]: row[1] for row in await cursor.fetchall()}


async def save_forwarded(message_id: int, student_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO forwarded_map (message_id, student_id) VALUES (?, ?)",
            (message_id, student_id),
        )
        await db.commit()


async def get_student_by_message(message_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT student_id FROM forwarded_map WHERE message_id = ?",
            (message_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None


# ── Bookings ──────────────────────────────────────────────────────────────────

async def add_booking(user_id: int, student_name: str, topic: str,
                      day_key: str, day_name: str, time: str,
                      lesson_date: str = "") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO bookings "
            "(user_id, student_name, topic, day_key, day_name, time, lesson_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, student_name, topic, day_key, day_name, time, lesson_date),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_bookings(user_id: int, today: str = "") -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, student_name, topic, day_key, day_name, time, lesson_date "
            "FROM bookings WHERE user_id = ? AND lesson_date >= ? ORDER BY lesson_date, time",
            (user_id, today),
        )
        return [dict(row) for row in await cursor.fetchall()]


async def delete_booking(booking_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, user_id, student_name, topic, day_key, day_name, time "
            "FROM bookings WHERE id = ?",
            (booking_id,),
        )
        row = await cursor.fetchone()
        if row:
            result = dict(row)
            await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            await db.commit()
            return result
        return None


async def get_all_bookings(today: str = "") -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, user_id, student_name, topic, day_key, day_name, time, lesson_date "
            "FROM bookings WHERE lesson_date >= ? ORDER BY lesson_date, time",
            (today,),
        )
        return [dict(row) for row in await cursor.fetchall()]


async def is_slot_taken(day_key: str, time: str, today: str = "") -> bool:
    from datetime import datetime, timedelta
    if not today:
        today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM bookings WHERE day_key = ? AND time = ? "
            "AND lesson_date >= ? AND lesson_date < ?",
            (day_key, time, today, next_week),
        )
        return await cursor.fetchone() is not None


# ── Time slots ────────────────────────────────────────────────────────────────

async def add_time_slot(day_key: str, time: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO time_slots (day_key, time) VALUES (?, ?)",
                (day_key, time),
            )
            await db.commit()
        return True
    except Exception:
        return False


async def remove_time_slot(day_key: str, time: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM time_slots WHERE day_key = ? AND time = ?",
            (day_key, time),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_all_slots() -> dict[str, list[str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT day_key, time FROM time_slots ORDER BY day_key, time"
        )
        result: dict[str, list[str]] = {}
        for day_key, t in await cursor.fetchall():
            result.setdefault(day_key, []).append(t)
        return result


async def get_available_slots(day_key: str, today: str = "") -> list[str]:
    from datetime import datetime, timedelta
    if not today:
        today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT ts.time FROM time_slots ts "
            "LEFT JOIN bookings b ON ts.day_key = b.day_key AND ts.time = b.time "
            "AND b.lesson_date >= ? AND b.lesson_date < ? "
            "WHERE ts.day_key = ? AND b.id IS NULL "
            "ORDER BY ts.time",
            (today, next_week, day_key),
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_days_with_available_slots(today: str = "") -> list[str]:
    from datetime import datetime, timedelta
    if not today:
        today = datetime.now().strftime("%Y-%m-%d")
    next_week = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT DISTINCT ts.day_key FROM time_slots ts "
            "LEFT JOIN bookings b ON ts.day_key = b.day_key AND ts.time = b.time "
            "AND b.lesson_date >= ? AND b.lesson_date < ? "
            "WHERE b.id IS NULL "
            "ORDER BY ts.day_key",
            (today, next_week),
        )
        return [row[0] for row in await cursor.fetchall()]


# ── Student profiles ──────────────────────────────────────────────────────────

async def get_profile(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT user_id, name, grade FROM student_profiles WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def save_profile(user_id: int, name: str, grade: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO student_profiles (user_id, name, grade) "
            "VALUES (?, ?, ?)",
            (user_id, name, grade),
        )
        await conn.commit()


# ── Questions ─────────────────────────────────────────────────────────────────

async def save_question(user_id: int, question_text: str,
                        fwd_message_id: int, created_at: str) -> int:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "INSERT INTO questions (user_id, question_text, fwd_message_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, question_text, fwd_message_id, created_at),
        )
        await conn.commit()
        return cursor.lastrowid


async def save_answer(fwd_message_id: int, answer_text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE questions SET answer_text = ? WHERE fwd_message_id = ?",
            (answer_text, fwd_message_id),
        )
        await conn.commit()


async def get_question_by_id(question_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT id, user_id, question_text, answer_text, fwd_message_id, created_at "
            "FROM questions WHERE id = ?",
            (question_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def save_answer_by_id(question_id: int, answer_text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE questions SET answer_text = ? WHERE id = ?",
            (answer_text, question_id),
        )
        await conn.commit()


async def get_user_questions(user_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT id, question_text, answer_text, created_at "
            "FROM questions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_all_questions(limit: int = 30) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT q.id, q.user_id, q.question_text, q.answer_text, q.created_at, "
            "COALESCE(sp.name, '') AS student_name "
            "FROM questions q "
            "LEFT JOIN student_profiles sp ON q.user_id = sp.user_id "
            "ORDER BY q.id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in await cursor.fetchall()]


# ── Daily digest ──────────────────────────────────────────────────────────────

async def get_stats(today: str = "") -> dict:
    async with aiosqlite.connect(DB_PATH) as conn:
        c = await conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_langs")
        total_users = (await c.fetchone())[0]
        c = await conn.execute("SELECT COUNT(*) FROM student_profiles")
        profiles = (await c.fetchone())[0]
        c = await conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE lesson_date >= ?", (today,))
        active_bookings = (await c.fetchone())[0]
        c = await conn.execute(
            "SELECT COUNT(*) FROM questions WHERE answer_text = ''")
        unanswered = (await c.fetchone())[0]
        c = await conn.execute("SELECT COUNT(*) FROM questions")
        total_questions = (await c.fetchone())[0]
        c = await conn.execute("SELECT COUNT(*) FROM time_slots")
        total_slots = (await c.fetchone())[0]
        return {
            "total_users": total_users,
            "profiles": profiles,
            "active_bookings": active_bookings,
            "unanswered": unanswered,
            "total_questions": total_questions,
            "total_slots": total_slots,
        }


async def get_all_students() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT sp.user_id, sp.name, sp.grade, ul.lang "
            "FROM student_profiles sp "
            "LEFT JOIN user_langs ul ON sp.user_id = ul.user_id "
            "ORDER BY sp.name"
        )
        return [dict(row) for row in await cursor.fetchall()]


async def broadcast_users() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT DISTINCT user_id FROM user_langs")
        return [row[0] for row in await cursor.fetchall()]


async def get_bookings_for_date(date_str: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT id, user_id, student_name, topic, day_name, time "
            "FROM bookings WHERE lesson_date = ? ORDER BY time",
            (date_str,),
        )
        return [dict(row) for row in await cursor.fetchall()]


# ── Ban management ───────────────────────────────────────────────────────────────

async def add_ban(user_id: int, reason: str = "") -> None:
    from datetime import datetime
    banned_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO banned_users (user_id, banned_at, reason) VALUES (?, ?, ?)",
            (user_id, banned_at, reason),
        )
        await db.commit()


async def remove_ban(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM banned_users WHERE user_id = ?",
            (user_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM banned_users WHERE user_id = ?",
            (user_id,),
        )
        return await cursor.fetchone() is not None


async def get_all_banned() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT bu.user_id, bu.banned_at, bu.reason, sp.name, sp.grade "
            "FROM banned_users bu "
            "LEFT JOIN student_profiles sp ON bu.user_id = sp.user_id "
            "ORDER BY bu.banned_at DESC"
        )
        return [dict(row) for row in await cursor.fetchall()]

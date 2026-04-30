"""
Модуль локализации. Хранит переводы на три языка (ru, kk, en).
Языковые предпочтения кэшируются в памяти и сохраняются в SQLite.
"""

DEFAULT_LANG = "ru"

# ── хранилище язык → user_id ──────────────────────────────────────────────────

_user_langs: dict[int, str] = {}


def get_lang(user_id: int) -> str:
    return _user_langs.get(user_id, DEFAULT_LANG)


async def set_lang(user_id: int, lang: str) -> None:
    _user_langs[user_id] = lang
    import db
    await db.save_lang(user_id, lang)


async def load_langs() -> None:
    """Load language preferences from DB into cache. Call on startup."""
    import db
    _user_langs.update(await db.get_all_langs())


def has_lang(user_id: int) -> bool:
    return user_id in _user_langs


# ── вспомогательные функции ───────────────────────────────────────────────────

def t(user_id: int, key: str, **kwargs: str) -> str:
    lang = get_lang(user_id)
    text = TEXTS[key].get(lang, TEXTS[key][DEFAULT_LANG])
    return text.format(**kwargs) if kwargs else text


def all_texts(key: str) -> set[str]:
    return set(TEXTS[key].values())


def day_name(key: str, lang: str) -> str:
    return WEEKDAYS[key].get(lang, WEEKDAYS[key][DEFAULT_LANG])


# ── дни недели ────────────────────────────────────────────────────────────────

WEEKDAYS: dict[str, dict[str, str]] = {
    "mon": {"ru": "Понедельник", "kk": "Дүйсенбі", "en": "Monday"},
    "tue": {"ru": "Вторник", "kk": "Сейсенбі", "en": "Tuesday"},
    "wed": {"ru": "Среда", "kk": "Сәрсенбі", "en": "Wednesday"},
    "thu": {"ru": "Четверг", "kk": "Бейсенбі", "en": "Thursday"},
    "fri": {"ru": "Пятница", "kk": "Жұма", "en": "Friday"},
}

# ── все переводы ──────────────────────────────────────────────────────────────

TEXTS: dict[str, dict[str, str]] = {

    # ── выбор языка ───────────────────────────────────────────────────────────
    "choose_lang": {
        "ru": "Выберите язык / Тілді таңдаңыз / Choose language:",
        "kk": "Выберите язык / Тілді таңдаңыз / Choose language:",
        "en": "Выберите язык / Тілді таңдаңыз / Choose language:",
    },

    # ── приветствие ───────────────────────────────────────────────────────────
    "greeting": {
        "ru": "Привет! Я помощник твоего учителя химии. Чем могу помочь?",
        "kk": "Сәлем! Мен химия мұғаліміңнің көмекшісімін. Қалай көмектесе аламын?",
        "en": "Hello! I'm your chemistry teacher's assistant. How can I help?",
    },

    # ── кнопки главного меню ──────────────────────────────────────────────────
    "btn_question": {
        "ru": "Задать вопрос преподавателю",
        "kk": "Мұғалімге сұрақ қою",
        "en": "Ask the teacher",
    },
    "btn_materials": {
        "ru": "Справочные материалы",
        "kk": "Анықтамалық материалдар",
        "en": "Reference materials",
    },
    "btn_lesson": {
        "ru": "Записаться на доп. урок",
        "kk": "Қосымша сабаққа жазылу",
        "en": "Sign up for extra lesson",
    },
    "btn_cancel": {
        "ru": "Отмена",
        "kk": "Болдырмау",
        "en": "Cancel",
    },
    "btn_change_lang": {
        "ru": "🌐 Сменить язык",
        "kk": "🌐 Тілді ауыстыру",
        "en": "🌐 Change language",
    },

    # ── вопрос преподавателю ──────────────────────────────────────────────────
    "ask_question_prompt": {
        "ru": "Напишите ваш вопрос текстом или отправьте фото с задачей.",
        "kk": "Сұрағыңызды мәтін түрінде жазыңыз немесе тапсырманың фотосын жіберіңіз.",
        "en": "Type your question or send a photo of the problem.",
    },
    "cancelled": {
        "ru": "Отменено.",
        "kk": "Болдырылды.",
        "en": "Cancelled.",
    },
    "question_sent": {
        "ru": "✅ Ваш вопрос отправлен преподавателю, ожидайте ответа.",
        "kk": "✅ Сұрағыңыз мұғалімге жіберілді, жауап күтіңіз.",
        "en": "✅ Your question has been sent to the teacher. Please wait for a reply.",
    },
    "wrong_content": {
        "ru": "Пожалуйста, отправьте текст или фото.",
        "kk": "Мәтін немесе фото жіберіңіз.",
        "en": "Please send text or a photo.",
    },

    # ── справочные материалы ──────────────────────────────────────────────────
    "choose_material": {
        "ru": "📚 Выберите нужный справочный материал:",
        "kk": "📚 Қажетті анықтамалық материалды таңдаңыз:",
        "en": "📚 Choose the reference material you need:",
    },
    "mat_solubility_btn": {
        "ru": "Таблица растворимости",
        "kk": "Ерігіштік кестесі",
        "en": "Solubility table",
    },
    "mat_periodic_btn": {
        "ru": "Периодическая система",
        "kk": "Периодтық жүйе",
        "en": "Periodic table",
    },
    "mat_organic_btn": {
        "ru": "Формулы по органике",
        "kk": "Органика формулалары",
        "en": "Organic formulas",
    },
    "mat_solubility_text": {
        "ru": (
            "📋 Таблица растворимости:\n"
            "https://upload.wikimedia.org/wikipedia/commons/9/9b/Solubility_chart.png\n\n"
            "Используйте эту таблицу для определения растворимости солей, кислот и оснований."
        ),
        "kk": (
            "📋 Ерігіштік кестесі:\n"
            "https://upload.wikimedia.org/wikipedia/commons/9/9b/Solubility_chart.png\n\n"
            "Бұл кестені тұздардың, қышқылдар мен негіздердің ерігіштігін анықтау үшін пайдаланыңыз."
        ),
        "en": (
            "📋 Solubility table:\n"
            "https://upload.wikimedia.org/wikipedia/commons/9/9b/Solubility_chart.png\n\n"
            "Use this table to determine the solubility of salts, acids, and bases."
        ),
    },
    "mat_periodic_text": {
        "ru": (
            "🧪 Периодическая система элементов Менделеева:\n"
            "https://ptable.com/\n\n"
            "Интерактивная таблица с подробной информацией о каждом элементе."
        ),
        "kk": (
            "🧪 Менделеевтің периодтық жүйесі:\n"
            "https://ptable.com/\n\n"
            "Әр элемент туралы толық ақпараты бар интерактивті кесте."
        ),
        "en": (
            "🧪 Periodic table of elements:\n"
            "https://ptable.com/\n\n"
            "Interactive table with detailed information about each element."
        ),
    },
    "mat_organic_text": {
        "ru": (
            "🔬 Основные формулы по органической химии:\n\n"
            "• Алканы: CₙH₂ₙ₊₂\n"
            "• Алкены: CₙH₂ₙ\n"
            "• Алкины: CₙH₂ₙ₋₂\n"
            "• Арены: CₙH₂ₙ₋₆ (n ≥ 6)\n"
            "• Спирты: CₙH₂ₙ₊₁OH\n"
            "• Карбоновые кислоты: CₙH₂ₙ₊₁COOH"
        ),
        "kk": (
            "🔬 Органикалық химияның негізгі формулалары:\n\n"
            "• Алкандар: CₙH₂ₙ₊₂\n"
            "• Алкендер: CₙH₂ₙ\n"
            "• Алкиндер: CₙH₂ₙ₋₂\n"
            "• Арендер: CₙH₂ₙ₋₆ (n ≥ 6)\n"
            "• Спирттер: CₙH₂ₙ₊₁OH\n"
            "• Карбон қышқылдары: CₙH₂ₙ₊₁COOH"
        ),
        "en": (
            "🔬 Basic organic chemistry formulas:\n\n"
            "• Alkanes: CₙH₂ₙ₊₂\n"
            "• Alkenes: CₙH₂ₙ\n"
            "• Alkynes: CₙH₂ₙ₋₂\n"
            "• Arenes: CₙH₂ₙ₋₆ (n ≥ 6)\n"
            "• Alcohols: CₙH₂ₙ₊₁OH\n"
            "• Carboxylic acids: CₙH₂ₙ₊₁COOH"
        ),
    },

    # ── запись на доп. урок ───────────────────────────────────────────────────
    "enter_name": {
        "ru": "Введите ваши Фамилию и Имя (например: Иванов Иван):",
        "kk": "Тегіңіз бен атыңызды енгізіңіз (мысалы: Иванов Иван):",
        "en": "Enter your full name (e.g. John Smith):",
    },
    "enter_topic": {
        "ru": "Какую тему нужно подтянуть?",
        "kk": "Қай тақырыпты қайталау керек?",
        "en": "What topic do you need help with?",
    },
    "choose_day": {
        "ru": "Выберите удобный день недели для дополнительного занятия:",
        "kk": "Қосымша сабақ үшін ыңғайлы күнді таңдаңыз:",
        "en": "Choose a convenient day for the extra lesson:",
    },
    "available_time": {
        "ru": "Свободное время на {day}:",
        "kk": "{day} күніндегі бос уақыт:",
        "en": "Available time on {day}:",
    },
    "booking_confirmed": {
        "ru": "✅ Вы успешно записаны на дополнительный урок!\nДень: {day}\nВремя: {time}",
        "kk": "✅ Сіз қосымша сабаққа сәтті жазылдыңыз!\nКүн: {day}\nУақыт: {time}",
        "en": "✅ You have been successfully signed up for an extra lesson!\nDay: {day}\nTime: {time}",
    },
    "main_menu": {
        "ru": "Главное меню:",
        "kk": "Басты мәзір:",
        "en": "Main menu:",
    },
    "back": {
        "ru": "⬅️ Назад",
        "kk": "⬅️ Артқа",
        "en": "⬅️ Back",
    },

    "no_available_days": {
        "ru": "К сожалению, сейчас нет свободных слотов для записи.",
        "kk": "Кешіріңіз, қазір жазылуға бос слоттар жоқ.",
        "en": "Sorry, there are no available slots at the moment.",
    },
    "no_available_times": {
        "ru": "На этот день нет свободных слотов.",
        "kk": "Бұл күнге бос слоттар жоқ.",
        "en": "No available slots for this day.",
    },
    "slot_already_taken": {
        "ru": "Этот слот уже занят. Выберите другое время.",
        "kk": "Бұл слот бос емес. Басқа уақыт таңдаңыз.",
        "en": "This slot is already taken. Please choose another time.",
    },

    "lesson_menu": {
        "ru": "Выберите действие:",
        "kk": "Әрекетті таңдаңыз:",
        "en": "Choose an action:",
    },
    "btn_new_booking": {
        "ru": "📝 Записаться на урок",
        "kk": "📝 Сабаққа жазылу",
        "en": "📝 Book a lesson",
    },
    "btn_my_bookings": {
        "ru": "📋 Мои записи",
        "kk": "📋 Менің жазбаларым",
        "en": "📋 My bookings",
    },
    "no_bookings": {
        "ru": "У вас нет активных записей.",
        "kk": "Сізде белсенді жазбалар жоқ.",
        "en": "You have no active bookings.",
    },
    "my_bookings_title": {
        "ru": "📋 Ваши записи:",
        "kk": "📋 Сіздің жазбаларыңыз:",
        "en": "📋 Your bookings:",
    },
    "booking_line": {
        "ru": "{n}. {day} {time} — {topic}",
        "kk": "{n}. {day} {time} — {topic}",
        "en": "{n}. {day} {time} — {topic}",
    },
    "btn_cancel_booking": {
        "ru": "❌ Отменить",
        "kk": "❌ Болдырмау",
        "en": "❌ Cancel",
    },
    "booking_cancelled": {
        "ru": "🗑 Запись отменена.",
        "kk": "🗑 Жазба болдырылды.",
        "en": "🗑 Booking cancelled.",
    },
    "booking_cancelled_by_admin": {
        "ru": "❌ Ваша запись отменена преподавателем.\n\n📅 {day} {time} — {topic}\n\n📝 Причина: {reason}",
        "kk": "❌ Сіздің жазбаңызды мұғалім болдырды.\n\n📅 {day} {time} — {topic}\n\n📝 Себебі: {reason}",
        "en": "❌ Your booking was cancelled by the teacher.\n\n📅 {day} {time} — {topic}\n\n📝 Reason: {reason}",
    },
    "lesson_reminder": {
        "ru": "⏰ Напоминание! Завтра у вас дополнительный урок.\nДень: {day}\nВремя: {time}\nТема: {topic}",
        "kk": "⏰ Еске салу! Ертең сізде қосымша сабақ.\nКүн: {day}\nУақыт: {time}\nТақырып: {topic}",
        "en": "⏰ Reminder! You have an extra lesson tomorrow.\nDay: {day}\nTime: {time}\nTopic: {topic}",
    },

    # ── профиль ученика ──────────────────────────────────────────────────────
    "btn_profile": {
        "ru": "👤 Мой профиль",
        "kk": "👤 Менің профилім",
        "en": "👤 My profile",
    },
    "profile_info": {
        "ru": "👤 Ваш профиль:\n\nИмя: {name}\nКласс: {grade}",
        "kk": "👤 Сіздің профиліңіз:\n\nАты: {name}\nСынып: {grade}",
        "en": "👤 Your profile:\n\nName: {name}\nGrade: {grade}",
    },
    "profile_empty": {
        "ru": "У вас ещё нет профиля. Давайте создадим!",
        "kk": "Сізде профиль жоқ. Жасайық!",
        "en": "You don't have a profile yet. Let's create one!",
    },
    "profile_enter_name": {
        "ru": "Введите ваше имя и фамилию:",
        "kk": "Атыңыз бен тегіңізді енгізіңіз:",
        "en": "Enter your full name:",
    },
    "profile_enter_grade": {
        "ru": "Введите ваш класс (например: 9А):",
        "kk": "Сыныбыңызды енгізіңіз (мысалы: 9А):",
        "en": "Enter your grade (e.g. 9A):",
    },
    "profile_saved": {
        "ru": "✅ Профиль сохранён!",
        "kk": "✅ Профиль сақталды!",
        "en": "✅ Profile saved!",
    },
    "btn_edit_profile": {
        "ru": "✏️ Изменить профиль",
        "kk": "✏️ Профильді өзгерту",
        "en": "✏️ Edit profile",
    },

    # ── ответ преподавателя → ученику ─────────────────────────────────────────
    "teacher_reply": {
        "ru": "Ответ преподавателя:\n{text}",
        "kk": "Мұғалімнің жауабы:\n{text}",
        "en": "Teacher's reply:\n{text}",
    },

    # ── история вопросов ───────────────────────────────────────────────────────
    "btn_history": {
        "ru": "📜 История вопросов",
        "kk": "📜 Сұрақтар тарихы",
        "en": "📜 Question history",
    },
    "history_title": {
        "ru": "📜 Ваши последние вопросы:\n",
        "kk": "📜 Соңғы сұрақтарыңыз:\n",
        "en": "📜 Your recent questions:\n",
    },
    "history_q": {
        "ru": "❓ {text}",
        "kk": "❓ {text}",
        "en": "❓ {text}",
    },
    "history_a": {
        "ru": "💬 {text}",
        "kk": "💬 {text}",
        "en": "💬 {text}",
    },
    "history_no_answer": {
        "ru": "⏳ Ожидает ответа",
        "kk": "⏳ Жауап күтілуде",
        "en": "⏳ Awaiting reply",
    },
    "history_empty": {
        "ru": "Вы ещё не задавали вопросов.",
        "kk": "Сіз әлі сұрақ қоймадыңыз.",
        "en": "You haven't asked any questions yet.",
    },

    # ── ежедневное утреннее уведомление ────────────────────────────────────────
    "daily_digest": {
        "ru": "☀️ Доброе утро! Сегодня у тебя доп. урок:\n🕐 {time} — {topic}",
        "kk": "☀️ Қайырлы таң! Бүгін сенде қосымша сабақ:\n🕐 {time} — {topic}",
        "en": "☀️ Good morning! You have an extra lesson today:\n🕐 {time} — {topic}",
    },

    # ── FAQ ─────────────────────────────────────────────────────────────────────
    "btn_faq": {
        "ru": "❓ FAQ",
        "kk": "❓ FAQ",
        "en": "❓ FAQ",
    },
    "faq_title": {
        "ru": "Выберите вопрос:",
        "kk": "Сұрақты таңдаңыз:",
        "en": "Choose a question:",
    },

    # ── админ-панель ───────────────────────────────────────────────────────
    "adm_btn_stats": {"ru": "📊 Статистика", "kk": "📊 Статистика", "en": "📊 Stats"},
    "adm_btn_students": {"ru": "👥 Ученики", "kk": "👥 Оқушылар", "en": "👥 Students"},
    "adm_btn_bookings": {"ru": "📋 Записи", "kk": "📋 Жазбалар", "en": "📋 Bookings"},
    "adm_btn_unanswered": {"ru": "❓ Без ответа", "kk": "❓ Жауапсыз", "en": "❓ Unanswered"},
    "adm_btn_questions": {"ru": "📝 Вопросы", "kk": "📝 Сұрақтар", "en": "📝 Questions"},
    "adm_btn_slots": {"ru": "📅 Слоты", "kk": "📅 Слоттар", "en": "📅 Slots"},
    "adm_btn_broadcast": {"ru": "📢 Рассылка", "kk": "📢 Хабарлама", "en": "📢 Broadcast"},
    "adm_btn_lang": {"ru": "🌐 Язык", "kk": "🌐 Тіл", "en": "🌐 Language"},
    "adm_btn_cancel": {"ru": "❌ Отмена", "kk": "❌ Болдырмау", "en": "❌ Cancel"},
    "adm_btn_ban": {"ru": "🚫 Бан", "kk": "🚫 Блок", "en": "🚫 Ban"},
    "adm_ban_title": {"ru": "🚫 Управление банами", "kk": "🚫 Блоктауды басқару", "en": "🚫 Ban management"},
    "adm_no_banned": {"ru": "Нет заблокированных пользователей.", "kk": "Блокталған пайдаланушылар жоқ.", "en": "No banned users."},
    "adm_ban_list_title": {"ru": "🚫 Заблокированные:", "kk": "🚫 Блокталғандар:", "en": "🚫 Banned:"},
    "adm_btn_unban": {"ru": "✅ Разбанить", "kk": "✅ Блоктан шығару", "en": "✅ Unban"},
    "adm_user_unbanned": {"ru": "✅ Пользователь разбанен.", "kk": "✅ Пайдаланушы блоктан шығарылды.", "en": "✅ User unbanned."},
    "adm_ban_reason": {"ru": "📝 Напишите причину бана:", "kk": "📝 Блоктау себебін жазыңыз:", "en": "📝 Write the ban reason:"},
    "adm_user_banned": {"ru": "🚫 Пользователь заблокирован.", "kk": "🚫 Пайдаланушы блокталды.", "en": "🚫 User banned."},
    "adm_ban_cancelled": {"ru": "Отмена.", "kk": "Болдырылды.", "en": "Cancelled."},
    "adm_ban_prompt": {"ru": "📝 Напишите ID пользователя для бана:", "kk": "📝 Блоктау үшін пайдаланушы ID-сін жазыңыз:", "en": "📝 Enter user ID to ban:"},
    "adm_new_question": {
        "ru": "❓ Вопрос от: {name} ({username})\nID чата: {uid}",
        "kk": "❓ Сұрақ: {name} ({username})\nЧат ID: {uid}",
        "en": "❓ Question from: {name} ({username})\nChat ID: {uid}",
    },
    "adm_click_answer": {
        "ru": "⬆️ Нажмите кнопку чтобы ответить:",
        "kk": "⬆️ Жауап беру үшін батырманы басыңыз:",
        "en": "⬆️ Click the button to answer:",
    },
    "adm_new_booking": {
        "ru": "🔔 Новая запись на доп. урок!\nУченик: {name} ({username})\nТема: {topic}\nДень: {day}\nВремя: {time}",
        "kk": "🔔 Қосымша сабаққа жаңа жазба!\nОқушы: {name} ({username})\nТақырып: {topic}\nКүн: {day}\nУақыт: {time}",
        "en": "🔔 New lesson booking!\nStudent: {name} ({username})\nTopic: {topic}\nDay: {day}\nTime: {time}",
    },
    "adm_booking_cancel_notify": {
        "ru": "🗑 Отмена записи на доп. урок!\nУченик: {name} ({username})\nТема: {topic}\nДень: {day}\nВремя: {time}",
        "kk": "🗑 Қосымша сабаққа жазба болдырылды!\nОқушы: {name} ({username})\nТақырып: {topic}\nКүн: {day}\nУақыт: {time}",
        "en": "🗑 Lesson booking cancelled!\nStudent: {name} ({username})\nTopic: {topic}\nDay: {day}\nTime: {time}",
    },
    "no_username": {
        "ru": "нет username",
        "kk": "username жоқ",
        "en": "no username",
    },
    "adm_welcome": {
        "ru": "🔧 <b>Добро пожаловать в админ-панель!</b>",
        "kk": "🔧 <b>Админ панеліне қош келдіңіз!</b>",
        "en": "🔧 <b>Welcome to the admin panel!</b>",
    },
    "adm_panel_title": {
        "ru": "🔧 <b>Админ-панель</b>\n\nИспользуйте кнопки ниже для управления ботом.",
        "kk": "🔧 <b>Админ панелі</b>\n\nБотты басқару үшін төмендегі батырмаларды пайдаланыңыз.",
        "en": "🔧 <b>Admin Panel</b>\n\nUse the buttons below to manage the bot.",
    },
    "adm_stats": {
        "ru": "📊 <b>Статистика</b>\n\n👥 Пользователей: {total_users}\n👤 С профилем: {profiles}\n📅 Активных записей: {active_bookings}\n📝 Всего вопросов: {total_questions}\n❓ Без ответа: {unanswered}\n🕐 Тайм-слотов: {total_slots}",
        "kk": "📊 <b>Статистика</b>\n\n👥 Пайдаланушылар: {total_users}\n👤 Профильмен: {profiles}\n📅 Белсенді жазбалар: {active_bookings}\n📝 Барлық сұрақтар: {total_questions}\n❓ Жауапсыз: {unanswered}\n🕐 Слоттар: {total_slots}",
        "en": "📊 <b>Stats</b>\n\n👥 Users: {total_users}\n👤 With profile: {profiles}\n📅 Active bookings: {active_bookings}\n📝 Total questions: {total_questions}\n❓ Unanswered: {unanswered}\n🕐 Time slots: {total_slots}",
    },
    "adm_no_students": {
        "ru": "Нет учеников с заполненным профилем.",
        "kk": "Профилі толтырылған оқушылар жоқ.",
        "en": "No students with a filled profile.",
    },
    "adm_students_title": {
        "ru": "👥 <b>Ученики:</b>\n",
        "kk": "👥 <b>Оқушылар:</b>\n",
        "en": "👥 <b>Students:</b>\n",
    },
    "adm_no_bookings": {
        "ru": "Нет активных записей на ближайшее время.",
        "kk": "Жақын арада белсенді жазбалар жоқ.",
        "en": "No active bookings coming up.",
    },
    "adm_bookings_title": {
        "ru": "📋 <b>Активные записи:</b>\n",
        "kk": "📋 <b>Белсенді жазбалар:</b>\n",
        "en": "📋 <b>Active bookings:</b>\n",
    },
    "adm_all_answered": {
        "ru": "✅ Все вопросы отвечены!",
        "kk": "✅ Барлық сұрақтарға жауап берілді!",
        "en": "✅ All questions answered!",
    },
    "adm_unanswered_title": {
        "ru": "❓ <b>Без ответа:</b>\n",
        "kk": "❓ <b>Жауапсыз:</b>\n",
        "en": "❓ <b>Unanswered:</b>\n",
    },
    "adm_no_questions": {
        "ru": "Нет вопросов.",
        "kk": "Сұрақтар жоқ.",
        "en": "No questions.",
    },
    "adm_questions_title": {
        "ru": "📝 <b>Все вопросы:</b>\n",
        "kk": "📝 <b>Барлық сұрақтар:</b>\n",
        "en": "📝 <b>All questions:</b>\n",
    },
    "adm_no_slots": {
        "ru": "Нет настроенных слотов.",
        "kk": "Орнатылған слоттар жоқ.",
        "en": "No configured slots.",
    },
    "adm_slots_title": {
        "ru": "📅 <b>Текущие слоты:</b>\n",
        "kk": "📅 <b>Ағымдағы слоттар:</b>\n",
        "en": "📅 <b>Current slots:</b>\n",
    },
    "adm_broadcast_prompt": {
        "ru": "📢 Напишите сообщение для рассылки.\nМожно отправить текст или фото.",
        "kk": "📢 Хабарлама үшін мәтін жазыңыз.\nМәтін немесе фото жіберуге болады.",
        "en": "📢 Write a message to broadcast.\nYou can send text or a photo.",
    },
    "adm_broadcast_cancelled": {
        "ru": "Рассылка отменена.",
        "kk": "Хабарлама болдырылды.",
        "en": "Broadcast cancelled.",
    },
    "adm_broadcast_done": {
        "ru": "📢 Рассылка завершена.\n✅ Доставлено: {sent}\n❌ Ошибок: {failed}",
        "kk": "📢 Хабарлама аяқталды.\n✅ Жеткізілді: {sent}\n❌ Қателер: {failed}",
        "en": "📢 Broadcast done.\n✅ Delivered: {sent}\n❌ Failed: {failed}",
    },
    "adm_answer_prompt": {
        "ru": "✏️ Вопрос от ученика:\n<i>{q}</i>\n\nНапишите ваш ответ:",
        "kk": "✏️ Оқушының сұрағы:\n<i>{q}</i>\n\nЖауабыңызды жазыңыз:",
        "en": "✏️ Student's question:\n<i>{q}</i>\n\nWrite your answer:",
    },
    "adm_answer_sent": {
        "ru": "✅ Ответ отправлен ученику.",
        "kk": "✅ Жауап оқушыға жіберілді.",
        "en": "✅ Answer sent to student.",
    },
    "adm_cancel_reason": {
        "ru": "📝 Напишите причину отмены записи:",
        "kk": "📝 Жазбаны болдырмау себебін жазыңыз:",
        "en": "📝 Write the reason for cancellation:",
    },
    "adm_booking_deleted": {
        "ru": "🗑 Запись удалена: {name} — {day} {time}\nПричина: {reason}\nУченик уведомлён.",
        "kk": "🗑 Жазба жойылды: {name} — {day} {time}\nСебебі: {reason}\nОқушыға хабарланды.",
        "en": "🗑 Booking deleted: {name} — {day} {time}\nReason: {reason}\nStudent notified.",
    },
    "adm_cancelled": {
        "ru": "Отменено.",
        "kk": "Болдырылды.",
        "en": "Cancelled.",
    },
    "adm_lang_changed": {
        "ru": "✅ Язык изменён: {name}",
        "kk": "✅ Тіл өзгертілді: {name}",
        "en": "✅ Language changed: {name}",
    },
    "adm_btn_answer": {
        "ru": "✏️ Ответить",
        "kk": "✏️ Жауап беру",
        "en": "✏️ Answer",
    },
    "adm_btn_cancel_booking": {
        "ru": "❌ Отменить",
        "kk": "❌ Болдырмау",
        "en": "❌ Cancel",
    },
    "adm_btn_delete_question": {
        "ru": "🗑 Удалить",
        "kk": "🗑 Жою",
        "en": "🗑 Delete",
    },
    "adm_question_deleted": {
        "ru": "🗑 Вопрос удалён.",
        "kk": "🗑 Сұрақ жойылды.",
        "en": "🗑 Question deleted.",
    },
}


FAQ_DATA: list[dict[str, dict[str, str]]] = [
    {
        "q": {
            "ru": "Как записаться на доп. урок?",
            "kk": "Қосымша сабаққа қалай жазылуға болады?",
            "en": "How do I sign up for an extra lesson?",
        },
        "a": {
            "ru": "Нажмите кнопку «Записаться на доп. урок» в главном меню, затем выберите день и время.",
            "kk": "Басты мәзірден «Қосымша сабаққа жазылу» батырмасын басыңыз, содан кейін күн мен уақытты таңдаңыз.",
            "en": "Press 'Sign up for extra lesson' in the main menu, then choose a day and time.",
        },
    },
    {
        "q": {
            "ru": "Как отменить запись?",
            "kk": "Жазбаны қалай болдыруға болады?",
            "en": "How do I cancel a booking?",
        },
        "a": {
            "ru": "Нажмите «Записаться на доп. урок» → «Мои записи», затем нажмите кнопку отмены рядом с нужной записью.",
            "kk": "«Қосымша сабаққа жазылу» → «Менің жазбаларым» басыңыз, содан кейін қажетті жазба жанындағы болдырмау батырмасын басыңыз.",
            "en": "Press 'Sign up for extra lesson' → 'My bookings', then tap the cancel button next to the booking.",
        },
    },
    {
        "q": {
            "ru": "Как задать вопрос учителю?",
            "kk": "Мұғалімге қалай сұрақ қоюға болады?",
            "en": "How do I ask the teacher a question?",
        },
        "a": {
            "ru": "Нажмите «Задать вопрос преподавателю» и отправьте текст или фото. Ответ придёт в этот чат.",
            "kk": "«Мұғалімге сұрақ қою» батырмасын басып, мәтін немесе фото жіберіңіз. Жауап осы чатқа келеді.",
            "en": "Press 'Ask the teacher' and send text or a photo. The reply will arrive in this chat.",
        },
    },
    {
        "q": {
            "ru": "Как изменить язык?",
            "kk": "Тілді қалай ауыстыруға болады?",
            "en": "How do I change the language?",
        },
        "a": {
            "ru": "Нажмите «🌐 Сменить язык» в главном меню.",
            "kk": "Басты мәзірден «🌐 Тілді ауыстыру» батырмасын басыңыз.",
            "en": "Press '🌐 Change language' in the main menu.",
        },
    },
    {
        "q": {
            "ru": "Когда приходят напоминания?",
            "kk": "Еске салулар қашан келеді?",
            "en": "When do reminders arrive?",
        },
        "a": {
            "ru": "За 22 часа до урока и утром в день урока (в 8:00).",
            "kk": "Сабақтан 22 сағат бұрын және сабақ күні таңертең (8:00-де).",
            "en": "22 hours before the lesson and on the morning of the lesson day (at 8:00 AM).",
        },
    },
]

from aiogram.filters.callback_data import CallbackData


class LangCallbackFactory(CallbackData, prefix="lang", sep="|"):
    lang: str


class DayCallbackFactory(CallbackData, prefix="day", sep="|"):
    day: str


class TimeCallbackFactory(CallbackData, prefix="time", sep="|"):
    day: str
    time: str


class CancelBookingFactory(CallbackData, prefix="cdel", sep="|"):
    booking_id: int


class FaqCallbackFactory(CallbackData, prefix="faq", sep="|"):
    idx: int


class AdminCancelBookingFactory(CallbackData, prefix="adel", sep="|"):
    booking_id: int


class AnswerQuestionFactory(CallbackData, prefix="ansq", sep="|"):
    question_id: int


class BanCallbackFactory(CallbackData, prefix="ban", sep="|"):
    user_id: int
    action: str

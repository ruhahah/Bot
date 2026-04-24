from aiogram.fsm.state import State, StatesGroup


class QuestionFSM(StatesGroup):
    waiting_for_question = State()


class LessonFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_topic = State()
    choosing_day = State()
    choosing_time = State()


class ProfileFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_grade = State()


class BroadcastFSM(StatesGroup):
    waiting_for_message = State()


class AddSlotFSM(StatesGroup):
    waiting_for_input = State()


class DelSlotFSM(StatesGroup):
    waiting_for_input = State()


class AdminCancelFSM(StatesGroup):
    waiting_for_reason = State()


class AnswerQuestionFSM(StatesGroup):
    waiting_for_answer = State()


class BanFSM(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_reason = State()

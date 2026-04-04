from maxapi import Router
from maxapi.types import MessageCreated, Command, BotStarted
from maxapi.context import MemoryContext, StatesGroup, State
from core.config import bot
from core.models import db_helper
from .crud import create_user, get_chat_by_name

router = Router()

class UserStates(StatesGroup):
    waiting_for_city = State()
    accepting_advertisement = State()  # режим приёма сообщений о рекламе

# стартовое сообщение при запуске бота
@router.bot_started()
async def bot_started(event: BotStarted, context: MemoryContext):
    async with db_helper.scoped_session_dependency() as session:
        await create_user(session, event.from_user.user_id)

    await bot.send_message(
        chat_id=event.chat_id,
        text="""Здравствуйте 🖐

Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ В каком городе находится Ваше заведение?

Просто напишите город текстом."""
    )

    await context.set_state(UserStates.waiting_for_city)

# команда /start
@router.message_created(Command('start'))
async def start(event: MessageCreated, context: MemoryContext):
    async with db_helper.scoped_session_dependency() as session:
        await create_user(session, event.from_user.user_id)

    await event.message.answer(
        "Приветствую 🖐\n\nПожалуйста, напишите город, где нужно разместить рекламу:"
    )
    await context.set_state(UserStates.waiting_for_city)

@router.message_created(UserStates.waiting_for_city)
async def handle_message(event: MessageCreated, context: MemoryContext):
    state = await context.get_state()
    text = getattr(event.message.body, "text", "").strip()
    if not text:
        return

    if state == UserStates.waiting_for_city:
        async with db_helper.scoped_session_dependency() as session:
            chat = await get_chat_by_name(session, text)

            if not chat:
                return await event.message.answer(
                    f"Город '{text}' не найден в базе. Попробуйте еще раз."
                )

            await create_user(session, event.from_user.user_id, chat_id=chat.chat_id)

        await context.set_state(None)
        await context.clear()
        return await event.message.answer("""Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?"""
        )
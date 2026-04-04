from maxapi import Router
from maxapi.types import MessageCreated, Command, BotStarted
from core.config import bot
from core.models import db_helper
from .crud import create_user, get_child_chats, get_root_chats, get_chat_by_id
from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import MessageCallback


router = Router()

async def build_cities_keyboard(session):
    chats = await get_root_chats(session)

    builder = InlineKeyboardBuilder()

    for chat in chats:
        builder.row(
            CallbackButton(
                text=f"🔗 {chat.name}",
                payload=f"city_{chat.chat_id}"
            )
        )

    return builder.as_markup()

@router.bot_started()
async def bot_started(event: BotStarted):
    async with db_helper.scoped_session_dependency() as session:
        await create_user(session, event.from_user.user_id)

    await bot.send_message(
        chat_id=event.chat_id,
        text="""Здравствуйте 🖐

Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?

Мы ответим Вам в ближайшее время 😉""")


@router.message_created(Command('start'))
async def start(event: MessageCreated):
    async with db_helper.scoped_session_dependency() as session:
        keyboard = await build_cities_keyboard(session)

    await event.message.answer(
        "Приветствую 🖐\n\nВыберите город, где нужно разместить рекламу:",
        attachments=[keyboard]
    )

@router.message_callback()
async def handle_city(callback: MessageCallback):
    data = callback.callback.payload  # city_1

    if not data.startswith("city_"):
        return

    chat_id = int(data.split("_")[1])

    async with db_helper.scoped_session_dependency() as session:
        chat = await get_chat_by_id(session, chat_id)
        if not chat:
            await callback.message.answer("Ошибка: выбранный город не найден в базе.")
            return

        children = await get_child_chats(session, chat.id)

        if children:
            builder = InlineKeyboardBuilder()

            for child in children:
                builder.row(
                    CallbackButton(
                        text=f"🔗 {child.name}",
                        payload=f"city_{child.chat_id}"
                    )
                )

            await callback.message.answer(
                f"Выберите район ({chat.name}):",
                attachments=[builder.as_markup()]
            )
            return

        await create_user(
            session,
            callback.from_user.user_id,
            chat_id=chat.chat_id
        )

        await callback.message.answer(
            """Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?"""
        )


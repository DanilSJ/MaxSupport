from maxapi import Router, F
from maxapi.types import MessageCreated, Command, BotStarted
from core.config import bot
from maxapi.exceptions import MaxApiError
from maxapi.enums.parse_mode import ParseMode
from core.config import settings
from core.models import db_helper
from .crud import create_user, get_user_with_chat, get_all_chats_id, get_child_chats, get_root_chats, get_chat_by_id
from maxapi.context import MemoryContext
from app.utils.rate_limit import rate_limit
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
    async for session in db_helper.scoped_session_dependency():
        await create_user(session, event.from_user.user_id)
        break

    await bot.send_message(
        chat_id=event.chat_id,
        text="""Здравствуйте 🖐

Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?

Мы ответим Вам в ближайшее время 😉""")


@router.message_created(Command('start'))
async def start(event: MessageCreated):
    async for session in db_helper.scoped_session_dependency():
        keyboard = await build_cities_keyboard(session)

        await event.message.answer(
            "Приветствую 🖐\n\nВыберите город, где нужно разместить рекламу:",
            attachments=[keyboard]
        )
        break

@router.message_callback()
async def handle_city(callback: MessageCallback):
    data = callback.callback.payload  # city_1

    if not data.startswith("city_"):
        return

    chat_id = int(data.split("_")[1])

    async for session in db_helper.scoped_session_dependency():
        print(chat_id)
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

        break

@router.message_created(F.message.body)
@rate_limit(limit=2, seconds=2)
async def echo(event: MessageCreated, context: MemoryContext):

    current_state = await context.get_state()

    if current_state is not None:
        return

    try:

        async for session in db_helper.scoped_session_dependency():
            user = await get_user_with_chat(session, event.from_user.user_id)

            chats_id = await get_all_chats_id(session)

            if event.chat.chat_id not in chats_id:
                return await event.message.forward(chat_id=user.chat_id)


            if event.message.link.sender.user_id == 230120179:
                user = await bot.get_message(event.message.link.message.mid)

                try:
                    return await bot.send_message(user_id=user.link.sender.user_id, text=event.message.body.text)
                except MaxApiError:
                    return await bot.send_message(chat_id=settings.GROUP,
                                                  text=f"<a href='max://user/{user.link.sender.user_id}'>Пользователь</a> заблокировал бота",
                                                  parse_mode=ParseMode.HTML)

            break
    except Exception as e:
        print(e)
        return await event.message.answer("Бот не добавлен в группу")
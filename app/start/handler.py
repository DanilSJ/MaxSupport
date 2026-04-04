from maxapi import Router
from maxapi.types import MessageCreated, Command, BotStarted, MessageCallback, CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from core.config import bot
from core.models import db_helper
from .crud import create_user, get_child_chats, get_root_chats, get_chat_by_id

router = Router()

PAGE_SIZE = 10

async def build_cities_keyboard(session, page: int = 0):
    chats = await get_root_chats(session)
    builder = InlineKeyboardBuilder()

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    for chat in chats[start:end]:
        # payload теперь содержит chat_id и часть названия
        payload_name = chat.name.replace(" ", "_")
        builder.row(
            CallbackButton(
                text=f"🔗 {chat.name}",
                payload=f"city_{chat.chat_id}_{payload_name}"
            )
        )

    if end < len(chats):
        builder.row(
            CallbackButton(
                text="➡️ Следующие города",
                payload=f"city_page_{page+1}"
            )
        )

    builder.row(
        CallbackButton(
            text="Другое",
            payload="city_other"
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

Мы ответим Вам в ближайшее время 😉"""
    )


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
    data = callback.callback.payload

    async with db_helper.scoped_session_dependency() as session:
        if data == "city_other":
            fixed_chat_id = -73032999721126
            await create_user(
                session,
                callback.from_user.user_id,
                chat_id=fixed_chat_id
            )
            return await callback.message.answer(
                """Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?"""
            )

        # Обработка кнопок пагинации
        if data.startswith("city_page_"):
            page = int(data.split("_")[2])
            keyboard = await build_cities_keyboard(session, page=page)
            return await callback.message.edit(
                text="Выберите город, где нужно разместить рекламу:",
                attachments=[keyboard]
            )

        # Обработка выбора города
        if not data.startswith("city_"):
            return

        parts = data.split("_", 2)
        chat_id = int(parts[1])
        name_part = parts[2] if len(parts) > 2 else None

        chat = await get_chat_by_id(session, chat_id, name_part=name_part)
        if not chat:
            await callback.message.answer("Ошибка: выбранный город не найден в базе.")
            return

        children = await get_child_chats(session, chat.id)

        if children:
            builder = InlineKeyboardBuilder()
            for child in children:
                payload_name = child.name.replace(" ", "_")
                builder.row(
                    CallbackButton(
                        text=f"🔗 {child.name}",
                        payload=f"city_{child.chat_id}_{payload_name}"
                    )
                )
            builder.row(
                CallbackButton(
                    text="Другое",
                    payload="city_other"
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
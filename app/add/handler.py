from maxapi import Router
from maxapi.types import MessageCreated, Command

from app.add.crud import get_chat_by_name, update_user_chat
from core.config import bot
from maxapi.exceptions import MaxApiError
from maxapi.enums.parse_mode import ParseMode
from maxapi.context import MemoryContext

from core.models import db_helper

router = Router()

@router.message_created(Command('add'))
async def add(event: MessageCreated, context: MemoryContext):

    current_state = await context.get_state()

    if current_state is not None:
        return

    text = event.message.body.text.strip()
    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        return await event.message.answer(
            "❌ Укажите город!\nПример: /add Москва"
        )

    city_name = parts[1].strip().lower()  # Переименовал переменную для ясности

    try:
        if event.message.link.sender.user_id == 230120179:
            user = await bot.get_message(event.message.link.message.mid)
            async with db_helper.scoped_session_dependency() as session:
                # Используем get_chat_by_name для поиска города
                chat = await get_chat_by_name(session, city_name)

                try:
                    if chat:
                        await update_user_chat(session, user.link.sender.user_id, chat.chat_id)

                        await event.message.answer(
                            f"<a href='max://user/{user.link.sender.user_id}'>Пользователь</a> добавлен в чат {chat.name}",
                            parse_mode=ParseMode.HTML, )
                    else:
                        await event.message.answer(f"Город с названием {city_name} не найден")

                except MaxApiError:
                    await event.message.answer(
                        f"<a href='max://user/{user.link.sender.user_id}'>Пользователь</a> не добавлен в чат {chat.name if chat else 'неизвестный'} - заблокировал бота",
                        parse_mode=ParseMode.HTML,)

    except Exception as e:
        return await event.message.answer("Бот не добавлен в группу")
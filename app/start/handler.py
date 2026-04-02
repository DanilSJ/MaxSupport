from maxapi import Router, F
from maxapi.types import MessageCreated, Command, BotStarted
from core.config import bot
from maxapi.exceptions import MaxApiError
from maxapi.enums.parse_mode import ParseMode
from collections import defaultdict
import time
from core.config import settings

router = Router()

user_messages = defaultdict(list)


def rate_limit(limit: int = 2, seconds: int = 3):
    """Декоратор для ограничения частоты сообщений"""

    def decorator(func):
        async def wrapper(event: MessageCreated):
            user_id = event.message.sender.user_id
            current_time = time.time()

            user_messages[user_id] = [
                msg_time for msg_time in user_messages[user_id]
                if current_time - msg_time < seconds
            ]

            if len(user_messages[user_id]) >= limit:
                await event.message.answer(
                    "⏰ Пожалуйста, не отправляйте сообщения так часто. "
                    f"Подождите {seconds} секунды перед следующим сообщением."
                )
                return

            user_messages[user_id].append(current_time)

            return await func(event)

        return wrapper

    return decorator


@router.bot_started()
async def bot_started(event: BotStarted):
    await bot.send_message(
        chat_id=event.chat_id,
        text="""Здравствуйте 🖐

Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?

Мы ответим Вам в ближайшее время 😉""")


@router.message_created(Command('start'))
async def start(event: MessageCreated):
    await event.message.answer("""Здравствуйте 🖐

Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?

Мы ответим Вам в ближайшее время 😉""")


@router.message_created(F.message.body)
@rate_limit(limit=2, seconds=2)
async def echo(event: MessageCreated):
    try:
        if event.chat.chat_id != settings.GROUP:
            return await event.message.forward(chat_id=settings.GROUP)

        if event.message.link.sender.user_id == 230120179:
            user = await bot.get_message(event.message.link.message.mid)

            try:
                return await bot.send_message(user_id=user.link.sender.user_id, text=event.message.body.text)
            except MaxApiError:
                return await bot.send_message(chat_id=settings.GROUP,
                                              text=f"<a href='max://user/{user.link.sender.user_id}'>Пользователь</a> заблокировал бота",
                                              parse_mode=ParseMode.HTML)
    except MaxApiError:
        return await event.message.answer("Бот не добавлен в группу")
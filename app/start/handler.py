from maxapi import Router, F
from maxapi.types import MessageCreated, Command, BotStarted
from core.config import bot
from maxapi.exceptions import MaxApiError
from maxapi.enums.parse_mode import ParseMode
from collections import defaultdict
import time
import asyncio
from core.config import settings
from core.models import db_helper
from .crud import create_user, get_all_users
from maxapi.context import MemoryContext, StatesGroup, State

router = Router()

user_messages = defaultdict(list)


class MailingStates(StatesGroup):
    """Состояния для рассылки"""
    waiting_for_text = State()


def rate_limit(limit: int = 2, seconds: int = 3):
    def decorator(func):
        async def wrapper(event: MessageCreated, context: MemoryContext, *args, **kwargs):
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

            return await func(event, context, *args, **kwargs)

        return wrapper
    return decorator

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
        await create_user(session, event.from_user.user_id)
        break

    await event.message.answer("""Здравствуйте 🖐

Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?

Мы ответим Вам в ближайшее время 😉""")


@router.message_created(Command('mailing'))
async def mailing_command(event: MessageCreated, context: MemoryContext):
    """Команда для начала рассылки"""
    await context.set_state(MailingStates.waiting_for_text)
    await context.update_data(admin_id=event.message.sender.user_id)

    await event.message.answer(
        "📢 **Режим рассылки активирован**\n\n"
        "Отправьте текст сообщения, которое хотите разослать всем пользователям.\n\n"
        "Для отмены рассылки отправьте /cancel_mailing",
        parse_mode=ParseMode.MARKDOWN
    )


@router.message_created(Command('cancel_mailing'))
async def cancel_mailing(event: MessageCreated, context: MemoryContext):
    """Отмена рассылки"""
    current_state = await context.get_state()

    if current_state == MailingStates.waiting_for_text:
        await context.set_state(None)
        await context.clear()
        await event.message.answer("✅ Рассылка отменена.")
    else:
        await event.message.answer("❌ Активная рассылка не найдена.")


@router.message_created(MailingStates.waiting_for_text)
async def process_mailing_text(event: MessageCreated, context: MemoryContext):
    await event.message.answer(
        "**Начинаю рассылку...**",
        parse_mode=ParseMode.MARKDOWN
    )

    await context.set_state(None)

    users = []

    async for session in db_helper.scoped_session_dependency():
        users = await get_all_users(session)
        break

    if not users:
        await event.message.answer("❌ В базе данных нет пользователей для рассылки.")
        await context.clear()
        return

    for user in users:
        try:
            await bot.send_message(
                user_id=user.max_id,
                text=event.message.body.text,
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(0.1)
        except Exception as e:
            print(e)
            pass

    await event.message.answer("Рассылка завершена")

    await context.clear()

@router.message_created(F.message.body)
@rate_limit(limit=2, seconds=2)
async def echo(event: MessageCreated, context: MemoryContext):

    current_state = await context.get_state()

    if current_state is not None:
        return

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
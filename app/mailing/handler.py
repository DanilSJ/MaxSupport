from maxapi import Router
from maxapi.types import MessageCreated, Command
from core.config import bot
from maxapi.enums.parse_mode import ParseMode
import asyncio
from core.models import db_helper
from .crud import get_all_users, get_user
from maxapi.context import MemoryContext, StatesGroup, State

router = Router()

class MailingStates(StatesGroup):
    """Состояния для рассылки"""
    waiting_for_text = State()


@router.message_created(Command('mailing'))
async def mailing_command(event: MessageCreated, context: MemoryContext):
    """Команда для начала рассылки — доступ только для админов"""
    user_id = event.message.sender.user_id

    user = []

    async with db_helper.scoped_session_dependency() as session:
        user = await get_user(session, user_id)

    if user and getattr(user, 'admin', False):
        await context.set_state(MailingStates.waiting_for_text)
        await context.update_data(admin_id=user_id)
        await event.message.answer(
            "📢 **Режим рассылки активирован**\n\n"
            "Отправьте текст сообщения для рассылки всем пользователям.\n\n"
            "Для отмены рассылки отправьте /cancel_mailing",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await event.message.answer("❌ У вас нет доступа к этой команде.")


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
    async with db_helper.scoped_session_dependency() as session:
        users = await get_all_users(session)

    if not users:
        await event.message.answer("❌ В базе данных нет пользователей для рассылки.")
        await context.clear()
        return

    success_count = 0
    blocked_count = 0

    for user in users:
        try:
            await bot.send_message(
                user_id=user.max_id,
                text=event.message.body.text,
                parse_mode=ParseMode.HTML
            )
            success_count += 1
            await asyncio.sleep(0.1)
        except Exception:
            blocked_count += 1
            continue

    await event.message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"Всего пользователей в боте: {len(users)}\n"
        f"Сообщений отправлено: {success_count}\n"
        f"Не смогли доставить (заблокировали бота или ошибки): {blocked_count}"
    )

    await context.clear()
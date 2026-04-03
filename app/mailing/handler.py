from maxapi import Router
from maxapi.types import MessageCreated, Command
from core.config import bot
from maxapi.enums.parse_mode import ParseMode
import asyncio
from core.models import db_helper
from .crud import get_all_users
from maxapi.context import MemoryContext, StatesGroup, State
router = Router()

class MailingStates(StatesGroup):
    """Состояния для рассылки"""
    waiting_for_text = State()


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

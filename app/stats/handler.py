from maxapi import Router
from maxapi.types import MessageCreated, Command
from core.models import db_helper
from .crud import get_users_count, get_user
from maxapi.enums.parse_mode import ParseMode

router = Router()


@router.message_created(Command('stats'))
async def stats(event: MessageCreated):
    user_id = event.message.sender.user_id
    users_count = 0
    async with db_helper.scoped_session_dependency() as session:
        user = await get_user(session, user_id)
        if not user or not getattr(user, 'admin', False):
            await event.message.answer("❌ У вас нет доступа к этой команде.")
            return

        users_count = await get_users_count(session)

    await event.message.answer(
        f"📊 **Статистика бота**\n\n"
        f"Всего пользователей: {users_count}",
        parse_mode=ParseMode.MARKDOWN
    )
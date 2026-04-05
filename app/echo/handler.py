from maxapi import Router, F
from maxapi.types import MessageCreated
from core.config import bot
from maxapi.exceptions import MaxApiError
from maxapi.enums.parse_mode import ParseMode
from core.models import db_helper
from maxapi.context import MemoryContext
from app.utils.rate_limit import rate_limit
from .crud import get_all_chats_id, get_user_with_chat
from app.utils.crud import create_message

router = Router()

@router.message_created(F.message.body)
@rate_limit(limit=2, seconds=2)
async def echo(event: MessageCreated, context: MemoryContext):
    current_state = await context.get_state()

    if current_state is not None:
        return

    try:
        async with db_helper.scoped_session_dependency() as session:
            user = await get_user_with_chat(session, event.from_user.user_id)

            chats_id = await get_all_chats_id(session)

            try:
                if event.chat.chat_id not in chats_id:
                    if not user.chat_id:
                        return await event.message.answer("Выберите сначала свой город через команду /start")
                    await create_message(session, user.max_id, user.chat_id, False, True)

                    return await event.message.forward(chat_id=user.chat_id)
            except Exception as e:
                print(e)
                return await event.message.answer("Выберите сначала свой город через команду /start")

            if event.message.link.sender.user_id == 230120179:
                user_obj = await bot.get_message(event.message.link.message.mid)

                try:
                    await create_message(session, user_obj.link.sender.user_id, user_obj.link.sender.user_id, True, False)

                    if event.message.body.attachments:
                        attachment = event.message.body.attachments[0]
                        text = event.message.body.text if event.message.body.text else None
                        return await bot.send_message(
                            user_id=user_obj.link.sender.user_id,
                            text=text,
                            attachments=[attachment],
                            parse_mode=ParseMode.HTML if text else None
                        )
                    else:
                        return await bot.send_message(
                            user_id=user_obj.link.sender.user_id,
                            text=event.message.body.text
                        )
                except MaxApiError:
                    return await bot.send_message(chat_id=event.chat.chat_id,
                                                  text=f"<a href='max://user/{user_obj.link.sender.user_id}'>Пользователь</a> заблокировал бота",
                                                  parse_mode=ParseMode.HTML)

    except Exception as e:
        print(e)
        return await event.message.answer("Бот не добавлен в группу")
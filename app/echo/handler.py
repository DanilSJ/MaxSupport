from maxapi import Router, F
from maxapi.types import MessageCreated, MessageEdited
from core.config import bot
from maxapi.exceptions import MaxApiError
from maxapi.enums.parse_mode import ParseMode
from core.models import db_helper
from maxapi.context import MemoryContext
from app.utils.rate_limit import rate_limit
from .crud import get_all_chats_id, get_user_with_chat
from app.utils.crud import create_message, get_message_by_admin_id

router = Router()

@router.message_edited()
async def message_edited(event: MessageEdited):
    if event.message.link.sender.user_id != 230120179:
        return

    admin_message_id = event.message.link.message.mid
    print(admin_message_id)
    async with db_helper.scoped_session_dependency() as session:
        db_message = await get_message_by_admin_id(
            session,
            admin_message_id
        )
        if not db_message:
            return

        user_chat_id = db_message.chat_id
        user_message_id = db_message.user_message_id

        try:
            await bot.edit_message(
                message_id=user_message_id,
                text=event.message.body.text,
                attachments=event.message.body.attachments if event.message.body.attachments else None,
                parse_mode=ParseMode.HTML if event.message.body.text else None
            )

        except MaxApiError:
            await bot.send_message(
                chat_id=event.chat.chat_id,
                text=f"<a href='max://user/{user_chat_id}'>Пользователь</a> заблокировал бота",
                parse_mode=ParseMode.HTML
            )


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

                    await create_message(session, user.max_id, user.chat_id, None, event.message.body.mid,False, True)

                    event.message.body.text = f"ID: {event.from_user.user_id} UserName:{event.from_user.username}\nИмя фамилия: {event.from_user.first_name} {event.from_user.last_name}\n\n{event.message.body.text}"

                    return await event.message.forward(chat_id=user.chat_id)
            except Exception as e:
                print(e)
                return await event.message.answer("Выберите сначала свой город через команду /start")

            if event.message.link.sender.user_id == 230120179:
                user_obj = await bot.get_message(event.message.link.message.mid)

                try:
                    if event.message.body.attachments:
                        text = event.message.body.text if event.message.body.text else None
                        sent = await bot.send_message(
                            user_id=user_obj.link.sender.user_id,
                            text=text,
                            attachments=event.message.body.attachments,
                            parse_mode=ParseMode.HTML if text else None
                        )
                    else:
                        sent = await bot.send_message(
                            user_id=user_obj.link.sender.user_id,
                            text=event.message.body.text
                        )

                    await create_message(session, user_obj.link.sender.user_id, user_obj.link.sender.user_id, event.message.link.message.mid, sent.message.body.mid,True, False,)

                except MaxApiError:
                    return await bot.send_message(chat_id=event.chat.chat_id,
                                                  text=f"<a href='max://user/{user_obj.link.sender.user_id}'>Пользователь</a> заблокировал бота",
                                                  parse_mode=ParseMode.HTML)

    except Exception as e:
        print(e)
        return await event.message.answer("Бот не добавлен в группу")
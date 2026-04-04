from maxapi import Router
from maxapi.types import MessageCreated, Command
from core.config import bot
from maxapi.enums.parse_mode import ParseMode
import asyncio
from core.models import db_helper
from .crud import get_all_users, get_user, get_all_chats, get_users_by_chat
from maxapi.context import MemoryContext, StatesGroup, State

router = Router()


class MailingStates(StatesGroup):
    """Состояния для рассылки"""
    waiting_for_city = State()
    waiting_for_text = State()


@router.message_created(Command('mailing'))
async def mailing_command(event: MessageCreated, context: MemoryContext):
    """Команда для начала рассылки — доступ только для админов"""
    user_id = event.message.sender.user_id

    user = []

    async with db_helper.scoped_session_dependency() as session:
        user = await get_user(session, user_id)

    if user and getattr(user, 'admin', False):
        await context.set_state(MailingStates.waiting_for_city)
        await context.update_data(admin_id=user_id)

        # Получаем список всех городов
        async with db_helper.scoped_session_dependency() as session:
            chats = await get_all_chats(session)

        if not chats:
            await event.message.answer("❌ В базе данных нет доступных городов для рассылки.")
            await context.set_state(None)
            await context.clear()
            return

        # Формируем список городов
        cities_list = "\n".join([f"• {chat.name}" for chat in chats])

        await event.message.answer(
            f"🏙️ **Выберите город для рассылки**\n\n"
            f"Доступные города:\n{cities_list}\n\n"
            f"Введите название города из списка выше.\n\n"
            f"Для рассылки ВСЕМ пользователям отправьте: **всем**\n\n"
            f"Для отмены рассылки отправьте /cancel_mailing",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await event.message.answer("❌ У вас нет доступа к этой команде.")


@router.message_created(MailingStates.waiting_for_city)
async def process_city_selection(event: MessageCreated, context: MemoryContext):
    """Обработка выбора города"""
    city_name = event.message.body.text.strip()

    if city_name.lower() == "/cancel_mailing":
        await cancel_mailing(event, context)
        return

    async with db_helper.scoped_session_dependency() as session:
        # Если выбрана рассылка всем
        if city_name.lower() == "всем":
            await context.update_data(selected_city="all", city_id=None)
            await context.set_state(MailingStates.waiting_for_text)
            await event.message.answer(
                "📢 **Выбрана рассылка ВСЕМ пользователям**\n\n"
                "Отправьте текст сообщения для рассылки.\n\n"
                "Для отмены рассылки отправьте /cancel_mailing",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Ищем выбранный город
        chats = await get_all_chats(session)
        selected_chat = None

        for chat in chats:
            if chat.name.lower() == city_name.lower():
                selected_chat = chat
                break

        if selected_chat:
            await context.update_data(selected_city=selected_chat.name, city_id=selected_chat.id)
            await context.set_state(MailingStates.waiting_for_text)
            await event.message.answer(
                f"🏙️ **Выбран город: {selected_chat.name}**\n\n"
                f"Отправьте текст сообщения для рассылки всем пользователям из этого города.\n\n"
                f"Для отмены рассылки отправьте /cancel_mailing",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Город не найден - показываем список снова
            chats = await get_all_chats(session)
            cities_list = "\n".join([f"• {chat.name}" for chat in chats])

            await event.message.answer(
                f"❌ Город '{city_name}' не найден.\n\n"
                f"Доступные города:\n{cities_list}\n\n"
                f"Введите название города из списка или 'всем' для рассылки всем пользователям.",
                parse_mode=ParseMode.MARKDOWN
            )


@router.message_created(Command('cancel_mailing'))
async def cancel_mailing(event: MessageCreated, context: MemoryContext):
    """Отмена рассылки"""
    current_state = await context.get_state()

    if current_state in [MailingStates.waiting_for_city, MailingStates.waiting_for_text]:
        await context.set_state(None)
        await context.clear()
        await event.message.answer("✅ Рассылка отменена.")
    else:
        await event.message.answer("❌ Активная рассылка не найдена.")


@router.message_created(MailingStates.waiting_for_text)
async def process_mailing_text(event: MessageCreated, context: MemoryContext):
    """Обработка текста рассылки и отправка"""
    await event.message.answer(
        "**Начинаю рассылку...**",
        parse_mode=ParseMode.MARKDOWN
    )

    # Получаем данные о выбранном городе
    data = await context.get_data()
    selected_city = data.get('selected_city')
    city_id = data.get('city_id')

    await context.set_state(None)

    # Получаем пользователей в зависимости от выбора города
    async with db_helper.scoped_session_dependency() as session:
        if selected_city == "all":
            users = await get_all_users(session)
            city_info = "ВСЕМ пользователям"
        else:
            users = await get_users_by_chat(session, city_id)
            city_info = f"городу {selected_city}"

    if not users:
        await event.message.answer(
            f"❌ Нет пользователей для рассылки {city_info}.",
            parse_mode=ParseMode.MARKDOWN
        )
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
            await asyncio.sleep(0.1)  # Защита от флуда
        except Exception:
            blocked_count += 1
            continue

    await event.message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"Целевая аудитория: {city_info}\n"
        f"Всего пользователей: {len(users)}\n"
        f"Сообщений отправлено: {success_count}\n"
        f"Не смогли доставить (заблокировали бота или ошибки): {blocked_count}",
        parse_mode=ParseMode.MARKDOWN
    )

    await context.clear()
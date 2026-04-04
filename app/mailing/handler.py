from maxapi import Router
from maxapi.types import MessageCreated, Command, InputMedia
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
    waiting_for_content = State()


def find_chat_by_name(chats, search_name: str):
    """
    Ищет чат/город по названию или сокращению.
    Поддерживает поиск по любому слову в строке name (разделенному пробелами).
    """
    search_name_lower = search_name.lower().strip()

    for chat in chats:
        # Разбиваем name на отдельные слова/варианты названий
        name_variants = chat.name.lower().split()

        # Проверяем, совпадает ли искомое слово с любым из вариантов
        if search_name_lower in name_variants:
            return chat

        # Также проверяем полное совпадение (на случай если название состоит из нескольких слов)
        if chat.name.lower() == search_name_lower:
            return chat

    return None


@router.message_created(Command('mailing'))
async def mailing_command(event: MessageCreated, context: MemoryContext):
    """Команда для начала рассылки — доступ только для админов"""
    user_id = event.message.sender.user_id

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

        # Формируем список городов (показываем только основные названия)
        cities_list = "\n".join([f"• {chat.name.split()[0]}" for chat in chats])

        await event.message.answer(
            f"🏙️ **Выберите город для рассылки**\n\n"
            f"Доступные города:\n{cities_list}\n\n"
            f"Введите название города или его сокращение из списка выше.\n\n"
            f"Например: 'Москва', 'МСК', 'СПБ', 'НСК', 'ЕКБ' и т.д.\n\n"
            f"Для рассылки ВСЕМ пользователям отправьте: **всем**\n\n"
            f"Для отмены рассылки отправьте /cancel_mailing",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await event.message.answer("❌ У вас нет доступа к этой команде.")


@router.message_created(MailingStates.waiting_for_city)
async def process_city_selection(event: MessageCreated, context: MemoryContext):
    """Обработка выбора города с поддержкой сокращений"""
    city_name = event.message.body.text.strip()

    if city_name.lower() == "/cancel_mailing":
        await cancel_mailing(event, context)
        return

    async with db_helper.scoped_session_dependency() as session:
        # Если выбрана рассылка всем
        if city_name.lower() == "всем":
            await context.update_data(selected_city="all", city_id=None)
            await context.set_state(MailingStates.waiting_for_content)
            await event.message.answer(
                "📢 **Выбрана рассылка ВСЕМ пользователям**\n\n"
                "Отправьте сообщение для рассылки.\n\n"
                "Поддерживаются: текст, фото, видео, документы, аудио.\n\n"
                "Для отмены рассылки отправьте /cancel_mailing",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Получаем все чаты и ищем по названию или сокращению
        chats = await get_all_chats(session)
        selected_chat = find_chat_by_name(chats, city_name)

        if selected_chat:
            await context.update_data(selected_city=selected_chat.name, city_id=selected_chat.id)
            await context.set_state(MailingStates.waiting_for_content)
            await event.message.answer(
                f"🏙️ **Выбран город: {selected_chat.name.split()[0]}**\n\n"
                f"Отправьте сообщение для рассылки всем пользователям из этого города.\n\n"
                f"Поддерживаются: текст, фото, видео, документы, аудио.\n\n"
                f"Для отмены рассылки отправьте /cancel_mailing",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Город не найден - показываем список снова
            cities_list = "\n".join([f"• {chat.name.split()[0]}" for chat in chats])

            await event.message.answer(
                f"❌ Город или сокращение '{city_name}' не найдены.\n\n"
                f"Доступные города и их сокращения:\n{cities_list}\n\n"
                f"Примеры ввода: 'Москва', 'МСК', 'Санкт-Петербург', 'СПБ', 'Новосибирск', 'НСК'\n\n"
                f"Или отправьте 'всем' для рассылки всем пользователям.",
                parse_mode=ParseMode.MARKDOWN
            )


@router.message_created(Command('cancel_mailing'))
async def cancel_mailing(event: MessageCreated, context: MemoryContext):
    """Отмена рассылки"""
    current_state = await context.get_state()

    if current_state in [MailingStates.waiting_for_city, MailingStates.waiting_for_content]:
        await context.set_state(None)
        await context.clear()
        await event.message.answer("✅ Рассылка отменена.")
    else:
        await event.message.answer("❌ Активная рассылка не найдена.")


@router.message_created(MailingStates.waiting_for_content)
async def process_mailing_content(event: MessageCreated, context: MemoryContext):
    """Обработка контента рассылки (текст, фото, видео и т.д.)"""
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
            city_info = f"городу {selected_city.split()[0]}"

    if not users:
        await event.message.answer(
            f"❌ Нет пользователей для рассылки {city_info}.",
            parse_mode=ParseMode.MARKDOWN
        )
        await context.clear()
        return

    success_count = 0
    blocked_count = 0

    # Сохраняем оригинальное сообщение для рассылки
    mailing_message = event.message

    # Предварительно загружаем медиа (если есть)
    uploaded_attachment = None
    if mailing_message.body.attachments:
        try:
            uploaded_attachment = await bot.upload_media(mailing_message.body.attachments[0])
        except Exception as e:
            await event.message.answer(
                f"❌ Ошибка при загрузке медиафайла: {e}",
                parse_mode=ParseMode.MARKDOWN
            )
            await context.clear()
            return

    for user in users:
        try:
            if uploaded_attachment:
                # Отправляем с предварительно загруженным вложением
                text = mailing_message.body.text if mailing_message.body.text else None
                await bot.send_message(
                    user_id=user.max_id,
                    text=text,
                    attachments=[uploaded_attachment],
                    parse_mode=ParseMode.HTML if text else None
                )
            elif mailing_message.body.text:
                # Отправляем только текст
                await bot.send_message(
                    user_id=user.max_id,
                    text=mailing_message.body.text,
                    parse_mode=ParseMode.HTML
                )
            else:
                raise Exception("No content to send")

            success_count += 1
            await asyncio.sleep(0.1)  # Защита от флуда
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user.max_id}: {e}")
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
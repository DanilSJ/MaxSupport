from maxapi import Router
from maxapi.types import MessageCreated, Command, BotStarted, MessageCallback
from maxapi.context import MemoryContext, StatesGroup, State
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton
from core.config import bot
from core.models import db_helper
from .crud import create_user, get_chat_by_name

router = Router()


class UserStates(StatesGroup):
    waiting_for_city = State()


# Список округов Москвы и городов Подмосковья
MOSCOW_DISTRICTS = [
    "Москва ВАО",
    "Москва ЗАО",
    "Москва НАО",
    "Москва САО",
    "Москва СВАО",
    "Москва СЗАО",
    "Москва ЦАО",
    "Москва ЮАО",
    "Москва ЮВАО",
    "Москва ЮЗАО",
    "Балашиха",
    "Богородск",
    "Домодедово",
    "Зеленоград",
    "Королев",
    "Красногорск",
    "Ленино",
    "Люберцы",
    "Мытищи",
    "Одинцово",
    "Орехово-Зуево",
    "Подольск",
    "Пушкино",
    "Раменское",
    "Сергиев Посад",
    "Химки",
    "Щелково",
    "Другой",
]

# Список районов Санкт-Петербурга
SPB_DISTRICTS = [
    "СПБ Адмиралтейский",
    "СПБ Василеостровский",
    "СПБ Выборгский",
    "СПБ Калининский",
    "СПБ Колпинский",
    "СПБ Красногвардейский",
    "СПБ Красносельский",
    "СПБ Курортный",
    "СПБ Московский",
    "СПБ Мурино",
    "СПБ Невский",
    "СПБ Петродворцовый",
    "СПБ Петроградский",
    "СПБ Приморский",
    "СПБ Пушкинский",
    "СПБ Фрунзенский",
    "СПБ Центральный",
    "Другой",
]


def create_moscow_keyboard():
    """Создает клавиатуру с округами Москвы и городами Подмосковья"""
    builder = InlineKeyboardBuilder()

    # Добавляем все города/округа Москвы
    for city in MOSCOW_DISTRICTS:
        builder.row(CallbackButton(
            text=city,
            payload=f"moscow_{city}"
        ))

    return builder.as_markup()


def create_spb_keyboard():
    """Создает клавиатуру с районами Санкт-Петербурга"""
    builder = InlineKeyboardBuilder()

    # Добавляем все районы СПБ
    for district in SPB_DISTRICTS:
        builder.row(CallbackButton(
            text=district,
            payload=f"spb_{district}"
        ))

    # Добавляем кнопку "Другое"
    builder.row(CallbackButton(
        text="📍 Другое",
        payload="other_city"
    ))

    return builder.as_markup()


@router.bot_started()
async def bot_started(event: BotStarted, context: MemoryContext):
    async with db_helper.scoped_session_dependency() as session:
        await create_user(session, event.from_user.user_id)

    await bot.send_message(
        chat_id=event.chat_id,
        text="""Здравствуйте 🖐

Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ В каком городе находится Ваше заведение?

Просто напишите город текстом."""
    )

    await context.set_state(UserStates.waiting_for_city)


# команда /start
@router.message_created(Command('start'))
async def start(event: MessageCreated, context: MemoryContext):
    async with db_helper.scoped_session_dependency() as session:
        await create_user(session, event.from_user.user_id)

    await event.message.answer(
        "Приветствую 🖐\n\nПожалуйста, напишите город, где нужно разместить рекламу:"
    )
    await context.set_state(UserStates.waiting_for_city)


@router.message_callback()
async def handle_city_callback(callback: MessageCallback, context: MemoryContext):
    """Обрабатывает нажатие на кнопки с городами"""
    payload = callback.callback.payload

    if not payload:
        await callback.answer()
        return

    if payload == "other_city":
        await callback.message.answer("Пожалуйста, напишите название вашего города:")
        await callback.answer()
        return

    city_name = None
    if payload.startswith("moscow_"):
        city_name = payload[7:]  # убираем префикс "moscow_"
    elif payload.startswith("spb_"):
        city_name = payload[4:]  # убираем префикс "spb_"

    if city_name:
        async with db_helper.scoped_session_dependency() as session:
            # Ищем чат по названию города/округа
            chat = await get_chat_by_name(session, city_name)

            if not chat:
                await callback.message.answer(
                    f"Извините, '{city_name}' не найден в базе. Пожалуйста, напишите город текстом."
                )
                await callback.answer()
                return

            await create_user(session, callback.from_user.user_id, chat_id=chat.chat_id)

        await context.set_state(None)
        await context.clear()

        await callback.message.answer("""Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?"""
                                      )
        await callback.answer(f"Выбран город: {city_name}")


@router.message_created(UserStates.waiting_for_city)
async def handle_message(event: MessageCreated, context: MemoryContext):
    state = await context.get_state()
    text = getattr(event.message.body, "text", "").strip()
    if not text:
        return

    if state == UserStates.waiting_for_city:
        text_lower = text.lower()

        # Проверяем на Москву
        if text_lower == "москва" or text_lower == "мск" or text_lower == "москв":
            await event.message.answer(
                "Выберите округ Москвы или город:",
                attachments=[create_moscow_keyboard()]
            )
            return

        # Проверяем на Санкт-Петербург
        if (text_lower == "санкт-петербург" or
                text_lower == "спб" or
                text_lower == "питер" or
                text_lower == "санкт петербург" or
                text_lower.startswith("петерб")):
            await event.message.answer(
                "Выберите район Санкт-Петербурга:",
                attachments=[create_spb_keyboard()]
            )
            return

        # Если не Москва и не СПБ - ищем в базе как обычно
        async with db_helper.scoped_session_dependency() as session:
            chat = await get_chat_by_name(session, text)

            if not chat:
                return await event.message.answer(
                    f"Город '{text}' не найден в базе. Попробуйте еще раз."
                )

            await create_user(session, event.from_user.user_id, chat_id=chat.chat_id)

        await context.set_state(None)
        await context.clear()
        return await event.message.answer("""Чтобы получить актуальные расценки на рекламу, ответьте пожалуйста на пару вопросов:
1️⃣ Что планируете рекламировать?
2️⃣ Где находится Ваше заведение (либо по какому адресу предоставляете услугу)?"""
                                          )
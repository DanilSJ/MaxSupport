from maxapi.types import MessageCreated
from maxapi.context import MemoryContext
from collections import defaultdict
import time

user_messages = defaultdict(list)


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

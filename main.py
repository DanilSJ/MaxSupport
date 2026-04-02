import asyncio
import logging
from maxapi import Dispatcher
from core.config import bot
from app.start.handler import router as start_router


logging.basicConfig(level=logging.INFO)
dp = Dispatcher()

async def main():
    dp.include_routers(start_router)

    await asyncio.gather(
        dp.start_polling(bot)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
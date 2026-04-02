from maxapi import Router
from maxapi.types import MessageCreated, Command

router = Router()

@router.message_created(Command('start'))
async def start(event: MessageCreated):
    await event.message.answer("Привет")

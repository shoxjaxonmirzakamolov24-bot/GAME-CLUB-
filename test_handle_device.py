import asyncio
from unittest.mock import MagicMock
from telegram import Update, CallbackQuery, Message
from telegram.ext import ContextTypes
import database
from handlers.booking import handle_device

async def test():
    await database.init_db()
    
    update = MagicMock(spec=Update)
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.data = "device_1"
    
    # We need to mock edit_message_text as an async function
    async def mock_edit_message_text(*args, **kwargs):
        print("edit_message_text called with:", args, kwargs)
    update.callback_query.edit_message_text = mock_edit_message_text
    
    async def mock_answer(*args, **kwargs):
        pass
    update.callback_query.answer = mock_answer

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {'selected_day': 'today'}

    try:
        result = await handle_device(update, context)
        print("Success! Next state:", result)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

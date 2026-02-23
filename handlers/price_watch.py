# handlers/price_watch.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from handlers.volatility import get_current_prices
from ui_utils import create_price_table

router = Router()

@router.message(F.text == "📈 Курсы валют")
async def show_prices(message: Message, state: FSMContext):
    """Показывает текущие курсы валют"""
    await state.clear()
    
    prices = get_current_prices()
    
    # Используем функцию из ui_utils
    text = create_price_table(prices)
    
    await message.answer(text)

@router.message(F.text == "◀ Назад в меню")
async def back_to_main(message: Message):
    from keyboards import main_menu
    await message.answer("Главное меню:", reply_markup=main_menu())
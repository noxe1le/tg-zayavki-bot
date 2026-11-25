import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import main_menu

log = logging.getLogger(__name__)
router = Router(name="common")

HELLO = (
    "Здравствуйте, {name}!\n\n"
    "Здесь можно оставить заявку — отвечу и уточню детали. "
    "Занимает минуту: имя, телефон и пара слов о задаче."
)

HELP = (
    "Как это работает:\n"
    "1. Нажмите «Оставить заявку»\n"
    "2. Ответьте на три вопроса\n"
    "3. Заявка уйдёт мне, я свяжусь с вами\n\n"
    "Свои заявки можно посмотреть в разделе «Мои заявки»."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        HELLO.format(name=message.from_user.first_name if message.from_user else "друг"),
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP)


@router.callback_query(F.data == "menu:main")
async def back_to_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if call.message:
        await call.message.edit_text("Главное меню", reply_markup=main_menu())
    await call.answer()

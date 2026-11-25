import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.db.repository import RequestRepository
from app.keyboards.inline import cancel_only, main_menu, requests_page
from app.validators import clean_comment, clean_name, normalize_phone

log = logging.getLogger(__name__)
router = Router(name="requests")

PAGE_SIZE = 5


class RequestForm(StatesGroup):
    name = State()
    phone = State()
    comment = State()


@router.callback_query(F.data == "request:new")
async def start_form(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RequestForm.name)
    if call.message:
        await call.message.edit_text("Как вас зовут?", reply_markup=cancel_only())
    await call.answer()


@router.message(RequestForm.name)
async def form_name(message: Message, state: FSMContext) -> None:
    name = clean_name(message.text or "")
    if name is None:
        await message.answer("Имя должно быть от 2 до 40 символов и без цифр")
        return
    await state.update_data(name=name)
    await state.set_state(RequestForm.phone)
    await message.answer("Телефон для связи? Например +7 900 123-45-67", reply_markup=cancel_only())


@router.message(RequestForm.phone)
async def form_phone(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text or "")
    if phone is None:
        await message.answer("Не похоже на номер. Попробуйте в формате +7 900 123-45-67")
        return
    await state.update_data(phone=phone)
    await state.set_state(RequestForm.comment)
    await message.answer(
        "Что нужно сделать? Опишите в двух-трёх предложениях",
        reply_markup=cancel_only(),
    )


@router.message(RequestForm.comment)
async def form_comment(
    message: Message,
    state: FSMContext,
    repo: RequestRepository,
    bot: Bot,
    settings: Settings,
) -> None:
    comment = clean_comment(message.text or "")
    if comment is None:
        await message.answer("Слишком коротко — напишите хотя бы одно предложение")
        return

    data = await state.get_data()
    request = await repo.add(
        user_id=message.from_user.id,
        username=message.from_user.username,
        name=data["name"],
        phone=data["phone"],
        comment=comment,
    )
    await state.clear()
    await message.answer(
        f"Заявка №{request.id} принята. Свяжусь с вами в ближайшее время.",
        reply_markup=main_menu(),
    )
    await _notify_admin(bot, settings, request)


async def _notify_admin(bot: Bot, settings: Settings, request) -> None:
    if not settings.admin_id:
        return
    try:
        await bot.send_message(
            settings.admin_id,
            f"<b>Новая заявка №{request.id}</b>\n"
            f"Имя: {request.name}\n"
            f"Телефон: {request.phone}\n"
            f"Задача: {request.comment}\n"
            f"От: @{request.username or request.user_id}",
        )
    except Exception:
        # админ мог заблокировать бота; заявка уже в базе, терять её нельзя
        log.exception("не удалось отправить уведомление админу по заявке %s", request.id)


@router.callback_query(F.data.startswith("request:list:"))
async def list_requests(call: CallbackQuery, repo: RequestRepository) -> None:
    page = int(call.data.rsplit(":", 1)[-1])
    items = await repo.by_user(call.from_user.id, limit=PAGE_SIZE + 1, offset=page * PAGE_SIZE)
    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]

    if not items and page == 0:
        if call.message:
            await call.message.edit_text("Заявок пока нет", reply_markup=main_menu())
        await call.answer()
        return

    blocks = [
        f"№{item.id} · {item.created_at:%d.%m %H:%M}\n"
        f"{item.name}, {item.phone}\n{item.short_comment}"
        for item in items
    ]
    if call.message:
        await call.message.edit_text(
            "Ваши заявки:\n\n" + "\n\n".join(blocks),
            reply_markup=requests_page(page, has_next),
        )
    await call.answer()

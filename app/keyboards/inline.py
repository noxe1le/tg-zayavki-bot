from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оставить заявку", callback_data="request:new")],
            [InlineKeyboardButton(text="Мои заявки", callback_data="request:list:0")],
        ]
    )


def cancel_only() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="menu:main")]]
    )


def requests_page(page: int, has_next: bool) -> InlineKeyboardMarkup:
    row: list[InlineKeyboardButton] = []
    if page > 0:
        row.append(InlineKeyboardButton(text="← Назад", callback_data=f"request:list:{page - 1}"))
    if has_next:
        row.append(InlineKeyboardButton(text="Ещё →", callback_data=f"request:list:{page + 1}"))
    buttons = [row] if row else []
    buttons.append([InlineKeyboardButton(text="В меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

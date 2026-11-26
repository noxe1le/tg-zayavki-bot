"""Рисует превью экранов бота для README.

Тексты и клавиатуры берутся не из головы: скрипт прогоняет настоящие хендлеры
с заглушками Telegram-объектов и рисует то, что они реально вернули.
Запуск: python scripts/make_screens.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.handlers import common  # noqa: E402
from app.handlers import requests as req_handlers  # noqa: E402
from app.models import Request  # noqa: E402

W = 900
PAD = 28
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG = "#0E1621"
HEADER = "#17212B"
BOT_BUBBLE = "#182533"
USER_BUBBLE = "#2B5278"
TEXT = "#FFFFFF"
MUTED = "#7D8E98"
BTN = "#1C4A6E"

LINE_H = 31
PAD_IN = 18


class FakeState:
    def __init__(self) -> None:
        self.data: dict = {}
        self.state: str | None = None

    async def set_state(self, state) -> None:
        self.state = state

    async def update_data(self, **kwargs) -> None:
        self.data.update(kwargs)

    async def get_data(self) -> dict:
        return dict(self.data)

    async def clear(self) -> None:
        self.data.clear()
        self.state = None


class FakeBot:
    async def send_message(self, chat_id, text, **kwargs) -> None:
        log.append(("bot", text, []))


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.from_user = SimpleNamespace(id=1, username="ivan", first_name="Иван")
        self.bot = FakeBot()

    async def answer(self, text: str, reply_markup=None, **kwargs) -> None:
        log.append(("bot", text, rows(reply_markup)))


class FakeCallMessage:
    async def edit_text(self, text: str, reply_markup=None, **kwargs) -> None:
        log.append(("bot", text, rows(reply_markup)))


class FakeCall:
    def __init__(self, data: str) -> None:
        self.data = data
        self.from_user = SimpleNamespace(id=1, username="ivan", first_name="Иван")
        self.message = FakeCallMessage()

    async def answer(self, *args, **kwargs) -> None:
        pass


class FakeRepo:
    def __init__(self) -> None:
        self.items: list[Request] = []

    async def add(self, **kwargs) -> Request:
        item = Request(id=len(self.items) + 1, created_at=datetime(2026, 11, 25, 21, 14), **kwargs)
        self.items.insert(0, item)
        return item

    async def by_user(self, user_id, *, limit=5, offset=0) -> list[Request]:
        return self.items[offset : offset + limit + 1]


def rows(reply_markup) -> list[list[str]]:
    if reply_markup is None:
        return []
    return [[b.text for b in row] for row in reply_markup.inline_keyboard]


log: list[tuple[str, str, list[list[str]]]] = []


def wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for word in paragraph.split(" "):
            probe = f"{line} {word}".strip()
            if draw.textlength(probe, font=font) <= width:
                line = probe
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def layout(draw, messages, font):
    """Считает раскладку заранее: высота картинки зависит от длины сообщений."""
    max_w = int(W * 0.66)
    blocks = []
    y = 128
    for who, text, kb in messages:
        lines = wrap(draw, text, font, max_w)
        bh = len(lines) * LINE_H + 2 * PAD_IN
        bw = max(draw.textlength(line, font=font) for line in lines) + 2 * PAD_IN
        blocks.append((who, lines, min(bw, max_w + 2 * PAD_IN), bh, y, kb))
        y += bh + 12
        if kb:
            y += 74 * len(kb) + 8
        y += 10
    return blocks, y + 40


def draw_screen(messages, path: Path) -> None:
    probe = Image.new("RGB", (W, 10))
    pdraw = ImageDraw.Draw(probe)
    font = ImageFont.truetype(FONT, 26)
    font_small = ImageFont.truetype(FONT, 21)
    font_bold = ImageFont.truetype(FONT_BOLD, 27)

    blocks, height = layout(pdraw, messages, font)
    img = Image.new("RGB", (W, height), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 96], fill=HEADER)
    draw.text((PAD, 26), "Заявки", font=font_bold, fill=TEXT)
    draw.text((PAD, 62), "бот", font=font_small, fill=MUTED)

    for who, lines, bw, bh, y, kb in blocks:
        x = W - PAD - bw if who == "user" else PAD
        draw.rounded_rectangle(
            [x, y, x + bw, y + bh], radius=18, fill=USER_BUBBLE if who == "user" else BOT_BUBBLE
        )
        ty = y + PAD_IN
        for line in lines:
            draw.text((x + PAD_IN, ty), line, font=font, fill=TEXT)
            ty += LINE_H

        if kb:
            kx, ky = PAD, y + bh + 12
            kb_w = W - 2 * PAD
            for row in kb:
                btn_w = (kb_w - 12 * (len(row) - 1)) // max(len(row), 1)
                for i, label in enumerate(row):
                    bx = kx + i * (btn_w + 12)
                    draw.rounded_rectangle([bx, ky, bx + btn_w, ky + 62], radius=12, fill=BTN)
                    tw = draw.textlength(label, font=font_small)
                    draw.text((bx + (btn_w - tw) / 2, ky + 18), label, font=font_small, fill=TEXT)
                ky += 74

    img.save(path)
    print("сохранено:", path, img.size)


async def build() -> None:
    state = FakeState()
    repo = FakeRepo()
    settings = Settings(BOT_TOKEN="0:x", ADMIN_ID=None)

    await common.cmd_start(FakeMessage("/start"), state)
    menu_screen = [("user", "/start", []), *log]
    log.clear()

    await req_handlers.start_form(FakeCall("request:new"), state)
    name_q = list(log)
    log.clear()
    await req_handlers.form_name(FakeMessage("Иван Петров"), state)
    phone_q = list(log)
    log.clear()
    await req_handlers.form_phone(FakeMessage("8 900 123-45-67"), state)
    comment_q = list(log)
    log.clear()

    await req_handlers.form_comment(
        FakeMessage("Нужен парсер цен с сайта конкурентов, выгрузка в Excel раз в день"),
        state,
        repo,
        FakeBot(),
        settings,
    )
    done = list(log)
    log.clear()

    form_screen = [
        name_q[0],
        ("user", "Иван Петров", []),
        phone_q[0],
        ("user", "8 900 123-45-67", []),
        comment_q[0],
    ]
    done_screen = [
        ("user", "Нужен парсер цен с сайта конкурентов, выгрузка в Excel раз в день", []),
        done[0],
    ]

    await req_handlers.list_requests(FakeCall("request:list:0"), repo)
    list_screen = list(log)

    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    draw_screen(menu_screen, out / "screen-menu.png")
    draw_screen(form_screen, out / "screen-form.png")
    draw_screen(done_screen, out / "screen-done.png")
    draw_screen(list_screen, out / "screen-list.png")


if __name__ == "__main__":
    asyncio.run(build())

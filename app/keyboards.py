from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_start_kb() -> InlineKeyboardMarkup:
    """Return inline keyboard with greeting button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="получить поздравление", callback_data="get_greeting"
                )
            ]
        ]
    )



import argparse
from telegram_ui.bot import TelegramBotUI

from faceverification.verification import get_default_face_verificator


def main(telegram_bot_token: str):
    verificator = get_default_face_verificator()
    tg_bot = TelegramBotUI(telegram_bot_token, verificator)
    tg_bot.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="Telegram bot token from @BotFather")
    args = parser.parse_args()
    main(args.token)

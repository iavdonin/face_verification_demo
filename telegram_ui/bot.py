""" Telegram bot server """

from enum import Enum

from telegram import Update
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
)
from faceverification.verification import FaceVerificator
from faceverification.exceptions import (
    FaceNotFoundError,
    MultipleFacesError,
    PresentationAttackError,
)

from .log import get_logger

logger = get_logger(__name__)


class STATE(Enum):
    """Conversation states"""

    START = 0
    WAITING_NAME = 1
    WAITING_ID = 2
    WAITING_SELFIE = 3


class TelegramBotUI:
    """
    Telegram bot user interface implementation for face recognition system

    Args:
        token: telegram bot token.
        verificator: face verification model.
    """

    def __init__(self, token: str, verificator: FaceVerificator) -> None:
        self.token = token
        self.verificator = verificator

        self._updater = None
        self._conversation_handler = None
        self._file_cache = {}  # stores sended by user id image for verification

    def _start(self, update: Update, context: CallbackContext) -> STATE:
        hello_msg = f"Добрый день, {update.message.from_user['first_name']}!"
        descroption_msg = (
            "Этот бот эмулирует прохождение цифрового онбординга с использованием верификации "
            "пользователя по лицу."
            "Суть в том, чтобы пройти проверку личности с помощью документа, удостоверяющего "
            "личность и фотографии лица (селфи)."
        )
        request_name_msg = "Для начала прошу прислать мне ваше ФИО"
        update.message.reply_text(hello_msg)
        update.message.reply_text(descroption_msg)
        update.message.reply_text(request_name_msg)
        return STATE.WAITING_NAME

    def _request_id_doc(self, update: Update, context: CallbackContext) -> STATE:
        name = update.message.text
        name_response_msg = f"{name}, понятно, записал."
        id_desc_msg = (
            "Для верификации мне требуется фотография твоего документа, удостоверящиего личность. "
            "Таким документом могут быть: паспорт, водительские права или другой, обязвтельно "
            "содержащий фотографию лица.\n"
            "Требования к документу следующие:\n"
            "1. Документ должен быть полностью в кадре\n"
            "2. Фото лица должно быть четко видно\n"
            "3. Фото документа должно быть сделано при хорошем освещении, но не должно содержать "
            "бликов\n"
        )
        id_request_msg = "Пришли мне фото документа ответным сообщением"
        update.message.reply_text(name_response_msg)
        update.message.reply_text(id_desc_msg)
        update.message.reply_text(id_request_msg)
        return STATE.WAITING_ID

    def _get_id_and_request_selfie(
        self, update: Update, context: CallbackContext
    ) -> STATE:
        photos = update.message.photo
        photo = photos[-1].get_file().download_as_bytearray()
        self._file_cache[update.effective_user.id] = {}
        self._file_cache[update.effective_user.id]["id_photo"] = photo
        selfie_request_msg = (
            "Получено! А теперь отправь мне твою фотографию (селфи). Требования "
            "примерно такие же:\n"
            "1. Хорошее освещение\n"
            "2. Лицо по центру изображения и хорошо видно\n"
            "3. Только одно лицо на изображении"
        )
        update.message.reply_text(selfie_request_msg)
        return STATE.WAITING_SELFIE

    def _get_selfice_and_verify(
        self, update: Update, context: CallbackContext
    ) -> STATE:
        photos = update.message.photo
        selfie_photo = photos[-1].get_file().download_as_bytearray()
        id_photo = self._file_cache.pop(update.effective_user.id)["id_photo"]

        err_msg = None
        try:
            is_verified, _ = self.verificator.verify(id_photo, selfie_photo)
        except FaceNotFoundError:
            err_msg = (
                "Верификация не пройдена, т.к. не найдено лицо на изображении. "
                "Проверьте изображения или попробуйте переснять фотографию."
            )
        except MultipleFacesError:
            err_msg = (
                "Верификация не пройдена, т.к. найдено несколько лиц на изображении. "
                "Проверьте изображения или попробуйте переснять фотографию."
            )
        except PresentationAttackError:
            err_msg = "Верификация не пройдена (обнаружена атака представления)"

        if is_verified:
            update.message.reply_text(
                "Верификация пройдена успешно! Конец сценария. "
                "Введи /start для перезапуска бота."
            )
            context.user_data.clear()
            return ConversationHandler.END
        else:
            if err_msg:
                update.message.reply_text(err_msg)
            else:
                update.message.reply_text(
                    "Верификация не пройдена. Попробуйте еще раз."
                )
            update.message.reply_text(
                "Пришлите заново фотографию документа, " "удостоверяющего личность"
            )
            return STATE.WAITING_ID

    def run(self) -> None:
        """Starts the telegram server (bot)"""
        if self._updater is not None:
            logger.critical(
                "Trying to run telegram server while it is already running!"
            )
            raise RuntimeError("Application is already running!")
        self._updater = Updater(self.token)
        dispatcher = self._updater.dispatcher
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self._start)],
            states={
                STATE.WAITING_NAME: [
                    MessageHandler(Filters.text, self._request_id_doc)
                ],
                STATE.WAITING_ID: [
                    MessageHandler(Filters.photo, self._get_id_and_request_selfie)
                ],
                STATE.WAITING_SELFIE: [
                    MessageHandler(Filters.photo, self._get_selfice_and_verify)
                ],
            },
            fallbacks=[],
        )
        dispatcher.add_handler(conv_handler)
        self._updater.start_polling()
        self._updater.idle()

from electroncash.keyserver import plain_text_metadata
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from electroncash.i18n import _
from .util import *

def telegram_executor(handle: str):
    QDesktopServices.openUrl(QUrl("https://t.me/" + handle))


class KeyserverForm:
    def is_full(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def _get_data(self):
        raise NotImplementedError

    def _construct_metadata(self, addr: str, data, signer, ttl: int):
        raise NotImplementedError

    def _get_ttl(self):
        raise NotImplementedError

    def set_signer(self, signer):
        self.signer = signer

    def get_metadata(self, addr):
        data = self._get_data()
        metadata = self._construct_metadata(addr, data, self.signer, ttl=self._get_ttl())
        return metadata


class PlainTextForm(QWidget, KeyserverForm):
    def __init__(self, on_text_changed, *args, **kwargs):
        super(PlainTextForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Plain text to be uploaded.')
        description_label = HelpLabel(_('&Text'), msg)
        plain_text_grid.addWidget(description_label, 3, 0)
        self.upload_plain_text_e = QTextEdit()
        self.upload_plain_text_e.textChanged.connect(on_text_changed)
        description_label.setBuddy(self.upload_plain_text_e)
        plain_text_grid.addWidget(self.upload_plain_text_e, 3, 1, 1, -1)
        self.setLayout(plain_text_grid)

    def is_full(self):
        return bool(self.upload_plain_text_e.toPlainText())

    def clear(self):
        self.upload_plain_text_e.clear()

    def _get_ttl(self):
        return 60*60

    def _get_data(self):
        return self.upload_plain_text_e.toPlainText()

    def _construct_metadata(self, addr, data, signer, ttl):
        return plain_text_metadata(addr, data, signer, ttl)


class TelegramForm(QWidget, KeyserverForm):
    def __init__(self, on_text_changed, *args, **kwargs):
        super(TelegramForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Telegram handle to be uploaded.')
        description_label = HelpLabel(_('&Handle'), msg)
        plain_text_grid.addWidget(description_label, 3, 0)
        self.upload_telegram_e = QLineEdit()
        self.upload_telegram_e.textChanged.connect(on_text_changed)
        description_label.setBuddy(self.upload_telegram_e)
        plain_text_grid.addWidget(self.upload_telegram_e, 3, 1, 1, -1)
        self.setLayout(plain_text_grid)

    def is_full(self):
        return bool(self.upload_telegram_e.text())

    def clear(self):
        self.upload_telegram_e.clear()

    def _get_ttl(self):
        return 60*60

    def _get_data(self):
        return self.upload_telegram_e.text()

    def _construct_metadata(self, addr, data, signer, ttl):
        return plain_text_metadata(addr, data, signer, ttl, type_override="telegram")


# TODO
class StealthAddressForm(QWidget, KeyserverForm):
    def __init__(self, on_text_changed, *args, **kwargs):
        super(StealthAddressForm, self).__init__(*args, **kwargs)

    def is_full(self):
        return bool(self.upload_telegram_e.text())

    def clear(self):
        pass

    def _get_data(self):
        return None

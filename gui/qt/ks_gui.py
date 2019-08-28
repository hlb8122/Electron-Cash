from electroncash.keyserver.tools import *
from electroncash.i18n import _

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from .util import *


def telegram_executor(handle: str):
    QDesktopServices.openUrl(QUrl("https://t.me/" + handle))


class KeyserverForm(QWidget):
    def is_full(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def construct_entry(self, addr):
        raise NotImplementedError


class PlainTextForm(KeyserverForm):
    def __init__(self, *args, **kwargs):
        super(PlainTextForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Plain text to be uploaded.')
        description_label = HelpLabel(_('&Text'), msg)
        plain_text_grid.addWidget(description_label, 3, 0)
        self.upload_plain_text_e = QTextEdit()
        description_label.setBuddy(self.upload_plain_text_e)
        plain_text_grid.addWidget(self.upload_plain_text_e, 3, 1, 1, -1)
        self.setLayout(plain_text_grid)

    def is_full(self):
        return bool(self.upload_plain_text_e.toPlainText())

    def clear(self):
        self.upload_plain_text_e.clear()

    def construct_entry(self):
        data = self.upload_plain_text_e.toPlainText()
        return plain_text_entry(data)


class TelegramForm(KeyserverForm):
    def __init__(self, *args, **kwargs):
        super(TelegramForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Telegram handle to be uploaded.')
        description_label = HelpLabel(_('&Handle'), msg)
        plain_text_grid.addWidget(description_label, 3, 0)
        self.upload_telegram_e = QLineEdit()
        description_label.setBuddy(self.upload_telegram_e)
        plain_text_grid.addWidget(self.upload_telegram_e, 3, 1, 1, -1)
        self.setLayout(plain_text_grid)

    def is_full(self):
        return bool(self.upload_telegram_e.text())

    def clear(self):
        self.upload_telegram_e.clear()

    def construct_entry(self):
        text = self.upload_telegram_e.text()
        return telegram_entry(text)


class KeyserverURLForm(KeyserverForm):
    def __init__(self, *args, **kwargs):
        super(KeyserverURLForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Keyserver list to be uploaded. Line delimited.')
        description_label = HelpLabel(_('&Servers'), msg)
        plain_text_grid.addWidget(description_label, 3, 0)
        self.upload_ks_urls_e = QTextEdit()
        description_label.setBuddy(self.upload_ks_urls_e)
        plain_text_grid.addWidget(self.upload_ks_urls_e, 3, 1, 1, -1)
        self.setLayout(plain_text_grid)

    def is_full(self):
        return bool(self.upload_ks_urls_e.toPlainText())

    def clear(self):
        self.upload_ks_urls_e.clear()

    def construct_entry(self):
        urls = self.upload_ks_urls_e.toPlainText().split("\n")
        return ks_urls_entry(urls)


# TODO
class StealthAddressForm(KeyserverForm):
    def __init__(self, *args, **kwargs):
        super(StealthAddressForm, self).__init__(*args, **kwargs)

    def is_full(self):
        return bool(self.upload_telegram_e.text())

    def clear(self):
        pass

    def _get_data(self):
        return None


class VCardForm(KeyserverForm):
    def __init__(self, *args, **kwargs):
        super(VCardForm, self).__init__(*args, **kwargs)
        vcard_grid = QGridLayout()

        msg = _('Name of contact.')
        description_label = HelpLabel(_('&Name'), msg)
        vcard_grid.addWidget(description_label, 0, 0)
        self.upload_vName_e = QLineEdit()
        description_label.setBuddy(self.upload_vName_e)
        vcard_grid.addWidget(self.upload_vName_e, 0, 1, 1, -1)

        msg = _('Mobile number of contact.')
        description_label = HelpLabel(_('&Mobile'), msg)
        vcard_grid.addWidget(description_label, 1, 0)
        self.upload_vMobile_e = QLineEdit()
        description_label.setBuddy(self.upload_vMobile_e)
        vcard_grid.addWidget(self.upload_vMobile_e, 1, 1, 1, -1)

        msg = _('Email of contact.')
        description_label = HelpLabel(_('&Email'), msg)
        vcard_grid.addWidget(description_label, 2, 0)
        self.upload_vEmail_e = QLineEdit()
        description_label.setBuddy(self.upload_vEmail_e)
        vcard_grid.addWidget(self.upload_vEmail_e, 2, 1, 1, -1)

        self.setLayout(vcard_grid)

    def is_full(self):
        # Name is required
        return bool(self.upload_vName_e.text())

    def clear(self):
        self.upload_vName_e.clear()
        self.upload_vMobile_e.clear()
        self.upload_vEmail_e.clear()

    def construct_entry(self):
        card = {
            "name": self.upload_vName_e.text(),
            "mobile": self.upload_vMobile_e.text(),
            "email": self.upload_vEmail_e.text()
        }
        return vcard_entry(card)


class TabBar(QTabBar):
    def tabSizeHint(self, index):
        s = QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class TabWidget(QTabWidget):
    def __init__(self, *args, **kwargs):
        QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(TabBar(self))
        self.setTabPosition(QTabWidget.West)

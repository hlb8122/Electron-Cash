from PyQt5.QtWidgets import *
from ..util import *
from electroncash.i18n import _
from electroncash.keyserver.metadata_tools import *
from electroncash.keyserver.handler import Extracted

def construct_download_forms(extracted):
    return [OverviewForm(extracted)]


class OverviewForm(QWidget):
    def __init__(self, extracted: Extracted, *args, **kwargs):
        from datetime import datetime
        super(OverviewForm, self).__init__(*args, **kwargs)
        overview_grid = QGridLayout()

        msg = _('URL the metadata was sourced from.')
        description_label = HelpLabel(_('&Source URL'), msg)
        overview_grid.addWidget(description_label, 0, 0)
        self.source_url_text_e = QLineEdit()
        self.source_url_text_e.setReadOnly(True)
        self.source_url_text_e.setText(extracted.url)
        description_label.setBuddy(self.source_url_text_e)
        overview_grid.addWidget(self.source_url_text_e, 0, 1, 1, -1)

        msg = _('Timestamp the metadata was uploaded.')
        description_label = HelpLabel(_('&Timestamp'), msg)
        overview_grid.addWidget(description_label, 1, 0)
        self.dt_text_e = QLineEdit()
        self.dt_text_e.setReadOnly(True)
        dt = datetime.utcfromtimestamp(extracted.metadata.payload.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        self.dt_text_e.setText(dt)
        description_label.setBuddy(self.dt_text_e)
        overview_grid.addWidget(self.dt_text_e, 1, 1, 1, -1)

        msg = _('Expiry time the item.')
        description_label = HelpLabel(_('&Expiry'), msg)
        overview_grid.addWidget(description_label, 2, 0)
        self.expiry_text_e = QLineEdit()
        self.expiry_text_e.setReadOnly(True)
        expiry_time = extracted.metadata.payload.timestamp + extracted.metadata.payload.ttl
        dt = datetime.utcfromtimestamp(expiry_time).strftime('%Y-%m-%d %H:%M:%S')
        self.expiry_text_e.setText(dt)
        description_label.setBuddy(self.expiry_text_e)
        overview_grid.addWidget(self.expiry_text_e, 2, 1, 1, -1)

        msg = _('Percentage of sampled nodes which have accepted the metadata.')
        description_label = HelpLabel(_('&Confidence'), msg)
        overview_grid.addWidget(description_label, 3, 0)
        self.confidence_text_e = QLineEdit()
        self.confidence_text_e.setReadOnly(True)
        percentage = str(round(float(extracted.confidence) * 100, 2)) + "%"
        self.confidence_text_e.setText(percentage)
        description_label.setBuddy(self.confidence_text_e)
        overview_grid.addWidget(self.confidence_text_e, 3, 1, 1, -1)

        self.setLayout(overview_grid)



class DKeyserverForm(QWidget):
    def __init__(self, entry, *args, **kwargs):
        raise NotImplementedError


class DPlainTextForm(DKeyserverForm):
    def __init__(self, text: str, *args, **kwargs):
        super(DPlainTextForm, self).__init__(*args, **kwargs)
        plain_text_grid = QGridLayout()
        msg = _('Plain text contained in the entry.')
        description_label = HelpLabel(_('&Text'), msg)
        plain_text_grid.addWidget(description_label, 0, 0)
        self.upload_plain_text_e = QTextEdit()
        self.upload_plain_text_e.setReadOnly(True)
        self.upload_plain_text_e.setText(text)
        description_label.setBuddy(self.upload_plain_text_e)
        plain_text_grid.addWidget(self.upload_plain_text_e, 0, 1, 1, -1)

        self.setLayout(plain_text_grid)


class DTelegramForm(DKeyserverForm):
    def __init__(self, handle: str, *args, **kwargs):
        super(DTelegramForm, self).__init__(*args, **kwargs)
        telegram_grid = QGridLayout()
        msg = _('Telegram handle contained in the entry.')
        description_label = HelpLabel(_('&Handle'), msg)
        telegram_grid.addWidget(description_label, 0, 0)
        self.upload_telegram_e = QLineEdit()
        self.upload_telegram_e.setReadOnly(True)
        self.upload_plain_text_e.setText(handle)
        description_label.setBuddy(self.upload_telegram_e)
        telegram_grid.addWidget(self.upload_telegram_e, 0, 1, 1, -1)

        self.setLayout(telegram_grid)

class DPubKeyForm(DKeyserverForm):
    def __init__(self, pubkey: bytes, *args, **kwargs):
        super(DPubKeyForm, self).__init__(*args, **kwargs)
        pubkey_grid = QGridLayout()
        msg = _('Plain text contained in the entry.')
        description_label = HelpLabel(_('&Text'), msg)
        pubkey_grid.addWidget(description_label, 0, 0)
        self.upload_pubkey_e = QLineEdit()
        self.upload_pubkey_e.setReadOnly(True)
        self.upload_pubkey_e.setText(pubkey.hex())
        description_label.setBuddy(self.upload_pubkey_e)
        pubkey_grid.addWidget(self.upload_pubkey_e, 0, 1, 1, -1)

        self.setLayout(pubkey_grid)


class DKeyserverURLForm(DKeyserverForm):
    def __init__(self, keyservers: list, *args, **kwargs):
        super(DKeyserverForm, self).__init__(*args, **kwargs)
        keyserver_grid = QGridLayout()
        msg = _('Keyserver list contained in the entry.')
        description_label = HelpLabel(_('&Servers'), msg)
        keyserver_grid.addWidget(description_label, 0, 0)
        self.upload_ks_urls_e = QTextEdit()
        self.upload_ks_urls_e.setReadOnly(True)
        self.upload_ks_urls_e.setText("\n".join(keyservers))
        description_label.setBuddy(self.upload_ks_urls_e)
        keyserver_grid.addWidget(self.upload_ks_urls_e, 0, 1, 1, -1)

        self.setLayout(keyserver_grid)


class DVCardForm(DKeyserverForm):
    def __init__(self, card: dict, *args, **kwargs):
        super(DVCardForm, self).__init__(*args, **kwargs)
        vcard_grid = QGridLayout()

        msg = _('Name of contact.')
        description_label = HelpLabel(_('&Name'), msg)
        vcard_grid.addWidget(description_label, 0, 0)
        self.upload_vName_e = QLineEdit()
        self.upload_vName_e.setReadOnly(True)
        self.upload_vName_e.setText(card["name"])
        description_label.setBuddy(self.upload_vName_e)
        vcard_grid.addWidget(self.upload_vName_e, 0, 1, 1, -1)

        msg = _('Mobile number of contact.')
        description_label = HelpLabel(_('&Mobile'), msg)
        vcard_grid.addWidget(description_label, 1, 0)
        self.upload_vMobile_e = QLineEdit()
        self.upload_vMobile_e.setReadOnly(True)
        self.upload_vMobile_e.setText(card["mobile"])
        description_label.setBuddy(self.upload_vMobile_e)
        vcard_grid.addWidget(self.upload_vMobile_e, 1, 1, 1, -1)

        msg = _('Email of contact.')
        description_label = HelpLabel(_('&Email'), msg)
        vcard_grid.addWidget(description_label, 2, 0)
        self.upload_vEmail_e = QLineEdit()
        self.upload_vEmail_e.setReadOnly(True)
        self.upload_vEmail_e.setText(card["email"])
        description_label.setBuddy(self.upload_vEmail_e)
        vcard_grid.addWidget(self.upload_vEmail_e, 2, 1, 1, -1)

        self.setLayout(vcard_grid)

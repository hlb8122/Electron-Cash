from PyQt5.QtWidgets import *
from ..util import *
from electroncash.i18n import _
from electroncash.keyserver.metadata_tools import *
from electroncash.keyserver.handler import Extracted


def construct_download_forms(parent, extracted):
    import vobject
    from electroncash.keyserver.keyservers_pb2 import Keyservers

    forms = [OverviewForm(parent, extracted)]
    for entry in extracted.metadata.payload.entries:
        if entry.kind == "text_utf8":
            text = entry.entry_data.decode('utf8')
            forms.append(DPlainTextForm(text))
        elif entry.kind == "telegram":
            handle = entry.entry_data.decode('utf8')
            forms.append(DTelegramForm(handle))
        elif entry.kind == "ks_urls":
            pb = Keyservers.FromString(parent, entry.entry_data)
            urls = list(pb.urls)
            forms.append(DKeyserverURLForm(urls))
        elif entry.kind == "vcard":
            text = entry.entry_data.decode('utf8')
            vcard = vobject.readOne(text, validate=True)
            forms.append(DVCardForm(vcard))
        elif entry.kind == "pubkey":
            forms.append(DPubKeyForm(parent, entry.entry_data))

    return forms


def pubkey_encrypt(parent, dest_pubkey: bytes):
    import base64
    from ecdsa.ecdsa import curve_secp256k1, generator_secp256k1
    from ecdsa.util import string_to_number, number_to_string, randrange
    from electroncash.bitcoin import EC_KEY
    from electroncash.keyserver.w2w_tools import w2w_plain_text_entry
    from electroncash.keyserver.w2w_messages import encrypt_entries
    from electroncash.keyserver.messaging_pb2 import Entries

    exponent = number_to_string(
        randrange(pow(2, 256)), generator_secp256k1.order())
    src_pubkey = EC_KEY(exponent)

    plain_text = text_dialog(parent.top_level_window(),
                             "Message Encryption", "Plain text", "Ok")
    entries = Entries(entries=[w2w_plain_text_entry(plain_text)])
    encrypted_message = encrypt_entries(entries, src_pubkey, dest_pubkey)
    encoded = str(base64.b64encode(encrypted_message))
    parent.msg_box(QMessageBox.Information, None,
                   "Cipher Text (Base 64)", encoded)


class OverviewForm(QWidget):
    name = "Overview"

    def __init__(self, parent, extracted: Extracted, *args, **kwargs):
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
        dt = datetime.utcfromtimestamp(
            extracted.metadata.payload.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        self.dt_text_e.setText(dt)
        description_label.setBuddy(self.dt_text_e)
        overview_grid.addWidget(self.dt_text_e, 1, 1, 1, -1)

        msg = _('Expiry time the item.')
        description_label = HelpLabel(_('&Expiry'), msg)
        overview_grid.addWidget(description_label, 2, 0)
        self.expiry_text_e = QLineEdit()
        self.expiry_text_e.setReadOnly(True)
        expiry_time = extracted.metadata.payload.timestamp + extracted.metadata.payload.ttl
        dt = datetime.utcfromtimestamp(
            expiry_time).strftime('%Y-%m-%d %H:%M:%S')
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

        msg = _('Public Key of the address.')
        description_label = HelpLabel(_('&Public Key'), msg)
        overview_grid.addWidget(description_label, 4, 0)
        self.public_key_text_e = QLineEdit()
        self.public_key_text_e.setReadOnly(True)
        pubkey_hex = extracted.metadata.pub_key.hex()
        self.public_key_text_e.setText(pubkey_hex)
        description_label.setBuddy(self.public_key_text_e)
        overview_grid.addWidget(self.public_key_text_e, 4, 1, 1, -1)

        encrypt = QPushButton(_("&Encrypt"))
        encrypt.clicked.connect(lambda: pubkey_encrypt(
            parent, extracted.metadata.pub_key))
        overview_grid.addLayout(Buttons(encrypt), 5, 1, 1, -1)

        self.setLayout(overview_grid)


class DPlainTextForm(QWidget):
    name = "Plain Text"

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


class DTelegramForm(QWidget):
    name = "Telegram"

    def __init__(self, handle: str, *args, **kwargs):
        super(DTelegramForm, self).__init__(*args, **kwargs)
        telegram_grid = QGridLayout()
        msg = _('Telegram handle contained in the entry.')
        description_label = HelpLabel(_('&Handle'), msg)
        telegram_grid.addWidget(description_label, 0, 0)
        self.upload_telegram_e = QLineEdit()
        self.upload_telegram_e.setReadOnly(True)
        self.upload_telegram_e.setText(handle)
        description_label.setBuddy(self.upload_telegram_e)
        telegram_grid.addWidget(self.upload_telegram_e, 0, 1, 1, -1)

        open_tg_button = QPushButton(_("&Open Telegram"))

        def open_telegram():
            QDesktopServices.openUrl(QUrl("https://t.me/" + handle))
        open_tg_button.clicked.connect(open_telegram)
        telegram_grid.addLayout(Buttons(open_tg_button), 1, 1, 1, -1)

        self.setLayout(telegram_grid)


class DPubKeyForm(QWidget):
    name = "Public Key"

    def __init__(self, parent, pubkey: bytes, *args, **kwargs):
        super(DPubKeyForm, self).__init__(*args, **kwargs)
        pubkey_grid = QGridLayout()
        msg = _('Plain text contained in the entry.')
        description_label = HelpLabel(_('&Public Key'), msg)
        pubkey_grid.addWidget(description_label, 0, 0)
        self.upload_pubkey_e = QLineEdit()
        self.upload_pubkey_e.setReadOnly(True)
        self.upload_pubkey_e.setText(pubkey.hex())
        description_label.setBuddy(self.upload_pubkey_e)
        pubkey_grid.addWidget(self.upload_pubkey_e, 0, 1, 1, -1)

        encrypt_button = QPushButton(_("&Encrypt"))
        pubkey_grid.addLayout(Buttons(encrypt_button), 1, 1, 1, -1)
        encrypt_button.clicked.connect(lambda: pubkey_encrypt(parent, pubkey))

        self.setLayout(pubkey_grid)


class DKeyserverURLForm(QWidget):
    name = "Keyservers"

    def __init__(self, parent, keyservers: list, *args, **kwargs):
        super(QWidget, self).__init__(*args, **kwargs)
        keyserver_grid = QGridLayout()
        msg = _('Keyserver list contained in the entry.')
        description_label = HelpLabel(_('&Servers'), msg)
        keyserver_grid.addWidget(description_label, 0, 0)
        self.upload_ks_urls_e = QTextEdit()
        self.upload_ks_urls_e.setReadOnly(True)
        self.upload_ks_urls_e.setText("\n".join(keyservers))
        description_label.setBuddy(self.upload_ks_urls_e)
        keyserver_grid.addWidget(self.upload_ks_urls_e, 0, 1, 1, -1)

        set_button = QPushButton(_("&Set Keyservers"))

        def set_keyservers():
            parent.ks_handler.set_keyservers(keyservers)
        set_button.clicked.connect(set_keyservers)
        keyserver_grid.addLayout(Buttons(set_button), 1, 1, 1, -1)

        self.setLayout(keyserver_grid)


class DVCardForm(QWidget):
    name = "vCard"

    def __init__(self, card: dict, *args, **kwargs):
        super(DVCardForm, self).__init__(*args, **kwargs)
        vcard_grid = QGridLayout()

        msg = _('Name of contact.')
        description_label = HelpLabel(_('&Name'), msg)
        vcard_grid.addWidget(description_label, 0, 0)
        self.upload_vName_e = QLineEdit()
        self.upload_vName_e.setReadOnly(True)
        self.upload_vName_e.setText(card.fn.value)
        description_label.setBuddy(self.upload_vName_e)
        vcard_grid.addWidget(self.upload_vName_e, 0, 1, 1, -1)

        msg = _('Mobile number of contact.')
        description_label = HelpLabel(_('&Mobile'), msg)
        vcard_grid.addWidget(description_label, 1, 0)
        self.upload_vMobile_e = QLineEdit()
        self.upload_vMobile_e.setReadOnly(True)
        self.upload_vMobile_e.setText(card.tel.value)
        description_label.setBuddy(self.upload_vMobile_e)
        vcard_grid.addWidget(self.upload_vMobile_e, 1, 1, 1, -1)

        msg = _('Email of contact.')
        description_label = HelpLabel(_('&Email'), msg)
        vcard_grid.addWidget(description_label, 2, 0)
        self.upload_vEmail_e = QLineEdit()
        self.upload_vEmail_e.setReadOnly(True)
        self.upload_vEmail_e.setText(card.email.value)
        description_label.setBuddy(self.upload_vEmail_e)
        vcard_grid.addWidget(self.upload_vEmail_e, 2, 1, 1, -1)

        add_button = QPushButton(_("&Add Contact"))
        # TODO: Add contract
        vcard_grid.addLayout(Buttons(add_button), 3, 1, 1, -1)

        self.setLayout(vcard_grid)

import copy
import datetime
import time
from functools import partial
import json
import threading
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from electroncash.address import Address, PublicKey
from electroncash.bitcoin import base_encode, TYPE_ADDRESS, TYPE_SCRIPT
from electroncash.i18n import _
from electroncash.plugins import run_hook

from .util import *

from electroncash.util import bfh, format_satoshis_nofloat, format_satoshis_plain_nofloat, NotEnoughFunds, ExcessiveFee
from electroncash.transaction import Transaction

from electroncash import bitcoinfiles

from .transaction_dialog import show_transaction

from electroncash.bitcoinfiles import *

dialogs = []  # Otherwise python randomly garbage collects the dialogs...


class BitcoinFilesUploadDialog(QDialog, MessageBoxMixin):

    def __init__(self, parent):
        # We want to be a top-level window
        QDialog.__init__(self, parent=None)

        self.parent = parent
        self.main_window = parent.main_window
        self.network = parent.main_window.network

        self.fileTransactions = []

        self.setWindowTitle(_("Upload Token Document"))

        #self.setMinimumWidth(750)
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(QLabel("Upload a document to the blockchain using the Bitcoin Files Protocol (<a href=https://bitcoinfiles.com>bitcoinfiles.com</a>)"))

        # Select File
        self.select_file_button = b = QPushButton(_("Select File..."))
        self.select_file_button.setAutoDefault(False)
        self.select_file_button.setDefault(False)
        b.clicked.connect(self.select_file)
        b.setDefault(False)
        vbox.addWidget(self.select_file_button)#, row, 0)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        vbox.addLayout(grid)
        row = 0

        # self.tx_batch = []
        # self.tx_batch_signed_count = 0
        # self.chunks_processed = 0
        # self.chunks_total = 1 

        # Local file path
        grid.addWidget(QLabel(_('Local Path:')), row, 0)
        self.path = QLineEdit("")
        self.path.setReadOnly(True)
        self.path.setFixedWidth(570)
        grid.addWidget(self.path, row, 1)
        row += 1

        # File hash
        grid.addWidget(QLabel(_('File Hash:')), row, 0)
        self.hash = QLineEdit("")
        self.hash.setReadOnly(True)
        self.hash.setFixedWidth(570)
        self.hash.setInputMask("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
        grid.addWidget(self.hash, row, 1)
        row += 1

        # Estimated Fees
        grid.addWidget(QLabel(_('Upload Cost (sat):')), row, 0)
        self.upload_cost_label = QLabel("")
        grid.addWidget(self.upload_cost_label, row, 1)
        row += 1

        # File path
        grid.addWidget(QLabel(_('URI after upload:')), row, 0)
        self.bitcoinfileAddr_label = QLineEdit("")
        self.bitcoinfileAddr_label.setReadOnly(True)
        self.bitcoinfileAddr_label.setFixedWidth(570)
        grid.addWidget(self.bitcoinfileAddr_label, row, 1)
        row += 1

        self.progress = QProgressBar(self)
        self.progress.setGeometry(200, 80, 250, 20)
        vbox.addWidget(self.progress)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        self.cancel_button = b = QPushButton(_("Cancel"))
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setDefault(False)
        b.clicked.connect(self.close)
        b.setDefault(False)
        hbox.addWidget(self.cancel_button)

        hbox.addStretch(1)

        self.upload_button = b = QPushButton(_("Upload"))
        self.upload_button.setAutoDefault(False)
        self.upload_button.setDefault(False)
        self.upload_button.setDisabled(True)
        b.clicked.connect(self.upload)
        b.setDefault(False)
        hbox.addWidget(self.upload_button)
            

    def select_file(self):
        self.progress.setValue(0)
        self.tx_batch = []
        self.tx_batch_signed_count = 0
        self.chunks_processed = 0
        self.chunks_total = 1 

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Select File to Upload", "","All Files (*)", options=options)

        if filename != '':
            with open(filename,"rb") as f:
                bytes = f.read() # read entire file as bytes
                if len(bytes) > 214:
                    self.show_error("At the moment you cannot be larger than 214 bytes. This will be updated to allow larger files soon.")
                    return
                # set the file hash in parent dialog
                import hashlib
                readable_hash = hashlib.sha256(bytes).hexdigest()
                self.hash.setText(readable_hash)
                self.path.setText(filename)

                cost = calculateUploadCost(len(bytes))
                self.upload_cost_label.setText(str(cost))

                addr = self.parent.wallet.get_unused_address()

                try: 
                    self.tx_batch.append(getFundingTxn(self.parent.wallet, addr, cost, self.parent.config))
                except NotEnoughFunds:
                    self.show_message("Insufficient funds for funding transaction")
                    return

                def sign_done(success):
                    if success:
                        self.tx_batch_signed_count += 1
                        if self.chunks_processed < self.chunks_total:
                            chunk_bytes = bytes # fix this for chunk_count > 1
                            try:
                                self.tx_batch.append(getUploadTxn(self.parent.wallet, self.tx_batch[self.chunks_processed], self.chunks_processed + 1, self.chunks_total, chunk_bytes, self.parent.config))
                            except NotEnoughFunds as e:
                                raise e
                                self.show_message("Insufficient funds for file chunk #" + str(self.chunks_processed + 1))
                                return

                            self.chunks_processed += 1

                        if len(self.tx_batch) > self.tx_batch_signed_count:
                            
                            # IMPORTANT: set wallet.sedn_slpTokenId to None to guard tokens during this transaction
                            self.main_window.token_type_combo.setCurrentIndex(0)
                            assert self.main_window.wallet.send_slpTokenId == None

                            self.main_window.push_top_level_window(self)
                            self.main_window.sign_tx(self.tx_batch[self.tx_batch_signed_count], sign_done)
                        else:
                            uri = "bitcoinfiles:" + self.tx_batch[len(self.tx_batch)-1].txid()
                            self.bitcoinfileAddr_label.setText(uri)
                            self.upload_button.setEnabled(True)
                            self.upload_button.setDefault(True)

                # IMPORTANT: set wallet.sedn_slpTokenId to None to guard tokens during this transaction
                self.main_window.token_type_combo.setCurrentIndex(0)
                assert self.main_window.wallet.send_slpTokenId == None

                self.main_window.push_top_level_window(self)
                self.main_window.sign_tx(self.tx_batch[self.tx_batch_signed_count], sign_done)

    def upload(self):
        self.progress.setMinimum(0)
        self.progress.setMaximum(len(self.tx_batch))
        broadcast_count = 0
        #self.main_window.push_top_level_window(self)
        for tx in self.tx_batch:
            tx_desc = None
            #self.main_window.broadcast_transaction(tx, tx_desc)
            status, msg = self.network.broadcast(tx)
            print(status)
            print(msg)
            if status == False:
                self.show_error(msg)
                self.show_error("Upload failed. Try again.")
                return 
            
            broadcast_count += 1
            time.sleep(0.1)
            self.progress.setValue(broadcast_count)
            QApplication.processEvents()

        self.parent.token_dochash_e.setText(self.hash.text())
        self.parent.token_url_e.setText(self.bitcoinfileAddr_label.text())
        self.show_message("File upload complete.")
        self.close()

    def closeEvent(self, event):
        event.accept()
        self.parent.raise_()
        self.parent.activateWindow()
        try:
            dialogs.remove(self)
        except ValueError:
            pass
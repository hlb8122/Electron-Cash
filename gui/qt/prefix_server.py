from electroncash.prefix_server.prefix_server_pb2 import Item, SearchParams
from electroncash.prefix_server.prefix_server_pb2_grpc import PublicStub
from electroncash.transaction import Transaction, BCDataStream, parse_input
from electroncash.bitcoin import sha256

from PyQt5.QtCore import QThread, pyqtSignal


def is_match(input_hash: bytes, raw_tx: bytes, input_index: int):
    vds = BCDataStream()
    vds.write(raw_tx[4:])  # Skip version number
    vds.read_compact_size()  # Skip number of vin's

    # Ignore all inputs before input hex
    for _ in range(input_index - 1):
        parse_input(vds)

    start_index = vds.read_cursor
    parse_input(vds)
    end_index = vds.read_cursor

    raw_input = raw_tx[4+start_index:end_index]
    digest = sha256(raw_input)
    return digest == input_hash


class SearchThread(QThread):
    found_signal = pyqtSignal(Item)
    completion_signal = pyqtSignal()

    def __init__(self, channel, input_hash: bytes, n_bytes: int = 1, parent=None):
        self.stub = PublicStub(channel)
        self.input_hash = input_hash
        self.prefix = input_hash[:n_bytes]
        QThread.__init__(self, parent)

    def run(self):
        search_params = SearchParams(prefix=self.prefix)
        for item in self.stub.PrefixSearch(search_params):
            found = False
            if not found:
                if is_match(self.input_hash, item.raw_tx, item.input_index):
                    found = True
                    self.found_signal.emit(item)

        self.completion_signal.emit()

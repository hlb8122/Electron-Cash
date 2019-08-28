import random
import requests
from .addressmetadata_pb2 import Entry, Payload, AddressMetadata, Header


class KSHandler:
    '''
    KSHandler deals with operations relating to the management of keyservers
    and GET and PUT requests
    '''
    # Hardcoded trusted nodes
    trusted_ks_urls = ["http://35.232.229.28", "http://34.67.137.105"]

    # Address holding peer list
    trusted_keyservers_addr = ""

    def __init__(self, ks_urls: list = None, default_sample_size: int = 6):
        self.default_sample_size = default_sample_size
        self.handlers = dict()

        if ks_urls is None:
            self.ks_urls = self.trusted_ks_urls
        else:
            self.ks_urls = self.trusted_ks_urls + ks_urls

    def add_handler(self, name: str, extractor, executor):
        self.handlers[name] = (extractor, executor)

    @staticmethod
    def fetch_from_trusted(sample_size: int = 6):
        from peer_list import peer_list_extractor
        '''Fetch keyserver list from one of the trusted nodes'''
        ks_urls = KSHandler._uniform_aggregate(
            KSHandler.trusted_ks_urls, KSHandler.trusted_keyservers_addr, peer_list_extractor, sample_size=sample_size)
        return KSHandler(ks_urls)

    def set_keyservers(self, urls: list):
        self.ks_urls = self.trusted_ks_urls + urls

    @staticmethod
    def _validate_sig(addr: str, payload: Payload):
        # TODO: Check signature
        # TODO: Check addr ~ pubkey
        return True

    @staticmethod
    def construct_metadata(ks_url: str, addr: str):
        url = "%s/keys/%s" % (ks_url, addr)
        response = requests.get(url=url)
        if response.status_code != 200:
            raise Exception("%s - %s" % (response.status_code, response.text))
        addr_metadata = AddressMetadata.FromString(response.content)
        return addr_metadata

    @staticmethod
    def _uniform_aggregate(ks_urls: list, addr: str, sample_size: int):
        class Extracted:
            url = None
            metadata = None
            timestamp = 0
            confidence = 0

        best = Extracted()
        errors = []

        sample_size = min([len(ks_urls), sample_size])
        sample_set = random.sample(ks_urls, sample_size)

        for url in sample_set:
            try:
                new_metadata = KSHandler.construct_metadata(url, addr)
                new_timestamp = new_metadata.payload.timestamp

                if new_timestamp < best.timestamp:
                    raise Exception("Older timestamp")

                if KSHandler._validate_sig(addr, new_metadata):
                    if new_metadata == best.metadata:
                        if new_timestamp > best.timestamp:
                            best.timestamp = new_timestamp
                            best.confidence = 0
                            best.url = url
                        else:
                            best.confidence += 1
                    else:
                        best.metadata = new_metadata
                        best.timestamp = new_timestamp
                        best.confidence = 0
                        best.url = url

            except Exception as e:
                errors.append((url, e))

        # This is safe because it'll raise earlier if len is 0
        best.confidence = best.confidence / len(ks_urls)

        return best, errors

    def uniform_aggregate(self, addr: str, sample_size: int = None):
        if sample_size is None:
            sample_size = self.default_sample_size
        return KSHandler._uniform_aggregate(self.ks_urls, addr, sample_size=sample_size)

    def uniform_sample(self):
        return random.choice(self.ks_urls)

    def get_data(self, addr, sample_size: int = None):
        aggregate, errors = self.uniform_aggregate(addr)

        if aggregate.metadata is None:
            return None, errors

        extracted = []
        for entry in aggregate.metadata.payload.entries:
            extractor, _ = self.handlers[entry.kind]

            try:
                extracted.append(extractor(entry.entry_data))
            except Exception as e:
                errors.append((aggregate.url, e))

        return extracted, errors

    def execute(self, addr, sample_size: int = None):
        aggregate, errors = self.uniform_aggregate(addr)

        if aggregate.metadata is None:
            return None, errors

        for entry in aggregate.metadata.payload.entries:
            extractor, executor = self.handlers[entry.kind]
            try:
                data = extractor(entry.entry_data)
                executor(data)
            except Exception as e:
                errors.append((aggregate.url, e))

        return errors

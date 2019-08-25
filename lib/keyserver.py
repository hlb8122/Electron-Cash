import random
import requests
from electroncash.addressmetadata_pb2 import MetadataField, Payload, AddressMetadata

'''
Parsers extract data from the payload returning a value and a flag 
signalling searching should halt, or throw an error.
'''


def null_extractor(payload: Payload):
    return None, False


def peer_extractor(payload: Payload):
    # TODO
    return None, False


class KSHandler:
    '''
    KSHandler handles operations relating to the management of keyservers
    and GET and PUT requests
    '''

    # Hardcoded trusted nodes
    trusted_ks_urls = ["http://35.232.229.28", "http://34.67.137.105"]

    # Address holding peer list
    trusted_peerlist_addr = ""

    def __init__(self, ks_urls: list = None, default_sample_size: int = 6):
        self.default_sample_size = default_sample_size

        if ks_urls is None:
            self.ks_urls = KSHandler.trusted_ks_urls
        else:
            self.ks_urls = ks_urls

    @staticmethod
    def fetch_from_trusted(sample_size: int = 6):
        '''Fetch keyserver list from one of the trusted nodes'''
        peer_list = KSHandler._uniform_aggregate(
            KSHandler.trusted_ks_urls, KSHandler.trusted_peerlist_addr, peer_extractor, sample_size=sample_size)
        return KSHandler(peer_list)

    @staticmethod
    def _validate_sig(addr: str, payload: Payload):
        # TODO: Check signature
        # TODO: Check addr ~ pubkey
        return True

    @staticmethod
    def get_metadata(ks_url: str, addr: str):
        url = "%s/keys/%s" % (ks_url, addr)
        response = requests.get(url=url)
        if response.status_code != 200:
            raise Exception("%s - %s" % (response.status_code, response.text))
        addr_metadata = AddressMetadata.FromString(response.content)
        return addr_metadata

    @staticmethod
    def _uniform_aggregate(ks_urls: list, addr: str, extractor, sample_size):
        class Extracted:
            metadata = None
            result = None
            timestamp = 0
            confidence = 0

            def is_empty(self):
                return self.metadata is None

        best = Extracted()
        errors = []

        sample_size = min([len(ks_urls), sample_size])
        sample_set = random.sample(ks_urls, sample_size)

        for sample in sample_set:
            found = False

            try:
                new_metadata = KSHandler.get_metadata(sample, addr)
                new_timestamp = new_metadata.payload.timestamp
                result, found = extractor(new_metadata)

                if new_timestamp < best.timestamp:
                    raise Exception("Older timestamp")

                if KSHandler._validate_sig(addr, new_metadata):
                    if new_metadata == best.metadata:
                        if new_timestamp > best.timestamp:
                            best.timestamp = new_timestamp
                            best.confidence = 0
                        else:
                            best.confidence += 1
                    else:
                        best.metadata = new_metadata
                        best.result = result
                        best.timestamp = new_timestamp
                        best.confidence = 0

            except Exception as e:
                errors.append((sample, e))

            if found:
                break

        return best, errors

    def uniform_aggregate(self, addr: str, extractor=null_extractor, sample_size: int = None):
        if sample_size is None:
            sample_size = self.default_sample_size
        return KSHandler._uniform_aggregate(self.ks_urls, addr, extractor, sample_size=sample_size)

    def uniform_sample(self):
        return random.choice(self.ks_urls)

import random
import requests
from electroncash.addressmetadata_pb2 import MetadataField, Payload, AddressMetadata, Header
import base64
import time

'''
Parsers extract data from the payload returning a value and a flag 
signalling searching should halt, or throw an error.
'''

def plain_text_metadata(addr, data:str, signer, ttl:int=3000, type_override="text_utf8"):
    from hashlib import sha256
        
    text = data.encode('utf8')

    # Construct Payload
    header = Header(name="type", value=type_override)
    metadata_field = MetadataField(
        headers=[header], metadata=text)
    timestamp = int(time.time())
    payload = Payload(timestamp=timestamp, ttl=ttl, rows=[metadata_field])

    # Sign
    raw_payload = payload.SerializeToString()
    digest = sha256(sha256(raw_payload).digest()).digest()
    public_key, signature = signer(addr, digest)

    # Address metadata
    addr_metadata = AddressMetadata(
        pub_key=public_key, payload=payload, scheme=1, signature=signature)
    raw_addr_meta = addr_metadata.SerializeToString()
    return raw_addr_meta

def plain_text_extractor(body: bytes):
    return body.decode('utf8')

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
        self.payload_types = dict()

        if ks_urls is None:
            self.ks_urls = KSHandler.trusted_ks_urls
        else:
            self.ks_urls = ks_urls

    def add_executor(self, name: str, extractor, executor):
        self.payload_types[name] = (extractor, executor)

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
    def _uniform_aggregate(ks_urls: list, addr: str, sample_size: int):
        class Extracted:
            sample = None
            metadata = None
            timestamp = 0
            confidence = 0

        best = Extracted()
        errors = []

        sample_size = min([len(ks_urls), sample_size])
        sample_set = random.sample(ks_urls, sample_size)

        for sample in sample_set:
            try:
                new_metadata = KSHandler.get_metadata(sample, addr)
                new_timestamp = new_metadata.payload.timestamp

                if new_timestamp < best.timestamp:
                    raise Exception("Older timestamp")

                if KSHandler._validate_sig(addr, new_metadata):
                    if new_metadata == best.metadata:
                        if new_timestamp > best.timestamp:
                            best.timestamp = new_timestamp
                            best.confidence = 0
                            best.sample = sample
                        else:
                            best.confidence += 1
                    else:
                        best.metadata = new_metadata
                        best.timestamp = new_timestamp
                        best.confidence = 0
                        best.sample = sample

            except Exception as e:
                errors.append((sample, e))

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

        if aggregate is None:
            return None, errors

        headers = {
            header.name: header.value for header in aggregate.metadata.payload.rows[0].headers}
        extractor, _ = self.payload_types[headers["type"]]

        extracted = None
        try:
            # TODO: Don't ignore other rows
            body = aggregate.metadata.payload.rows[0].metadata
            extracted = extractor(body)
        except Exception as e:
            errors.append((aggregate.sample, e))

        return extracted, errors

    def get_exec(self, addr, sample_size: int = None):
        aggregate, errors = self.uniform_aggregate(addr)

        if aggregate.metadata is None:
            return None, errors

        headers = {
            header.name: header.value for header in aggregate.metadata.payload.rows[0].headers}
        extractor, executor = self.payload_types[headers["type"]]

        extracted = None
        try:
            # TODO: Don't ignore other rows
            body = aggregate.metadata.payload.rows[0].metadata
            extracted = extractor(body)
        except Exception as e:
            errors.append((aggregate.sample, e))

        if extracted is None:
            return None, errors

        def execution(): return executor(extracted)

        return execution, errors

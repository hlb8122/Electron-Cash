import time
from .addressmetadata_pb2 import MetadataField, Payload, AddressMetadata, Header
from .peer_list_pb2 import *


def plain_text_metadata(addr, data: str, signer, ttl: int = 3000, type_override="text_utf8"):
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


def telegram_metadata(addr, data: str, signer, ttl: int = 3000):
    return plain_text_metadata(addr, data, signer, ttl=ttl, type_override="telegram")


def peer_list_metadata(addr, urls: list, signer, ttl: int = 3000):
    from hashlib import sha256

    raw = PeerList(urls=urls).SerializeToString()

    # Construct Payload
    header = Header(name="type", value="peer_list")
    metadata_field = MetadataField(
        headers=[header], metadata=raw)
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


def peer_list_extractor(body: bytes):
    pb = PeerList.FromString(body)
    return pb.urls

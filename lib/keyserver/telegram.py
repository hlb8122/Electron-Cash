import time
from .addressmetadata_pb2 import MetadataField, Payload, AddressMetadata, Header
from .plain_text import plain_text_metadata


def telegram_metadata(addr, data: str, signer, ttl: int = 3000):
    return plain_text_metadata(addr, data, signer, ttl=ttl, type_override="telegram")

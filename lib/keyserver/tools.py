import time
from .addressmetadata_pb2 import MetadataField, Payload, AddressMetadata, Header
from .keyservers_pb2 import *


def blob_metadata(addr, body: bytes, signer, ttl: int = 3000, type="raw"):
    from hashlib import sha256

    # Construct Payload
    header = Header(name="type", value=type)
    metadata_field = MetadataField(
        headers=[header], metadata=body)
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

# Plain text
def plain_text_metadata(addr, text: str, signer, ttl: int = 3000):
    body = text.encode('utf8')
    return blob_metadata(addr, body, signer, ttl, type="text_utf8")

def plain_text_extractor(body: bytes):
    return body.decode('utf8')

def telegram_metadata(addr, text: str, signer, ttl: int = 3000):
    body = text.encode('utf8')
    return blob_metadata(addr, body, signer, ttl, type="telegram")

# Keyserver URLs
def ks_urls_metadata(addr, urls: list, signer, ttl: int = 3000):
    body = Keyservers(urls=urls).SerializeToString()
    return blob_metadata(addr, body, signer, ttl, type="ks_urls")

def ks_urls_extractor(body: bytes):
    pb = Keyservers.FromString(body)
    return list(pb.urls)

# vCard
def vcard_metadata(addr, card: dict, signer, ttl: int = 3000):
    import vobject
    v = vobject.vCard()
    v.add('fn')
    v.fn.value = card["name"]
    v.add('email')
    v.email.value = card["email"]
    v.add('tel')
    v.tel.type_param = "MOBILE"
    v.email.value = card["mobile"]
    body = v.serialize().encode('utf8')
    return blob_metadata(addr, body, signer, ttl, type="vcard")

def vcard_extractor(body: bytes):
    import vobject
    text = body.decode('utf8')
    v = vobject.readOne(text, validate=True)
    return v
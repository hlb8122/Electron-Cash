import pyaes
from .messaging_pb2 import Message, Payload, Entry, Entries
from ..bitcoin import EC_KEY, point_to_ser, ser_to_point, aes_encrypt_with_iv, aes_decrypt_with_iv
from ..util import assert_bytes
from ecdsa import VerifyingKey, BadSignatureError
from ecdsa.curves import SECP256k1
from ecdsa.ecdsa import curve_secp256k1, generator_secp256k1, point_is_valid
from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point
from ecdsa.util import string_to_number, number_to_string, randrange
from hashlib import sha256, sha512
from time import time

def sign_ecdsa(key, digest):
    return (Message.ECDSA, key.sign(digest))

def verify_ecdsa(pk, signature, digest):
    verify_key = VerifyingKey.from_public_point(
        pk,
        curve=SECP256k1)
    try:
        verify_key.verify_digest(signature, digest)
        return True
    except BadSignatureError:
        return False

def sign_schnorr(key, digest):
    # TODO: This requires extra work to use schnorr.py
    pass

def verify_schnorr(pk, signature, digest):
    # TODO: This requires extra work to use schnorr.py
    pass

def encrypt(raw_entries, dest_pubkey, src_pubkey):
    assert_bytes(raw_entries)
    pk = dest_pubkey.pubkey.point
    if not point_is_valid(generator_secp256k1, pk.x(), pk.y()):
        raise Exception('invalid pubkey')
    ephemeral_exponent = number_to_string(randrange(pow(2,256)), generator_secp256k1.order())
    ephemeral = EC_KEY(ephemeral_exponent)
    # We need a commitment to the src key here, otherwise
    # someone could co-opt an encrypted payload, resign it, and send
    # it to the intended recipient claiming to be the author.
    ecdh_key = point_to_ser(pk * ephemeral.privkey.secret_multiplier + src_pubkey.pubkey.point)
    key = sha512(ecdh_key).digest()
    iv, key_e, _ = key[0:16], key[16:32], key[32:]
    ciphertext = aes_encrypt_with_iv(key_e, iv, raw_entries)
    return ciphertext, point_to_ser(ephemeral.pubkey.point)

def decrypt(raw_entries, dest_secret, src_pk, seed):
    assert_bytes(raw_entries)
    seed_pk = ser_to_point(seed)
    if not point_is_valid(generator_secp256k1, seed_pk.x(), seed_pk.y()):
        raise Exception('invalid seed pubkey')
    if not point_is_valid(generator_secp256k1, src_pk.x(), src_pk.y()):
        raise Exception('invalid src pubkey')

    # Reconstruct shared secret
    ecdh_key = point_to_ser(dest_secret * seed_pk + src_pk)
    # We need a commitment to the src key here, otherwise
    # someone could co-opt an encrypted payload, resign it, and send
    # it to the intended recipient claiming to be the author.
    key = sha512(ecdh_key).digest()
    iv, key_e, _ = key[0:16], key[16:32], key[32:]
    plaintext = aes_decrypt_with_iv(key_e, iv, raw_entries)
    return plaintext   

def encrypt_txt_message(text_message, src_pubkey, dest_pubkey, signer=sign_ecdsa):
    assert_bytes(text_message)
    # Create a text payload message
    entry = Entry()
    entry.kind = "text_utf8"
    entry.entry_data = bytes(text_message)
    entries = Entries(entries=[entry])
    # Encrypt the payload using AES with an ephemeral diffie-helmen key
    serialized_payload = bytes(entries.SerializeToString())
    encrypted_entries, seed = encrypt(serialized_payload, dest_pubkey, src_pubkey)
    # Put it in the payload that will be signed.
    text_payload = Payload(
        timestamp=int(time()),
        destination=point_to_ser(dest_pubkey.pubkey.point, True),
        scheme=Payload.EphemeralDH,
        entries=encrypted_entries,
        secret_seed=seed
        )
    # Generate final signature for payload for non-repudiation and authenticit
    msg = Message(payload=text_payload.SerializeToString(), sender_pub_key=point_to_ser(src_pubkey.pubkey.point, True))
    digest = sha256(msg.payload).digest()
    scheme, signature = signer(src_pubkey, digest)
    msg.scheme = scheme
    msg.signature = signature
    # NOTE: Someone can steal the encrypted payload and claim it as their own.
    # We need a commitment to the source key somewhere as part of the encrypted
    # data.  Possibly has the ephemeral seed with the source pubkey to generate
    # the secret.  H(sP + eP) rather than H(eP) 
    return bytes(msg.SerializeToString())

def decrypt_txt_message(msg, dest_key):
    assert_bytes(msg)
    msg = Message.FromString(msg)
    # Verify signature
    if msg.scheme == Message.ECDSA:
        verifier = verify_ecdsa
    elif Message.scheme == Message.SCHNORR:
        verifier = verify_schnorr
    digest = sha256(msg.payload).digest()
    src_key_pk = ser_to_point(msg.sender_pub_key)
    if not point_is_valid(generator_secp256k1, src_key_pk.x(), src_key_pk.y()):
        raise Exception('invalid pubkey')

    if not verifier(src_key_pk, msg.signature, digest):
        raise Exception('invalid signature')

    payload = Payload.FromString(msg.payload)
    entries = decrypt(payload.entries,
                      dest_key.privkey.secret_multiplier,
                      src_key_pk,
                      payload.secret_seed)
    decoded_entries = Entries.FromString(entries)

    return (msg, payload.timestamp, decoded_entries.entries)
#!/usr/bin/python3

# Copyright (c) 2017 Pieter Wuille
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Reference tests for cashaddr adresses"""

import binascii
import unittest
import random
import base64

from ecdsa.ecdsa import curve_secp256k1, generator_secp256k1
from ecdsa.curves import SECP256k1
from ecdsa.ellipticcurve import Point
from ecdsa.util import string_to_number, number_to_string, randrange
from ..keyserver.w2w_messages import encrypt_entries, decrypt_entries
from ..bitcoin import EC_KEY

def generate_key():
    exponent = number_to_string(randrange(pow(2,256)), generator_secp256k1.order())
    return EC_KEY(exponent)


class TestW2WMessaging(unittest.TestCase):
    """Unit test class for cashaddr addressess."""
    def test_encrypt_decrypt(self):
        entry = Entry()
        entry.kind = "text_utf8"
        entry.entry_data = bytes("Hello world!")
        entries = Entries(entries=[entry])

        dest_key = generate_key()
        src_key = generate_key()
        encrypted_message = encrypt_entries(entries, src_key, dest_key.pubkey.point)
        msg, timestamp, decoded_entries = decrypt_txt_message(encrypted_message, dest_key)
        assert decoded_entries[0].entry_data == entry.entry_data, "Failed to decrypt"
        base64.b64encode(encrypted_message)
        with open("message.txt", "w") as f:
            f.write(base64.b64encode(encrypted_message).decode('utf-8'))

        with open("message.txt", "rb") as f:
            ciphertext = base64.b64decode(f.read())
            msg, timestamp, decoded_entries = decrypt_txt_message(ciphertext, dest_key)
            assert decoded_entries[0].entry_data == b"Hello world!", "Failed to decrypt"

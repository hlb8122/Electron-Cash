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
from ..keyserver.w2w_messages import encrypt_txt_message, decrypt_txt_message
from ..bitcoin import EC_KEY

def generate_key():
    exponent = number_to_string(randrange(pow(2,256)), generator_secp256k1.order())
    return EC_KEY(exponent)


class TestW2WMessaging(unittest.TestCase):
    """Unit test class for cashaddr addressess."""
    def test_encrypt_decrypt(self):
        dest_pubkey = generate_key()
        src_pubkey = generate_key()
        encrypted_message = encrypt_txt_message(b"Hello world!", src_pubkey, dest_pubkey)
        msg, timestamp, entries = decrypt_txt_message(encrypted_message, dest_pubkey)
        assert entries[0].entry_data == b"Hello world!", "Failed to decrypt"
        # base64.b64encode(encrypted_message)


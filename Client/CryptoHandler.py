import hashlib
import sys
import time
from base64 import b64encode, b64decode
from typing import Union

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Random import get_random_bytes
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme

from Client.Utils import Singleton
from Node.NodeConfig import NodeConfig


# CryptoHandler est un singleton : son instanciation n'est possible qu'une fois.
@Singleton
class CryptoHandler:
    str_public_key: str
    __private_key: RsaKey
    public_key: RsaKey

    def __init__(self):
        self.testvar = None
        self.__private_key, self.public_key = NodeConfig.load_keys()
        if not self.__private_key or not self.public_key:
            print("RSA generation...")
            self.generate_keys()
            self.__private_key, self.public_key = NodeConfig.load_keys()
        self.str_public_key = b64encode(self.public_key.export_key(format="DER")).decode("utf-8")
        self.identity = hashlib.sha1(self.public_key.export_key(format="DER")).hexdigest()

    def generate_keys(self) -> (RsaKey, RsaKey):
        key_length = 2048
        private_key: RsaKey = RSA.generate(key_length)
        public_key: RsaKey = private_key.publickey()
        print("New keys generated !")
        NodeConfig.store_keys(private_key, public_key)

    def to_rsa(self, key: str) -> RsaKey:
        return RSA.import_key(b64decode(key))

    def check_authenticator(self, key: RsaKey, authenticator: str) -> bool:
        msg = str(round(time.time()))[:-1]
        hash = SHA256.new(msg.encode())
        verifier = PKCS115_SigScheme(key)
        try:
            verifier.verify(hash, b64decode(authenticator))
            return True
        except ValueError:
            return False

    def get_authenticator(self) -> str:
        message = str(round(time.time()))[:-1]
        tstamp_hash = SHA256.new(message.encode())
        signer = PKCS115_SigScheme(self.__private_key)
        return b64encode(signer.sign(tstamp_hash)).decode("utf-8")

    def generate_session_key(self) -> bytes:
        return get_random_bytes(16)

    def encrypt_rsa(self, data: Union[str, bytes], public_key: RsaKey) -> bytes:
        if type(data) == str:
            data = data.encode()
        if sys.getsizeof(data) > 200:
            raise Exception("Trying to encrypt too large data with RSA. Limit is 200 bytes.")
        cipher_rsa = PKCS1_OAEP.new(public_key)
        encrypted_data = cipher_rsa.encrypt(data)
        return encrypted_data


if __name__ == '__main__':
    # noinspection PyCallByClass
    ch: CryptoHandler = Singleton.Instance(CryptoHandler)

import time
from base64 import b64encode, b64decode
from typing import Union

from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme

from Node.NodeConfig import NodeConfig
from Node.Utils import Singleton


# CryptoHandler est un singleton : son instanciation n'est possible qu'une fois.
# noinspection DuplicatedCode
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

    def decrypt_rsa(self, data: Union[str, bytes]) -> bytes:
        if type(data) == str:
            data = data.encode()
        cipher_rsa = PKCS1_OAEP.new(self.__private_key)
        return cipher_rsa.decrypt(data)

    def encrypt(self, data: Union[str, bytes], session_key: bytes) -> bytes:
        if type(data) == str:
            data = data.encode()
        cipher = AES.new(session_key, AES.MODE_GCM)
        cipher_data, tag = cipher.encrypt_and_digest(data)
        nonce = cipher.nonce

        full_data = nonce + tag + cipher_data
        # print("Tag : " + str(b64encode(tag)))
        # print("Nonce : " + str(b64encode(nonce)))
        # print("Cipher data : " + str(b64encode(cipher_data)))
        # print("Full data : " + str(b64encode(full_data)))

        return full_data

    def decrypt(self, data: bytes, session_key: bytes) -> bytes:
        # nonce, tag, cipher_data = [data[x] for x in (16, 16, -1)]
        nonce = data[:16]
        tag = data[16:32]
        cipher_data = data[32:]
        cipher = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
        clear_data = cipher.decrypt_and_verify(cipher_data, tag)
        # print("Cipher data : " + str(b64encode(cipher_data)))
        # print("Tag : " + str(b64encode(tag)))
        # print("Nonce : " + str(b64encode(nonce)))
        # print("Clear data : " + str(clear_data))

        return clear_data


if __name__ == '__main__':
    # noinspection PyCallByClass
    ch: CryptoHandler = Singleton.Instance(CryptoHandler)

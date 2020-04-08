import hashlib
import time
from base64 import b64encode, b64decode

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
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

if __name__ == '__main__':
    # noinspection PyCallByClass
    ch: CryptoHandler = Singleton.Instance(CryptoHandler)

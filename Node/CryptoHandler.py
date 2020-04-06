import time
from base64 import b64encode

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme

from Node.NodeConfig import NodeConfig


class Singleton:

    def __init__(self, cls):
        self._cls = cls

    def Instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Singleton.Instance(<object>)`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._cls)


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

    def generate_keys(self) -> (RsaKey, RsaKey):
        key_length = 2048
        private_key: RsaKey = RSA.generate(key_length)
        public_key: RsaKey = private_key.publickey()
        print("New keys generated !")
        NodeConfig.store_keys(private_key, public_key)

    def get_authenticator(self) -> str:
        message = str(round(time.time()))[:-1]
        tstamp_hash = SHA256.new(message.encode())
        signer = PKCS115_SigScheme(self.__private_key)
        return b64encode(signer.sign(tstamp_hash)).decode("utf-8")


if __name__ == '__main__':
    # noinspection PyCallByClass
    ch: CryptoHandler = Singleton.Instance(CryptoHandler)

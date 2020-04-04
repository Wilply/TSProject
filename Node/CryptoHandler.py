import os
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey

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
    private_key: RsaKey
    public_key : RsaKey

    def __init__(self):
        self.testvar = None
        self.private_key, self.public_key = NodeConfig.load_keys()
        if not self.private_key or not self.public_key:
            print("RSA generation...")
            self.generate_keys()
            self.private_key, self.public_key = NodeConfig.load_keys()
        print("Private : " + self.private_key.export_key().decode("utf-8"))

    def generate_keys(self) -> (RsaKey, RsaKey):
        key_length = 2048
        private_key: RsaKey = RSA.generate(key_length)
        public_key: RsaKey = private_key.publickey()
        print("Keys generation OK")
        NodeConfig.store_keys(private_key, public_key)


if __name__ == '__main__':
    ch: CryptoHandler = Singleton.Instance(CryptoHandler)
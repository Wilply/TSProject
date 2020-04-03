import os
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey

from Node.NodeConfig import NodeConfig


class CryptoHandler():
    private_key: RsaKey
    public_key: RsaKey

    def __init__(self):
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
    CryptoHandler()

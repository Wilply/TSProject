import hashlib
import socket
from base64 import b64decode, b64encode

from Crypto.PublicKey.RSA import RsaKey
from func_timeout import func_set_timeout, FunctionTimedOut

from Node.ClientNetworking import ThrClientManagementRequestHandler
from Node.CryptoHandler import CryptoHandler
from Node.Utils import Singleton


class ClientDisconnected(Exception):
    pass


class Client:
    client_identity: str
    # noinspection PyCallByClass,PyCallByClass
    crypto_handler: CryptoHandler = Singleton.Instance(CryptoHandler)

    def __init__(self, comm_handler: ThrClientManagementRequestHandler):
        self.comm_handler: ThrClientManagementRequestHandler = comm_handler
        self.client_address = comm_handler.client_address
        self.client_identity = ""
        self.client_key_str = None
        self.client_key = None
        self.session_key = None

        # Envoi de la bannière de bienvenue
        self.send("WELCOME TSProject node, listening", is_encrypted=False)

        # Envoi de la clé publique du serveur
        self.send("SERVER-KEY " + Client.crypto_handler.str_public_key, is_encrypted=False)

        # Envoi de l'authenticator
        self.send("SERVER-AUTH " + self.crypto_handler.get_authenticator(), is_encrypted=False)

        # Lancement de la phase de négociation de clé de session. Timeout de 5 sec
        try:
            self.client_crypto_exchange()
        except (Exception, FunctionTimedOut):
            self.close("error during session encryption key exchange")

        # A partir de ce point, tous les échanges sont chiffrés avec la clé de session

        # Lancement de la phase d'authentification du client. Timeout de 5 sec
        try:
            self.client_auth()
        # except (Exception, FunctionTimedOut):
        except FunctionTimedOut:
            self.close("client authentication timed out")

        # Lancement de la boucle d'écoute des commandes client
        self.main_loop()

    @func_set_timeout(5)
    def client_crypto_exchange(self):
        while True:
            data = self.listen_wait(False).decode()
            if data.split()[0] == "SESSION-KEY":
                break
            else:
                self.send("SESSION-NEEDED Please send session key", True, False)
        self.session_key = self.crypto_handler.decrypt_rsa(b64decode(data.split()[1]))
        print("Session key : " + str(b64encode(self.session_key)))
        self.send("SESSION-OK Session key exchange successful", is_encrypted=False)

    @func_set_timeout(5)
    def client_auth(self):
        # On attend que le client envoie ses infos d'authentification
        while True:
            data = self.listen_wait().decode()
            if data.split()[0] == "CLIENT-KEY":
                break
            else:
                self.send("KEY-NEEDED Please send public key", True)

        self.client_key_str = data.split()[1]
        self.client_key: RsaKey = self.crypto_handler.to_rsa(self.client_key_str)

        while True:
            data = self.listen_wait().decode()
            if data.split()[0] == "CLIENT-AUTH":
                break
            else:
                self.send("AUTH-NEEDED Please auth", True)

        client_authenticator = data.split()[1]

        # Si le client est bien qui il prétend être
        if self.crypto_handler.check_authenticator(self.client_key, client_authenticator):
            self.client_identity: str = hashlib.sha1(self.client_key.export_key(format="DER")).hexdigest()
            self.comm_handler.client_identity = self.client_identity
            self.send("AUTH-OK Successfully authenticated, welcome " + self.client_identity)
            self.print_debug("authenticated")
        else:
            self.send("AUTH-ERROR Authentication error, wrong identity. Closing.")
            raise Exception

    def do_hello(self, data):
        self.send("Hello user ! You said " + data)

    def do_whoami(self, data):
        self.send("You are " + self.client_identity)

    def do_quit(self, data):
        pass

    def do_unknown_command(self):
        self.send("Unknown command", True)

    def main_loop(self):

        function_switcher = {
            "hello": self.do_hello,
            "whoami": self.do_whoami,
            "quit": self.do_quit,
        }
        while True:
            data = self.listen_wait().decode()
            # On redirige vers la fonction correspondant à la commande
            main_command = data.split()[0]
            function_call = function_switcher.get(main_command)
            if function_call:
                function_call(data)
            else:
                self.do_unknown_command()

    def listen_wait(self, is_encrypted: bool = True) -> bytes:
        try:
            while True:
                # On attend que le client envoie quelque chose et on renvoie cette valeur
                data: bytes = self.comm_handler.receive()
                # Si le socket n'envoie plus rien, alors le client est déconnecté
                if not data or data == "":
                    self.close("client left")
                # Si la donnée reçue n'est pas un keepalive, on process (sinon on recommence la boucle)
                if data != b"keepalive":
                    # Si on s'attend à des données chiffrées, alors on les déchiffre avec clé de session et un décode
                    # base64
                    if is_encrypted:
                        data: bytes = self.crypto_handler.decrypt(data, self.session_key)
                        print(str(self) + " (E) -> " + str(data))
                    else:
                        print(str(self) + " -> " + str(data))
                    break
            return data
        # Si le socket timeout alors on ferme la connexion
        except socket.timeout:
            self.close("timed out")
        except ValueError:
            self.close("encryption error, received cleartext data while expecting encrytion")
        # except OSError:
        #     pass

    def send(self, data, is_error: bool = False, is_encrypted: bool = True):
        code: bytes = b"OK" if not is_error else b"ERR"
        if type(data) == str:
            data = data.encode()
        prefixed_data: bytes = code + b" " + data

        if is_encrypted:
            print(str(self) + " (E) <- " + str(prefixed_data))
            prefixed_data = (self.crypto_handler.encrypt(prefixed_data, self.session_key))
        else:
            print(str(self) + " <- " + str(prefixed_data))

        self.comm_handler.send(prefixed_data)

    def close(self, message: str = "unkown"):
        self.print_debug("connection closed  (" + message + ")")
        raise ClientDisconnected

    def print_debug(self, msg: str):
        print(str(self) + " : " + msg)

    def __str__(self):
        return str(self.client_identity) if self.client_identity else str(self.client_address)

import hashlib
import threading

from Crypto.PublicKey.RSA import RsaKey
from timeout_decorator import timeout_decorator

from Node.ClientNetworking import ThrClientManagementRequestHandler
from Node.CryptoHandler import CryptoHandler
from Node.Utils import Singleton


class ClientDisconnected(Exception):
    pass


class ClientAuthError(Exception):
    pass


class ClientAuthTimeout(Exception):
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

        # Envoi de la bannière de bienvenue
        self.comm_handler.send("WELCOME TSProject node, listening")

        # Envoi de la clé publique du serveur
        self.comm_handler.send("SERVER-KEY " + Client.crypto_handler.str_public_key)

        # Envoi de l'authenticator
        self.comm_handler.send("SERVER-AUTH " + self.crypto_handler.get_authenticator())

        # Lancement de la phase d'authentification du client. Il a 10 secondes pour s'authentifier,
        # au dela desquelles la connexion est fermée
        try:
            self.client_auth()
        except Exception:
            raise ClientAuthError

        # Démarrage boucle d'écoute une fois le client authentifié
        while True:
            data = self.listen_wait()
            # On redirige vers la fonction correspondant à la commande
            main_command = data.split()[0]
            function_call = self.function_switcher.get(main_command)
            if function_call:
                function_call(self, data)
            else:
                self.do_unknown_command()

    # TODO envoyer les infos du client en les chiffrant avec la pubkey du serveur
    @timeout_decorator.timeout(10, use_signals=False, timeout_exception=ClientAuthTimeout)
    def client_auth(self):
        # On attend que le client envoie ses infos d'authentification
        while True:
            data = self.listen_wait()
            if data.split()[0] == "CLIENT-KEY":
                break
            else:
                self.comm_handler.send("KEY-NEEDED Please send public key", True)

        self.client_key_str = data.split()[1]
        self.client_key: RsaKey = self.crypto_handler.to_rsa(self.client_key_str)

        while True:
            data = self.listen_wait()
            if data.split()[0] == "CLIENT-AUTH":
                break
            else:
                self.comm_handler.send("AUTH-NEEDED Please auth", True)

        client_authenticator = data.split()[1]

        # Si le client est bien qui il prétend être
        if self.crypto_handler.check_authenticator(self.client_key, client_authenticator):
            self.comm_handler.send("AUTH-OK Successfully authenticated, welcome")
            self.client_identity: str = hashlib.sha1(self.client_key.export_key(format="DER")).hexdigest()
            self.print_debug("authenticated")
        else:
            raise Exception

    def listen_wait(self) -> str:
        try:
            # On attend que le client envoie quelque chose et on renvoie cette valeur
            data: str = self.comm_handler.receive()
            if not data or data == "":
                raise ClientDisconnected()
            return data
        except OSError:
            pass

    def print_debug(self, msg: str):
        print(str(self) + " : " + msg)

    def do_hello(self, data):
        self.comm_handler.send("Hello user ! You said " + data)

    def do_unknown_command(self):
        self.comm_handler.send("Unknown command", True)

    def do_quit(self, data):
        pass

    def __str__(self):
        return "Client " + str(threading.currentThread().getName()) + " " + str(
            self.client_address) + " " + self.client_identity

    function_switcher = {
        "hello": do_hello,
        "quit": do_quit
    }

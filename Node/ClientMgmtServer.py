import socketserver
import threading

import time

from Node.CryptoHandler import CryptoHandler


class ThrClientManagementRequestHandler(socketserver.BaseRequestHandler):
    def send_text(self, data_string):
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " <- " + data_string)
        self.request.send(data_string.encode())

    def do_unknown_command(self, data_string):
        self.send_text("ERR Unkowwn_command")

    def do_hello(self, data_string):
        self.send_text("OK Hello")

    def do_quit(self, data_string):
        self.send_text("OK Quit")
        self.request.close()
        print(str(threading.currentThread().getName()) + " " + str(
            self.client_address) + " has left the server.")
        return


    # Attribut de classe (dictionnaire) indiquant la fonction à appeler selon la commande envoyée par le client
    switcher = {
        "hello": do_hello,
        "quit": do_quit,
    }

    # Point d'entrée de chaque connexion client établie
    def handle(self):
        # Un nouveau client est connecté :
        print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " connected.")
        while True:
            try:
                data = self.request.recv(1024)
                # On process les données reçues par le client
                if data:
                    data_string = data.decode("utf-8").replace("\r\n", "")
                    print(str(threading.currentThread().getName()) + " " + str(
                        self.client_address) + " -> " + data_string)
                    # On appelle la fonction associée à la commande par le dictionnaire switcher
                    # Si la commande est inconnue, on appelle do_unkown_command
                    function_call = self.switcher.get(data_string)
                    if function_call:
                        function_call(self, data_string)
                    else:
                        self.do_unknown_command(data_string)
                else:
                    self.request.close()
                    print(str(threading.currentThread().getName()) + " " + str(
                        self.client_address) + " has unexpectedly stopped the connection.")
                    return
            except OSError:
                pass


class ThrClientManagementServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    # Starting Client Management server
    address = ('localhost', 37405)
    server = ThrClientManagementServer(address, ThrClientManagementRequestHandler)
    print("Server launched : " + str(server.server_address))
    serverThread = threading.Thread(target=server.serve_forever)
    serverThread.setDaemon(True)
    serverThread.start()
    print("Server running in " + serverThread.getName())
    while True:
        input("")

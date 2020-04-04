from Node.ClientNetworking import ThrClientManagementRequestHandler


class Client:
    def __init__(self, comm_handler: ThrClientManagementRequestHandler):
        self.comm_handler = comm_handler
        self.address = comm_handler.client_address

    def do_hello(self, data):
        self.comm_handler.send("Hello user ! You said "+data)

    def do_unkown_command(self, data):
        self.comm_handler.send("Unknown command", True)

    def do_quit(self):
        self.comm_handler.close()

    function_switcher = {
        "hello": do_hello
    }

    def process_request(self, data: str):
        # Appel de la fonction correspondant à la commande utilisateur
        main_command = data.split()[0]
        function_call = self.function_switcher.get(main_command)
        if function_call:
            function_call(self, data)
        else:
            self.do_unkown_command(data)
        return

# def send_text(self, data_string):
#     print(str(threading.currentThread().getName()) + " " + str(self.client_address) + " <- " + data_string)
#     self.request.send(data_string.encode())
#
# def do_unknown_command(self, data_string):
#     self.send_text("ERR Unkowwn_command")
#
# def do_hello(self, data_string):
#     self.send_text("OK Hello")
#
# def do_quit(self, data_string):
#     self.send_text("OK Quit")
#     self.request.close()
#     print(str(threading.currentThread().getName()) + " " + str(
#         self.client_address) + " has left the server.")
#     return
#
# # Attribut de classe (dictionnaire) indiquant la fonction à appeler selon la commande envoyée par le client
# switcher = {
#     "hello": do_hello,
#     "quit": do_quit,
# }

# data_string = data.decode("utf-8").replace("\r\n", "")
# print(str(threading.currentThread().getName()) + " " + str(
#     self.client_address) + " -> " + data_string)
# # On appelle la fonction associée à la commande par le dictionnaire switcher
# # Si la commande est inconnue, on appelle do_unkown_command
# function_call = self.switcher.get(data_string)
# if function_call:
#     function_call(self, data_string)
# else:
#     self.do_unknown_command(data_string)

from ClientMgmtServer import ThrClientManagementServer, ThrClientManagementRequestHandler
import threading


class Prompt:
    def __init__(self):
        while True:
            cmd = input("> ")
            if cmd == "hello":
                self.hello()
            elif cmd == "exit":
                self.exit()
            elif cmd == "list":
                self.list()

    def hello(self):
        print("hello too")

    def list(self):
        print("WIP")

    def exit(self):
        print("Exiting TSPCHAT...")
        raise SystemExit


if __name__ == '__main__':
    # Starting Client Management server
    # address = ('localhost', 8085)
    # server = ThrClientManagementServer(address, ThrClientManagementRequestHandler)
    # print("Server launched : " + str(server.server_address))
    # serverThread = threading.Thread(target=server.serve_forever)
    # serverThread.setDaemon(True)
    # serverThread.start()
    # print("Server running in " + serverThread.getName())

    Prompt()

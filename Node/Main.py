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
    Prompt()

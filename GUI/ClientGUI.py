
from PyQt5.QtWidgets import QMainWindow,QApplication,QListWidget,QPushButton,QVBoxLayout,QHBoxLayout,QMessageBox,QWidget,QLabel,QLineEdit
import socket
import pickle
import select
import struct
import sys
import threading
import datetime


class nameEnter(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('Welcome!')
        self.setMinimumSize(400,300)
        nameLabel = QLabel("Enter your name: ")
        self.nameField = QLineEdit()
        namePanel = QHBoxLayout()
        namePanel.addWidget(nameLabel)
        namePanel.addWidget(self.nameField)
        nameWidget = QWidget()
        nameWidget.setLayout(namePanel)
        connectButton = QPushButton("Connect")
        panel = QVBoxLayout()
        panel.addWidget(nameWidget)
        panel.addWidget(connectButton)
        panelWidget = QWidget()
        panelWidget.setLayout(panel)
        connectButton.clicked.connect(self.openChannel)
        self.setCentralWidget(panelWidget)

    def openChannel(self):
        username = self.nameField.text()
        global client
        client = clientConnection(username)
        client.show()
        self.close()




class clientConnection(QMainWindow):
    def __init__(self,name):
        QMainWindow.__init__(self)
        self.name = name
        self.setWindowTitle('Chat')
        self.setMinimumSize(1200,800)
        self.messages = QListWidget()
        self.messages.setMinimumSize(800,600)
        self.participants = QListWidget()
        self.participants.setMinimumSize(300,600)
        self.input = QLineEdit()
        self.sendButton = QPushButton('Send')
        self.quitButton = QPushButton('Quit')
        listPanel = QHBoxLayout()
        listPanel.addWidget(self.messages)
        listPanel.addWidget(self.participants)
        listWidget = QWidget()
        listWidget.setLayout(listPanel)
        downPanel = QVBoxLayout()
        downPanel.addWidget(self.input)
        downPanel.addWidget(self.sendButton)
        downPanel.addWidget(self.quitButton)
        downWidget = QWidget()
        downWidget.setLayout(downPanel)
        panel = QVBoxLayout()
        panel.addWidget(listWidget)
        panel.addWidget(downWidget)
        panelWidget = QWidget()
        panelWidget.setLayout(panel)
        self.sendButton.clicked.connect(self.sendMessage)
        self.quitButton.clicked.connect(self.quitChannel)
        self.setCentralWidget(panelWidget)
        self.initConnection()


    def initConnection(self):
        self.tcp_socket = socket.socket()
        self.tcp_socket.connect(('127.0.0.1', 10000))

        number_of_clients = struct.unpack("!I", self.tcp_socket.recv(4))[0]
        self.other_clients = set()
        for _ in range(number_of_clients):
            clientrecv = self.tcp_socket.recv(4094)
            client = pickle.loads(clientrecv)
            self.other_clients.add(client)
            self.tcp_socket.send(b'S')
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.udp_socket.sendto(b'random', ('8.8.8.8', 2355))

        _, udp_port = self.udp_socket.getsockname()

        me = (self.name, '', udp_port)
        new_me = pickle.dumps(me)
        self.tcp_socket.sendall(new_me)
        self.messages.addItem('Welcome, ' + self.name +'!')
        self.populateParticipants()
        threading.Thread(target=self.communication, daemon=True).start()

    def communication(self):
        try:
            while True:
                sockets, _, _ = select.select([self.tcp_socket, self.udp_socket], [], [])
                if self.tcp_socket in sockets:
                    operation = self.tcp_socket.recv(1)
                    if operation == b'/':
                        self.messages.addItem("You have been disconnected")
                        self.sendButton.blockSignals(True)
                        return
                    new_client = pickle.loads(self.tcp_socket.recv(1024))
                    if operation == b'N':
                        self.messages.addItem('['+ str(datetime.datetime.now().strftime('%X'))+ '] '+new_client[0]+' has connected to the chat')
                        self.other_clients.add(new_client)
                        self.populateParticipants()
                    elif operation == b'L':
                        self.messages.addItem('['+ str(datetime.datetime.now().strftime('%X'))+ '] '+new_client[0] +' has left the chat')
                        self.other_clients.discard(new_client)
                        self.populateParticipants()
                    else:
                        print('Unknown operation received')

                if self.udp_socket in sockets:
                    message = pickle.loads(self.udp_socket.recv(256))
                    self.messages.addItem('['+ str(datetime.datetime.now().strftime('%X'))+ '] '+ message[0] +': '+ message[1])
        except OSError as o:
            self.tcp_socket.close()
            self.udp_socket.close()
            print(o)


    def sendMessage(self):

        for other_client in self.other_clients:
            package = (self.name, self.input.text())
            package_send = pickle.dumps(package)
            self.udp_socket.sendto(package_send, (other_client[1], other_client[2]))
        self.messages.addItem(
            '[' + str(datetime.datetime.now().strftime('%X')) + '] ' + 'You ' + ': ' + self.input.text())
        self.input.clear()

    def quitChannel(self):
        self.tcp_socket.send(b'L')
        self.close()

    def closeEvent(self, event):
        self.quitChannel()
        event.accept()

    def populateParticipants(self):
        self.participants.clear()
        for client in self.other_clients:
            self.participants.addItem(client[0])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    nameWindow = nameEnter()
    nameWindow.show()
    app.exec_()
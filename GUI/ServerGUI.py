import datetime

from PyQt5.QtWidgets import QMainWindow,QApplication,QListWidget,QPushButton,QVBoxLayout,QHBoxLayout,QMessageBox,QWidget
import socket
import pickle
import select
import struct
import sys
import threading

class ServerWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('Server')
        self.setMinimumSize(1000,600)
        self.logs = QListWidget()
        self.participants = QListWidget()
        self.exitButton = QPushButton('Quit')
        self.startButton = QPushButton('Start')
        self.connected = 1
        panel = QVBoxLayout()
        logsPanel = QHBoxLayout()
        buttonPanel = QHBoxLayout()
        logsPanel.addWidget(self.logs)
        logsPanel.addWidget(self.participants)
        buttonPanel.addWidget(self.startButton)
        buttonPanel.addWidget(self.exitButton)
        logWidget = QWidget()
        logWidget.setLayout(logsPanel)
        buttonWidget = QWidget()
        buttonWidget.setLayout(buttonPanel)
        panel.addWidget(logWidget)
        panel.addWidget(buttonWidget)
        self.startButton.clicked.connect(self.startServer)
        self.exitButton.clicked.connect(self.quitServer)
        panelWidget = QWidget()
        panelWidget.setLayout(panel)

        self.setCentralWidget(panelWidget)


    def startServer(self):
        if self.connected == 0:
            global s
            s = QMessageBox()
            s.setText("Server already running!")
            s.show()
            return
        self.logs.addItem('[' + datetime.datetime.now().strftime('%X')+'] ' +' Server starting...')
        threading.Thread(target=self.serverConnection,daemon=True).start()
        self.connected = 0


    def serverConnection(self):

       try:
        self.listening_sock = socket.create_server(('', 10000))
        self.listening_sock.listen()
        self.clients = {}
        self.select_sockets_list = [self.listening_sock]

        while True:

            slist, _, _ = select.select(self.select_sockets_list, [], [])
            for sock in slist:
                if sock == self.listening_sock:
                    client_socket, (client_ip, _) = self.listening_sock.accept()
                    client_socket.sendall(struct.pack("!I", len(self.clients)))
                    for client in self.clients:
                        client_data = self.clients[client]
                        client_sending = pickle.dumps(client_data)
                        client_socket.sendall(client_sending)
                        if client_socket.recv(1) == b'S':
                            self.logs.addItem('[' + str(datetime.datetime.now().strftime('%X')) + '] '+" Client " + str(client_ip) + ' received participant '+ str(client_data[1]) +" "+ str(client_data[2]))
                        else:
                            self.logs.addItem('[' + datetime.datetime.now().strftime('%X')+']' + " Client " + str(client_ip) + ' failed to received participant ' + str(client_data[1]) +' ' + str(client_data[2]))

                    new_client = pickle.loads(client_socket.recv(1024))
                    self.logs.addItem('[' + datetime.datetime.now().strftime('%X')+']' +" New client connected " + str(new_client[0]) +" "+ str(client_ip))

                    for other_client_socket in self.clients:
                        other_client_socket.send(b'N')
                        client_send = (new_client[0], client_ip, new_client[2])
                        client_sending = pickle.dumps(client_send)
                        other_client_socket.sendall(client_sending)

                    good_client = (new_client[0], client_ip, new_client[2])
                    self.clients[client_socket] = good_client
                    self.select_sockets_list.append(client_socket)
                    self.updateParticipants()

                else:
                    operation = sock.recv(1)
                    if operation == b'L':
                        print("Client is leaving...")
                        sock.close()
                        deleted_client = self.clients[sock]
                        del self.clients[sock]
                        self.select_sockets_list.remove(sock)

                        for other_client_socket in self.clients:
                            other_client_socket.send(b'L')
                            deleted_client_send = pickle.dumps(deleted_client)
                            other_client_socket.send(deleted_client_send)
       except OSError as oe:
           print(oe)


    def quitServer(self):
        if self.connected == 1:
            global b
            b = QMessageBox()
            b.setText("The server isn't running!")
            b.show()
            return
        for other_client_socket in self.clients:
            other_client_socket.send(b'/')
        self.connected = 1
        self.listening_sock.close()
        self.logs.addItem('[' + datetime.datetime.now().strftime('%X')+']'+" Server closing...")


    def updateParticipants(self):
        self.participants.clear()
        for client in self.clients:
            client_data = self.clients[client]
            self.participants.addItem(str(client_data[1]) +" " + str(client_data[2]))



    def closeEvent(self, event):
        if self.connected == 1:
            self.quitServer()
        event.accept()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    serverWindow = ServerWindow()
    serverWindow.show()
    app.exec_()



import socket
from _thread import *
from threading import Event
import sys
import re

DEFAULT_PORT = 5555
LOCALHOST = "127.0.0.1"

class GameNet:
    def __init__(self, role, port=DEFAULT_PORT, server_ip=LOCALHOST):
        self.role = role
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.state='idle'
        try:
            if role=='server':
                addr = (LOCALHOST, port) # for server side, IP is localhost
                self.socket.bind(addr)
                self.socket.listen(2)
                start_new_thread(self.thread_server, ())
            else:
                print(f"Trying to connect to {server_ip}:{port}...")
                addr = (server_ip, port)
                self.socket.connect(addr)
                start_new_thread(self.thread_worker, (self.socket,))
        except socket.error as e: print(e)

    def thread_server(self):
        print("Waiting for a connection, Server Started")
        while True:
            conn, addr = self.socket.accept()
            print("Connected to:", addr)
            start_new_thread(self.thread_worker, (conn,))
            # exit here if only allow one client connected

    def thread_worker(self, conn):
        self.state='connected'
        event=Event()
        print(f"{self.role} side connected")
        counter=0
        conn.send(str.encode(f"{self.role} sending {counter}\n"))
        while True:
            counter+=1
            try:
                recv_data = conn.recv(2048).decode("utf-8")
                if recv_data:
                    print("Received: ", recv_data)
                    event.wait(1)
                    conn.sendall(str.encode(f"{self.role} sending {counter}\n"))
                #else: print("Disconnected"); break
            except Exception as e:
                print(e)
                break
        print("Lost connection")
        conn.close()
        self.state='disconnected'

if __name__ == "__main__":
    argc = len(sys.argv)
    #print(f"Arguments count: {argc}")
    server_ip = LOCALHOST
    port = DEFAULT_PORT
    if argc<2:
        print(f"Need less one argument like:  (s|c) [[server_ip:]port]\n\tDefault sever_ip: 127.0.0.1\n\tDefault port: {DEFAULT_PORT}")
        sys.exit(1)
    elif argc>2:
        m = re.match(r'(([^:]+):)?(\d+)', sys.argv[2])
        if m!=None:
            if m.group(1)!='': server_ip=m.group(2)
            ip = m.group(3)
    if sys.argv[1]=='s': session=GameNet('server', port)
    else: session=GameNet('client', port, server_ip)
    while(session.state!='disconnected'): pass
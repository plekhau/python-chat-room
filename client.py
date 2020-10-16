"""
Create client socket and connect to server socket.
Just receives and sends messages

Start:
- for connecting to localhost:     python client.py
- for connecting to remote host:   python client.py ip_address port

See server documentation for details about chat features
"""

import select
import socket
import sys
from time import sleep
import common


def start_client():
    """
    Create client socket and connect to server socket.
    Just receives and sends messages
    """
    if len(sys.argv) == 3:
        host = str(sys.argv[1])
        port = int(sys.argv[2])
    else:
        host = "localhost"
        port = common.DEFAULT_PORT

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print("Failed to create socket", flush=True)
        sys.exit()

    try:
        remote_ip = socket.gethostbyname(host)
    except socket.gaierror:
        print("Hostname could not be resolved. Exiting", flush=True)
        sys.exit()

    client_socket.connect((remote_ip, port))

    print("Socket Connected to {} on ip {}".format(host, remote_ip), flush=True)

    while True:
        sockets_list = [client_socket]
        read_sockets, _, _ = select.select(sockets_list, [], [], 1)

        try:
            for socks in read_sockets:
                if socks == client_socket:
                    message = socks.recv(common.BUFFER_SIZE).decode()
                    print(message, flush=True)

            message = sys.stdin.readline().strip()
            if message:
                client_socket.sendall(message.encode())
                sleep(0.1)
        except ConnectionError:
            print("You were disconnected.", flush=True)
            break

    client_socket.close()


if __name__ == "__main__":
    start_client()

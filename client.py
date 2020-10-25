"""
Create client socket and connect to server socket.
Just receives and sends messages

Start:
- for connecting to localhost:     python client.py
- for connecting to remote host:   python client.py ip_address port

See server documentation for details about chat features
"""
import logging.config
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
    logger = logging.getLogger('chat_logger')

    if len(sys.argv) == 3:
        host = str(sys.argv[1])
        port = int(sys.argv[2])
    else:
        host = "localhost"
        port = common.DEFAULT_PORT

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        logger.error("Failed to create socket")
        sys.exit()

    try:
        remote_ip = socket.gethostbyname(host)
    except socket.gaierror:
        logger.error("Hostname could not be resolved. Exiting")
        sys.exit()

    client_socket.connect((remote_ip, port))

    logger.info("Socket Connected to {} on ip {}".format(host, remote_ip))

    while True:
        sockets_list = [client_socket]
        read_sockets, _, _ = select.select(sockets_list, [], [], 1)

        try:
            for socks in read_sockets:
                if socks == client_socket:
                    message = socks.recv(common.BUFFER_SIZE).decode()
                    logger.info(message)

            message = sys.stdin.readline().strip()
            if message:
                client_socket.sendall(message.encode())
                sleep(0.1)
        except ConnectionError:
            logger.warning("You were disconnected.")
            break

    client_socket.close()


if __name__ == "__main__":
    start_client()

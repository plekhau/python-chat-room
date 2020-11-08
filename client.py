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
import asyncio
from concurrent.futures import FIRST_COMPLETED
from aioconsole import ainput
import common

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
logger = logging.getLogger('chat_logger')


async def receiving_messages(loop):
    """
    Receiving messages from server
    """
    while True:
        try:
            read_sockets, _, _ = select.select([client_socket], [], [], 1)

            for socks in read_sockets:
                if socks == client_socket:
                    # message = socks.recv(common.BUFFER_SIZE).decode().strip()
                    message = (await loop.sock_recv(socks, common.BUFFER_SIZE)).decode().strip()
                    logger.info(message)
            await asyncio.sleep(0.03)
        except ConnectionError:
            logger.warning("You were disconnected.")
            break


async def sending_messages(loop):
    """
    Get message from console input and send it to server
    """
    while True:
        message = (await ainput()).strip()
        if message:
            try:
                await loop.sock_sendall(client_socket, message.encode())
            except ConnectionError:
                logger.warning("You were disconnected.")
                break


def process_messages():
    """
    Run receiving/sending messages using asyncio
    """
    loop = asyncio.get_event_loop()
    tasks = [receiving_messages(loop), sending_messages(loop)]
    loop.run_until_complete(asyncio.wait(tasks, return_when=FIRST_COMPLETED))


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
        remote_ip = socket.gethostbyname(host)
    except socket.gaierror:
        logger.error("Hostname could not be resolved. Exiting")
        sys.exit()

    client_socket.connect((remote_ip, port))

    logger.info("Socket Connected to {} on ip {}".format(host, remote_ip))

    process_messages()

    client_socket.close()


if __name__ == "__main__":
    start_client()

"""
Create server socket and start endless loop with checking client socket responses

Start:
- for connecting to localhost:     python server.py
- for connecting to remote host:   python server.py ip_address port

Features:
- All users have unique name
- User can get the last chat messages by sending any message or pressing Enter
- Users can send public message just typing any text
- Users can send private message, i.e [recipient] message
- Users can interact with server, i.e. [server] command
- List of server commands:
    [server] help                   - info about chat
    [server] participants           - return list of chat participants
    [server] participants-count     - return count of chat participants
    [server] rock-paper-scissors    - play rock-paper-scissors game with server
    [server] 21                     - play 21 game with server
    [server] quiz                   - quiz game for all participants
"""
import select
import socket
from typing import Optional, Tuple
import logging.config
import common
from games.game_21 import one_player_game_21
from games.game_quiz import all_players_game_quiz
from games.game_rock_paper_scissors import one_player_game_rock_paper_scissors

logger = logging.getLogger('chat_logger')


def split_message(msg: str) -> Tuple[Optional[str], str]:
    """
    Split message from socket if it has format "[recipient] command"
    Otherwise, return whole message as command

    :param msg: str, message from socket to server
    :return: tuple, (recipient, command)
    """
    if msg[0] == "[" and "]" in msg:
        pos = msg.find("]")
        recipient = msg[1:pos].strip()
        cmd = msg[pos + 1:].strip()
        return recipient, cmd
    return None, msg


def process_message_to_server(sock: socket.socket, cmd: str):
    """
    Process commands like '[server] <command>'

    :param sock: socket
    :param cmd: str, command that can be processed, see help command for details
    :return: None
    """
    if cmd == "help":
        about_chat = """To send a public message: just send any text.
        To send private message: [<username>] <your message>
        To send message to server: [server] command
        Server supports the following commands:
        [server] help - info about chat
        [server] participants - return list of chat participants
        [server] participants-count - return count of chat participants
        [server] rock-paper-scissors - play rock-paper-scissors game with server
        [server] 21 - play 21 game with server
        [server] quiz - quiz game for all participants"""
        common.private_message(common.server_socket, sock, about_chat)
    elif cmd == "participants":
        participants = list(common.sockets_list.values())
        participants.remove(common.sockets_list[common.server_socket])
        common.private_message(common.server_socket, sock, "List of participants: {}".format(", ".join(participants)))
    elif cmd == "participants-count":
        common.private_message(common.server_socket, sock, "Participants count: {}"
                               .format(len(common.sockets_list.values()) - 1))
    elif cmd == "rock-paper-scissors":
        one_player_game_rock_paper_scissors(sock, common.INIT_GAME_MSG)
    elif cmd == "21":
        one_player_game_21(sock, common.INIT_GAME_MSG)
    elif cmd == "quiz":
        all_players_game_quiz(None, common.INIT_GAME_MSG)
    else:
        common.private_message(common.server_socket, sock, "Unknown command")


def process_message(sock: socket.socket, msg: str):
    """
    Common function for processing message from socket

    :param sock: socket, socket-sender
    :param msg: str, message from socket
    :return: None
    """
    try:
        if common.all_player_game:
            common.all_player_game["game"](sock, msg)
        elif sock in common.one_player_game_list:
            common.one_player_game_list[sock]["game"](sock, msg)
        else:
            recipient, cmd = split_message(msg)
            if recipient is None:
                common.send_to_all("[{}] {}".format(common.sockets_list[sock], cmd), sock)
            else:
                recipient_socket = common.get_socket_by_name(recipient)
                msg = "[{}] -> [{}] {}".format(common.sockets_list[sock], recipient, cmd)
                logger.info(msg)

                if recipient_socket is None:
                    common.send_to_one(sock, "Unknown recipient. Please try again.")
                elif recipient == common.sockets_list[common.server_socket]:
                    process_message_to_server(sock, cmd)
                else:
                    # Private message from client to client
                    common.send_to_one(recipient_socket, msg)
    except Exception as ex:
        logger.error("Something goes wrong:(\n{}".format(ex))


def start_server():
    """
    Create server socket and start endless loop with checking client socket responses
    """
    common.create_server_socket()

    while True:
        read_sockets, _, _ = select.select(common.sockets_list.keys(), [], [])

        for read_socket in read_sockets:
            if read_socket == common.server_socket:
                client_socket, _ = read_socket.accept()
                common.sockets_list[client_socket] = ""
                common.send_to_one(client_socket, "Hi! You are trying to connect to chat room.\nWhat is your name?")
            else:
                try:
                    message = read_socket.recv(common.BUFFER_SIZE).decode()
                    if not message:
                        raise ConnectionError
                    if not common.sockets_list[read_socket]:
                        common.user_registration(read_socket, message)
                    else:
                        process_message(read_socket, message)
                except ConnectionError:
                    username = common.sockets_list.pop(read_socket)
                    if username == "":
                        logger.info("Unknown user was disconnected")
                    else:
                        common.send_to_all("User '{}' was disconnected".format(username))


if __name__ == "__main__":
    start_server()

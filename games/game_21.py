"""
21: one player game with server
"""
import random
import socket
from typing import Tuple
import common


def init_new_game(sock: socket.socket):
    """
    Initialization game parameters, send rules to user

    :param sock: socket, client socket that is playing game
    :return: None
    """
    common.private_message(common.server_socket, sock,
                           "Let's play 21!\nYou and server will throw numbers from 0 to 10 and calculate them.\n"
                           "Your goal: score as much as possible, but not more than 21.\n"
                           "Throwing out for you (need to send: number from 0 to 10 or 'stop')")
    common.one_player_game_list[sock] = {"game": one_player_game_21,
                                         "status": "throwing_for_player",
                                         "player": 0,
                                         "server": 0}


def server_choice(player_score: int, server_score: int, is_throwing_for_player: bool) -> int:
    """
    Generate server choice according to current game state
    TODO: the easiest logic is implemented, need to do it smarter

    :param player_score: player score before current round
    :param server_score: server score before current round
    :param is_throwing_for_player:
    :return:
    """
    if is_throwing_for_player:
        server = random.randint(0, 10) if player_score < 12 else 10
    else:
        server = random.randint(0, 10) if server_score < 11 else random.choice([0, 8, 9, 10])
    return server


def one_round(sock: socket.socket, msg: str) -> Tuple[int, int, int, int]:
    """
    One round:
        - get current scores
        - get player choice and calculate server choice
        - save scores

    :param sock: socket, client socket that is playing game
    :param msg: str, client choice (numbers [0..10])
    :return: (int, int, int, int) - player and server choices, player and server scores
    """
    player_score = common.one_player_game_list[sock]["player"]
    server_score = common.one_player_game_list[sock]["server"]
    player = int(msg)
    is_throwing_for_player = common.one_player_game_list[sock]["status"] == "throwing_for_player"
    server = server_choice(player_score, server_score, is_throwing_for_player)
    if is_throwing_for_player:
        player_score += player + server
    else:
        server_score += player + server
    common.one_player_game_list[sock]["player"] = player_score
    common.one_player_game_list[sock]["server"] = server_score
    return player, server, player_score, server_score


def round_response(sock: socket.socket, player: int, server: int, player_score: int, server_score: int) -> str:
    """
    Generate round response. Remove current game if it is finished

    :param sock: socket, client socket that is playing game
    :param player: int, player choice in current round
    :param server: int, server choice in current round
    :param player_score: player score after current round
    :param server_score: server score after current round
    :return: str, round response that will send to client
    """
    response = "You thrown {}, server thrown {}. Total: you - {}, server - {}\n" \
        .format(player, server, player_score, server_score)
    if common.one_player_game_list[sock]["status"] == "throwing_for_player":
        if player_score < 21:
            response += "Throwing out for you (need to send: number from 0 to 10 or 'stop')"
        else:
            response += "Wow! BlackJack! You won!" if player_score == 21 else "You took more 21! You lost!"
            common.one_player_game_list.pop(sock)
    else:
        if server_score <= player_score and server_score <= 11:
            response += "Throwing out for server (need to send: number from 0 to 10)"
        else:
            if server_score > 21:
                response += "Server took more 21! You won!"
            elif server_score > player_score:
                response += "Server won!"
            elif server_score == player_score:
                response += "No winner!"
            else:
                response += "You won!"
            common.one_player_game_list.pop(sock)
    return response


def one_player_game_21(sock: socket.socket, msg: str):
    """
    Game: 21

    :param sock: socket, client socket that is playing game
    :param msg: str, client choice (numbers [0..10] or stop)
    :return: None
    """
    if msg == common.INIT_GAME_MSG:
        init_new_game(sock)
    else:
        if "stop" in msg and common.one_player_game_list[sock]["status"] == "throwing_for_player":
            common.one_player_game_list[sock]["status"] = "throwing_for_server"
            response = "Throwing out for server (need to send: number from 0 to 10)"
        else:
            if msg.isdigit() and int(msg) < 11:
                player, server, player_score, server_score = one_round(sock, msg)
                response = round_response(sock, player, server, player_score, server_score)
            else:
                response = "You sent incorrect value. Please try again."
        common.private_message(common.server_socket, sock, response)

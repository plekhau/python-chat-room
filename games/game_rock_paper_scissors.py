import random
import socket
import common

reductions = {"r": "rock", "p": "paper", "s": "scissors"}
win_msg = "You won!"
lose_msg = "Server won!"
rules = {"rs": win_msg, "rp": lose_msg,
         "pr": win_msg, "ps": lose_msg,
         "sp": win_msg, "sr": lose_msg}


def one_player_game_rock_paper_scissors(sock: socket, msg: str):
    """
    Game: rock-paper-scissors

    :param sock: socket, client socket that is playing game
    :param msg: str, client choice (rock/r, paper/p or scissors/s)
    :return: None
    """
    if msg == common.init_game_msg:
        common.private_message(common.server_socket, sock,
                               "Let's play rock-paper-scissors!\nWhat is your choice?"
                               " (need to send: rock or r / paper or p /scissors or s)")
        common.one_player_game_list[sock] = {"game": one_player_game_rock_paper_scissors}
    else:
        if msg in ["rock", "r", "paper", "p", "scissors", "s"]:
            msg = reductions.get(msg, msg)
            server_choice = random.choice(["rock", "paper", "scissors"])
            status = rules.get(msg[0] + server_choice[0], "No winner!")
            common.private_message(common.server_socket, sock, "Your choice: {}, server choice: {}. {}"
                                   .format(msg, server_choice, status))
            common.one_player_game_list.pop(sock)
        else:
            common.private_message(common.server_socket, sock,
                                   "You sent incorrect value. Please try again.\nWhat is your choice?"
                                   " (need to send: rock or r / paper or p /scissors or s)")

"""
Quiz: all players game
"""
# pylint: disable=C0103     # UPPER_CASE naming style
# pylint: disable=W0603     # global statement
import random
import socket
from typing import Optional
from threading import Timer
import common

questions = [("How many bytes in one kilobyte?", "1024", "equal"),
             ("What is the capital of Belarus?", "Minsk", "equal"),
             ("Who is the creator of the Python?", "Guido", "contains")]
_answer: str            # right answer on the current question
_comparison: str        # how to compare user answer and right one (equal, contains)
_winner: Optional[str]  # quiz winner
_log: str               # log of user answers


def init_new_game():
    """
    Initialization game parameters, send question to users and start timer
    """
    global _answer, _comparison, _winner, _log
    question, _answer, _comparison = random.choice(questions)
    _winner = None
    _log = ""
    common.send_to_all(f"Let's start Quiz round!\nYou have 30 sec and you can send several answers\n{question}")
    common.all_player_game["game"] = all_players_game_quiz
    Timer(30, all_players_game_quiz, [None, common.STOP_GAME_MSG]).start()


def is_right_answer(answer: str):
    """
    Check if user answer is correct.
    _comparison can have values:
        - equal - the answer must strictly correspond to the correct one
        - contains - the answer must contain the correct one
                     (i.e. "Guido", "Guido van Rossum" are both correct if right answer is "Guido")
    :param answer: str, user answer
    :return: None
    """
    if _comparison == "equal":
        return _answer.lower() == answer.lower()
    return _answer.lower() in answer.lower()    # _comparison = "contains"


def finish_game():
    """
    Send result messages and remove game
    """
    if len(_log) > 0:
        response = "Participants' answer(s):\n{}The right answer: {}\n".format(_log, _answer)
        if _winner is None:
            response += "No winner!"
        else:
            response += "The winner is {}! Congratulations!".format(_winner)
    else:
        response = "Nobody sent an answer. No winner!"
    common.send_to_all(response)
    common.all_player_game.clear()


def all_players_game_quiz(sock: Optional[socket.socket], msg: str):
    """
    Game: Quiz (all players game)

    :param sock: socket, client socket that is playing game
    :param msg: str, client answer
    :return: None
    """
    global _winner, _log
    if msg == common.INIT_GAME_MSG:
        init_new_game()
    elif sock is None:
        raise ValueError("sock=None is allowed only with init message, but message is {}".format(msg))
    elif msg == common.STOP_GAME_MSG:
        finish_game()
    else:
        _log += "[{}] {}\n".format(common.sockets_list[sock], msg)
        if _winner is None and is_right_answer(msg):
            _winner = common.sockets_list[sock]

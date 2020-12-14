# python-chat-room
## Start
### Run Slack bot
Provide correct SLACK_TOKEN and SLACK_SIGNING_SECRET in bots/.slack_env

Setup channel name in bots/slack_bot.py file, i.e. CHAT_CHANNEL = "chat"

Run slack bot server:
```bash
python bots/slack_bot.py
```
### localhost
```bash
python server.py
python client.py
```
### remote host
```bash
python server.py 192.168.100.5 8888
python client.py 192.168.100.5 8888
```
*Use ip address of host where server is running
## Features
- All users have unique name
- User can get the last chat messages by sending any message or pressing Enter
- Users can send public message just typing any text
- Users can send private message, i.e [recipient] message
- Users can interact with server, i.e. [server] command
- List of server commands:
```
    [server] help                   - info about chat
    [server] participants           - return list of chat participants
    [server] participants-count     - return count of chat participants
    [server] rock-paper-scissors    - play rock-paper-scissors game with server
    [server] 21                     - play 21 game with server
    [server] quiz                   - quiz game for all participants
```
- Slack features:
  - All messages from selected slack channel send to this chat room
  - All public messages from this chat room send to slack channel
  - Simple AI to answer on private messages to slack bot

## Tests
For running tests using pytest:
```bash
python -m pytest -s --cache-clear .
```
*Some scenarios are covered, except for games (rock-paper-scissors, 21, quiz)

** cache-clear is used as just one more parameter to fix test_create_server_socket

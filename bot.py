import os
import time
from slackclient import SlackClient


class Robot:

    def __init__(self, name='robot'):
        self.name = name
        self.slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        self.bot_id = self.get_bot_id()
        self.bot_start_time = time.time()
        self.read_delay = 0.2
        self.version = '0.1.0 (alpha)'
        self.COMMANDS_MAP = self.build_commands_map()

    def get_bot_id(self):
        if __name__ == "__main__":
            api_call = self.slack_client.api_call("users.list")
            if api_call.get("ok"):
                users = api_call.get('members')
                for user in users:
                    if 'name' in user and user.get('name') == self.name:
                        return user.get('id')
            else:
                print("could not find bot user with the name " + self.name)
                return None

    def handle_command(self, command, channel):
        if command.partition(' ')[0] in self.COMMANDS_MAP:
            method_name = self.COMMANDS_MAP[command.partition(' ')[0]]['function']
            try:
                method = getattr(self, method_name)
            except Exception:
                method = None
            if callable(method):
                response = method(command)
            else:
                response = "function not implemented"
            self.slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

    def build_commands_map(self):
        return {
            '!help': {
                'function': 'command_help',
                'example': '!help',
                'description': 'Displays a list of valid commands'
            },
            '!version': {
                'function': 'command_version',
                'example': '!version',
                'description': 'Show <@{}>\'s version'.format(self.name)
            },
        }

    def start(self):
        if __name__ == "__main__":

            if self.slack_client.rtm_connect():
                print('{} activated and online...({})'.format(self.name, self.bot_id))
                while True:
                    try:
                        command, channel = self.parse_slack_output(self.slack_client.rtm_read())
                        if command and channel:
                            self.handle_command(command, channel)
                        time.sleep(self.read_delay)
                    except Exception as e:
                        logging.debug(e)
                        print(e)
                        print('Disconnected!')
                        print('Reconnecting...')
                        time.sleep(self.read_delay)
                        self.start()
            else:
                print('robot offline due to invalid token or bot id?')


robot = Robot('devbot')
robot.start()

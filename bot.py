import os
import time
from slackclient import SlackClient
from duckduckpy import query
import wolframalpha
import logging


class Robot:

    def __init__(self, name='robot'):
        self.name = name
        self.slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        self.bot_id = self.get_bot_id()
        self.bot_start_time = time.time()
        self.read_delay = 0.2
        self.version = '0.5.5 (alpha)'
        self.COMMANDS_MAP = self.build_commands_map()
        self.wa_client = wolframalpha.Client(os.environ.get('WA_TOKEN'))

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
            '!wiki': {
                'function': 'command_wiki',
                'example': '!wiki <search phrase>',
                'description': 'returns a single search result from wiki (via DuckDuckGo)'
            },
            '<@{}>'.format(self.bot_id): {
                'function': 'command_robot',
                'example': '@{} <question>'.format(self.name),
                'description': 'chat with {}'.format(self.name)
            },
            '!uptime': {
                'function': 'command_uptime',
                'example': '!uptime',
                'description': 'Show <@{}>\'s uptime'.format(self.name)
            },
        }

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

    @staticmethod
    def parse_slack_output(slack_rtm_output):
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output:
                    return output['text'], output['channel']
        return None, None

    def command_help(self, command):
        response = ''
        if len(command.partition(' ')[2]) > 0:
            argument = '!' + command.partition(' ')[2]
            if argument in self.COMMANDS_MAP:
                response += '`{}` - _{}_'.format(
                    self.COMMANDS_MAP[argument]['example'],
                    self.COMMANDS_MAP[argument]['description']) + '\n'
        else:
            for cmd in self.COMMANDS_MAP:
                response += '`{}` - _{}_'.format(
                    self.COMMANDS_MAP[cmd]['example'],
                    self.COMMANDS_MAP[cmd]['description']) + '\n'
        return response

    @staticmethod
    def command_wiki(command):
        result = ''
        new_list = command.split()
        if len(new_list) > 1:
            new_list.pop(0)
            if len(new_list) > 1:
                result = query("wiki {}".format(' '.join(new_list)), False, 'namedtuple', False, 'duckduckpy 0.2', True,
                               False, True)
            if len(new_list) is 1:
                result = query("{}".format(' '.join(new_list)), False, 'namedtuple', False, 'duckduckpy 0.2', True,
                               False, True)
            response = result.abstract_url
            if len(response) > 0:
                return response
            else:
                return "No results found"
        return "?"

    def command_version(self, _):
        return 'Botbot {}'.format(self.version)

    def command_robot(self, command):
        new_list = command.split()
        if len(new_list) > 1:
            new_list.pop(0)
            if len(new_list) > 0:
                try:
                    result = self.wa_client.query("{}".format(' '.join(new_list)))
                    i = 1
                    for pod in result:
                        if i is 2:
                            try:
                                for sub in pod.subpods:
                                    if sub.plaintext is not None:
                                        return sub.plaintext.replace(
                                            "Stephen Wolfram and his team",
                                            "seria1zed & Stephen Wolfram and his team"
                                        )
                            except Exception:
                                continue
                        i += 1
                except Exception:
                    return 'Sir, I don\'t have an answer for that'
        else:
            return 'Sir ?'

    def command_uptime(self, _):
        bot_command_time = time.time()
        time_diff_from_start = bot_command_time - self.bot_start_time
        m, s = divmod(time_diff_from_start, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return self.days((int(d), int(h), int(m), int(s)))

    @staticmethod
    def days(t):
        oxford_comma = False
        a = [" day", " hour", " minute", "second"]
        s = []
        if len(t) != 4:
            return "incorrect format"
        else:
            for i in range(4):
                if t[i] != 0:
                    plural = "s" if t[i] > 1 else ""
                    s.append(str(t[i]) + a[i] + plural + ", ")
            if len(s) > 1:
                if not oxford_comma:
                    s[-2] = s[-2].replace(",", "")
                s.insert(len(s) - 1, "and ")
            return "".join(s)[:-2]

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

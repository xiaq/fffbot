# coding: utf-8

from collections import OrderedDict
import sys
import os.path
import logging

import requests


commands = OrderedDict([
    ('install', ('p q ...', u'把人捆♂绑到火刑柱上')),
    ('add',     ('i j ...', u'添加调料')),
    ('ignite',  ('',        u'开始烧烧烧！')),
    ('water',   ('',        u'灭火')),
    ('status',  ('',        u'查询火刑柱状态')),
    ('help',    ('',        u'命令帮助'))
])

def make_help_line(name):
    args, desc = commands[name]
    return '/fff ' + name + (' ' + args if args else '') + ': ' + desc

help_text = u'释放 FFF 团的怒火吧！'

for name in commands.iterkeys():
    help_text += '\n' + make_help_line(name)


stake_commands = {}

def command(f):
    stake_commands[f.__name__] = f

class Stake(object):
    def __init__(self):
        self.state = 'idle'

    def make_str(self, things):
        if len(things) == 0:
            return u'啥都没有'
        elif len(things) == 1:
            return things[0]
        return u'、'.join(things[:-1]) + u' 和 ' + things[-1]

    def get_be(self, *things):
        return 'are' if len(things) > 1 else 'is'

    @property
    def status_desc(self):
        if self.state == 'idle':
            return u'火刑柱上现在什么都没有。'
        elif self.state == 'installed':
            return u'火刑柱上现在绑着 %s。' % self.people_str
        elif self.state == 'ignited':
            return u'%s 正在熊熊燃烧。' % self.people_str

    @command
    def install(self, *people):
        if self.state != 'idle':
            return self.status_desc
        if len(people) == 0:
            return u'至少要绑一个人。'
        people = [person.lstrip('@') for person in people]
        self.people = people
        self.people_str = self.make_str(people)
        self.people_be = self.get_be(people)
        self.state = 'installed'
        return u'%s 把 %s 绑到了火刑柱上。' % (
            self.from_str, self.people_str)

    @command
    def add(self, *things):
        if self.state not in ('installed', 'ignited'):
            return self.status_desc
        if len(things) == 0:
            return u'请至少指定一种调料 - -b'
        return u'%s 往火刑柱上加了 %s。' % (
            self.from_str, self.make_str(things))

    @command
    def ignite(self, *args):
        if self.state != 'installed':
            return self.status_desc
        self.state = 'ignited'
        return u'%s 烧起来了！此处应有欢呼。' % self.people_str

    @command
    def water(self, *args):
        if self.state != 'ignited':
            return self.status_desc
        self.state = 'idle'
        if self.from_str == self.people_str:
            return u'%s 居然自己挣脱了！哪位勇士快来把他捉回去！' % (
                self.from_str)
        else:
            return u'%s 突然解救了 %s。我们中出了一个叛徒！' % (
                self.from_str, self.people_str)

    @command
    def status(self, *args):
        return self.status_desc

    def react(self, cmd, *args):
        if cmd not in stake_commands:
            return help_text
        return stake_commands[cmd](self, *args)


def make_name(from_):
    if 'last_name' not in from_:
        return from_['first_name']
    return from_['first_name'] + ' ' + from_['last_name']


class FFFBot(object):
    def __init__(self, token):
        self.token = token
        self.url_prefix = 'https://api.telegram.org/bot' + token
        self.cooldown = 0
        self.offset = 0
        self.stakes = {}

    def inc_cooldown(self):
        self.cooldown = min(64, self.cooldown * 2 if self.cooldown else 1)

    def process_update(self, up):
        self.offset = up['update_id'] + 1
        msg = up['message']
        id_ = msg['chat']['id']
        if 'text' not in msg:
            return
        text = msg['text']
        fields = text.split(' ')
        if fields[0] != '/fff' and not fields[0].startswith('/fff@'):
            if msg['chat']['type'] == 'private':
                return help_text
            else:
                return
        if len(fields) == 1:
            fields.append('status')
        if id_ not in self.stakes:
            self.stakes[id_] = Stake()
        stake = self.stakes[id_]
        # uh
        stake.from_str = make_name(msg['from'])
        return stake.react(*fields[1:])

    def main_loop(self):
        offset = 0

        while True:
            if self.cooldown:
                time.sleep(self.cooldown)

            # Grab updates
            try:
                res = requests.get(self.url_prefix + '/getUpdates',
                                   dict(offset=self.offset, timeout=60))
            except requests.ConnectionError as e:
                logging.warn('Connection error, try again after %d seconds' %
                             self.cooldown)
                logging.exception(e)
                self.inc_cooldown()
                continue
            else:
                self.cooldown = 0

            # Decode
            try:
                res = res.json()
            except ValueError:
                logging.error("Response not JSON. Sth terribly wrong")
                break

            if not res['ok']:
                logging.warn('Response not OK, try again after %d seconds' %
                             self.cooldown)
                self.inc_cooldown()
                continue
            else:
                self.cooldown = 0

            # Process updates
            for up in res['result']:
                ans = self.process_update(up)
                if not ans:
                    continue
                requests.get(self.url_prefix + '/sendMessage',
                             dict(chat_id=up['message']['chat']['id'],
                                  text=ans))


def main():
    if not os.path.exists('token.txt'):
        print 'Put the token in token.txt'
        os.exit(1)
    with open('token.txt') as f:
        token = f.readline().strip()
    try:
        FFFBot(token).main_loop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

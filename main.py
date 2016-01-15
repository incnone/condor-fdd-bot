#TODO: more robust message reading (e.g. should be able to read history in case of temporary crash etc)
#TODO: thread safety for database access

import asyncio
import datetime
import discord
import logging
import textwrap
import time
import traceback
import sys

import config
import seedgen

from cffdbot import CffdBot


##-Logging-------------------------------
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
##--------------------------------------


class LoginData(object):
    email = ''
    password = ''
    admin_id = None
    server_id = None

## Global variables
login_data = LoginData()                    # data to be read from the login file
client = discord.Client()                   # the client for discord
cffdbot = CffdBot(client)                   # main class for bot behavior

#----Main------------------------------------------------------
config.init()

login_info = open('data/login_info', 'r')
login_data.email = login_info.readline().rstrip('\n')
login_data.password = login_info.readline().rstrip('\n')
login_data.admin_id = login_info.readline().rstrip('\n')
login_data.server_id = login_info.readline().rstrip('\n')

seedgen.init_seed()
     
# Define client events
@client.event
@asyncio.coroutine
def on_ready():
    print('-Logged in---------------')
    print('User name: {0}'.format(client.user.name))
    print('User id  : {0}'.format(client.user.id))
    print('-------------------------')
    print(' ')
    print('Initializing bot...')
    cffdbot.post_login_init(login_data.server_id, login_data.admin_id)
    print('...done.')

@client.event
@asyncio.coroutine
def on_message(message):
    yield from cffdbot.parse_message(message)

#TODO : handle errors

# Run client
client.run(login_data.email, login_data.password)

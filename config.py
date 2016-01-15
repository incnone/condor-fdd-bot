CONFIG_FILE = 'data/bot_config'

def init():
    global BOT_COMMAND_PREFIX
    global BOT_VERSION
    global MAIN_CHANNEL_NAME
    global VOICE_CHANNEL_NAME
    global ADMIN_ROLE_NAME

    fileformat = [
        'bot_command_prefix',
        'bot_version',
        'channel_main',
        'voice_channel',
        'admin_role'
        ]

    defaults = {
        'bot_command_prefix':'.',
        'bot_version':'0.1',
        'channel_main':'botcommands',
        'voice_channel':'Race Room',
        'admin_role':'CoNDOR Staff'
        }
            
    file = open(CONFIG_FILE, 'r')
    if file:
        for line in file:
            args = line.split('=')
            if len(args) == 2:
                if args[0] in defaults:
                    defaults[args[0]] = args[1].rstrip('\n')
                else:
                    print("Error in {0}: variable {1} isn't recognized.".format(filename, args[0]))

    BOT_COMMAND_PREFIX = defaults['bot_command_prefix']
    BOT_VERSION = defaults['bot_version']
    MAIN_CHANNEL_NAME = defaults['channel_main']
    VOICE_CHANNEL_NAME = defaults['voice_channel']
    ADMIN_ROLE_NAME = defaults['admin_role']

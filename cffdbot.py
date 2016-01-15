#TODO: maybe a command to .dailyseed should not register for the new daily if you've yet to complete old one?

import asyncio
import discord
import seedgen

import config

HELP_BOTCOMMANDS = \
'`.make:` ' \
'Create a channel that only users in the "Race Room" voice channel (and CoNDOR Staff) can read. The channel ' \
'will be called  #race-name1-name2, where name1 and name2 are the names of any users in the "Race Room" voice ' \
'channel who do not also have the "CoNDOR Staff" role.\n' \
'`.randomseed`: ' \
'Generate a random seed.'
HELP_RACE_CHANNELS = \
'`.add username...` or `.add @username...`: ' \
'Allow any users with given usernames to read/write in the channel in which this command is called.\n' \
'`.cleanup`: ' \
'Delete the channel.\n' \
'`.randomseed`: ' \
'Generate a random seed.\n' \
'`.remove username...` or `.remove @username...`: ' \
'Remove the mentioned users from the channel in which this command is called.' 
          

class CffdBot(object):

    ## Info string
    def infostr():
        return 'CffdBot v-{}. Use `.help` for a list of commands.'.format(config.BOT_VERSION)

    ## Barebones constructor
    def __init__(self, client,):
        self._client = client
        self._server = None
        self._main_channel = None
        self._admin_id = None
        self._room_list = []

    ## Write to the channel
    @asyncio.coroutine
    def _write(self, channel, text):
        asyncio.ensure_future(self._client.send_message(channel, text))

    @asyncio.coroutine
    def _write_now(self, channel, text):
        yield from self._client.send_message(channel, text)

    @asyncio.coroutine
    def write_error(self, text):
        print('Error: {}'.format(text))
        asyncio.ensure_future(self._client.send_message(self._main_channel, 'Error: {}'.format(text)))

    ## Checks whether the user has the admin role
    def is_admin(self, user):
        return self.get_admin_role() in user.roles

    ## Initializes object; call after client has been logged in to discord
    def post_login_init(self, server_id, admin_id=None):

        self._admin_id = admin_id if admin_id != 0 else None
        
        #set up server
        id_is_int = False
        try:
            server_id_int = int(server_id)
            id_is_int = True
        except ValueError:
            id_is_int = False
            
        if self._client.servers:
            for s in self._client.servers:
                if id_is_int and s.id == server_id:
                    self._server = s
                elif s.name == server_id:
                    print("Server id: {}".format(s.id))
                    self._server = s
        else:
            print('Error: Could not find the server <{}>.'.format(server_id))
            exit(1)

        #find main channel
        for channel in self._server.channels:
            if channel.name == config.MAIN_CHANNEL_NAME:
                self._main_channel = channel

        if not self._main_channel:
            print('Error: Could not find the command channel <{}>.'.format(config.MAIN_CHANNEL_NAME))
            exit(1)

    ## Log out of discord
    @asyncio.coroutine
    def logout(self):
        yield from self._client.logout()       

    @asyncio.coroutine
    def parse_message(self, message):
        # don't reply to self
        if message.author == self._client.user:
            return

        # don't reply off server
        if not message.server == self._server:
            return

        # don't reply to non-admin
        if not self.is_admin(message.author):
            return

        # check for command prefix
        if not message.content.startswith(config.BOT_COMMAND_PREFIX):
            return

        # parse the command, depending on the channel it was typed in (this just restricts which commands are available from where)
        if message.channel == self._main_channel:
            yield from self.main_channel_command(message)
        else:
            for channel in self._room_list:
                if message.channel == channel:
                    yield from self.race_channel_command(channel, message)
                

    @asyncio.coroutine
    def main_channel_command(self, message):
        args = message.content.split()
        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)

        #.help : Quick help reference
        if command == 'help':
            bot_cmd_str = 'In this channel only:\n'
            yield from self._write_now(message.channel, bot_cmd_str + HELP_BOTCOMMANDS)
            race_chnl_str = 'In race channels only:\n'
            yield from self._write_now(message.channel, race_chnl_str + HELP_RACE_CHANNELS)

        #.make : Create race room
        elif command == 'make':
            yield from self.make_room()
            
        #.randomseed : Generate a new random seed
        elif command == 'randomseed':
            seed = seedgen.get_new_seed()
            yield from self._write(message.channel, 'Seed generated: {1}'.format(message.author.mention, seed))       

        elif command == 'info':
            yield from self._write(message.channel, CffdBot.infostr())

    @asyncio.coroutine
    def race_channel_command(self, room_channel, message):
        args = message.content.split()
        command = args.pop(0).replace(config.BOT_COMMAND_PREFIX, '', 1)

        read_permit = discord.Permissions.none()
        read_permit.read_messages = True

        #.add : Add users
        if command == 'add':
            mentioned_user = False
            for member in message.mentions:
                asyncio.ensure_future(self._client.edit_channel_permissions(room_channel, member, allow=read_permit))
                mentioned_user = True

            if not mentioned_user:
                not_found = ''
                for username in args:
                    found_user = False
                    for member in self._server.members:
                        if member.name == username:
                            asyncio.ensure_future(self._client.edit_channel_permissions(room_channel, member, allow=read_permit))
                            found_user = True
                    if not found_user:
                        not_found += username + ' '

                if not_found:
                    yield from self._write(room_channel, "Couldn't find users: {}".format(not_found))

        #.cleanup : Delete this room
        elif command == 'cleanup':
            room_list = [room for room in self._room_list if room != room_channel]
            asyncio.ensure_future(self._client.delete_channel(room_channel))

        #.randomseed : Generate a new random seed
        elif command == 'randomseed':
            seed = seedgen.get_new_seed()
            yield from self._write(message.channel, 'Seed generated: {1}'.format(message.author.mention, seed))   

        #.remove : Remove users
        elif command == 'remove':
            mentioned_user = False
            for member in message.mentions:
                asyncio.ensure_future(self._client.edit_channel_permissions(room_channel, member, deny=read_permit))
                mentioned_user = True

            if not mentioned_user:
                not_found = ''
                for username in args:
                    found_user = False
                    for member in self._server.members:
                        if member.name == username:
                            asyncio.ensure_future(self._client.edit_channel_permissions(room_channel, member, deny=read_permit))
                            found_user = True
                    if not found_user:
                        not_found += username + ' '

                if not_found:
                    self._write(room_channel, "Couldn't find users: {}".format(not_found))

    @asyncio.coroutine
    def make_room(self):
        voice_channel = None

        #get the Discord voice channel
        for channel in self._server.channels:
            if channel.type == discord.ChannelType.voice and channel.name == config.VOICE_CHANNEL_NAME:
                voice_channel = channel

        if not voice_channel:
            yield from self._write_error('Could not find the voice channel "{0}"'.format(config.VOICE_CHANNEL_NAME))
            return
        
        channel_name = self.get_race_channel_name(voice_channel)

        #we now have the voice channel. create a new room and set its permissions
        new_channel = yield from self._client.create_channel(self._server, channel_name)
        if new_channel:
            self._room_list.append(new_channel)
            asyncio.ensure_future(self.set_raceroom_permissions(new_channel, voice_channel))

        name_list_string = ''
        for user in self.get_non_admins(voice_channel):
            name_list_string += ' ' + user.mention + ','

        self._write('Made race channel {0} for{1}.'.format(new_channel.mention, name_list_string[:-1]))

    def get_admin_role(self):
        for role in self._server.roles:
            if role.name == config.ADMIN_ROLE_NAME:
                return role
        return None

    def get_non_admins(self, voice_channel):
        non_admins = []
        admin_role = self.get_admin_role()
        
        for member in voice_channel.voice_members:
            if not (admin_role in member.roles):
                non_admins.append(member)

        return non_admins

    def get_race_channel_name(self, voice_channel):
        channel_name = 'race_'
        for user in self.get_non_admins(voice_channel):
            channel_name += user.name + '-'

        return (channel_name[:-1])[:64]

    #Allow only the admin-role members and the users in the voice channel to read the room channel
    @asyncio.coroutine
    def set_raceroom_permissions(self, room_channel, voice_channel):
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True
        admin_role = self.get_admin_role()
            
        asyncio.ensure_future(self._client.edit_channel_permissions(room_channel, self._server.default_role, deny=read_permit))
        if admin_role:
            asyncio.ensure_future(self._client.edit_channel_permissions(room_channel, admin_role, allow=read_permit))
        else:
            yield from self._write_error('Could not find admin role <{}>.'.format(config.ADMIN_ROLE_NAME))

        for member in voice_channel.voice_members:
            asyncio.ensure_future(self._client.edit_channel_permissions(room_channel, member, allow=read_permit))
    
    

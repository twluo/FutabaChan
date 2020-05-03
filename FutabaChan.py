import discord
import re
from AUTH_KEYS import DISCORD_TOKEN
from clients import RiotClient

futaba_chan = discord.Client()
rc = RiotClient.RiotClient()

@futaba_chan.event
async def on_ready():
    """ Event handler for when Futaba is ready to receive messages """
    print('Logged in as')
    print(futaba_chan.user.name)
    print(futaba_chan.user.id)
    print('------')

@futaba_chan.event
async def on_message(message):
    """ Event handler for receiving messages
    Arguments
    ---------
    message : Message
        Message received
    """
    if message.content.startswith('!league'):
        channel = message.channel
        p = re.compile("[\"][\w\s]+[\"]")
        m = p.findall(message.content)
        user1 = m[0].strip('"')
        user2 = m[1].strip('"')
        await channel.send("Finding path between %s and %s" % (user1, user2))
        path, match_history = rc.find_shortest_distance(user1, user2)
        print(path, match_history)
        await channel.send(path)
        await channel.send(match_history)

futaba_chan.run(DISCORD_TOKEN)
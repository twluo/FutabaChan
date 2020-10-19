import discord
from AUTH_KEYS import DISCORD_TOKEN
from clients import RiotClient
import statistics
from statistics import mode

def get_combo(sum, n, repeat_flag = False):
    # Initialize final answer
    if repeat_flag is None:
        repeat_flag = False
    solutions = set()
    def combo_helper(sum, n, path, repeat_flag):
        if (n < 0):
            return
        if (n == 0 and sum == 0):
            path.sort()
            x = str(path)
            solutions.add(x)
        for i in range(1, 10):
            new_path = [x for x in path]
            new_path.append(i)
            if repeat_flag:
                if sum - 1 >= 0:
                    combo_helper(sum - i, n - 1, new_path, repeat_flag)
            else:
                if sum - i >= 0 and i not in path:
                    combo_helper(sum - i, n - 1, new_path, repeat_flag)
    combo_helper(sum, n, [], repeat_flag)
    return solutions

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
    channel = message.channel
    if message.content.startswith("!get_rivalry"):
        message_split = message.content.split()
        protag = str(message_split[1])
        rival = str(message_split[2])
        history = int(message_split[3])
        with_wins, with_losses, against_wins, against_losses, friends, rivals = rc.get_rival_record(protag, rival, 0, history)
        total_withs = with_wins + with_losses
        total_againts = against_wins + against_losses
        await channel.send("You've won " + str(with_wins) + " out of " + str(total_withs) + " games together.")
        await channel.send("You've won " + str(against_wins) + " out of " + str(total_againts) + " games against.")
        bff, enemy = mode(friends), mode(rivals)
        await channel.send("Your bff is " + str(bff) + " with " + str(friends.count(bff)) + " games.")
        await channel.send("Your biggest rival is " + str(enemy) + " with " + str(rivals.count(enemy)) + " games.")
    if message.content.startswith("!get_combo"):
        message_split = message.content.split()
        target = int(message_split[1])
        n = int(message_split[2])
        await channel.send(get_combo(target, n))
    if message.content.startswith("!get_combo_repeat"):
        message_split = message.content.split()
        target = int(message_split[1])
        n = int(message_split[2])
        message_send = get_combo(target, n, True)
        print(message_send)
        await channel.send(message_send)


futaba_chan.run(DISCORD_TOKEN)

import discord
import requests
import time
import asyncio
import sqlite3
import operator
import datetime
from bs4 import BeautifulSoup
from urllib.request import urlopen
from discord.ext import commands


class Player:

    def __init__(self, name, profession, level):
        self.name = name
        self.profession = profession
        self.level = level

    def __gt__(self, other):
        return self.level > other

    def __lt__(self, other):
        return self.level < other


def isTrue(x):
    if x:
        return 1
    else:
        return 0

bot = commands.Bot(command_prefix='!')

onlinePlayers = list()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def add(ctx, a: int, b: int):
    await ctx.send(a + b)

@bot.command()
async def startfriends(ctx):
    msg = await ctx.send("Loading friend list...")
    find = lambda searchList, elem: [[i for i, x in enumerate(searchList) if x.name == e] for e in elem]
    tfl = list()
    conn = sqlite3.connect("viplist.db")
    c = conn.cursor()

    while(1):
        await asyncio.sleep(3)
        for player in c.execute("SELECT name FROM friends"):
            print(player[0])
            tfl.append(player[0])

        #conn.close()

        print(find(onlinePlayers,tfl))
        msg2 = "Friendlist: \n"
        friendlist = list()
        findlist = list(filter(isTrue,find(onlinePlayers,tfl)))
        for fin in findlist:
            print(fin[0])
            friendlist.append(onlinePlayers[fin[0]])
            msg2 = msg2 + onlinePlayers[fin[0]].name + "\n"

        await msg.edit(content="```" + msg2 + "```")
        del findlist[:]
        del friendlist[:]
        del tfl[:]

@bot.command()
async def addfriend(ctx, *a):

    name = ('' + ' '.join(a))
    r = requests.get('https://medivia.online/community/character/' + name)

    if ((r.text).find("name:</div><div class=\"med-width-50\">") == -1):
        await ctx.send("Character with that name does not exist!")
        return

    conn = sqlite3.connect("viplist.db")
    c = conn.cursor()
    #c.execute('''CREATE TABLE friends (date text, name text)''')
    c.execute("INSERT INTO friends VALUES ('datea','"+name+"')")
    conn.commit()
    conn.close()

@bot.command()
async def multiply(ctx, a: int, b: int):
    await ctx.send(a * b)


@bot.command()
async def test(ctx):
    global onlinePlayers
    msg = await ctx.send("Loading online list...")
    url = 'http://medivia.online/community/online/legacy'
    minlvl = 120

    print(ctx.channel)

    while (1):
        await asyncio.sleep(5)
        try:
            data = urlopen(url).read()
            soup = BeautifulSoup(data, "html.parser")
            names = soup.find_all('div', class_='med-width-35')
            vocs = soup.find_all('div', class_='med-width-15')
            levels = soup.find_all('div', class_='med-width-25 med-text-right med-pr-40')
            players = list();

            for name, voc, level in zip(names, vocs, levels):
                players.append(Player(name.get_text(), voc.get_text(), level.get_text()))

            del players[len(players) - 1]
            del players[0]

            for player in players:
                player.level = int(player.level)

            players.sort()

            onlinePlayers = list(players)

            playerList = "```Players lvl " + str(minlvl) + "+ : " + "\n-----------------\n"
            counter = 0
            for player in players:
                if (int(player.level) > minlvl):
                    counter = counter + 1
                    playerList = playerList + str(
                        counter) + ". " + player.name + " | " + player.profession + " | " + str(player.level) + "\n"

            print(len(playerList))
            await msg.edit(content=playerList + "```")
            await ctx.channel.edit(reason=None, name="Legacy online: " + str(len(players)))
            del players[:]
            del data

        except ():
            continue


@bot.command()
async def level(ctx, *a):
    # https://medivia.online/community/character/
    # parser = Parser()
    name = ('' + ' '.join(a))
    r = requests.get('https://medivia.online/community/character/' + name)
    index = (r.text).find("level:</div><div class=\"med-width-50\">")

    if (index == -1):
        await ctx.send("Character with that name does not exist!")
        return

    print('https://medivia.online/community/character/' + name)
    message = ""
    i = 0
    while (r.text[index + 38 + i] != '<'):
        message = message + r.text[index + 38 + i]
        i = i + 1

    await ctx.send(message)


@bot.command()
async def details(ctx, *a):

    name = ('' + ' '.join(a))
    r = requests.get('https://medivia.online/community/character/' + name)

    indexes = [
        (r.text).find("name:</div><div class=\"med-width-50\">") + 38 - 1,
        (r.text).find("level:</div><div class=\"med-width-50\">") + 38,
        (r.text).find("position:</div><div class=\"med-width-50\">") + 38 + 3,
        (r.text).find("sex:</div><div class=\"med-width-50\">") + 38 - 2,
        (r.text).find("profession:</div><div class=\"med-width-50\">") + 38 + 5,
        (r.text).find("world:</div><div class=\"med-width-50\">") + 38 + 0,
        (r.text).find("residence:</div><div class=\"med-width-50\">") + 38 + 4,
        (r.text).find("last login:</div><div class=\"med-width-50\"><strong>") + 38 + 8 + 5,
        (r.text).find("account status:</div><div class=\"med-width-50\">") + 38 + 9
    ]

    stat = ["Name", "Level", "Position", "Sex", "Profession", "World", "Residence", "Last login", "Account status"]
    if (indexes[1]-38 == -1):
        await ctx.send("Character with that name does not exist!")
        return

    print (indexes[1]-38)
    print('https://medivia.online/community/character/' + name)
    embed = discord.Embed(title=name, description="Detailed information about this player:", color=0xeee657)

    for i in range(0, len(indexes)):
        k = 0
        message = ""
        while (r.text[indexes[i] + k] != '<'):
            message = message + r.text[indexes[i] + k]
            k = k + 1

        embed.add_field(name=stat[i], value=message, inline=True)

    await ctx.send(embed=embed)


@bot.command()
async def start_feed(ctx):
    lastName = ''
    while (1):
        time.sleep(5)
        # r = requests.get('http://mediviastats.info/recent-deaths.php?server=Legacy')
        # (r.text).find("name:</div><div class=\"med-width-50\">")+38-1,
        # get the contents
        url = 'http://mediviastats.info/recent-deaths.php?server=Legacy'
        data = urlopen(url).read()
        soup = BeautifulSoup(data, "html.parser")
        links = soup.findAll('a')

        name = links[29]["href"]
        msg = ''
        if (name != lastName):
            s = name.find('=') + 1
            while (s != len(name)):
                msg = msg + name[s]
                s = s + 1

            print(links[29]["href"])
            await ctx.send(msg)
            lastName = name

        # for link in links:
        # print(link["href"])


@bot.command()
async def parse(ctx):
    url = 'http://www.investing.com/currencies/usd-brl-historical-data'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find("table", {"id": "curr_table"})
    # first row is empty
    tableRows = [[td.text for td in row.find_all("td")] for row in table.findAll("tr")[1:]]
    print(tableRows)


@bot.command()
async def greet(ctx):
    await ctx.send(":smiley: :wave: Hello, there!")


@bot.command()
async def cat(ctx):
    await ctx.send("https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif")


@bot.command()
async def info(ctx):
    embed = discord.Embed(title="MedBot", description="Medivia statistics on discord.", color=0xeee657)

    # give info about you here
    embed.add_field(name="Author", value="buy dip kek")

    # Shows the number of servers the bot is member of.
    embed.add_field(name="Server count", value=f"{len(bot.guilds)}")

    # give users a link to invite thsi bot to their server
    # embed.add_field(name="Invite", value="[Invite link](<insert your OAuth invitation link here>)")

    await ctx.send(embed=embed)


bot.remove_command('help')


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="MedBot", description="Bot for medivia statistics. List of commands are:",
                          color=0xeee657)

    embed.add_field(name="!level player_name", value="Returns player's level.", inline=False)
    embed.add_field(name="!details player_name", value="Returns player's details.", inline=False)

    await ctx.send(embed=embed)


bot.run('NDU1NzE3MTA1NDE4MTA4OTI5.DgAFIA.XMuqoE1CZKwhUGduFre4dDgdIok')


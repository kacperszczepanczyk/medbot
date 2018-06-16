import discord
import requests
import time
import asyncio
import sqlite3
import ssl
import urllib
import aiohttp
import os
from tabulate import tabulate
from bs4 import BeautifulSoup
from urllib.request import urlopen
from discord.ext import commands
from http.client import IncompleteRead

TOKEN_d = 'NDU1NzE3MTA1NDE4MTA4OTI5.DgAFIA.XMuqoE1CZKwhUGduFre4dDgdIok' #developer version - MedBot
TOKEN_p = 'NDU2NTIzNjg3MTEwMzc3NDky.DgLyZg.vL7F4jesEYVp_qG5q-s8gNRRT-4' #somewhat stable version - MedBotBaby
TOKEN = TOKEN_d


sqlite_d = "viplist.db"
sqlite_p = "..\\viplist.db"
sqlite = sqlite_d

bot = commands.Bot(command_prefix='!')
onlinePlayers = list()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    await startOnlineLoop(5)

class Player:

    def __init__(self, name, profession, level):
        self.name = name
        self.profession = profession
        self.level = level

    def __gt__(self, other):
        return self.level > other #reversed for sorting purposes, too lazy

    def __lt__(self, other):
        return self.level < other #same

async def startOnlineLoop(interval):
    global onlinePlayers
    context = ssl._create_unverified_context()
    url = 'https://medivia.online/community/online/legacy'

    print("Fetching online players started with interval: " + str(interval))

    while (True):

        try:
            data = urlopen(url, context=context).read()
        except IncompleteRead:
            print("INCOMPLETE READ EXCEPTION")
            await asyncio.sleep(2)
            continue
        except urllib.error.HTTPError:
            print("HTTP ERROR EXCEPTION")
            await asyncio.sleep(2)
            continue
        except urllib.error.URLError:
            print("URL ERROR EXCEPTION")
            await asyncio.sleep(2)
            continue
        except aiohttp.errors.ClientOSError:
            print("CLIENT OS ERROR EXCEPTION")
            await asyncio.sleep(2)
            continue
        except ConnectionResetError:
            print("CONNECTION RESET EXCEPTION")
            await asyncio.sleep(2)
            continue
        except Exception:
            import traceback
            print("INCOMPLETE READ EXCEPTION")
            await asyncio.sleep(2)
            continue

        soup = BeautifulSoup(data, "html.parser")
        names = soup.find_all('div', class_='med-width-35')
        vocs = soup.find_all('div', class_='med-width-15')
        levels = soup.find_all('div', class_='med-width-25 med-text-right med-pr-40')

        players = list()
        for name, voc, level in zip(names, vocs, levels):
            players.append(Player(name.get_text(), voc.get_text(), level.get_text()))

        if len(players) > 2:
            del players[len(players) - 1]
            del players[0]

            for player in players:
                player.level = int(player.level)

            players.sort(reverse=True)
            onlinePlayers = list(players)

            del players[:]
            del data

        else:
            print("Fetching online players stopped - 0 players online.")
            print(len(players))

        await asyncio.sleep(interval)


def playerDataIntoArray(player, i):
    pvoc = player.profession
    voc = ""
    if pvoc == "Archmage" or pvoc == "Sorcerer":
        voc = "MS"
    if pvoc == "Druid" or pvoc == "Cleric":
        voc = "ED"
    if pvoc == "Knight" or pvoc == "Warrior":
        voc = "EK"
    if pvoc == "Ranger" or pvoc == "Scout":
        voc = "RP"
    if pvoc == "None":
        voc = "None"
    return [i, player.name, voc, str(player.level) + "``"]

def isTrue(x):
    if x:
        return 1
    else:
        return 0


findMatchingElems = lambda searchList, elem: [[i for i, x in enumerate(searchList) if x.name == e] for e in elem]

@bot.command()
async def friends(ctx): #todo fetch friends only on start, !addfriend and !removefriend commands
    topMessage = await ctx.send("...")
    initialMessage = await ctx.send("Loading friend list...")
    displayLimit = 45
    #find = lambda searchList, elem: [[i for i, x in enumerate(searchList) if x.name == e] for e in elem]
    tfl = list()
    conn = sqlite3.connect(sqlite)
    c = conn.cursor()

    while(1):
        await asyncio.sleep(1)
        for player in c.execute("SELECT name FROM friends"):
            tfl.append(player[0])

        findlist = list(filter(isTrue, findMatchingElems(onlinePlayers, tfl)))
        combinedLevels = 0
        vocAmounts = {"Archmage": 0, "Ranger": 0, "Druid": 0, "Knight": 0}
        playersArr = []
        for fin in findlist:
            if (len(playersArr) < displayLimit):
                player = onlinePlayers[fin[0]]
                playersArr.append(playerDataIntoArray(player, "``" + str(len(playersArr) + 1)))
                vocAmounts[player.profession] = vocAmounts[player.profession] + 1
                combinedLevels = combinedLevels + player.level

        formatedPlayersList = tabulate(playersArr, headers=['', '', '', ''], tablefmt="plain")
        total = sum(vocAmounts.values())
        if total <= 0:
            total = 1
        await initialMessage.edit(content=formatedPlayersList)
        await topMessage.edit(content=
                              "**``MS``**``: " + str(vocAmounts["Archmage"]) + ", "
                              "``**``EK``**``: " + str(vocAmounts["Knight"]) + ", "
                              "``**``RP``**``: " + str(vocAmounts["Ranger"]) + ", "
                              "``**``ED``**``: " + str(vocAmounts["Druid"]) + ", "
                              "``**``total``**``: " + str(sum(vocAmounts.values())) + " online.`` \n"
                              "**``Combined levels``**``: " + str(combinedLevels) + "`` \n"
                              "**``Average level``**``:   " + str("{0:.2f}".format(combinedLevels/total)) + "``")
        await ctx.channel.edit(reason=None, name="💗Friends " + str(sum(vocAmounts.values())))

        del findlist[:]
        del tfl[:]
        del playersArr[:]
        del vocAmounts

@bot.command()
async def addfriend(ctx, *a):

    name = ('' + ' '.join(a))
    r = requests.get('https://medivia.online/community/character/' + name)

    index = (r.text).find("name:</div><div class=\"med-width-50\">")

    if (index == -1):
        await ctx.send("Character with that name does not exist!")
        return

    message = ""
    i = 0
    while (r.text[index + 38 - 1 + i] != '<'):
        message = message + r.text[index + 38 - 1 + i]
        i = i + 1

    conn = sqlite3.connect(sqlite)
    c = conn.cursor()
    #c.execute('''CREATE TABLE friends (date text, name text)''')
    c.execute("INSERT INTO friends VALUES ('datea','"+message+"')")
    conn.commit()
    conn.close()
    await ctx.send("Character " + message + " has been added successfully!")

@bot.command()
async def removefriend(ctx, *a):

    name = ('' + ' '.join(a))
    r = requests.get('https://medivia.online/community/character/' + name)

    if ((r.text).find("name:</div><div class=\"med-width-50\">") == -1):
        await ctx.send("Character with that name doesnt not exist!")
        return

    conn = sqlite3.connect(sqlite)
    c = conn.cursor()
    c.execute("DELETE FROM friends WHERE name = '"+name+"'")
    conn.commit()
    conn.close()
    await ctx.send("Character " + name + " has been removed successfully!")

@bot.command()
async def online(ctx):
    minlvl = 0
    displayLimit = 45

    print("Starting online list on channel: " + str(ctx.channel))
    await ctx.send("Showing top " + str(displayLimit) + " online players on Legacy: \n")
    initialMessage = await ctx.send("Loading online list...")

    while(1):
        await asyncio.sleep(1)
        players = list(onlinePlayers)
        playersArr = []

        for player in players:
            if (int(player.level) >= minlvl and len(playersArr) < displayLimit):
                playersArr.append(playerDataIntoArray(player, "``" + str(len(playersArr)+1)))

        formatedPlayersList = tabulate(playersArr, headers=['','', '', ''], tablefmt="plain")
        print(str(time.asctime(time.localtime(time.time()))) + " - " + str(len(formatedPlayersList)))
        await initialMessage.edit(content="" + formatedPlayersList + "")
        await ctx.channel.edit(reason=None, name="Legacy online: " + str(len(players)))
        del players[:]
        del playersArr[:]

@bot.command()
async def level(ctx, *a):
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
async def deathfeed(ctx):
    lastName = ""
    while (1):
        await asyncio.sleep(5)
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
async def cat(ctx):
    await ctx.send("https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif")


@bot.command()
async def info(ctx):
    embed = discord.Embed(title="MedBot", description="v000 lots of bugs etc.", color=0xeee657)

    # give info about you here
    embed.add_field(name="Author", value="buy dip kek")

    # Shows the number of servers the bot is member of.
    embed.add_field(name="Server count", value=f"{len(bot.guilds)}")

    # give users a link to invite this bot to their server
    # embed.add_field(name="Invite", value="[Invite link](<insert your OAuth invitation link here>)")

    await ctx.send(embed=embed)


bot.remove_command('help')


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="MedBot", description="Some tools for medivia v000. List of commands:",
                          color=0xeee657)

    embed.add_field(name="!level player_name", value="Returns player's level.", inline=False)
    embed.add_field(name="!details player_name", value="Returns player's details.", inline=False)
    embed.add_field(name="!addfriend player_name", value="Adds player to the friend list.", inline=False)
    embed.add_field(name="!removefriend player_name", value="Removes player from the friend list.", inline=False)

    await ctx.send(embed=embed)


bot.run(TOKEN)



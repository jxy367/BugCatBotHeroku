import asyncio
import io
import os
import urllib
from urllib import request
import aiohttp

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands


API_KEY = os.environ.get('API_KEY')
TOKEN = os.environ.get('TOKEN')

# GOOGLE_CHROME_BIN = os.environ.get('GOOGLE_CHROM_BIN')
# CHROMEDRIVER_PATH = os.environ.get('CHROMEDRIVER_PATH')

client = commands.Bot(command_prefix="bugcat ", case_insensitive=True)

# Bug Cat Messages #

# Bug Cat Embeds #

on_cooldown = {}
cooldown_time = 10

noah_cooldown = False

# People
me = 191797757357457408
julian = 185940933160730624
kaius = 115589615603286024
kolson = 316041338862829569
riley = 306997179367555074
danny = 191426236935831552
esther = 145075344095969281
noah = 165481032043331584
mark = 213097197456064512
miguel = 385306442439065601


# Channels
venting_channel = 400096015740567552
main_channel = 239214414132281344
TS_channel = 405046053809946647
voice_text_channel = 455118686315872257


def make_mention(user_id: int):
    return "<@" + str(user_id) + ">"


def make_request(request_url, header):
    return requests.get(request_url, headers=header)


def get_cooldown_key(message_or_channel):
    global on_cooldown
    try:
        key = message_or_channel.guild
    except AttributeError:
        if isinstance(message_or_channel, discord.Message):
            key = message_or_channel.channel.id
        elif isinstance(message_or_channel, discord.TextChannel):
            key = message_or_channel.id
        else:
            key = "unfortunate"
    if key not in on_cooldown:
        on_cooldown[key] = 0
    return key


def get_current_cooldown(message_or_channel):
    key = get_cooldown_key(message_or_channel)
    return on_cooldown[key]


def reset_cooldown(message_or_channel):
    global on_cooldown
    global cooldown_time
    key = get_cooldown_key(message_or_channel)
    on_cooldown[key] = cooldown_time


def get_bug_cat_comic(ep_num: int):
    comic_url = get_bug_cat_comic_url(ep_num)
    if comic_url == -1:
        return ""

    comic_images = get_bug_cat_comic_images(comic_url)
    return comic_images


def get_bug_cat_comic_url(ep_num: int):
    main_request = requests.get(
        "https://www.webtoons.com/zh-hant/comedy/maomaochongkapo/a/viewer?title_no=394&episode_no=" + str(ep_num))
    alt_request = requests.get(
        "https://www.webtoons.com/zh-hant/comedy/maomaochongkapo/a/viewer?title_no=394&episode_no=" + str(ep_num + 8))
    main_url = main_request.url
    alt_url = alt_request.url
    main_title_section = main_url.split("/")[6]
    alt_title_section = alt_url.split("/")[6]

    if main_title_section.count(str(ep_num)) >= 1:
        print(main_url)
        return main_url

    elif alt_title_section.count(str(ep_num)) >= 1:
        print(alt_url)
        return alt_url

    else:
        x = ep_num
        while main_request.status_code == 200:
            x = x + 1
            main_request = requests.get(
                "https://www.webtoons.com/zh-hant/comedy/maomaochongkapo/a/viewer?title_no=394&episode_no=" + str(x))
            url = main_request.url
            if url.count(str(ep_num)) == 1:
                return url
    return -1


def get_latest_bug_cat_comic():
    list_url = "https://www.webtoons.com/zh-hant/comedy/maomaochongkapo/list?title_no=394&page=1"

    response = urllib.request.urlopen(list_url)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')

    list_object = soup.find(attrs={'id': "_listUl"})
    list_item = list_object.findChild()
    episode_object = list_item.findChild()
    episode_url = episode_object['href']

    comic_images = get_bug_cat_comic_images(episode_url)
    return comic_images


def get_bug_cat_comic_images(url: str):
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')

    comic_images = []

    for image in soup.findAll(attrs={'class': "_images"}):
        comic_images.append(image['data-url'])

    return comic_images


# Get information of message
async def get_message_data(msg):
    # Get string content
    content = msg.content

    # Get all file objects
    files = []
    for attachment in msg.attachments:
        f = open(attachment.filename, mode='w+b')
        await attachment.save(f)
        file = discord.File(f, attachment.filename)
        files.append(file)

    return content, files


async def get_dm_channel(user_id):
    user = client.get_user(user_id)
    user_dm = user.dm_channel
    if user_dm is None:
        await user.create_dm()
        user_dm = user.dm_channel
    return user_dm


# Functions run in loop


# reset display name loop
async def reset_display_name():
    await client.wait_until_ready()
    while not client.is_closed():
        for changed_guild in client.guilds:
            if changed_guild.me.display_name != "BugCat Bot":
                print(changed_guild.name)
                print(changed_guild.me.display_name)
                print("---")
                await changed_guild.me.edit(nick=None)
        await asyncio.sleep(60)


# cooldown loop
async def cooldown():
    global on_cooldown
    await client.wait_until_ready()
    while not client.is_closed():
        for guild in on_cooldown:
            on_cooldown[guild] = on_cooldown[guild] - 1
            if on_cooldown[guild] < 0:
                on_cooldown[guild] = 0
        await asyncio.sleep(1)


# Various awaited responses
async def await_message(message: discord.Message, content=None, embed=None):
    if content is None:
        await message.channel.send(embed=embed)
    elif embed is None:
        await message.channel.send(content=content)
    else:
        await message.channel.send(content=content, embed=embed)

    reset_cooldown(message)


async def await_channel(channel: discord.TextChannel, content=None, embed=None):
    if channel is not None:
        if content is None:
            await channel.send(embed=embed)
        elif embed is None:
            await channel.send(content=content)
        else:
            await channel.send(content=content, embed=embed)

    reset_cooldown(channel)


async def await_ctx(ctx: discord.ext.commands.Context, content=None, embed=None, files=None):
    await ctx.send(content=content, embed=embed, files=files)

    reset_cooldown(ctx.channel)


### Bug Cat Commands ###


@client.command()
async def ep(ctx, value):
    value = value.strip()
    value = value.lower()

    comic_images = []

    if value == "latest":
        comic_images = get_latest_bug_cat_comic()

    if value.isnumeric() and int(value) > 0:
        ep_num = int(value)
        comic_images = get_bug_cat_comic(ep_num)

    if len(comic_images) > 0:
        print(comic_images)

        i = 1
        await await_ctx(ctx, content="Episode found")
        for image_url in comic_images:
            async with aiohttp.ClientSession(headers={'referer': "https://www.webtoons.com/"}) as session:
                async with session.get(image_url) as resp:
                    print(resp.status)
                    data = io.BytesIO(await resp.read())
                    await ctx.send(file=discord.File(data, str(i)+".jpg"))
                    i += 1


@client.command()
async def fetch(ctx):
    return


@client.command()
async def kill(ctx):
    return

client.remove_command('help')


@client.command()
async def help(ctx):
    embed = discord.Embed(title="BugCat", description="List of commands:", color=0xeee657)

    embed.add_field(name="BugCat ep [# or 'latest']", value="Searches and returns the relevant episode",
                    inline=False)

    embed.add_field(name="BugCat help", value="Gives this message", inline=False)

    await ctx.send(embed=embed)


@client.event
async def on_message(message):
    global client

    cd = get_current_cooldown(message)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # Bot does not respond to bots
    if message.author.bot:
        return

    # Bot may be on cooldown
    guild_cooldown = cd <= 0
    if not guild_cooldown:
        return

    # Bot does not respond in the venting channel
    if message.channel.id == venting_channel:
        return

    if message.content.lower()[:6] == "bugcat":
        message.content = "bugcat" + message.content[6:]

    await client.process_commands(message)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    client.loop.create_task(reset_display_name())
    client.loop.create_task(cooldown())


client.run(TOKEN)

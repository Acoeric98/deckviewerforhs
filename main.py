import asyncio
import datetime
import os
import random

from patch import *

import discord
from discord import app_commands
from discord.ext import commands

from db.config import TOKEN
from image_creator import create_picture

client = commands.Bot(command_prefix="/",
                      activity=discord.Game(name="Analyzing decks"),
                      intents=discord.Intents.default())


generation_queue: asyncio.Queue[discord.Message] = asyncio.Queue()
queue_worker_task: asyncio.Task | None = None


async def generate_and_save(deck_code):
    image = await create_picture(deck_code)

    if not image:
        return

    x, y = image.size
    image = image.resize((int(x / 1.2), int(y / 1.2)))

    name = random.randint(1000000, 10000000)

    image.save(f"{name}.png", format="PNG")

    return name


async def process_mention_queue():
    while True:
        message = await generation_queue.get()
        start_time = datetime.datetime.now()

        try:
            deck_code = next(
                (word for word in message.content.split() if word.startswith("AA")),
                None,
            )
            if not deck_code:
                continue

            name = await generate_and_save(deck_code)
            if not name:
                continue

            await message.reply(file=discord.File(f"{name}.png"), mention_author=False)
            os.remove(f"{name}.png")
            print(datetime.datetime.now() - start_time)
        except Exception as exc:
            print("queue processing error:", exc)
        finally:
            generation_queue.task_done()


@client.event
async def on_ready():
    global queue_worker_task

    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print(discord.__version__)
    print("------")

    try:
        synced = await client.tree.sync()
        print(f"synced {len(synced)} commands")
        print("\n\n---------\n\n")
    except Exception as e:
        print("sync error:", e)

    print("Servers connected to:")
    sum_servers, sum_members = 0, 0
    for guild in sorted(client.guilds, key=lambda cl: cl.member_count):
        sum_servers += 1
        sum_members += guild.member_count
        print(guild.name, "-----", guild.member_count, "members")

    print(f"ALL: {sum_servers} servers, {sum_members} members")
    print("\n\n---------\n\n")

    if queue_worker_task is None or queue_worker_task.done():
        queue_worker_task = asyncio.create_task(process_mention_queue())


@client.tree.command(name="deck", description="Generates picture of deck by"
                                              'its code. Same as "/code"')
@app_commands.describe(deck_code="Generates picture of deck by its code."
                                 " May take a while")
async def deck(interaction: discord.Interaction, deck_code: str):
    await interaction.response.send_message("_Waiting for image to "
                                            "generate... "
                                            "It will be here soon_")
    name = await generate_and_save(deck_code)

    await interaction.edit_original_response(
        content="",
        attachments=[discord.File(f"{name}.png")]
    )

    os.remove(f"{name}.png")


@client.tree.command(name="code", description="Generates picture of deck by "
                                              'its code. Same as "/deck"')
@app_commands.describe(deck_code="Generates picture of deck by its code."
                                 " May take a while")
async def code(interaction: discord.Interaction, deck_code: str):
    await interaction.response.send_message("_Waiting for image to "
                                            "generate... "
                                            "It will be here soon_")
    name = await generate_and_save(deck_code)

    await interaction.edit_original_response(
        content="",
        attachments=[discord.File(f"{name}.png")]
    )

    os.remove(f"{name}.png")


@client.command(name='deck')
async def deck(ctx, deck_code):
    name = await generate_and_save(deck_code)

    await ctx.send(file=discord.File(f"{name}.png"))

    os.remove(f"{name}.png")


@client.event
async def on_message(message: discord.message.Message):
    if message.author.bot:
        return

    if client.user in message.mentions:
        has_deck_code = any(word.startswith("AA") for word in message.content.split())
        if has_deck_code:
            await generation_queue.put(message)

    await client.process_commands(message)


client.run(TOKEN)

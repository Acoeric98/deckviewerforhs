import os
import shutil
import asyncio

from db.config import FOLDER
from framework import GRequestsDownloader


async def download_cards(cards):
    if os.path.exists(FOLDER):
        shutil.rmtree(FOLDER)
    os.mkdir(FOLDER)

    cards_api = GRequestsDownloader()
    await asyncio.to_thread(cards_api.process_cards, cards)

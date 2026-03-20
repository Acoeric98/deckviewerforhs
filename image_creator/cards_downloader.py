import asyncio
import os

from db.config import FOLDER
from framework import GRequestsDownloader


async def download_cards(cards):
    os.makedirs(FOLDER, exist_ok=True)

    missing_cards = []
    seen = set()
    for card in cards:
        if card["slug"] in seen:
            continue
        seen.add(card["slug"])

        path = os.path.join(FOLDER, f"{card['slug']}.png")
        if not os.path.exists(path):
            missing_cards.append(card)

    if not missing_cards:
        return

    cards_api = GRequestsDownloader()
    await asyncio.to_thread(cards_api.process_cards, missing_cards)

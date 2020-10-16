import typing
import random
import data

FIVE_STAR_RATE = 0.006
FIVE_STAR_BOT = 90
FOUR_STAR_RATE = 0.051
FOUR_STAR_BOT = 10
FIVE_STAR_THRESHOLD = FIVE_STAR_RATE
FOUR_STAR_THRESHOLD = FIVE_STAR_RATE + FOUR_STAR_RATE

# Initialize the database
repo = {}
for i in range(3, 6):
    repo[i] = []
for weapon_key in data.weapons.getall():
    rarity = data.weapons.get(weapon_key)["rarity"]
    # Only include 3+ rarity weapons
    if rarity >= 3:
        repo[rarity].append(weapon_key)

for char_key in data.characters.getall():
    # Exclude traveler
    if char_key != "traveler":
        repo[data.characters.get(char_key)["rarity"]].append(char_key)


def pull(five_star_base: int = 0, four_star_base: int = 0):

    # Decide which the bottom pool is. Lower can still get items in a hgiher pool
    bot_pool = 3
    if five_star_base >= FIVE_STAR_BOT - 1:
        bot_pool = 5
    elif four_star_base >= FOUR_STAR_BOT - 1:
        bot_pool = 4

    # Decide which pool to get
    pool = 3
    pool_rand = random.random()
    if bot_pool == 5 or pool_rand <= FIVE_STAR_THRESHOLD:
        pool = 5
    elif bot_pool == 4 or pool_rand <= FOUR_STAR_THRESHOLD:
        pool = 4
    else:
        pool = 3

    # Decide which item to get
    item_rand = random.randrange(0, len(repo[pool]))
    item_id = repo[pool][item_rand]

    return item_id, pool


def main():
    """
    Test function
    """
    return

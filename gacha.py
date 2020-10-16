import typing
import random
import data

FIVE_STAR_RATE = 0.006
FIVE_STAR_BOT = 90
FOUR_STAR_RATE = 0.051
FOUR_STAR_BOT = 10
FIVE_STAR_THRESHOLD = FIVE_STAR_RATE
FOUR_STAR_THRESHOLD = FIVE_STAR_RATE + FOUR_STAR_RATE
UP_RATE = 0.5
NORMAL = "normal"
UP = "up"
IS_UP = "is_up"

# Initialize the database
wishes = []
for wish_key in data.wishes.getall():
    wishes.append({})
    wishes[-1]["name"] = wish_key
    wishes[-1][NORMAL] = {}
    for i in range(3, 6):
        wishes[-1][NORMAL][i] = []
    wish = data.wishes.get(wish_key)
    for item in wish[NORMAL]:
        rarity = data.get_rarity(item)
        wishes[-1][NORMAL][rarity].append(item)

    wishes[-1][IS_UP] = wish[IS_UP]
    if wishes[-1][IS_UP]:
        wishes[-1][UP] = {}
        for i in range(3, 6):
            wishes[-1][UP][i] = []
        for item in wish[UP]:
            rarity = data.get_rarity(item)
            wishes[-1][UP][rarity].append(item)


def pull(wish: int = 0, five_star_base: int = 0, four_star_base: int = 0):

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

    # If the pool has up, decide if get up items
    wish_repo = wishes[wish][NORMAL]
    if wishes[wish][IS_UP] and len(wishes[wish][UP][pool]) > 0:
        up_rand = random.random()
        if up_rand >= UP_RATE:
            wish_repo = wishes[wish][UP]

    # Decide which item to get
    item_rand = random.randrange(0, len(wish_repo[pool]))
    item_id = wish_repo[pool][item_rand]

    return item_id, pool


def main():
    """
    Test function
    """
    return

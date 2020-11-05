import json
import pickledb

weapons = pickledb.load('weapons.db', False)
characters = pickledb.load('characters.db', False)
word_keys = pickledb.load('word_keys.db', False)
wishes = pickledb.load('wishes.db', False)


def readWeeklyData(file: str):
    # Read file
    f = open(file, "r")
    content = f.read()
    f.close()

    # Load as JSON
    data_dic = json.loads(content)

    weekday_dic = [None]*7
    for i in range(7):
        weekday_dic[i] = []
    for character in data_dic:
        for weekday in data_dic[character]:
            weekday_dic[weekday-1].append(character)

    return weekday_dic


def get_rarity(key: str):
    if key in characters.getall():
        return characters.get(key)["rarity"]
    if key in weapons.getall():
        return weapons.get(key)["rarity"]
    return 0

import json

# Read JSON data as a dictionary
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
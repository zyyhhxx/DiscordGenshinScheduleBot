import language
from datetime import datetime

SELF = "self"
DEFAULT_MINE_REFRESH_INTERVAL = 259200
DEFAULT_MINE_NOTIFY_INTERVAL = 1800


def get_char_repr(char_name: str, language_key: str):
    char_repr = language.get_word("you", language_key)
    if char_name != SELF:
        char_repr = char_name
    return char_repr


def get_time_repr(datetime_string: str, elapsed: bool, language_key: str,
                  mine_refresh_interval: int = DEFAULT_MINE_REFRESH_INTERVAL):
    current_datetime = datetime.now()
    start_datetime = datetime.strptime(
        datetime_string, "%Y-%m-%d %H:%M:%S.%f")
    delta_datetime = current_datetime - start_datetime
    if elapsed:
        total_seconds = delta_datetime.total_seconds()
    else:
        total_seconds = mine_refresh_interval - delta_datetime.total_seconds()
    mins = (total_seconds // 60) % 60
    hours = (total_seconds // 3600) % 24
    days = total_seconds // 86400
    time_repr = "{}{}".format(
        int(mins), language.get_word("minutes", language_key))
    if hours > 0:
        time_repr = "{}{}".format(int(hours), language.get_word(
            "hours", language_key)) + time_repr
    if days > 0:
        time_repr = "{}{}".format(int(days), language.get_word(
            "days", language_key)) + time_repr

    return time_repr

from json import loads
from random import choice

with open("tourist.json", mode="r", encoding="utf-8") as json_file:
    f = json_file.read()
PHRASES = loads(f)


def get_phrase(state: str, stage: str) -> dict:
    return PHRASES["state"][state][stage]


def get_error_phrase(arg=None):
    if not arg:
        return choice(
            [
                PHRASES["errors"]["first_error"],
                PHRASES["errors"]["second_error"],
                PHRASES["errors"]["third_error"]
            ]
        )
    return PHRASES["errors"][arg]

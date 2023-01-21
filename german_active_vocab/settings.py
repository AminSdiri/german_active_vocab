from pathlib import Path

from PyQt5.QtGui import QFont
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

# TODO (5) expose this vars to user interraction

DICT_DATA_PATH = Path(__file__).parents[1].resolve() / 'data'
DICT_SRC_PATH = Path(__file__).parents[0].resolve()

MAINWORD_FONT = '"Arial Black"'
CONJUGATION_FONT = '"Lato"'
WORDCLASS_FONT = '"Lato"'
NORMAL_FONT = QFont("Arial", 12)  # 3, QFont.Bold)
FOCUS_FONT = QFont("Arial", 20)

QUIZ_PRIORITY_ORDER: str = 'due_words'
MAX_REV_PER_SESSION = 10

JINJA_ENVIRONEMENT = Environment(loader=FileSystemLoader(DICT_SRC_PATH / 'RenderHTML' / 'templates'),
                                 trim_blocks=True,
                                 lstrip_blocks=True)

ANKI_CONFIG = {
        "base": "/home/parkdepot/.local/share/Anki2/",
        "profile": "nachi",
        "deck": 'Active German',
        "model": 'GermanCloze with_Hint',
        "overwrite": False
        }

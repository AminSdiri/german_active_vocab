from pathlib import Path

from PyQt5.QtGui import QFont
from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

# TODO (4) expose this vars to user interraction

dict_data_path = Path(__file__).parents[1].resolve() / 'data'
dict_src_path = Path(__file__).parents[0].resolve()

Main_word_font = '"Arial Black"'
Conjugation_font = '"Lato"'
Word_classe_font = '"Lato"'
normal_font = QFont("Arial", 12)  # 3, QFont.Bold)
focus_font = QFont("Arial", 20)
quiz_priority_order: str = 'due_words'
maxrevpersession = 10

jinja_env = Environment(loader=FileSystemLoader(dict_src_path / 'templates'),
                        trim_blocks=True,
                        lstrip_blocks=True)

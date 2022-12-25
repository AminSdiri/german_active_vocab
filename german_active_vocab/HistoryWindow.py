import os
from PyQt5.QtWidgets import (QPushButton, QWidget, QTextEdit, QListWidget)
from PyQt5.QtGui import QTextCursor

from settings import dict_data_path


from utils import read_str_from_file, read_text_from_files, set_up_logger, update_dataframe_file

logger = set_up_logger(__name__)

class WordlistWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        logger.info("init Wordlist_Window")

        self.wordlist = QListWidget(self)

        self.fill_wordlist()
        self.wordlist.itemDoubleClicked.connect(self.parent().show_html_from_history_list)
        self.wordlist.resize(390, 490)
        self.wordlist.move(5, 5)

    def fill_wordlist(self):
        files = (dict_data_path / 'html').glob("*.html")
        files = list(files)
        files.sort(key=os.path.getmtime, reverse=True)
        files = [x.stem for x in files]
        self.wordlist.addItems(files)


class HistoryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init defHistory")

        self.return_button = QPushButton('Return', self)
        self.return_button.move(390, 660)

        self.focus_button = QPushButton('Focus', self)
        self.focus_button.move(490, 660)

        self.close_button = QPushButton('Close', self)
        self.close_button.move(590, 660)

        self.txt_cont = QTextEdit(self)
        self.txt_cont.move(5, 5)
        self.txt_cont.resize(690, 640)
        self.txt_cont.setReadOnly(True)

        index = parent.wordlist_window.returned_index
        self.history_entry = index if type(index) is str else index.text()
        history_entry_path = dict_data_path / 'html' / f'{self.history_entry}.html'
        text = read_str_from_file(history_entry_path)

        self.txt_cont.insertHtml(text)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

        self.return_button.clicked.connect(self.parent().launch_history_list_window)
        self.close_button.clicked.connect(self.parent().close)
        self.focus_button.clicked.connect(self.add_to_focus_from_history)

    def add_to_focus_from_history(self):
        logger.info("add_to_focus_from_history")

        word = self.history_entry.replace('.quiz', '')
        full_text, quiz_text = read_text_from_files(word)

        update_dataframe_file(word, full_text, quiz_text)
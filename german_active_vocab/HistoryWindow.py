import os
from PyQt5.QtWidgets import (QPushButton, QWidget, QTextEdit, QListWidget)
from PyQt5.QtGui import QTextCursor
from GetDict.GenerateDict import update_hidden_words_in_dict
from SavingToQuiz import hide_text

from settings import DICT_DATA_PATH


from utils import read_str_from_file, read_text_from_files, sanitize_word, set_up_logger, update_dataframe_file, write_str_to_file

logger = set_up_logger(__name__)

# TODO (1) add ability to delete enteries from history window
# TODO (1) use database to save everything

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
        files = (DICT_DATA_PATH / 'html').glob("*.html")
        files = list(files)
        files.sort(key=os.path.getmtime, reverse=True)
        files = [x.stem for x in files]
        self.wordlist.addItems(files)


class HistoryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init defHistory")

        self.hide_button = QPushButton('Hide', self)
        self.hide_button.move(290, 660)

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
        history_entry_path = DICT_DATA_PATH / 'html' / f'{self.history_entry}.html'
        text = read_str_from_file(history_entry_path)

        self.txt_cont.insertHtml(text)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

        self.return_button.clicked.connect(self.parent().launch_history_list_window)
        self.close_button.clicked.connect(self.parent().close)
        self.focus_button.clicked.connect(self.add_to_focus_from_history)
        self.hide_button.clicked.connect(self.hide_word_manually_from_history_window)

    def add_to_focus_from_history(self):
        logger.info("add_to_focus_from_history")

        word = self.history_entry.replace('.quiz', '')
        full_text, quiz_text = read_text_from_files(word)

        update_dataframe_file(word, full_text, quiz_text)

    def hide_word_manually_from_history_window(self):
        logger.info("hide_word_manually")
        # DONE (1) add manually hidden words to dict_file
        selected_text2hide = self.txt_cont.textCursor().selectedText()

        word = self.history_entry.replace('.quiz', '')
        saving_word = sanitize_word(word)
        update_hidden_words_in_dict(selected_text2hide, saving_word)

        logger.debug(f'word2hide: {selected_text2hide}')
        self.txt_cont.clear()
        history_entry_path = DICT_DATA_PATH / 'html' / f'{self.history_entry}.html'
        text = read_str_from_file(history_entry_path)
        text = hide_text(text, selected_text2hide)
        self.txt_cont.insertHtml(text)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)
        logger.info("save_custom_quiztext_from_historymode")
        write_str_to_file(history_entry_path, text, notification_list=['gespeichert!'], overwrite=True)
        logger.info('gespeichert!')

        self.show()
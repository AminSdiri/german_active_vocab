# !/usr/bin/env python3
# coding = utf-8

import logging
from pathlib import Path
import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QMessageBox
from PyQt5.QtGui import QTextCharFormat, QFont, QTextCursor, QColor
from datetime import datetime, timedelta
import pandas as pd

from GetData import DefEntry
from ProcessData import save_function
from WordProcessing import create_quiz_html, hide_text
from DictWindows import (SearchWindow,
                         DefinitionWindow,
                         QuizWindow,
                         FocusWindow,
                         FocusRatingDiag,
                         QuizRatingDiag,
                         HistoryWindow)
from ProcessQuizData import (
    FocusEntry, QuizEntry, spaced_repetition)
# ,quiz_counter

# TODO write test functions for the different functionalities,
# use the debug_mode variable for pytest

# TODO! create setup.py to take care of
# - creating dirs
# - install requirements.txt
# etc

# TODO! add licence for only personal use, no commercial use

# set up logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)  # Levels: debug, info, warning, error, critical
formatter = logging.Formatter(
    '%(levelname)8s -- %(name)-15s line %(lineno)-4s: %(message)s')
logger.handlers[0].setFormatter(formatter)

now = datetime.now() - timedelta(hours=3)

logger.debug(now)

dict_path = Path.home() / 'Dictionnary'

Main_word_font = '"Arial Black"'
Conjugation_font = '"Lato"'
Word_classe_font = '"Lato"'
normal_font = QFont("Arial", 12)  # 3, QFont.Bold)
focus_font = QFont("Arial", 20)
quiz_priority_order: str = 'due_words'
maxrevpersession = 10

# TODO! find alternative to notify-send for windows and macos
# os-agnostic notification alternative

# subprocess.Popen(['notify-send', 'N-Dict'])


# TODO convert functions to methods for Def, Quiz and Focus entries classes


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        logger.info("init MainWindow")
        super(MainWindow, self).__init__(parent)
        self.setGeometry(535, 150, 210, 50)
        self.launch_search_window()

        df = pd.read_csv(dict_path / 'wordlist.csv')
        df.set_index('Word', inplace=True)
        df['Next_date'] = pd.to_datetime(
            df['Next_date'])  # , format='%d.%m.%y')
        df['Created'] = pd.to_datetime(df['Created'])  # , format='%d.%m.%y')
        df['Previous_date'] = pd.to_datetime(
            df['Previous_date'])  # , format='%d.%m.%y')
        self.wordlist_df = df

        # TODO! check datetimeformat by writing df to csv
        # (WARNING: inconsistant datetimes)
        focus_df = pd.read_csv(dict_path / 'wordpart_list.csv')
        focus_df['Next_date'] = pd.to_datetime(
            focus_df['Next_date'], format='%d.%m.%y')
        focus_df['Created'] = pd.to_datetime(
            focus_df['Created'], format='%d.%m.%y')
        focus_df['Previous_date'] = pd.to_datetime(
            focus_df['Previous_date'], format='%d.%m.%y')

        focus_df.set_index('Wordpart', inplace=True)
        self.focus_df = focus_df

    def launch_search_window(self):
        logger.info("Launch search window")

        nbargin = len(sys.argv) - 1
        if nbargin > 0:
            logger.debug('shell commade with args')
            self.launch_definition_window()
        else:
            logger.debug('0 Args')
            self.resize(345, 50)  # 45
            self.move(535, 150)
            self.search_form = SearchWindow(self)
            self.setWindowTitle("Dictionnary")
            self.setCentralWidget(self.search_form)
            try:
                self.search_form.line.setText(self.def_obj.word)
            except AttributeError:
                pass
            self.search_form.line.returnPressed.connect(
                self.launch_definition_window)
            self.search_form.define_button.clicked.connect(
                self.launch_definition_window)
            self.search_form.history_button.clicked.connect(
                self.launch_history_window)
            self.search_form.quiz_button.clicked.connect(
                self.launch_quiz_window)
            self.search_form.focus_button.clicked.connect(
                self.launch_focus_window)
            self.show()

    def launch_definition_window(self):
        logger.info("launch definition window")
        self.move(315, 50)
        self.resize(700, 690)
        self.def_window = DefinitionWindow(self)
        self.setWindowTitle("Wörterbuch")
        self.setCentralWidget(self.def_window)

        nbargin = len(sys.argv) - 1
        if nbargin == 0:
            logger.debug('Opening from Classical')

            word = self.search_form.line.text()
            checkbox_en = self.search_form.translate_en.isChecked()
            checkbox_fr = self.search_form.translate_fr.isChecked()

            self.def_obj = DefEntry(word=word,
                                    checkbox_en=checkbox_en,
                                    checkbox_fr=checkbox_fr)

        elif nbargin == 1:
            logger.debug('Opening from Magical 1 Arg')

            word = sys.argv[1]

            self.def_obj = DefEntry(word=word)

        elif nbargin == 2:
            logger.debug('Opening from Magical 2 Args')

            word = sys.argv[1]
            beispiel_de = sys.argv[2].replace("//QUOTE", "'")

            self.def_obj = DefEntry(word=word,
                                    beispiel_de=beispiel_de)

            self.def_window.beispiel.insert(beispiel_de)
        elif nbargin == 3:
            logger.debug('Opening from Magical 3 Args')

            word = sys.argv[1]
            beispiel_de = sys.argv[2].replace("//QUOTE", "'")
            beispiel_en = sys.argv[3].replace("//QUOTE", "'")

            self.def_obj = DefEntry(word=word,
                                    beispiel_de=beispiel_de,
                                    beispiel_en=beispiel_en
                                    )

            self.def_window.beispiel.insert(beispiel_de)
            self.def_window.beispiel2.insert(beispiel_en)
        else:
            raise RuntimeError('Number of argument exceeds 3')

        self.def_window.txt_cont.setFont(normal_font)
        self.def_window.txt_cont.insertHtml(self.def_obj.defined_html)
        self.def_window.txt_cont.moveCursor(
            QTextCursor.Start)  # .textCursor(defined_html)

        self.def_window.return_button.clicked.connect(
            self.launch_search_window)
        self.def_window.save_button.clicked.connect(self.save_definition)
        self.def_window.close_button.clicked.connect(self.close)
        self.def_window.highlight_button.clicked.connect(self.highlight_text)
        self.show()

    def launch_history_window(self):
        logger.info("launch history list window")
        self.resize(400, 500)
        self.move(315, 50)
        self.history_window = HistoryWindow(self)
        self.setWindowTitle("Wörterbuch")
        files = dict_path.glob("*.html")
        files = list(files)
        files.sort(key=os.path.getmtime, reverse=True)
        files = [x.stem for x in files]
        self.allwords = QListWidget(self)
        self.allwords.addItems(files)
        self.allwords.itemDoubleClicked.connect(
            self.show_html_from_history_list)
        self.setCentralWidget(self.history_window)
        self.allwords.resize(390, 490)
        self.allwords.move(5, 5)
        self.allwords.show()

    def launch_quiz_window(self):
        logger.info("launch_quiz_window")
        self.resize(700, 700)
        self.move(315, 10)
        self.quiz_window = QuizWindow(self)
        self.setCentralWidget(self.quiz_window)

        self.quiz_obj = QuizEntry(quiz_priority_order=quiz_priority_order,
                                  words_dataframe=self.wordlist_df,
                                  maxrevpersession=maxrevpersession)

        logger.debug('queued_word output: ' +
                     self.quiz_obj.quiz_params['queued_word'])

        no_words_left4today, reached_daily_limit = self.quiz_obj.quiz_counter()

        if reached_daily_limit:
            self.reached_daily_limit_dialogue()

        if no_words_left4today:
            self.no_words_left4today_dialogue()

        self.setWindowTitle(self.quiz_obj.quiz_window_titel)
        self.quiz_window.txt_cont.insertHtml(self.quiz_obj.quiz_text)
        self.quiz_window.next_btn.clicked.connect(self.quiz_score)
        self.quiz_window.next_btn.clicked.connect(self.launch_quiz_window)
        self.quiz_window.close_button.clicked.connect(self.close)
        self.quiz_window.populate.clicked.connect(self.reveal_full_html_quiz)
        self.quiz_window.save_button.clicked.connect(
            self.save_custom_quiztext_from_quizmode)
        self.quiz_window.update_button.clicked.connect(self.update_word_html)
        self.quiz_window.hide_button.clicked.connect(self.hide_word_manually)
        self.show()

    def launch_focus_window(self, index):
        logger.info("launch_focus_window")
        self.resize(700, 300)
        self.move(315, 180)
        self.focus_window = FocusWindow(self)
        self.setCentralWidget(self.focus_window)
        self.setWindowTitle("Wörterbuch: Focus mode")

        self.focus_obj = FocusEntry(focus_df=self.focus_df)

        self.focus_window.txt_cont.setFont(focus_font)
        self.focus_window.txt_cont.insertHtml(self.focus_obj.focus_part)

        self.focus_window.next_btn.clicked.connect(self.focus_score)
        self.focus_window.next_btn.clicked.connect(self.launch_focus_window)
        self.focus_window.ignore_button.clicked.connect(self.ignore_part)
        self.focus_window.ignore_button.clicked.connect(
            self.launch_focus_window)
        self.show()

    def quiz_score(self):
        logger.info("quiz_score")
        self.rating_diag_quiz = QuizRatingDiag(self)
        df = self.wordlist_df
        self.rating_diag_quiz.show()
        self.reveal_full_html_quiz()
        if self.rating_diag_quiz.exec_():
            saving_file = 'wordlist.csv'
            easiness = self.rating_diag_quiz.easiness
            spaced_repetition(easiness,
                              now,
                              df,
                              saving_file,
                              **self.quiz_obj.quiz_params)

    def focus_score(self):
        logger.info("focus_score")
        logger.debug('updating wordpart scores')
        self.rating_diag_focus = FocusRatingDiag(self)
        self.rating_diag_focus.show()
        self.reveal_full_html_focus()
        if self.rating_diag_focus.exec_():
            saving_file = 'wordpart_list.csv'
            easiness = self.rating_diag_focus.easiness
            spaced_repetition(easiness,
                              now,
                              self.focus_obj.focus_df,
                              saving_file,
                              **self.focus_obj.focus_params_dict)

    def reached_daily_limit_dialogue(self):
        logger.info("reached_daily_limit_dialogue")
        choice = QMessageBox.question(self, 'Extract!',
                                      "you have revisited 10 Words, Well done!"
                                      " Come back later... "
                                      "(If you want to continue hit Yes!)",
                                      QMessageBox.Yes | QMessageBox.Close)
        if choice == QMessageBox.Yes:
            logger.debug("resetting Count")
            self.quiz_obj._nb_revisited = 0
            self.show()
        else:
            sys.exit()

    def no_words_left4today_dialogue(self):
        global quiz_priority_order
        logger.info("no_words_left4today_dialogue")
        choice = QMessageBox.question(self, 'Extract!',
                                      "Well done, you have all planned words "
                                      "revisited. Want to switch priority to "
                                      "old words?",
                                      QMessageBox.Yes | QMessageBox.Close)
        if choice == QMessageBox.Yes:
            logger.debug("Repeating list Naaaaaaoooww!!!!")
            quiz_priority_order = 'old_words'
            logger.debug('mod switch')
            self.quiz_window.txt_cont.clear()
            self.launch_quiz_window()
        else:
            sys.exit()

    def show_html_from_history_list(self, index):
        logger.info("show_html_from_history_list")
        self.resize(700, 700)
        self.move(315, 50)

        self.history_window = HistoryWindow(self)
        self.setWindowTitle("Wörterbuch")
        self.setCentralWidget(self.history_window)

        if type(index) is str:
            wrd = index
        else:
            wrd = index.text()
        name = dict_path / (wrd+'.html')
        file = open(name, 'r')
        text = file.read()
        self.history_window.txt_cont.insertHtml(text)

        self.history_window.return_button.clicked.connect(
            self.launch_history_window)
        self.history_window.close_button.clicked.connect(self.close)
        self.show()

    def ignore_part(self):
        logger.info("ignore_part")
        focus_df = self.focus_obj.focus_df
        focus_df.loc[
            self.focus_obj.focus_params_dict['queued_word'], "Ignore"] = 1
        focus_df.to_csv(dict_path / 'wordpart_list.csv')

    def update_word_html(self):
        logger.info("update_word_html")
        subprocess.Popen(['dic.py', self.quiz_obj.quiz_params['queued_word']])

    def hide_word_manually(self):
        logger.info("hide_word_manually")
        selected_text2hide = self.quiz_window.txt_cont.textCursor()\
            .selectedText()
        logger.debug('word2hide: '+selected_text2hide)
        self.quiz_window.txt_cont.clear()
        self.quiz_obj.quiz_text = hide_text(self.quiz_obj.quiz_text,
                                            selected_text2hide)
        self.quiz_window.txt_cont.insertHtml(self.quiz_obj.quiz_text)
        self.show()

    def reveal_full_html_quiz(self):
        logger.info("reveal_full_html_quiz")
        self.quiz_window.txt_cont.clear()
        self.quiz_window.txt_cont.insertHtml(self.quiz_obj.full_text)

        self.quiz_window.next_btn.clicked.connect(self.quiz_score)
        self.quiz_window.next_btn.clicked.connect(self.launch_quiz_window)
        self.quiz_window.save_button.clicked.connect(
            self.save_custom_definition_from_quizmode)
        self.show()

    def reveal_full_html_focus(self):
        logger.info("reveal_full_html_focus")
        logger.debug('reveal_full_html_focus')
        full_text = self.focus_obj.focus_part_revealed
        self.focus_window = FocusWindow(self)
        self.setWindowTitle("Wörterbuch: Focus")
        self.setCentralWidget(self.focus_window)
        self.focus_window.txt_cont.setFont(focus_font)
        self.focus_window.txt_cont.insertHtml(full_text)
        self.focus_window.next_btn.clicked.connect(self.focus_score)
        self.focus_window.next_btn.clicked.connect(self.launch_focus_window)
        self.show()

    def highlight_text(self):
        logger.info("highlight_text")
        format = QTextCharFormat()
        color = QColor(3, 155, 224)
        color = QColor(220*1.15, 212*1.15, 39*1.15)
        format.setForeground(color)
        self.def_window.txt_cont.textCursor().mergeCharFormat(format)

    def save_definition(self):
        logger.info("save_definition")

        studie_tag = self.def_window.save_to_stud.isChecked()
        defined_user_html = self.def_window.txt_cont.toHtml()
        beispiel_de = self.def_window.beispiel.text()
        beispiel_en = self.def_window.beispiel2.text()
        words_2_hide = self.def_obj.words2hide
        word = self.def_obj.word
        tag = ''
        if studie_tag:
            tag = 'Studium'

        save_function(dict_path, word, defined_user_html, beispiel_de,
                      beispiel_en, tag, words_2_hide, now)

    def save_custom_definition_from_quizmode(self):
        logger.info("save_custom_definition_from_quizmode")
        beispiel_de = self.quiz_window.beispiel.text()
        defined_html = self.quiz_obj.full_text
        clean_html = self.quiz_obj.quiz_text
        if not beispiel_de == '':
            clean_beispiel_de = create_quiz_html(
                beispiel_de, self.def_obj.words2hide)
            if 'Eigenes Beispiel' in defined_html:
                clean_html += ('<br><i>&nbsp;&nbsp;&nbsp;&nbsp;' +
                               clean_beispiel_de+'</i>')
                defined_html += ('<br><i>&nbsp;&nbsp;&nbsp;&nbsp;' +
                                 beispiel_de+'</i>')
            else:
                clean_html += ('<br><br><b>Eigenes Beispiel:</b><br><i>&nbsp;'
                               '&nbsp;&nbsp;&nbsp;' + clean_beispiel_de+'</i>')
                defined_html += ('<br><br><b>Eigenes Beispiel:</b><br><i>'
                                 '&nbsp;&nbsp;&nbsp;&nbsp;' +
                                 beispiel_de+'</i>')

        quiz_file_path = self.quiz_obj.quiz_file_path
        full_file_path = self.quiz_obj.full_file_path

        # try:
        f = open(quiz_file_path, 'w')
        f.write(defined_html)
        f.close()
        # except:
        #     pass
        # try:
        f = open(full_file_path, 'w')
        f.write(clean_html)
        f.close()
        # subprocess.Popen(['notify-send', 'Beispiel gespeichert!'])
        logger.info('Beispiel gespeichert!')
        # except:
        #     logger.error('Error writing')
        #     # subprocess.Popen(['notify-send', 'Error writing'])
        #     pass

    def save_custom_quiztext_from_quizmode(self):
        logger.info("save_custom_quiztext_from_quizmode")
        clean_html = self.quiz_window.txt_cont.toHtml()

        quiz_file_path = self.quiz_obj.quiz_file_path

        # try:
        f = open(quiz_file_path, 'w')
        f.write(clean_html)
        f.close()
        # subprocess.Popen(['notify-send', 'gespeichert!'])
        logger.info('gespeichert!')
        # except:
        #     logger.error('Error writing')
        #     # subprocess.Popen(['notify-send', 'Error writing'])
        #     pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
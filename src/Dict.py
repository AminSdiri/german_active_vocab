# !/usr/bin/env python3
# coding = utf-8

from pathlib import Path
import sys
import os
import subprocess
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QApplication,
                             QErrorMessage,
                             QMainWindow,
                             QListWidget,
                             QMessageBox)
from PyQt5.QtGui import QTextCharFormat, QFont, QTextCursor, QColor
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup as bs
import traceback

from GetData import DefEntry
from ProcessData import save_function
from WordProcessing import (create_quiz_html,
                            fix_html_with_custom_example,
                            hide_text)
from DictWindows import (SearchWindow,
                         DefinitionWindow,
                         QuizWindow,
                         FocusWindow,
                         FocusRatingDiag,
                         QuizRatingDiag,
                         HistoryWindow)
from ProcessQuizData import (
    FocusEntry, QuizEntry, ignore_headers, spaced_repetition)
from utils import set_up_logger

# TODO write test functions for the different functionalities,
# use the debug_mode variable for pytest

# TODO! create setup.py to take care of
# - creating dirs
# - install requirements.txt
# etc

# TODO! add licence for only personal use, no commercial use

# TODO! find alternative to notify-send for windows and macos
# os-agnostic notification alternative

# subprocess.Popen(['notify-send', 'N-Dict'])


# TODO convert functions to methods for Def, Quiz and Focus entries classes

logger = set_up_logger(__name__)

dict_path = Path.home() / 'Dictionnary'
Main_word_font = '"Arial Black"'
Conjugation_font = '"Lato"'
Word_classe_font = '"Lato"'
normal_font = QFont("Arial", 12)  # 3, QFont.Bold)
focus_font = QFont("Arial", 20)
quiz_priority_order: str = 'due_words'
maxrevpersession = 10
now = datetime.now() - timedelta(hours=3)


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
        df['Created'] = pd.to_datetime(df['Created'])
        df['Previous_date'] = pd.to_datetime(
            df['Previous_date'])
        self.wordlist_df = df

        # TODO! check datetimeformat by writing df to csv
        # (WARNING: inconsistant datetimes)
        focus_df = pd.read_csv(dict_path / 'wordpart_list.csv')
        focus_df['Next_date'] = pd.to_datetime(
            focus_df['Next_date'])
        focus_df['Created'] = pd.to_datetime(
            focus_df['Created'])
        focus_df['Previous_date'] = pd.to_datetime(
            focus_df['Previous_date'])
        focus_df.set_index('Wordpart', inplace=True)
        self.focus_df = focus_df

        self.error_dialog = QErrorMessage()
        # self.error_dialog.showMessage('Oh no!')

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
            if hasattr(self, 'def_obj'):
                self.search_form.line.setText(self.def_obj.word)
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

    def highlight_text(self):
        logger.info("highlight_text")
        format = QTextCharFormat()
        color = QColor(3, 155, 224)
        color = QColor(220*1.15, 212*1.15, 39*1.15)
        format.setForeground(color)
        self.def_window.txt_cont.textCursor().mergeCharFormat(format)

    def launch_history_window(self):

        logger.info("launch history list window")

        # TODO!!! allow modifing html in history Window
        # TODO!!! allow deleting html from history Window ( file and DF entry)
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

    def show_html_from_history_list(self, index):
        logger.info("show_html_from_history_list")
        self.resize(700, 700)
        self.move(315, 50)

        self.history_window = HistoryWindow(self)  # Why?
        self.setWindowTitle("Wörterbuch")
        self.setCentralWidget(self.history_window)

        if type(index) is str:
            self.history_entry = index
        else:
            self.history_entry = index.text()

        name = dict_path / (self.history_entry+'.html')
        with open(name, 'r') as file:
            text = file.read()

        self.history_window.txt_cont.insertHtml(text)

        self.history_window.return_button.clicked.connect(
            self.launch_history_window)
        self.history_window.close_button.clicked.connect(self.close)
        self.history_window.focus_button.clicked.connect(
            self.add_to_focus_from_history)
        self.show()

    def add_to_focus_from_history(self):
        logger.info("add_to_focus_from_history")
        now = datetime.now() - timedelta(hours=3)

        word = self.history_entry.replace('.quiz', '')

        quiz_file_path = (dict_path / (word+".quiz.html"))
        with open(quiz_file_path, 'r') as f:
            quiz_text = f.read()

        full_file_path = (dict_path / (word+".html"))
        with open(full_file_path, 'r') as f:
            full_text = f.read()

        full_text = fix_html_with_custom_example(full_text)
        with open(full_file_path, 'w') as f:
            f.write(full_text)
        quiz_text = fix_html_with_custom_example(quiz_text)
        with open(quiz_file_path, 'w') as f:
            f.write(quiz_text)

        quiz_parts = bs(quiz_text, "lxml").find_all('p')
        full_parts = bs(full_text, "lxml").find_all('p')
        assert len(quiz_parts) == len(full_parts)

        ignore_list, nb_parts = ignore_headers(quiz_text)
        logger.debug(f'Ignore List: {ignore_list}')

        general_EF = self.wordlist_df.loc[word, 'EF_score']
        self.wordlist_df.loc[word, 'Focused'] = 1
        self.wordlist_df.to_csv(dict_path / 'wordlist.csv')

        # TODO Read dfs only one time, save it multiple times after modifying
        df = pd.read_csv(dict_path / 'wordpart_list.csv')
        df.set_index("Wordpart", inplace=True)
        for k in range(0, nb_parts):
            wordpart = word+' '+str(k)
            df.loc[wordpart, "Word"] = word
            df.loc[wordpart, "Repetitions"] = 0
            df.loc[wordpart, "EF_score"] = general_EF
            df.loc[wordpart, "Interval"] = 6
            df.loc[wordpart, "Previous_date"] = now     # .strftime("%d.%m.%y")
            df.loc[wordpart, "Created"] = now   # .strftime("%d.%m.%y")
            insixdays = now + timedelta(days=6)
            df.loc[wordpart, "Next_date"] = insixdays   # .strftime("%d.%m.%y")
            df.loc[wordpart, "Part"] = k
            df.loc[wordpart, "Ignore"] = ignore_list[k]
        df.to_csv(dict_path / 'wordpart_list.csv')

        subprocess.Popen(
            ['notify-send', '"'+word+'"', 'Add to Focus Mode'])
        logger.info(f'{word} switched to Focus Mode')

    def launch_quiz_window(self):

        logger.info("launch_quiz_window")

        self.quiz_obj = QuizEntry(quiz_priority_order=quiz_priority_order,
                                  words_dataframe=self.wordlist_df,
                                  maxrevpersession=maxrevpersession)

        logger.debug(
            f'queued_word output: {self.quiz_obj.quiz_params["queued_word"]}')

        no_words_left4today, reached_daily_limit = self.quiz_obj.quiz_counter()

        if reached_daily_limit:
            self.reached_daily_limit_dialogue()

        if no_words_left4today:
            self.no_words_left4today_dialogue()

        self.resize(700, 700)
        self.move(315, 10)

        self.quiz_window = QuizWindow()
        self.setCentralWidget(self.quiz_window)

        self.setWindowTitle(self.quiz_obj.quiz_window_titel)
        # self.quiz_window.txt_cont.clear()
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
            logger.info("Repeating list Naaaaaaoooww!!!!")
            quiz_priority_order = 'old_words'
            logger.debug('mod switch')
            self.launch_quiz_window()
        else:
            sys.exit()

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

    def update_word_html(self):
        logger.info("update_word_html")
        subprocess.Popen(['dic.py', self.quiz_obj.quiz_params['queued_word']])

    def launch_focus_window(self):
        logger.info("launch_focus_window")
        self.resize(700, 300)
        self.move(315, 180)
        self.focus_window = FocusWindow(self)
        self.setCentralWidget(self.focus_window)

        self.focus_obj = FocusEntry(focus_df=self.focus_df)

        self.setWindowTitle(self.focus_obj.window_titel)
        self.focus_window.txt_cont.setFont(focus_font)
        self.focus_window.txt_cont.insertHtml(self.focus_obj.focus_part)

        self.focus_window.next_btn.clicked.connect(self.focus_score)
        self.focus_window.next_btn.clicked.connect(self.launch_focus_window)
        self.focus_window.ignore_button.clicked.connect(
            self.sure_method)   # sure_method
        self.show()

    @pyqtSlot()     # just increases button reactivity
    def sure_method(self):
        logger.info("sure_method")
        self.focus_window.txt_cont.clear()
        self.focus_window.txt_cont.insertHtml(
            self.focus_obj.focus_part_revealed)
        self.focus_window.ignore_button.setText('Sure?')
        self.focus_window.ignore_button.move(50, 240)
        self.focus_window.ignore_button.clicked.connect(self.ignore_part)
        self.focus_window.next_btn.clicked.connect(self.launch_focus_window)
        self.show()

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

    def ignore_part(self):
        logger.info("ignore_part")
        focus_df = self.focus_obj.focus_df
        focus_df.loc[
            self.focus_obj.focus_params_dict['queued_word'],
            "Ignore"] = 1
        focus_df.to_csv(dict_path / 'wordpart_list.csv')
        self.launch_focus_window()

    def reveal_full_html_focus(self):
        logger.info("reveal_full_html_focus")
        full_text = self.focus_obj.focus_part_revealed
        self.focus_window = FocusWindow(self)
        self.setWindowTitle("Wörterbuch: Focus")
        self.setCentralWidget(self.focus_window)
        self.focus_window.txt_cont.setFont(focus_font)
        self.focus_window.txt_cont.insertHtml(full_text)
        self.focus_window.next_btn.clicked.connect(self.focus_score)
        self.focus_window.next_btn.clicked.connect(self.launch_focus_window)
        self.show()

    def save_definition(self):
        logger.info("save_definition")

        studie_tag = self.def_window.save_to_stud.isChecked()
        defined_user_html = self.def_window.txt_cont.toHtml()

        # TODO normalement yabdew fel Quiz Obj chya3mlou lena msaybine?
        beispiel_de = self.def_window.beispiel.text()
        beispiel_en = self.def_window.beispiel2.text()
        beispiel_de = beispiel_de.replace('- ', '– ')
        beispiel_en = beispiel_en.replace('- ', '– ')
        words_2_hide = self.def_obj.words_to_hide
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
                beispiel_de, self.def_obj.words_to_hide)
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

        # TODO Overwrite files?, in wich case I want to do that
        # in wich ccase I want to reset DF ries
        with open(self.quiz_obj.quiz_file_path, 'w') as f:
            f.write(defined_html)

        with open(self.quiz_obj.full_file_path, 'w') as f:
            f.write(clean_html)

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
        with open(quiz_file_path, 'w') as f:
            f.write(clean_html)
        # subprocess.Popen(['notify-send', 'gespeichert!'])
        logger.info('gespeichert!')
        # except:
        #     logger.error('Error writing')
        #     # subprocess.Popen(['notify-send', 'Error writing'])
        #     pass


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    subprocess.Popen(['notify-send', 'An Error Occured', exc_value.args[0]])
    QApplication.quit()
    sys.exit(1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = excepthook
    w = MainWindow()
    exit_code = app.exec_()
    sys.exit(exit_code)

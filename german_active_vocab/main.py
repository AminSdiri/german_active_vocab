# !/usr/bin/env python3
# coding = utf-8

# import setuptools
import sys
import os
import subprocess
from PyQt5.QtCore import pyqtSlot, Qt, QRect, QPropertyAnimation, QPoint
from PyQt5.QtWidgets import (QApplication,
                             QErrorMessage,
                             QMainWindow,
                             QListWidget,
                             QMessageBox,
                             QShortcut)
from PyQt5.QtGui import (QTextCharFormat,
                         QTextCursor,
                         QColor,
                         QKeySequence,
                         QGuiApplication) # QShortcut PyQt6
from datetime import datetime, timedelta
import traceback
from plyer import notification

from DictWindows import (SearchWindow,
                         DefinitionWindow,
                         QuizWindow,
                         FocusWindow,
                         FocusRatingDiag,
                         QuizRatingDiag,
                         HistoryWindow)
from DefEntry import DefEntry
from SavingToQuiz import save_from_def_mode
from WordProcessing import (hide_text)
from ProcessQuizData import (FocusEntry, QuizEntry, spaced_repetition)
from utils import read_str_from_file, read_text_from_files, set_up_logger, write_str_to_file, read_dataframe_from_file, update_dataframe_file
from settings import (dict_data_path,
                      dict_src_path,
                      maxrevpersession,
                      normal_font,
                      focus_font,
                      quiz_priority_order
                      )


# https://www.youtube.com/watch?v=0kpm10AxiNE&list=PLQVvvaa0QuDdVpDFNq4FwY9APZPGSUyR4&index=11 choose theme
# https://www.youtube.com/watch?v=ATZJSYEu8vQ  resizing animation


# user needs to generate API and put in in API path...
# TODO (0) create a public API for testing the app
# TODO (1) using boxLayout with percentages instead of hardcoded dimensions
# TODO (2) Write Readme file with examples (screenshots) and how to install
# TODO (1) List the different fonctionalities for the readme.md
# TODO (3) write test functions for the different functionalities,
# CANCELED (2) create setup.py to take care of
# - creating dirs and csv files
# - install requirements.txt
# DONE (2) find os-agnostic alternative to notify-send for windows and macos
# example: from plyer import notification

logger = set_up_logger(__name__)

# .strftime("%d.%m.%y") is a bad idea! losing the time information
# TODO (0) create now and now_(-3h) and move theme to settings.py
now = datetime.now() - timedelta(hours=3)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):

        logger.info("init MainWindow")

        super(MainWindow, self).__init__(parent)
        self.setGeometry(535, 150, 210, 50)
        # logger.info(self.pos())
        # self.move_to_center() 


        self.launch_search_window()

        self.move_to_center() 

        self.shortcut_close = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.shortcut_close.activated.connect(lambda :sys.exit())

        self.error_dialog = QErrorMessage()    
        # self.error_dialog.showMessage('Oh no!')


    def launch_search_window(self):

        logger.info("Launch search window")

        nbargin = len(sys.argv) - 1
        if nbargin > 0:
            logger.debug('shell command with args')
            self.launch_definition_window()
        else:
            logger.debug('0 Args')
            self.resize(345, 50)  # 45
            # self.move(535, 150)
            # self.resize(240, 40)

            self.base_width = 233
            self.extended_width = 400
            self.rect = QRect(600, 300, self.base_width, 40)
            self.setGeometry(self.rect)

            self.search_form = SearchWindow(self)
            self.setWindowTitle("Dictionnary")
            self.setCentralWidget(self.search_form)
            if hasattr(self, 'def_obj'):
                self.search_form.line.setText(self.def_obj.word)
            self.search_form.line.returnPressed.connect(self.launch_definition_window)
            self.search_form.history_button.clicked.connect(self.launch_history_window)
            self.search_form.quiz_button.clicked.connect(self.launch_quiz_window)
            self.search_form.focus_button.clicked.connect(self.launch_focus_window)
            self.search_form.expand_btn.clicked.connect(self.expand_window)
            # self.search_form.expand_btn.clicked.connect(self.move_to_center)


            self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
            self.move_to_center() 
            self.show()

    def expand_window(self):
        logger.info("expand_window")
        current_width = self.width()

        if self.base_width == current_width:
            start_width = self.base_width
            end_width = self.extended_width
            self.search_form.expand_btn.setText('<')
        else:
            start_width = self.extended_width
            end_width = self.base_width
            self.search_form.expand_btn.setText('>')

        self.animation = QPropertyAnimation(self, b'geometry')
        self.animation.setDuration(200)
        self.animation.setStartValue(QRect(self.x(), self.y(), start_width, 40))
        self.animation.setEndValue(QRect(self.x(), self.y(), end_width, 40))
        self.animation.start()


    def move_to_center(self):
        # TODO BUG move is not working at all!
        logger.info("move_to_center")
        frameGm=self.frameGeometry()           
        screen_width=int(QGuiApplication.primaryScreen().availableGeometry().width()/2)
        screen_hight_eye_level=int(QGuiApplication.primaryScreen().availableGeometry().height()*1/4)
        screen_pos=QPoint(screen_width,screen_hight_eye_level)
        frameGm.moveCenter(screen_pos)
        self.centered_pos = frameGm.topLeft()
        self.move(self.centered_pos)

    def launch_definition_window(self):

        logger.info("launch definition window")

        logger.info(self.pos())
        self.resize(700, 690)
        self.move_to_center()
        self.def_window = DefinitionWindow(self)
        self.setWindowTitle("Wörterbuch")
        print(self.windowFlags())
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
            beispiel_de = sys.argv[2].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')

            self.def_obj = DefEntry(word=word,
                                    beispiel_de=beispiel_de)

            self.def_window.beispiel.insert(beispiel_de)
        elif nbargin == 3:
            logger.debug('Opening from Magical 3 Args')

            word = sys.argv[1]
            beispiel_de = sys.argv[2].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')
            beispiel_en = sys.argv[3].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')

            self.def_obj = DefEntry(word=word,
                                    beispiel_de=beispiel_de,
                                    beispiel_en=beispiel_en
                                    )

            self.def_window.beispiel.insert(beispiel_de)
            self.def_window.beispiel2.insert(beispiel_en)
        else:
            raise RuntimeError('Number of argument exceeds 3')

        self.def_window.txt_cont.setFont(normal_font)
        directory = os.getcwd()
        # TODO nsit chta3mel ama ta3ti fi erreur ki 3malte update PyQt5 -> PyQt5
        # self.def_window.txt_cont.document().setMetaInformation(
        #     QTextDocument.DocumentUrl,
        #     QUrl.fromLocalFile(directory).toString() + "/",
        # )
        self.def_window.txt_cont.insertHtml(self.def_obj.defined_html)
        self.def_window.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

        self.def_window.return_button.clicked.connect(self.launch_search_window)
        self.def_window.save_button.clicked.connect(self.save_definition)
        self.def_window.close_button.clicked.connect(self.close)
        self.def_window.highlight_button.clicked.connect(self.highlight_text)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, on=False)
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

        # TODO (3) allow modifing html in history Window
        # TODO (3) allow deleting html from history Window ( file and DF entry)
        self.resize(400, 500)
        self.move(315, 50)
        self.history_window = HistoryWindow(self)
        self.setWindowTitle("Wörterbuch")
        files = (dict_data_path / 'html').glob("*.html")
        files = list(files)
        files.sort(key=os.path.getmtime, reverse=True)
        files = [x.stem for x in files]
        self.allwords = QListWidget(self)
        self.allwords.addItems(files)
        self.allwords.itemDoubleClicked.connect(self.show_html_from_history_list)
        self.setCentralWidget(self.history_window)
        self.allwords.resize(390, 490)
        self.allwords.move(5, 5)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, on=False)
        self.move_to_center()
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

        history_entry_path = dict_data_path / 'html' / f'{self.history_entry}.html'
        text = read_str_from_file(history_entry_path)

        self.history_window.txt_cont.insertHtml(text)
        # move the view to the beginning
        self.history_window.txt_cont.moveCursor(QTextCursor.Start)

        self.history_window.return_button.clicked.connect(self.launch_history_window)
        self.history_window.close_button.clicked.connect(self.close)
        self.history_window.focus_button.clicked.connect(self.add_to_focus_from_history)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, on=False)
        self.show()

    def add_to_focus_from_history(self):
        logger.info("add_to_focus_from_history")

        word = self.history_entry.replace('.quiz', '')
        full_text, quiz_text = read_text_from_files(word)

        update_dataframe_file(word, full_text, quiz_text)


    def launch_quiz_window(self):
        logger.info("launch_quiz_window")
        
        wordlist_df = read_dataframe_from_file(total=True)

        self.quiz_obj = QuizEntry(quiz_priority_order=quiz_priority_order,
                                  words_dataframe=wordlist_df,
                                  maxrevpersession=maxrevpersession)

        logger.debug(
            f'queued_word output: {self.quiz_obj.quiz_params["queued_word"]}')

        no_words_left4today, reached_daily_limit = self.quiz_obj.quiz_counter()

        if reached_daily_limit:
            self.reached_daily_limit_dialogue()

        if no_words_left4today:
            if quiz_priority_order == 'old_words':
                self.no_words_left_at_all_dialogue()
            else:
                self.no_planned_words_left_dialogue()

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
        self.quiz_window.save_button.clicked.connect(self.save_custom_quiztext_from_quizmode)
        self.quiz_window.update_button.clicked.connect(self.update_word_html)
        self.quiz_window.hide_button.clicked.connect(self.hide_word_manually)
        
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, on=False)

        self.show()

    def quiz_score(self):
        logger.info("quiz_score")
        self.rating_diag_quiz = QuizRatingDiag(self)
        self.rating_diag_quiz.word = self.quiz_obj.quiz_params["queued_word"]
        worldlist_df = read_dataframe_from_file(total=True)
        self.rating_diag_quiz.show()
        self.reveal_full_html_quiz()

        if self.rating_diag_quiz.exec():
            saving_file = 'wordlist.csv'
            easiness = self.rating_diag_quiz.easiness
            spaced_repetition(easiness,
                              now,
                              worldlist_df,
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

    def no_planned_words_left_dialogue(self):
        global quiz_priority_order
        logger.info("no_planned_words_left_dialogue")
        choice = QMessageBox.question(self, "You've got it all!",
                                      "Well done, you have all planned words "
                                      "revisited. Want to switch priority to "
                                      "oldest seen words?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Close)
        if choice == QMessageBox.StandardButton.Yes:
            logger.info("Repeating list Naaaaaaoooww!!!!")
            quiz_priority_order = 'old_words'
            logger.debug('mod switch')
            self.launch_quiz_window()
        else:
            sys.exit()

    def no_words_left_at_all_dialogue(self):
        global quiz_priority_order
        logger.info("no_words_left_at_all_dialogue")
        choice = QMessageBox.question(self, "Easy! You've got it all!",
                                      "Well done, you have all planned words and non planned"
                                      "revisited. so actually all of them. Add more words to the dict so we can keep up with your big brain :)",
                                      QMessageBox.StandardButton.Close)
        if choice == QMessageBox.StandardButton.Close:
            sys.exit()

    def hide_word_manually(self):
        logger.info("hide_word_manually")
        # TODO add manually hidden words to dict_file
        selected_text2hide = self.quiz_window.txt_cont.textCursor().selectedText()
        logger.debug('word2hide: '+selected_text2hide)
        self.quiz_window.txt_cont.clear()
        self.quiz_obj.quiz_text = hide_text(self.quiz_obj.quiz_text, selected_text2hide)
        self.quiz_window.txt_cont.insertHtml(self.quiz_obj.quiz_text)
        self.show()

    def reveal_full_html_quiz(self):
        logger.info("reveal_full_html_quiz")
        self.quiz_window.txt_cont.clear()
        self.quiz_window.txt_cont.insertHtml(self.quiz_obj.full_text)

        self.quiz_window.next_btn.clicked.connect(self.quiz_score)
        self.quiz_window.next_btn.clicked.connect(self.launch_quiz_window)
        self.quiz_window.save_button.clicked.connect(
            self.save_custom_quiztext_from_quizmode)
        self.show()

    def update_word_html(self):
        logger.info("update_word_html")
        queued_word = self.quiz_obj.quiz_params["queued_word"]
        subprocess.Popen(['python3', str(dict_src_path / 'main.py'),
                          f'{queued_word} new_dict'])

    def launch_focus_window(self):
        logger.info("launch_focus_window")
        self.resize(700, 300)
        self.move(315, 180)
        self.focus_window = FocusWindow(self)
        self.setCentralWidget(self.focus_window)
        
        focus_df = read_dataframe_from_file(total=False)
        self.focus_obj = FocusEntry(focus_df=focus_df)

        self.setWindowTitle(self.focus_obj.window_titel)
        self.focus_window.txt_cont.setFont(focus_font)
        self.focus_window.txt_cont.insertHtml(self.focus_obj.focus_part)

        self.focus_window.next_btn.clicked.connect(self.focus_score)
        self.focus_window.next_btn.clicked.connect(self.launch_focus_window)
        self.focus_window.ignore_button.clicked.connect(
            self.sure_method)   # sure_method

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, on=False)
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
        focus_df.to_csv(dict_data_path / 'wordpart_list.csv')
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
        custom_qt_html = self.def_window.txt_cont.toHtml()

        beispiel_de = self.def_window.beispiel.text()
        beispiel_en = self.def_window.beispiel2.text()
        beispiel_de = beispiel_de.replace('- ', '– ')
        beispiel_en = beispiel_en.replace('- ', '– ')
        word = self.def_obj.word
        dict_dict = self.def_obj.dict_dict
        tag = ''
        if studie_tag:
            tag = 'Studium'

        save_from_def_mode(dict_data_path, word, custom_qt_html, beispiel_de,
                          beispiel_en, tag, now,
                          dict_dict, self.def_obj.dict_dict_path)

    def save_custom_quiztext_from_quizmode(self):
        logger.info("save_custom_quiztext_from_quizmode")
        clean_html = self.quiz_window.txt_cont.toHtml()

        quiz_file_path = self.quiz_obj.quiz_file_path

        write_str_to_file(quiz_file_path, clean_html, notification_list=['gespeichert!'])

        logger.info('gespeichert!')


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    notification.notify(title='An Error Occured',
                        message=exc_value.args[0],
                        timeout=10)
    QApplication.quit()
    sys.exit(1)


def set_theme(app):
    # import platform
    # import darkdetect
    # import qdarkstyle
    # from darktheme.widget_template import DarkPalette
    # TODO (3) find os-compatible themes
    # I'm using (adwaita-qt in ubuntu or maybe qt5ct)
    # tried qdarkstyle (blueisch)
    # this one is close enough
    # if darkdetect.isDark():
    #     if 'Linux' in platform.system():
    #         pass
    #     elif 'Darwin' in platform.system():
    #         # QT supposedly adapts it automaticly in MacOs
    #         # app.setPalette(DarkPalette())
    #         pass
    #     elif 'Windows' in platform.system():
    #         pass
    #     app.setPalette(DarkPalette())
    # else:
    #     # sadely, using a light theme is not thought about yet! :D
    #     # TODO generate a white theme color palette for template rendering
    #     app.setPalette(DarkPalette())
    #     pass

    # dark_stylesheet = qdarkstyle.load_stylesheet_PyQt5()
    # app.setStyleSheet(dark_stylesheet)

    # from qt_material import apply_stylesheet
    # apply_stylesheet(app, theme='dark_teal.xml')
    
    import qdarktheme
    qdarktheme.setup_theme("dark")
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    set_theme(app)
    sys.excepthook = excepthook
    w = MainWindow()
    # print(w.pos())
    exit_code = app.exec()
    # print(w.pos())
    sys.exit(exit_code)

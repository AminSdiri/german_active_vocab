import subprocess
import sys
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QPushButton, QWidget, QLabel, QTextEdit,
                             QSlider, QDialog, QVBoxLayout, QMessageBox)
from PyQt5.QtGui import QTextCursor

from ProcessQuizData import QuizEntry, spaced_repetition
from SavingToQuiz import hide_text
from GetDict.GenerateDict import update_hidden_words_in_dict

from settings import (DICT_SRC_PATH,
                      MAX_REV_PER_SESSION,
                      QUIZ_PRIORITY_ORDER)


from utils import read_dataframe_from_file, read_text_from_files, sanitize_word, set_up_logger, update_dataframe_file, write_str_to_file

logger = set_up_logger(__name__)

class QuizWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        logger.info("init defQuiz")
                
        self.txt_cont = QTextEdit(self)
        self.txt_cont.move(5, 5)
        self.txt_cont.resize(690, 615)
        self.txt_cont.setReadOnly(True)

        # self.beispiel = QLineEdit(self)
        # self.beispiel.move(5, 625)
        # self.beispiel.resize(690, 40)

        self.next_btn = QPushButton('>>>Answer>>>', self)
        self.next_btn.resize(220, 40)
        self.next_btn.move(5, 625)
        self.save_button = QPushButton('Save', self)
        self.save_button.move(390, 625)
        self.populate = QPushButton('Populate', self)
        self.populate.move(490, 625)
        self.close_button = QPushButton('Close', self)
        self.close_button.move(590, 625)
        self.hide_button = QPushButton('Hide', self)
        self.hide_button.move(290, 625)
        self.update_button = QPushButton('Update', self)
        self.update_button.move(590, 670)

        self.quiz_window_connect_buttons()

        self.get_quiz_obj()


        # self.quiz_window.txt_cont.clear()
        self.txt_cont.insertHtml(self.quiz_obj.quiz_text)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

    def get_quiz_obj(self):
        wordlist_df = read_dataframe_from_file(parts=True)

        self.quiz_obj = QuizEntry(quiz_priority_order=QUIZ_PRIORITY_ORDER,
                                  words_dataframe=wordlist_df,
                                  maxrevpersession=MAX_REV_PER_SESSION)

        logger.debug(
            f'queued_word output: {self.quiz_obj.quiz_params["queued_word"]}')

        if not self.quiz_obj.quiz_params["queued_word"]:
            self.no_words_left_at_all_dialogue()

        no_words_left4today, reached_daily_limit = self.quiz_obj.quiz_counter()

        if reached_daily_limit:
            self.reached_daily_limit_dialogue()

        if no_words_left4today:
            if QUIZ_PRIORITY_ORDER == 'old_words':
                self.no_words_left_at_all_dialogue()
            else:
                self.no_planned_words_left_dialogue()

    def quiz_window_connect_buttons(self):
        self.next_btn.clicked.connect(self.quiz_score)
        self.close_button.clicked.connect(self.close)
        self.populate.clicked.connect(self.reveal_full_html_quiz)
        self.save_button.clicked.connect(self.save_custom_quiztext_from_quizmode)
        self.update_button.clicked.connect(self.update_word_html)
        self.hide_button.clicked.connect(self.hide_word_manually)

    def reached_daily_limit_dialogue(self):
        logger.info("reached_daily_limit_dialogue")
        choice = QMessageBox.question(self, 'Extract!',
                                      "you have revisited 10 Words, Well done!"
                                      " Come back later... "
                                      "(If you want to continue hit Yes!)",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Close)

        if choice == QMessageBox.Yes:
            logger.debug("resetting Count")
            self.quiz_obj._nb_revisited = 0
            self.show()
        else:
            sys.exit()

    def no_planned_words_left_dialogue(self):
        global QUIZ_PRIORITY_ORDER
        logger.info("no_planned_words_left_dialogue")
        choice = QMessageBox.question(self, "You've got it all!",
                                      "Well done, you have all planned words "
                                      "revisited. Want to switch priority to "
                                      "oldest seen words?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Close)
        if choice == QMessageBox.StandardButton.Yes:
            logger.info("Repeating list Naaaaaaoooww!!!!")
            QUIZ_PRIORITY_ORDER = 'old_words'
            logger.debug('mod switch')
            self.get_quiz_obj()
        else:
            sys.exit()

    def no_words_left_at_all_dialogue(self):
        global QUIZ_PRIORITY_ORDER
        logger.info("no_words_left_at_all_dialogue")
        choice = QMessageBox.question(self, "Easy! You've got it all!",
                                      "Well done, you have all planned words and non planned"
                                      "revisited. so actually all of them. Add more words to the dict so we can keep up with your big brain :)",
                                      QMessageBox.StandardButton.Close)
        if choice == QMessageBox.StandardButton.Close:
            sys.exit()

    def quiz_score(self):
        logger.info("quiz_score")
        self.rating_diag_quiz = QuizRatingDiag(self)
        self.rating_diag_quiz.word = self.quiz_obj.quiz_params["queued_word"]
        worldlist_df = read_dataframe_from_file(parts=True)
        self.rating_diag_quiz.show()
        self.reveal_full_html_quiz()

        if self.rating_diag_quiz.exec():
            logger.info("update word informations using spaced repetition")
            saving_file = 'wordlist.csv'
            easiness = self.rating_diag_quiz.easiness
            now = datetime.now() - timedelta(hours=3)

            spaced_repetition(easiness,
                              now,
                              worldlist_df,
                              saving_file,
                              **self.quiz_obj.quiz_params)

            self.parent().launch_quiz_window()

    def reveal_full_html_quiz(self):
        logger.info("reveal_full_html_quiz")
        self.txt_cont.clear()
        self.txt_cont.insertHtml(self.quiz_obj.full_text)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

        self.show()

    def update_word_html(self):
        logger.info("update_word_html")
        queued_word = self.quiz_obj.quiz_params["queued_word"]
        subprocess.Popen(['python3', str(DICT_SRC_PATH / 'main.py'),
                          f'{queued_word} new_dict'])


    def save_custom_quiztext_from_quizmode(self):
        logger.info("save_custom_quiztext_from_quizmode")
        qt_html_content = self.txt_cont.toHtml()

        quiz_file_path = self.quiz_obj.quiz_file_path

        write_str_to_file(quiz_file_path, qt_html_content, notification_list=['gespeichert!'], overwrite=True)

        logger.info('gespeichert!')


    def hide_word_manually(self):
        logger.info("hide_word_manually")
        # DONE (1) add manually hidden words to dict_file
        selected_text2hide = self.txt_cont.textCursor().selectedText()

        word = self.quiz_obj.quiz_params["queued_word"]
        saving_word = sanitize_word(word)
        update_hidden_words_in_dict(selected_text2hide, saving_word)

        logger.debug(f'word2hide: {selected_text2hide}')
        self.txt_cont.clear()
        self.quiz_obj.quiz_text = hide_text(self.quiz_obj.quiz_text, selected_text2hide)
        self.txt_cont.insertHtml(self.quiz_obj.quiz_text)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)
        self.show()


class QuizRatingDiag(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init input_easiness")
        self.setGeometry(430, 550, 450, 150)

        self.easiness_slider = QSlider(Qt.Orientation.Horizontal)
        self.easiness_slider.move(100, 350)
        self.easiness_slider.setMinimum(0)
        self.easiness_slider.setMaximum(5)
        self.easiness_slider.valueChanged.connect(self.valuechange)
        self.easiness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.easiness = self.easiness_slider.value()
        self.done(self.easiness)

        self.set_button = QPushButton('Set', self)
        self.set_button.clicked.connect(self.closing_dialog)
        self.set_button.clicked.connect(self.parent().parent().launch_quiz_window)

        self.quiz_text = parent.quiz_obj.quiz_text
        self.full_text = parent.quiz_obj.full_text
        self.queued_word = parent.quiz_obj.quiz_params['queued_word']
        self.general_EF = parent.quiz_obj.quiz_params['EF_score']
        # TODO (4) still relevant?
        # now = datetime.now() - timedelta(hours=3)
        # self.halfway_date = now + \
        #     timedelta(days=math.ceil(
        #         parent.quiz_obj.quiz_params['real_interval']/2))

        self.set_focus_button = QPushButton('add to Focus list', self)
        self.set_focus_button.clicked.connect(self.add_to_focus)

        # TODO (2) not needed?
        # word_already_added_to_focus = any(
        #     parent.focus_df.Word.str.contains(self.queued_word)
        # )
        # if word_already_added_to_focus:
        #     self.set_focus_button.setEnabled(False)

        self.l1 = QLabel(
            "How easy was it to remember this word, use the Cursor")
        self.l1.move(205, 50)
        self.l1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.l2 = QLabel("")
        self.l2.move(205, 50)
        self.l2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        layout.addWidget(self.easiness_slider)
        layout.addWidget(self.set_button)
        layout.addWidget(self.set_focus_button)
        layout.addWidget(self.l1)
        layout.addWidget(self.l2)

    def valuechange(self):
        logger.info("valuechange")

        self.easiness = self.easiness_slider.value()

        if self.easiness < 3:
            self.l1.setText('Forgeting')
        elif self.easiness >= 3:
            self.l1.setText('Remembering')

        if self.easiness == 5:
            self.l2.setText('5. Easy!')
        elif self.easiness == 4:
            self.l2.setText(
                '4. correct response provided with some hesitation')
        elif self.easiness == 3:
            self.l2.setText(
                '3. answer recalled with difficulty; '
                'perhaps, slightly incorrect')
        elif self.easiness == 2:
            self.l2.setText('2. wrong response that makes you say I knew it!')
        elif self.easiness == 1:
            self.l2.setText(
                '1. wrong response; the correct answer seems to be familiar')
        elif self.easiness == 0:
            self.l2.setText(
                '0. complete blackout; you do not even '
                'recall ever knowing the answer')

    def closing_dialog(self):
        logger.info("closing_dialog")
        self.accept()

    def add_to_focus(self):
        logger.info("add_to_focus")

        word = self.queued_word
        full_text, quiz_text = read_text_from_files(word)

        update_dataframe_file(word, full_text, quiz_text)
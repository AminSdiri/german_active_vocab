import math
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QPushButton, QWidget, QLabel,
                             QLineEdit, QTextEdit, QCheckBox,
                             QSlider, QDialog, QVBoxLayout)
from plyer import notification

from ProcessQuizData import ignore_headers
from utils import set_up_logger
from settings import dict_data_path

logger = set_up_logger(__name__)


class SearchWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init Search_win")

        # self.define_button = QPushButton("Define", self)
        # self.define_button.move(100, 350)
        self.line = QLineEdit(self)
        self.line.setFocus()
        self.line.move(5, 5)
        self.line.resize(200, 40)  # 30
        self.translate_fr = QCheckBox('Fr', self)
        self.translate_fr.move(205, 25)  # 20
        self.translate_en = QCheckBox('En', self)
        self.translate_en.move(205, 5)
        self.history_button = QPushButton('Hs', self)
        self.history_button.resize(30, 30)
        self.history_button.move(250, 10)  # 8
        self.quiz_button = QPushButton('Qz', self)
        self.quiz_button.resize(30, 30)
        self.quiz_button.move(280, 10)
        self.focus_button = QPushButton('Fc', self)
        self.focus_button.resize(30, 30)
        self.focus_button.move(310, 10)

        # TODO (0) adaptable window layout
        # self.focus_button.setSizePolicy(QSizePolicy.Expanding,
        #                                 QSizePolicy.Expanding)

        # checkboxes = QVBoxLayout()
        # checkboxes.addWidget(self.translate_fr)
        # checkboxes.addWidget(self.translate_en)

        # buttons = QHBoxLayout()
        # buttons.addWidget(self.history_button)
        # buttons.addWidget(self.quiz_button)
        # buttons.addWidget(self.focus_button)

        # layout = QGridLayout(self)
        # layout.addWidget(self.line, 1, 1, 1, 5)
        # layout.addLayout(checkboxes, 1, 6, 1, 1)
        # layout.addLayout(buttons, 1, 7, 1, 3)
        # self.setLayout(layout)


class DefinitionWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init defWindow")
        self.return_button = QPushButton('Return', self)
        self.return_button.move(390, 645)
        self.save_button = QPushButton('Save', self)
        self.save_button.move(490, 645)
        self.close_button = QPushButton('Close', self)
        self.close_button.move(590, 645)
        self.highlight_button = QPushButton('Highlight', self)
        self.highlight_button.move(190, 645)
        self.txt_cont = QTextEdit(self)
        self.txt_cont.move(5, 5)
        self.txt_cont.resize(690, 545)
        self.save_to_stud = QCheckBox('Studium', self)
        self.save_to_stud.move(5, 645)
        self.beispiel = QLineEdit(self)
        self.beispiel.move(5, 555)
        self.beispiel.resize(690, 40)
        self.beispiel2 = QLineEdit(self)
        self.beispiel2.move(5, 600)
        self.beispiel2.resize(690, 40)


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

        self.next_btn = QPushButton('>>>>>>', self)
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


class QuizRatingDiag(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init input_easiness")
        self.setGeometry(430, 550, 450, 150)

        self.easiness_slider = QSlider(Qt.Horizontal)
        self.easiness_slider.move(100, 350)
        self.easiness_slider.setMinimum(0)
        self.easiness_slider.setMaximum(5)
        self.easiness_slider.valueChanged.connect(self.valuechange)
        self.easiness_slider.setTickPosition(QSlider.TicksBelow)
        self.easiness = self.easiness_slider.value()
        self.done(self.easiness)

        self.set_button = QPushButton('Set', self)
        self.set_button.clicked.connect(self.closing_dialog)

        self.quiz_text = parent.quiz_obj.quiz_text
        self.full_text = parent.quiz_obj.full_text
        self.queued_word = parent.quiz_obj.quiz_params['queued_word']
        self.general_EF = parent.quiz_obj.quiz_params['EF_score']
        now = datetime.now() - timedelta(hours=3)
        self.halfway_date = now + \
            timedelta(days=math.ceil(
                parent.quiz_obj.quiz_params['real_interval']/2))

        self.set_focus_button = QPushButton('add to Focus list', self)
        self.set_focus_button.clicked.connect(self.add_to_focus)

        word_already_added_to_focus = any(
            parent.focus_df.Word.str.contains(self.queued_word)
        )
        if word_already_added_to_focus:
            self.set_focus_button.setEnabled(False)

        self.l1 = QLabel(
            "How easy was it to remember this word, use the Cursor")
        self.l1.move(205, 50)
        self.l1.setAlignment(Qt.AlignCenter)

        self.l2 = QLabel("")
        self.l2.move(205, 50)
        self.l2.setAlignment(Qt.AlignCenter)

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
        now = datetime.now() - timedelta(hours=3)

        ignore_list, nb_parts = ignore_headers(self.quiz_text)

        word = self.queued_word
        general_EF = self.general_EF
        logger.debug(f'Ignore List: {ignore_list}')

        quiz_parts = bs(self.quiz_text, "lxml").find_all('p')
        full_parts = bs(self.full_text, "lxml").find_all('p')
        assert len(quiz_parts) == len(full_parts)

        df_quiz = pd.read_csv(dict_data_path / 'wordlist.csv')
        df_quiz.set_index("Word", inplace=True)
        df_quiz.loc[word, "Focused"] = 1
        df_quiz.to_csv(dict_data_path / 'wordlist.csv')

        df = pd.read_csv(dict_data_path / 'wordpart_list.csv')
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
            df.loc[wordpart, "Halfway_date_from_quiz"] = self.halfway_date
            df.loc[wordpart, "Ignore"] = ignore_list[k]
        df.to_csv(dict_data_path / 'wordpart_list.csv')

        notification.notify(title=f'"{word}"',
                            message='Added to Focus Mode',
                            timeout=2)
        logger.info(f'{word} switched to Focus Mode')


class FocusWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init defFocus")

        self.txt_cont = QTextEdit(self)
        self.txt_cont.move(5, 5)
        self.txt_cont.resize(690, 215)
        self.txt_cont.setReadOnly(True)

        self.next_btn = QPushButton('>', self)
        self.next_btn.move(150, 240)
        self.next_btn.resize(400, 40)

        self.ignore_button = QPushButton('Ignore', self)
        self.ignore_button.move(50, 240)


class FocusRatingDiag(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init input_easiness_focus")
        self.setGeometry(430, 550, 450, 150)

        self.easiness_slider = QSlider(Qt.Horizontal)
        self.easiness_slider.move(100, 350)
        self.easiness_slider.setMinimum(0)
        self.easiness_slider.setMaximum(5)
        self.easiness_slider.valueChanged.connect(self.valuechange)
        self.easiness_slider.setTickPosition(QSlider.TicksBelow)

        self.set_button = QPushButton('Set', self)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.l1 = QLabel("Hello")
        self.l1.move(205, 50)
        self.l1.setAlignment(Qt.AlignCenter)

        self.l2 = QLabel("")
        self.l2.move(205, 50)
        self.l2.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.easiness_slider)
        layout.addWidget(self.l1)
        layout.addWidget(self.l2)
        layout.addWidget(self.set_button)

        self.easiness = self.easiness_slider.value()

        self.set_button.clicked.connect(self.closing_dialog)

        self.done(self.easiness)

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
        self.accept()


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

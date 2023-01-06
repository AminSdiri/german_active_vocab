from datetime import datetime, timedelta
from PyQt5.QtCore import Qt #, pyqtSlot
from PyQt5.QtWidgets import (QPushButton, QWidget, QLabel, QTextEdit,
                             QSlider, QDialog, QVBoxLayout)
from PyQt5.QtGui import (QTextCursor)
from ProcessQuizData import FocusEntry, spaced_repetition

from settings import (dict_data_path,
                      focus_font)


from utils import read_dataframe_from_file, set_up_logger

logger = set_up_logger(__name__)


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

        focus_df = read_dataframe_from_file(total=False)
        self.focus_obj = FocusEntry(focus_df=focus_df)
        self.txt_cont.setFont(focus_font)
        self.txt_cont.insertHtml(self.focus_obj.focus_part)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

        self.focus_window_connect_buttons() 

    def focus_window_connect_buttons(self):
        self.next_btn.clicked.connect(self.focus_score)
        self.ignore_button.clicked.connect(self.sure_method)  # sure_method

    # @pyqtSlot()     # just increases button reactivity
    def sure_method(self):
        logger.info("sure_method")
        self.txt_cont.clear()
        self.txt_cont.insertHtml(self.focus_obj.focus_part_revealed)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)
        self.ignore_button.setText('Sure?')
        self.ignore_button.move(50, 240)
        self.ignore_button.clicked.connect(self.ignore_part)
        self.next_btn.clicked.connect(self.parent().launch_focus_window)
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
            now = datetime.now() - timedelta(hours=3)
            spaced_repetition(easiness,
                              now,
                              self.focus_obj.focus_df,
                              saving_file,
                              **self.focus_obj.focus_params_dict)

            self.parent().launch_focus_window()

    def ignore_part(self):
        logger.info("ignore_part")
        focus_df = self.focus_obj.focus_df
        focus_df.loc[self.focus_obj.focus_params_dict['queued_word'], "Ignore"] = 1
        focus_df.to_csv(dict_data_path / 'wordpart_list.csv')
        self.parent().launch_focus_window()

    def reveal_full_html_focus(self):
        logger.info("reveal_full_html_focus")

        self.txt_cont.clear()
        self.txt_cont.setFont(focus_font)
        self.txt_cont.insertHtml(self.focus_obj.focus_part_revealed)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)
        
        self.show()


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
from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QCheckBox, QLabel)
from PyQt5.QtGui import QMovie

from utils import set_up_logger
from settings import DICT_SRC_PATH

logger = set_up_logger(__name__)

# DONE (0) use Qthread to prevent gui from freezing when waiting for the word data to be fetched 

class SearchWindow(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        logger.info("init Search_win")

        self.base_width = 233
        self.extended_width = 405
        # self.rect = QRect(600, 300, self.base_width, 40)
        # parent.setGeometry(self.rect)

        self.line = QLineEdit(self)
        self.line.setPlaceholderText("Search for a Word")
        # self.line.setFocus() # BUG not working
        self.line.move(2, 2)
        self.line.resize(200, 36)  # 30
        # TODO update this
        if hasattr(self, 'def_obj'):
            self.line.setText(self.def_obj.word)

        # DONE (0) show loading gif when process_data_thread is running
        self.label = QLabel(self)
        self.label.move(165, 2)
        self.label.resize(37, 37)
        self.label.raise_()
        # self.loading_animation.backgroundColor() 
        self.label.setObjectName("label")

        self.loading_animation = QMovie(str(DICT_SRC_PATH/'ressources'/'Spinner-1s-34px.gif')) # https://loading.io/
        # check if path is valid
        if not self.loading_animation.isValid():
            raise RuntimeError('Loading animation gif not found or invalid.') 
        self.label.setMovie(self.loading_animation)
        self.label.hide()

        self.expand_btn = QPushButton('>', self)
        self.expand_btn.move(205, 2)
        self.expand_btn.resize(25, 36)
        self.expand_btn.setToolTip('reveal more tools')
        self.translate_fr = QCheckBox('Fr', self)
        self.translate_fr.move(235, 18)  # 20
        self.translate_fr.setToolTip('traduire en français')
        self.translate_en = QCheckBox('En', self)
        self.translate_en.move(235, 0)
        self.translate_en.setToolTip('translate to english')
        self.history_button = QPushButton('Hs', self)
        self.history_button.resize(self.history_button.sizeHint())
        self.history_button.move(285, 7)  # 8
        self.history_button.setToolTip('saved words list')
        self.quiz_button = QPushButton('Qz', self)
        self.quiz_button.resize(self.quiz_button.sizeHint())
        self.quiz_button.move(325, 7)
        self.quiz_button.setToolTip('Quiz mode')
        self.focus_button = QPushButton('Fc', self)
        self.focus_button.resize(self.focus_button.sizeHint())
        self.focus_button.move(365, 7)
        self.focus_button.setToolTip('Focus mode')

        self.search_window_button_actions()

        # TODO (1) adaptable window layout
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

    def start_loading_animation(self) -> None:
        self.label.show()
        self.loading_animation.start()
        self.label.raise_()

    def stop_loading_animation(self) -> None:
        self.label.hide()
        self.loading_animation.stop()

    def search_window_button_actions(self) -> None:
        self.line.returnPressed.connect(self.parent().process_data_in_thread)
        self.history_button.clicked.connect(self.parent().launch_history_list_window)
        self.quiz_button.clicked.connect(self.parent().launch_quiz_window)
        self.focus_button.clicked.connect(self.parent().launch_focus_window)
        self.expand_btn.clicked.connect(self.parent().expand_search_window_animation)


    def get_filled_search_form(self) -> str:
        logger.info("return search form inputs")
        
        word = self.line.text()
        
        if self.translate_fr.isChecked():
            word += ' fr'
        if self.translate_fr.isChecked():
            word += ' en'

        return word

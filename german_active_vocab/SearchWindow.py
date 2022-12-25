from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QCheckBox)

from utils import set_up_logger

logger = set_up_logger(__name__)

class SearchWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("init Search_win")


        self.base_width = 233
        self.extended_width = 400
        # self.rect = QRect(600, 300, self.base_width, 40)
        # parent.setGeometry(self.rect)

        # self.define_button = QPushButton("Define", self)
        # self.define_button.move(100, 350)
        self.line = QLineEdit(self)
        self.line.setFocus()
        self.line.move(2, 2)
        self.line.resize(200, 36)  # 30
        if hasattr(self, 'def_obj'):
            self.line.setText(self.def_obj.word)

        self.translate_fr = QCheckBox('Fr', self)
        self.translate_fr.move(235, 18)  # 20
        self.translate_en = QCheckBox('En', self)
        self.translate_en.move(235, 0)

        self.expand_btn = QPushButton('>', self)
        self.expand_btn.move(205, 2)
        self.expand_btn.resize(25, 36)
        self.history_button = QPushButton('Hs', self)
        self.history_button.resize(self.history_button.sizeHint())
        self.history_button.move(280, 5)  # 8
        self.quiz_button = QPushButton('Qz', self)
        self.quiz_button.resize(self.quiz_button.sizeHint())
        self.quiz_button.move(320, 5)
        self.focus_button = QPushButton('Fc', self)
        self.focus_button.resize(self.focus_button.sizeHint())
        self.focus_button.move(360, 5)

        self.search_window_button_actions()

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

    def search_window_button_actions(self):
        self.line.returnPressed.connect(self.parent().launch_definition_window)
        self.history_button.clicked.connect(self.parent().launch_history_list_window)
        self.quiz_button.clicked.connect(self.parent().launch_quiz_window)
        self.focus_button.clicked.connect(self.parent().launch_focus_window)
        self.expand_btn.clicked.connect(self.parent().expand_window_animation)
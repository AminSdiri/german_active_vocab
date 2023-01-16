# !/usr/bin/env python3
# coding = utf-8

# import setuptools
from dataclasses import asdict
import sys
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QPoint, QSize
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow,
                             QShortcut)
from PyQt5.QtGui import (QKeySequence,
                         QGuiApplication) # QShortcut PyQt6
import traceback
from plyer import notification

from views.DefinitionWindow import DefinitionWindow
from FocusWindow import FocusWindow
from HistoryWindow import HistoryWindow, WordlistWindow
from QuizWindow import QuizWindow
from views.SearchWindow import SearchWindow
from DefEntry import DefEntry

from utils import set_up_logger
# from autologging import traced

# TODO STRUCT (0) Baddel structure mta3 Model, Viewer, controller walla Presenter

# git update-index --skip-worktree <file> to skip tracking files
# https://www.youtube.com/watch?v=0kpm10AxiNE&list=PLQVvvaa0QuDdVpDFNq4FwY9APZPGSUyR4&index=11 choose theme


# user needs to generate API and put in in API path...
# TODO (1) using boxLayout with percentages instead of hardcoded dimensions
# TODO (0) Write Readme file with examples (screenshots) and how to install
# TODO (0) List the different fonctionalities for the readme.md
# TODO BIG (2) write test functions for the different functionalities,
# DONE (2) find os-agnostic alternative to notify-send for windows and macos
# example: from plyer import notification

logger = set_up_logger(__name__)


# .strftime("%d.%m.%y") is a bad idea! losing the time information
# TODO STRUCT (1) organize now and now_(-3h) 
# TODO (2) move theme to settings.py

def wrap(pre, post):
	""" Wrapper """
	def decorate(func):
		""" Decorator """
		def call(*args, **kwargs):
			""" Actual wrapping """
			pre(func)
			result = func(*args, **kwargs)
			post(func)
			return result
		return call
	return decorate

def entering(func):
	""" Pre function logging """
	logger.debug("Entered %s", func.__name__)

def exiting(func):
	""" Post function logging """
	logger.debug("Exited  %s", func.__name__)



# @wrap(entering, exiting)

# @traced(logger)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        logger.info("init MainWindow")
        super(MainWindow, self).__init__(parent)
        self.setGeometry(535, 150, 210, 50)
        self.launch_search_window()
        self.move_to_center() 
        self.set_shortcuts()
            
    def launch_search_window(self):
        logger.info("Launch search window")

        self.search_form = SearchWindow(self)

        self.set_window_properties(title="Wörterbuch",
                                   central_widget=self.search_form,
                                   Frameless=True,
                                   size=QSize(self.search_form.base_width, 40))
        
        nbargin = len(sys.argv) - 1
        if nbargin:
            logger.debug('shell command with args')
            self.launch_definition_window()
        else:
            logger.debug('0 Args')
            self.show()

    def expand_search_window_animation(self):
        logger.info("expand_window")
        current_width = self.width()
        window_x = self.x()
        window_y = self.y()

        logger.info(current_width)

        if self.search_form.base_width == current_width:
            start_width = self.search_form.base_width
            end_width = self.search_form.extended_width
            self.search_form.expand_btn.setText('<')
        else:
            start_width = self.search_form.extended_width
            end_width = self.search_form.base_width
            self.search_form.expand_btn.setText('>')

        self.animation = QPropertyAnimation(self, b'geometry')
        self.animation.setDuration(200)
        self.animation.setStartValue(QRect(window_x, window_y, start_width, 40))
        self.animation.setEndValue(QRect(window_x, window_y, end_width, 40))
        self.animation.start()

    def launch_definition_window(self):
        logger.info("launch definition window")

        nbargin = len(sys.argv) - 1
        input_word = self.search_form.get_filled_search_form() if nbargin == 0  else sys.argv[1]

        def_obj = DefEntry(input_word=input_word)
        self.def_window = DefinitionWindow(def_obj)
        self.def_window.return_button.clicked.connect(self.launch_search_window)
        self.def_window.fill_def_window(def_obj) # BUG (0) thabet fel unpacking thaherli mayhemouch esm el variable
        
        self.set_window_properties(title="Wörterbuch",
                                   central_widget=self.def_window,
                                   Frameless=False,
                                   size=QSize(self.def_window.base_width, 690))
        self.show()

    def expand_definition_window_animation(self):
        logger.info("expand_window")
        current_width = self.width()
        window_x = self.x()
        window_y = self.y()

        logger.info(current_width)

        if self.def_window.base_width == current_width:
            start_width = self.def_window.base_width
            end_width = self.def_window.extended_width
        else:
            start_width = self.def_window.extended_width
            end_width = self.def_window.base_width

        self.animation = QPropertyAnimation(self, b'geometry')
        self.animation.setDuration(200)
        self.animation.setStartValue(QRect(window_x, window_y, start_width, 690))
        self.animation.setEndValue(QRect(window_x, window_y, end_width, 690))
        self.animation.start()

    def launch_history_list_window(self):
        logger.info("launch history list window")

        # TODO (3) allow modifing html in history Window
        # TODO (3) allow deleting html from history Window ( file and DF entry)

        self.wordlist_window = WordlistWindow(self)

        self.set_window_properties(title="Saved Words",
                                   central_widget=self.wordlist_window,
                                   Frameless=False,
                                   size=QSize(400, 500))

        self.show()

    def show_html_from_history_list(self, index):
        logger.info("show_html_from_history_list")

        self.wordlist_window.returned_index = index
        self.history_window = HistoryWindow(self)  # Why?, should be same as def window just with a different return action

        self.set_window_properties(title="Saved Words",
                                   central_widget=self.history_window,
                                   Frameless=False,
                                   size=QSize(700, 700))
        self.show()

    def launch_quiz_window(self):
        logger.info("launch_quiz_window")

        self.quiz_window = QuizWindow()

        self.set_window_properties(title=self.quiz_window.quiz_obj.quiz_window_titel,
                                   central_widget=self.quiz_window,
                                   Frameless=False,
                                   size=QSize(700, 700))

        self.show()

    def launch_focus_window(self):
        logger.info("launch_focus_window")

        self.focus_window = FocusWindow(self)

        self.set_window_properties(title=self.focus_window.focus_obj.window_titel,
                                   central_widget=self.focus_window,
                                   Frameless=False,
                                   size=QSize(700, 300))

        self.show()

    def set_window_properties(self, title, central_widget, Frameless, size):
        self.setWindowTitle(title)
        self.setCentralWidget(central_widget)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, on=Frameless)
        self.resize(size)
        self.move_to_center()

    def move_to_center(self):
        # TODO (5) BUG move is not working at all in pyqt6!
        logger.info("move_to_center")
        frameGm=self.frameGeometry()           
        screen_width=int(QGuiApplication.primaryScreen().availableGeometry().width()/2)
        screen_hight_eye_level=int(QGuiApplication.primaryScreen().availableGeometry().height()*1/4)
        screen_pos=QPoint(screen_width,screen_hight_eye_level)
        frameGm.moveCenter(screen_pos)
        self.centered_pos = frameGm.topLeft()
        self.move(self.centered_pos)

    def set_shortcuts(self):
        self.shortcut_close = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.shortcut_close.activated.connect(lambda :sys.exit())

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
    #     # TODO (3) generate a white theme color palette for template rendering
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
    exit_code = app.exec()
    sys.exit(exit_code)

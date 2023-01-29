 # import setuptools
from PyQt5.QtCore import (Qt, QPropertyAnimation,
                          QRect, QPoint, QSize,
                          pyqtSlot, QThreadPool,
                          QWaitCondition)
from PyQt5.QtWidgets import (QMainWindow,
                             QShortcut,
                             QMessageBox,
                             QApplication)
from PyQt5.QtGui import (QKeySequence,
                         QGuiApplication)

from views.DefinitionWindow import DefinitionWindow
from views.SearchWindow import SearchWindow
from FocusWindow import FocusWindow
from HistoryWindow import HistoryWindow, WordlistWindow
from QuizWindow import QuizWindow
from DefEntry import DefEntry
from utils import get_command_line_args, set_up_logger
from another_qthread import Worker

# from autologging import traced

# TODO (1) use rootword for filename and database enteries, different flexions of the word are now saved separetly
# TODO (1) separate Wendungen, Redensarten, Sprichwörter in different headers for duden_dict (example absehen)
# TODO (0) choose carefully your code helpers: mypy for type hinting, mccbee
# TODO (4) delete all out-commented code

logger = set_up_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        logger.info("init MainWindow")
        super(MainWindow, self).__init__(parent)

        self.def_window: DefinitionWindow
        self.search_form: SearchWindow
        self.centered_pos : QPoint
        self.animation = QPropertyAnimation(self, b'geometry')
        self.wait_condition = QWaitCondition()
        
        # init QThreads
        self.threadpool = QThreadPool()
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        self.set_shortcuts()

        cl_args = get_command_line_args()
        self.launch_search_window(cl_args)
            
    def launch_search_window(self, cl_args):
        logger.info("Launch search window")
        
        self.search_form = SearchWindow(parent=self)

        if cl_args and cl_args.word:
            logger.debug('shell command with args')
            self.search_form.line.setText(cl_args.word)
            self.process_data_in_thread(cl_args)

        self.set_window_properties(title="Wörterbuch",
                                   central_widget=self.search_form,
                                   frameless=True,
                                   size=QSize(self.search_form.base_width, 40))
        
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

        self.animation.setDuration(200)
        self.animation.setStartValue(QRect(window_x, window_y, start_width, 40))
        self.animation.setEndValue(QRect(window_x, window_y, end_width, 40))
        self.animation.start()

    def launch_definition_window(self, def_obj):
        logger.info("launch definition window")

        self.def_window = DefinitionWindow(def_obj=def_obj,
                                           parent=self)

        self.def_window.construct_model(def_obj)
        self.def_window.fill_def_window(def_obj) # BUG (0) thabet fel unpacking thaherli mayhemouch esm el variable
        self.set_window_properties(title="Wörterbuch",
                                   central_widget=self.def_window,
                                   frameless=False,
                                   size=QSize(self.def_window.base_width, 690))
        self.show()

    def process_data_in_thread(self, cl_args=None):
        logger.info("process_data_in_thread")

        # Pass the function to execute
        worker = Worker(self.get_def_obj, cl_args=cl_args) # Any other args, kwargs are passed to the run function
        
        # Execute
        self.search_form.start_loading_animation()
        # TODO grey out and setreadonly line edit
        self.threadpool.start(worker)

        # connect signals and slots from second thread
        worker.signals.result.connect(self.launch_definition_window)
        worker.signals.finished.connect(self.search_form.stop_loading_animation)
        worker.signals.message_box_content_carrier.connect(self.launch_message_box)
        # worker.signals.progress.connect(self.progress_fn)

    def get_def_obj(self, cl_args, message_box_content_carrier):
        input_word = cl_args.word if cl_args and cl_args.word else self.search_form.get_filled_search_form()
        def_obj = DefEntry(input_word=input_word, cl_args=cl_args,
                           message_box_content_carrier=message_box_content_carrier,
                           wait_for_usr=self.wait_condition) # (0)**** kammel lenna esta3mel wait condition bech tpausi el code mba3ed ki fama signal emitted yes wala no a3mel wait_condition wake all w khouth signal w kammel
        return def_obj

    @pyqtSlot(dict)
    def launch_message_box(self, message_box_info):
        "Asks the user about source and traget language for translation on receipt of a signal then signal a bool answer.`"
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText(message_box_info['text'])
        msg.setWindowTitle(message_box_info['title'])
        msg.setInformativeText(message_box_info['informative_text'])
        yes_button = msg.addButton(message_box_info['yes_button_text'], QMessageBox.YesRole)
        no_button = msg.addButton(message_box_info['no_button_text'], QMessageBox.NoRole)
        msg.exec_()
        
        # hacky, but didn't find an easy way to intercept button signal after pausing code
        from GetDict import GenerateDict
        GenerateDict.CLICKED_BUTTON = [msg.clickedButton() == yes_button,
                          msg.clickedButton() == no_button]
        self.wait_condition.wakeAll()

    def return_clicked(self):
        self._end_test = True
        QApplication.quit()

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
                                   frameless=False,
                                   size=QSize(400, 500))

        self.show()

    def show_html_from_history_list(self, index):
        logger.info("show_html_from_history_list")

        self.wordlist_window.returned_index = index
        self.history_window = HistoryWindow(self)  # Why?, should be same as def window just with a different return action

        self.set_window_properties(title="Saved Words",
                                   central_widget=self.history_window,
                                   frameless=False,
                                   size=QSize(700, 700))
        self.show()

    def launch_quiz_window(self):
        logger.info("launch_quiz_window")

        self.quiz_window = QuizWindow(self)

        self.set_window_properties(title=self.quiz_window.quiz_obj.quiz_window_titel,
                                   central_widget=self.quiz_window,
                                   frameless=False,
                                   size=QSize(700, 700))

        self.show()

    def launch_focus_window(self):
        logger.info("launch_focus_window")

        self.focus_window = FocusWindow(self)

        self.set_window_properties(title=self.focus_window.focus_obj.window_titel,
                                   central_widget=self.focus_window,
                                   frameless=False,
                                   size=QSize(700, 300))

        self.show()

    def set_window_properties(self, title, central_widget, frameless, size):
        self.setWindowTitle(title)
        # Each time you use setCentralWidget(), the object that was previously the central widget is deleted.
        self.setCentralWidget(central_widget)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, on=frameless)
        self.resize(size)
        self.move_to_center()

    def move_to_center(self):
        # TODO (5) BUG move is not working at all in pyqt6!
        logger.info("move_to_center")
        frame_geometry=self.frameGeometry()           
        screen_width=int(QGuiApplication.primaryScreen().availableGeometry().width()/2)
        screen_hight_eye_level=int(QGuiApplication.primaryScreen().availableGeometry().height()*1/4)
        screen_pos=QPoint(screen_width,screen_hight_eye_level)
        frame_geometry.moveCenter(screen_pos)
        self.centered_pos = frame_geometry.topLeft()
        self.move(self.centered_pos)

    def set_shortcuts(self):
        self.shortcut_close = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.shortcut_close.activated.connect(QApplication.quit)


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

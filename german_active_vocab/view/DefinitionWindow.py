import sys
from plyer import notification

from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QTextEdit, QCheckBox, QMessageBox)
from PyQt5.QtGui import (QTextCharFormat,
                         QTextCursor,
                         QColor)
from SavingToQuiz import quizify_and_save
from DefEntry import DefEntry
from utils import set_up_logger
from settings import (dict_data_path,
                      normal_font)

logger = set_up_logger(__name__)


class DefinitionWindow(QWidget):
    def __init__(self, def_obj, parent=None):
        super().__init__(parent)
        logger.info("init defWindow")
        
        self.txt_cont = QTextEdit(self)
        self.txt_cont.move(5, 5)
        self.txt_cont.resize(690, 545)

        self.save_to_stud = QCheckBox('Studium', self)
        self.save_to_stud.move(5, 645)
        
        self.return_button = QPushButton('Return', self)
        self.return_button.move(105, 645)
        self.return_button.resize(80, 30)

        self.highlight_button = QPushButton('Highlight', self)
        self.highlight_button.move(250, 645)
        self.highlight_button.resize(90, 30)

        self.anki_button = QPushButton('Anki', self)
        self.anki_button.move(390, 645)
        self.anki_button.resize(80, 30)
        self.anki_button.setToolTip("Send German example and it's english translation to your Anki Deck")

        self.save_button = QPushButton('Save', self)
        self.save_button.move(475, 645)
        self.save_button.resize(80, 30)

        self.close_button = QPushButton('Close', self)
        self.close_button.move(610, 645)
        self.close_button.resize(80, 30)

        # workaround to keep selection in focus for force_hide method
        class LineEdit(QLineEdit):
            def focusOutEvent(self, e):
                start = self.selectionStart()
                length = self.selectionLength()
                super().focusOutEvent(e)
                self.setSelection(start, length)

        self.beispiel = LineEdit(self)
        self.beispiel.move(5, 555)
        self.beispiel.resize(690, 40)
        self.beispiel.setPlaceholderText("Sie können hier Ihr eigenes Beispiel mit dem neuen Wort eingeben, um es zu behalten.")
        self.beispiel.setToolTip("We learn best by real world associations => Tip: The best example is the sentence that incited you to look up the word.")
        
        self.beispiel2 = QLineEdit(self)
        self.beispiel2.move(5, 600)
        self.beispiel2.resize(690, 40)
        self.beispiel2.setPlaceholderText("And its translation to english..")

        self.def_window_connect_buttons(def_obj)


        # TODO (6) nsit chta3mel ama ta3ti fi erreur ki 3malte update PyQt5 -> PyQt5
        # directory = os.getcwd()
        # self.def_window.txt_cont.document().setMetaInformation(
        #     QTextDocument.DocumentUrl,
        #     QUrl.fromLocalFile(directory).toString() + "/",
        # )

    def def_window_connect_buttons(self, def_obj):
        self.highlight_button.clicked.connect(self.highlight_selection)
        self.anki_button.clicked.connect(lambda: self.send_to_anki(def_obj))
        self.save_button.clicked.connect(lambda: self.save_definition(def_obj))
        self.close_button.clicked.connect(sys.exit)

    def fill_def_window(self, def_obj):

        if def_obj.beispiel_de:
            self.beispiel.insert(def_obj.beispiel_de)

        if def_obj.beispiel_en:
            self.beispiel2.insert(def_obj.beispiel_en)

        self.txt_cont.setFont(normal_font)
        self.txt_cont.insertHtml(def_obj.defined_html)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

    def highlight_selection(self):
        logger.info("highlight_selection")
        format = QTextCharFormat()
        color = QColor(3, 155, 224)
        color = QColor(int(220*1.15), int(212*1.15), int(39*1.15))
        format.setForeground(color)
        self.txt_cont.textCursor().mergeCharFormat(format)

    def send_to_anki(self, def_obj):

        _, german_phrase, english_translation, _ = self.get_DefWindow_content()

        def_obj.ankify(german_phrase, english_translation)

    def save_definition(self, def_obj):
        logger.info("save_definition")

        self.switch_highlight_button_action(new_action='highlight', def_obj=def_obj)

        custom_html_from_qt, beispiel_de, beispiel_en, tag = self.get_DefWindow_content()

        faulty_examples = quizify_and_save(dict_data_path=dict_data_path,
                                                        word=def_obj.word,
                                                        dict_dict=def_obj.dict_dict,
                                                        dict_dict_path=def_obj.dict_dict_path,
                                                        custom_html_from_qt=custom_html_from_qt,
                                                        beispiel_de=beispiel_de,
                                                        beispiel_en=beispiel_en,
                                                        tag=tag)

        if faulty_examples:
            self.launch_no_hidden_words_in_beispiel_de_dialog(faulty_examples, def_obj)

    def launch_no_hidden_words_in_beispiel_de_dialog(self, faulty_examples, def_obj):
        faulty_examples = [str(x+1) for x in faulty_examples]
        faulty_examples = ', '.join(faulty_examples)
        logger.info("launch_no_hidden_words_in_beispiel_de_dialog")
        choice = QMessageBox.information(self, "Attention a la vache",
                                    f"none of the words to hide are detected in your custom german example(s) {faulty_examples}. \n"
                                    "Please highlight the word you want to hide in quiz mode manually, hit Force Hide and save again",
                                    QMessageBox.Ok)
        
        if choice == QMessageBox.Ok:
            self.switch_highlight_button_action(new_action='hide', def_obj=def_obj)

    def switch_highlight_button_action(self, new_action, def_obj):
        if new_action=='hide':
            if self.highlight_button.text() != 'Force Hide':
                self.highlight_button.setText('Force Hide')
                self.highlight_button.clicked.disconnect(self.highlight_selection)
                self.highlight_button.clicked.connect(self.force_hide(def_obj))
                self.show()
        elif new_action=='highlight':
            if self.highlight_button.text() != 'Highlight':
                self.highlight_button.setText('Highlight')
                self.highlight_button.clicked.disconnect(self.force_hide(def_obj))
                self.highlight_button.clicked.connect(self.highlight_selection)
                self.show()
        else: 
            raise RuntimeError(f'Keyword {new_action} not recognized')
    
    def force_hide(self, def_obj):
        '''add selected word to  hidden words in dict file'''
        # TODO (1) descativate button if no selection
        logger.info("force_hide")
        # DONE (1) add manually hidden words to dict_file
        selected_text2hide = self.txt_cont.textCursor().selectedText() or self.beispiel.selectedText()

        def_obj.add_word_to_hidden_list(selected_text2hide)
        
        notification.notify(title='Word added to hidden words',
                            message=selected_text2hide,
                            timeout=5)

    def get_DefWindow_content(self):
        beispiel_de = self.beispiel.text()
        beispiel_en = self.beispiel2.text()
        beispiel_de = beispiel_de.replace('- ', '– ')
        beispiel_en = beispiel_en.replace('- ', '– ')
        custom_html_from_qt = self.txt_cont.toHtml()
        tag = 'Studium' if self.save_to_stud.isChecked() else ''
        return custom_html_from_qt, beispiel_de, beispiel_en, tag
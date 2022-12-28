import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QTextEdit, QCheckBox)
from PyQt5.QtGui import (QTextCharFormat,
                         QTextCursor,
                         QColor)
from SavingToQuiz import save_from_def_mode

from settings import (dict_data_path,
                      normal_font,
                      anki_cfg)
from DefEntry import DefEntry
from PushToAnki import Anki

from WordProcessing import update_words_to_hide
from SavingToQuiz import wrap_words_to_learn_in_clozes
from utils import set_up_logger

logger = set_up_logger(__name__)


class DefinitionWindow(QWidget):
    def __init__(self, parent=None):
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

        self.beispiel = QLineEdit(self)
        self.beispiel.move(5, 555)
        self.beispiel.resize(690, 40)
        self.beispiel.setPlaceholderText("Sie können hier Ihr eigenes Beispiel mit dem neuen Wort eingeben, um es zu behalten.")
        self.beispiel.setToolTip('We learn best by real world associations => Tip: The best example is the sentence that incited you to look up the word.')
        
        self.beispiel2 = QLineEdit(self)
        self.beispiel2.move(5, 600)
        self.beispiel2.resize(690, 40)
        self.beispiel2.setPlaceholderText("And its translation to english..")

        self.get_def_object()

        # TODO nsit chta3mel ama ta3ti fi erreur ki 3malte update PyQt5 -> PyQt5
        # directory = os.getcwd()
        # self.def_window.txt_cont.document().setMetaInformation(
        #     QTextDocument.DocumentUrl,
        #     QUrl.fromLocalFile(directory).toString() + "/",
        # )

        self.txt_cont.setFont(normal_font)
        self.txt_cont.insertHtml(self.def_obj.defined_html)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

        self.def_window_connect_buttons()

    def def_window_connect_buttons(self):
        self.return_button.clicked.connect(self.parent().launch_first_window)
        self.highlight_button.clicked.connect(self.highlight_selection)
        self.anki_button.clicked.connect(self.send_to_anki)
        self.save_button.clicked.connect(self.save_definition)
        self.close_button.clicked.connect(self.close)

    def get_def_object(self):
        nbargin = len(sys.argv) - 1

        if nbargin == 0:
            word, checkbox_en, checkbox_fr = self.parent().get_filled_search_form()
        else:
            word = sys.argv[1]
            checkbox_en = False
            checkbox_fr = False


        if nbargin <2:
            beispiel_de = ''
            beispiel_en = ''
        elif nbargin == 2:
            beispiel_de = sys.argv[2].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')
            beispiel_en = ''
        elif nbargin == 3 :
            beispiel_de = sys.argv[2].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')
            beispiel_en = sys.argv[3].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')
        else :
            raise RuntimeError('Number of argument exceeds 3')


        if nbargin == 2:
            self.beispiel.insert(beispiel_de)

        if nbargin == 3:
            self.beispiel2.insert(beispiel_en)

        self.def_obj = DefEntry(word=word,
                                checkbox_en=checkbox_en,
                                checkbox_fr=checkbox_fr,
                                beispiel_de=beispiel_de,
                                beispiel_en=beispiel_en)

    def highlight_selection(self):
        logger.info("highlight_selection")
        format = QTextCharFormat()
        color = QColor(3, 155, 224)
        color = QColor(int(220*1.15), int(212*1.15), int(39*1.15))
        format.setForeground(color)
        self.txt_cont.textCursor().mergeCharFormat(format)

    def send_to_anki(self):

        word = self.def_obj.word
        german_phrase, english_phrase = self.get_example_fileds_content()
        dict_dict = self.def_obj.dict_dict
        words_2_hide = update_words_to_hide(dict_dict)
        front_with_cloze_wrapping = wrap_words_to_learn_in_clozes(german_phrase, words_2_hide)

        fields = [front_with_cloze_wrapping, english_phrase, word]

        with Anki(base=anki_cfg['base'],
                  profile=anki_cfg['profile']) as a:
            a.add_notes_single(fields=fields, tags='', model=anki_cfg['model'], deck=anki_cfg['deck'])

    def save_definition(self):
        logger.info("save_definition")
        
        custom_html_from_qt = self.txt_cont.toHtml()
        studie_tag = self.save_to_stud.isChecked()
        beispiel_de, beispiel_en = self.get_example_fileds_content()
        tag = ''
        if studie_tag:
            tag = 'Studium'

        word = self.def_obj.word
        dict_dict = self.def_obj.dict_dict

        save_from_def_mode(dict_data_path, word, custom_html_from_qt, beispiel_de,
                          beispiel_en, tag,
                          dict_dict, self.def_obj.dict_dict_path)

    def get_example_fileds_content(self):
        beispiel_de = self.beispiel.text()
        beispiel_en = self.beispiel2.text()
        beispiel_de = beispiel_de.replace('- ', '– ')
        beispiel_en = beispiel_en.replace('- ', '– ')
        return beispiel_de,beispiel_en













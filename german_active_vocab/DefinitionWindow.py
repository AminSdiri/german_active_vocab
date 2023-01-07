import sys
from plyer import notification

from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QTextEdit, QCheckBox, QMessageBox)
from PyQt5.QtGui import (QTextCharFormat,
                         QTextCursor,
                         QColor)
from SavingToQuiz import save_from_def_mode
from DefEntry import DefEntry
from PushToAnki import Anki
from SavingToQuiz import wrap_words_to_learn_in_clozes
from GetDict.GenerateDict import extract_synonymes_in_html, get_definitions_from_dict_dict
from utils import set_up_logger
from settings import (dict_data_path,
                      normal_font,
                      anki_cfg)

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

        # workaround to keep selection in focus
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
        self.beispiel.setToolTip('We learn best by real world associations => Tip: The best example is the sentence that incited you to look up the word.')
        
        self.beispiel2 = QLineEdit(self)
        self.beispiel2.move(5, 600)
        self.beispiel2.resize(690, 40)
        self.beispiel2.setPlaceholderText("And its translation to english..")

        self.get_def_object()

        # TODO (6) nsit chta3mel ama ta3ti fi erreur ki 3malte update PyQt5 -> PyQt5
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
        self.close_button.clicked.connect(sys.exit)

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

        german_phrase, english_translation = self.get_example_fileds_content()

        front_with_cloze_wrapping = wrap_words_to_learn_in_clozes(german_phrase, self.def_obj.dict_dict, self.def_obj.dict_dict_path)

        definitions_list = get_definitions_from_dict_dict(self.def_obj.dict_dict, info='definition')
        definitions_html = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in definitions_list]) + '</ul>'

        synonymes_html = extract_synonymes_in_html(self.def_obj.dict_dict)

        with Anki(base=anki_cfg['base'],
                        profile=anki_cfg['profile']) as a:
                a.add_notes_single(cloze=front_with_cloze_wrapping,
                                   hint1=synonymes_html,
                                   hint2=english_translation,
                                   hint3=definitions_html,
                                   answer_extra=self.def_obj.word,
                                   tags='',
                                   model=anki_cfg['model'],
                                   deck=anki_cfg['deck'],
                                   overwrite_notes=anki_cfg['overwrite'])

    def save_definition(self):
        logger.info("save_definition")

        self.switch_highlight_button_action(new_action='highlight')

        beispiel_de, beispiel_en = self.get_example_fileds_content()
        tag = 'Studium' if self.save_to_stud.isChecked() else ''

        no_hidden_words_in_example = save_from_def_mode(dict_data_path=dict_data_path,
                                                        word=self.def_obj.word,
                                                        custom_html_from_qt=self.txt_cont.toHtml(),
                                                        beispiel_de=beispiel_de,
                                                        beispiel_en=beispiel_en,
                                                        tag=tag,
                                                        dict_dict=self.def_obj.dict_dict,
                                                        dict_dict_path=self.def_obj.dict_dict_path)

        if no_hidden_words_in_example:
            self.launch_no_hidden_words_in_beispiel_de_dialog(no_hidden_words_in_example)

    def launch_no_hidden_words_in_beispiel_de_dialog(self, no_hidden_words_in_example):
        faulty_examples = [str(x+1) for x in no_hidden_words_in_example]
        faulty_examples = ', '.join(faulty_examples)
        logger.info("launch_no_hidden_words_in_beispiel_de_dialog")
        choice = QMessageBox.information(self, "Attention a la vache",
                                    f"none of the words to hide are detected in your custom german example(s) {faulty_examples}. \n"
                                    "Please highlight the word you want to hide in quiz mode manually, hit Force Hide and save again",
                                    QMessageBox.Ok)
        
        if choice == QMessageBox.Ok:
            self.switch_highlight_button_action(new_action='hide')

    def switch_highlight_button_action(self, new_action):
        if new_action=='hide':
            if self.highlight_button.text() != 'Force Hide':
                self.highlight_button.setText('Force Hide')
                self.highlight_button.clicked.disconnect(self.highlight_selection)
                self.highlight_button.clicked.connect(self.force_hide)
                self.show()
        elif new_action=='highlight':
            if self.highlight_button.text() != 'Highlight':
                self.highlight_button.setText('Highlight')
                self.highlight_button.actions   #clicked.disconnect(self.force_hide)
                self.highlight_button.clicked.connect(self.highlight_selection)
                self.show()
        else: 
            raise RuntimeError(f'Keyword {new_action} not recognized')
    
    def force_hide(self):
        '''add selected word to  hidden words in dict file'''
        # TODO (1) descativate button if no selection
        logger.info("force_hide")
        # DONE (1) add manually hidden words to dict_file
        selected_text2hide = self.txt_cont.textCursor().selectedText() or self.beispiel.selectedText()

        if selected_text2hide in self.def_obj.dict_dict['hidden_words_list']:
            logger.warning('selected word is already in hidden words list, choose another one')
        self.def_obj.dict_dict['hidden_words_list'].append(selected_text2hide)
        # TODO else is not needed? dict have already constructed after save method?
        # else:
        #     self.def_obj.dict_dict['hidden_words_list'] = generate_hidden_words_list(self.def_obj.dict_dict)
        #     self.def_obj.dict_dict['hidden_words_list'].append(selected_text2hide)
        # write_str_to_file(dict_dict_path, json.dumps(self.def_obj.dict_dict))

        logger.debug(f'word2hide: {selected_text2hide}')
        # DONE (0) notify user
        notification.notify(title='Word added to hidden words',
                                message=selected_text2hide,
                                timeout=5)
        self.show()

    def get_example_fileds_content(self):
        beispiel_de = self.beispiel.text()
        beispiel_en = self.beispiel2.text()
        beispiel_de = beispiel_de.replace('- ', '– ')
        beispiel_en = beispiel_en.replace('- ', '– ')
        return beispiel_de,beispiel_en
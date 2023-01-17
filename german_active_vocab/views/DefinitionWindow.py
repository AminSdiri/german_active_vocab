from plyer import notification

from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QTextEdit, QCheckBox, QMessageBox)
from PyQt5.QtGui import (QTextCharFormat,
                         QTextCursor,
                         QColor)
from SavingToQuiz import quizify_and_save
from EditDictModelView import DictEditorWidget, TreeModel
from GetDict.GenerateDict import dict_replace_value
from utils import set_up_logger, format_html
from settings import (DICT_DATA_PATH,
                      NORMAL_FONT)

logger = set_up_logger(__name__)

# TODO* (1) separate Def-Obj Model operations from View 

class DefinitionWindow(QWidget):
    def __init__(self, def_obj, parent=None):
        super().__init__(parent)
        logger.info("init defWindow")

        self.base_width = 700
        self.extended_width = 1400
        
        # TODO add deleted and focused Properties from TreeModel, update TextView 
        # DONE delete an element should hide all of it's children -> select an element should select all of it's children
        # DONE get all selected items
        # DONE update get path in get_address 
        # DONE update tree construction in treeModel
        # DONE highlight deleted in red in tree
        
        headers = ["Type", "Content"]
        self.set_dict_tree_model(def_obj, headers)
        self.dict_tree_view = DictEditorWidget(self.model, parent = self)
        self.dict_tree_view.move(700, 5)
        self.dict_tree_view.resize(690, 635)

        self.def_obj = def_obj
        self.model.dataChanged.connect(self.refresh_textView)
        
        self.txt_cont = QTextEdit(self)
        self.txt_cont.move(5, 5)
        self.txt_cont.resize(690, 545)
        self.txt_cont.setReadOnly(True)

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

        self.edit_button = QPushButton('Edit >', self)
        self.edit_button.move(610, 645)
        self.edit_button.resize(80, 30)

        self.beispiel = LineEdit(self)
        self.beispiel.move(5, 555)
        self.beispiel.resize(690, 40)
        self.beispiel.setPlaceholderText("Sie können hier Ihr eigenes Beispiel mit dem neuen Wort eingeben, um es zu behalten.")
        self.beispiel.setToolTip("We learn best by real world associations => Tip: The best example is the sentence that incited you to look up the word.")
        
        self.beispiel2 = QLineEdit(self)
        self.beispiel2.move(5, 600)
        self.beispiel2.resize(690, 40)
        self.beispiel2.setPlaceholderText("And its translation to english..")

        self.discard_button = QPushButton('Discard', self)
        self.discard_button.move(1090, 645)
        self.discard_button.resize(80, 30)
        self.discard_button.setToolTip("Remove selection from dict view, those Elements will not be shown also in reviews")

        self.restore_button = QPushButton('Restore', self)
        self.restore_button.move(1175, 645)
        self.restore_button.resize(80, 30)
        self.restore_button.setToolTip("Restore discarded items")

        self.bookmark_button = QPushButton('Bookmark', self)
        self.bookmark_button.move(1270, 645)
        self.bookmark_button.resize(120, 30)
        self.bookmark_button.setToolTip("Add Items to Focus Mode, those parts will be seperatly reviewed and also will be sent to Anki.")


        self.def_window_connect_buttons()

    def set_dict_tree_model(self, def_obj, headers):
        if 'content' in def_obj.dict_dict:
            self.model = TreeModel(headers, def_obj.dict_dict['content'])
        elif 'content_1' in def_obj.dict_dict:
            # ugly, not working with code, make user choose a language direction
            # and have a unified dict
            self.model = TreeModel(headers, def_obj.dict_dict['content_1'])
            self.model.createData(def_obj.dict_dict['content_2'])

    def def_window_connect_buttons(self):
        # self.highlight_button.clicked.connect(self.highlight_selection)
        # self.highlight_button.clicked.connect(lambda: self.refresh(def_obj))
        self.anki_button.clicked.connect(self.send_to_anki)
        self.save_button.clicked.connect(self.save_definition)
        self.edit_button.clicked.connect(self.expend_window_to_edit_dict)
        self.discard_button.clicked.connect(lambda: self.format_selection(operation='discard'))
        self.restore_button.clicked.connect(self.restore_discarded)
        self.bookmark_button.clicked.connect(lambda: self.format_selection(operation='bookmark'))
        # self.highlight_button.clicked.connect()

    def format_selection(self, operation: str):
        for index in self.dict_tree_view.selectedIndexes():
            if not index.data() or not index.column():
                # ignore if it's in front of a branche or it's a key
                print(f'formatting {index.data()}')
                continue
            text, address = self.model.get_dict_address(index)
            text = format_html(text, operation)
            if operation == 'bookmark':
                # TODO (-1)
                # khouth definition wel examples me selection
                # zidhom lel anki
                # khouth l'adress mta3 lblock w khalih 3la jnab li tal9a kifeh structure mta3 el focus ejdida
                # 
                pass
            self.def_obj.update_dict(text, address)

            # update_model
            self.model.setData(index, text)
            self.model.dataChanged.emit(index, index)
        self.update_TextEdit()

    def restore_discarded(self):

        self.def_obj.dict_dict = dict_replace_value(self.def_obj.dict_dict)

        # update whole model
        # NOT WORKING
        # self.dict_tree_view.hide()
        # self.model.beginResetModel()
        # headers = ["Type", "Content"]
        # self.model = TreeModel(headers, self.def_obj.dict_dict['content'])
        # self.model.dataChanged.emit(QModelIndex(), QModelIndex())
        # self.model.endResetModel()
        # self.dict_tree_view.show()
        # self.dict_tree_view.update()
        # self.dict_tree_view.expandAll()

        self.dict_tree_view.deleteLater() # lets Qt knows it needs to delete this widget from the GUI
        
        headers = ["Type", "Content"]
        self.model = TreeModel(headers, self.def_obj.dict_dict['content'])
        
        del self.dict_tree_view
        
        self.update_TextEdit()
        
        self.dict_tree_view = DictEditorWidget(self.model, parent = self)
        self.dict_tree_view.move(700, 5)
        self.dict_tree_view.resize(690, 635)
        self.dict_tree_view.show()

    def refresh_textView(self, index):
        text, address = self.model.get_dict_address(index)
        self.def_obj.update_dict(text, address)
        self.update_TextEdit()

    def update_TextEdit(self):
        defined_html = self.def_obj.re_render_html()
        self.txt_cont.clear()
        self.txt_cont.insertHtml(defined_html)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)
        self.show()

    def expend_window_to_edit_dict(self):
        self.parent().expand_definition_window_animation()
        self.dict_tree_view.expandAll()
        self.dict_tree_view.show()

    def fill_def_window(self, def_obj):
        if def_obj.beispiel_de:
            self.beispiel.insert(def_obj.beispiel_de)

        if def_obj.beispiel_en:
            self.beispiel2.insert(def_obj.beispiel_en)

        self.txt_cont.setFont(NORMAL_FONT)
        self.txt_cont.insertHtml(def_obj.defined_html)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

    def highlight_selection(self):
        logger.info("highlight_selection")
        format = QTextCharFormat()
        color = QColor(3, 155, 224)
        color = QColor(int(220*1.15), int(212*1.15), int(39*1.15))
        format.setForeground(color)
        self.txt_cont.textCursor().mergeCharFormat(format)

    def send_to_anki(self):

        _, german_phrase, english_translation, _ = self.get_DefWindow_content()

        self.def_obj.ankify(german_phrase, english_translation)

    def save_definition(self):
        logger.info("save_definition")

        self.switch_highlight_button_action(new_action='highlight')

        custom_html_from_qt, beispiel_de, beispiel_en, tag = self.get_DefWindow_content()

        faulty_examples = quizify_and_save(dict_data_path=DICT_DATA_PATH,
                                            word=self.def_obj.search_word,
                                            dict_dict=self.def_obj.dict_dict,
                                            dict_dict_path=self.def_obj.dict_dict_path,
                                            qt_html_content=custom_html_from_qt,
                                            beispiel_de=beispiel_de,
                                            beispiel_en=beispiel_en,
                                            tag=tag)

        if faulty_examples:
            self.launch_no_hidden_words_in_beispiel_de_dialog(faulty_examples)

    def launch_no_hidden_words_in_beispiel_de_dialog(self, faulty_examples):
        faulty_examples = [str(x+1) for x in faulty_examples]
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
                self.highlight_button.clicked.disconnect()
                self.highlight_button.clicked.connect(self.force_hide)
                self.show()
        elif new_action=='highlight':
            if self.highlight_button.text() != 'Highlight':
                self.highlight_button.setText('Highlight')
                self.highlight_button.clicked.disconnect()
                self.highlight_button.clicked.connect(self.highlight_selection)
                self.show()
        else: 
            raise RuntimeError(f'Keyword {new_action} not recognized')
    
    def force_hide(self):
        '''add selected word to  hidden words in dict file'''
        # TODO (1) desactivate button if no selection
        logger.info("force_hide")
        # DONE (1) add manually hidden words to dict_file
        selected_text2hide = self.txt_cont.textCursor().selectedText() or self.beispiel.selectedText()

        self.def_obj.add_word_to_hidden_list(selected_text2hide)
        
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


class LineEdit(QLineEdit):
    # workaround to keep selection in focus for force_hide method
    # but we've lost the blinking cursor, no big deal
    def focusOutEvent(self, e):
        start = self.selectionStart()
        length = self.selectionLength()
        super().focusOutEvent(e)
        self.setSelection(start, length)
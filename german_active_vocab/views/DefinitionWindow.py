import sys
from typing import Literal
from plyer import notification

from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QTextEdit, QMessageBox)
from PyQt5.QtGui import (QTextCharFormat,
                         QTextCursor,
                         QColor)
from SavingToQuiz import check_for_hidden_words_presence_in_custom_examples, quizify_and_save
from EditDictModelView import DictEditorWidget, TreeModel
from GetDict.ParsingSoup import format_html, remove_html_wrapping, wrap_text_in_tag_with_attr
from views.ToggleButton import ToggleButton
from utils import set_up_logger
from settings import (DICT_DATA_PATH,
                      NORMAL_FONT)

logger = set_up_logger(__name__)

# TODO (1) LOOK&FEEL using boxLayout with percentages instead of hardcoded dimensions
# DONE (0)* add radio button to switch between duden and pons
# DONE (0) make text of radio button grey if dict_content is empty and white if it's full
# TODO (1) separate Def-Obj Model operations from View 
# TODO (1) rewrite refresh dict/text, address/all functions and use the model signal

# DONE add deleted and focused Properties from TreeModel, update TextView 
# DONE delete an element should hide all of it's children -> select an element should select all of it's children
# DONE get all selected items
# DONE update get path in get_address 
# DONE update tree construction in treeModel
# DONE highlight deleted in red in tree
# DONE Subtle color for all words that are supposed to be hidden.
# DONE Subtle color for all words that are supposed to be hidden in custom examples.
# This will help detect if no word will be hidden in the custom examples and 


class DefinitionWindow(QWidget):
    def __init__(self, def_obj=None, parent=None):
        super().__init__(parent)
        logger.info("init defWindow")

        self.base_width = 700
        self.extended_width = 1400
        
        self.def_obj: 'DefEntry' = def_obj
        self.model: TreeModel = None

        self.dict_tree_view = DictEditorWidget(self.model, parent = self)
        self.dict_tree_view.move(700, 5)
        self.dict_tree_view.resize(690, 635)

        self.text_view = QTextEdit(self)
        self.text_view.move(5, 5)
        self.text_view.resize(690, 545)
        self.text_view.setReadOnly(True)
        self.text_view.selectionChanged.connect(
            lambda: self.force_hide_button.setEnabled(
                self.text_view.textCursor().selectedText() != "")
                    )

        # if code is being tested, the Return button have the "Pass Test" fonctionality
        # Do NOT load pytest anywhere outside test files for this to work
        self.return_button = QPushButton('Return' if "pytest" not in sys.modules else "Pass Test", self)
        self.return_button.move(5, 645)
        self.return_button.resize(80, 30)

        pons_color = '#02AF31'
        duden_color ='#FFD500'
        self.du_pons_switch = ToggleButton(parent=self,
                                           hight=20,
                                           bg_color=pons_color,
                                           active_color=duden_color)
        self.du_pons_switch.move(115, 650)
        self.du_pons_switch.toggled.connect(self.change_requested)

        self.force_hide_button = QPushButton('Force Hide', self, enabled=False)
        self.force_hide_button.move(200, 645)
        self.force_hide_button.resize(90, 30)
        self.force_hide_button.setToolTip("Add selected word to words to learn if it's not automaticly recognized as a flexion (not colorized).")

        self.add_example_button = QPushButton('Add', self, enabled=False)
        self.add_example_button.move(300, 645)
        self.add_example_button.resize(80, 30)
        self.add_example_button.setToolTip("Add your examples to the word dictionnary")

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
        # enable add_example button only if a custom example is provided
        self.beispiel.textChanged[str].connect(lambda: self.add_example_button.setEnabled(self.beispiel.text() != ""))
        
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

    def construct_model(self):
        dict_content = self.def_obj.word_dict.get_dict_content()
        self.model = TreeModel(headers=["Type", "Content"],
                               data=dict_content)
        self.model.dataChanged.connect(self.refresh_dict)
        self.dict_tree_view.setModel(self.model)

    def change_requested(self):
        if self.du_pons_switch.isChecked():
            self.def_obj.word_dict['requested'] = 'duden'
        else:
            self.def_obj.word_dict['requested'] = 'pons'
        
        self.refresh_all()

    def def_window_connect_buttons(self):
        self.add_example_button.clicked.connect(self.add_example)
        self.force_hide_button.clicked.connect(self.force_hide)
        self.anki_button.clicked.connect(self.send_examples_to_anki)
        self.save_button.clicked.connect(self.save_definition)
        self.edit_button.clicked.connect(self.expend_window_to_edit_dict)
        self.discard_button.clicked.connect(lambda: self.format_selection(operation='discard'))
        self.restore_button.clicked.connect(self.restore_discarded)
        self.bookmark_button.clicked.connect(lambda: self.format_selection(operation='bookmark'))
        # if code is being tested, the Return button have the "Pass Test" fonctionality
        # Do NOT load pytest anywhere outside test files for this to work
        if "pytest" not in sys.modules:
            self.return_button.clicked.connect(self.parent().launch_search_window)
        else:
            self._end_test = False
            self.return_button.clicked.connect(self.parent().return_clicked)

    def add_example(self):
        _, german_phrase, english_translation, _ = self.get_def_window_content()
        # lenna add, lezemha tchouf machen fama fel example walle
        self.def_obj.word_dict = self.def_obj.word_dict.append_new_examples_in_word_dict(german_phrase, english_translation)
        # check if one of the words will get hidden in the custom german examples -> otherwise ask the user manually to select it
        # DONE (-1) kamel 3al old custom examples
        if 'custom_examples' in self.def_obj.word_dict:
            all_word_variants, _ = self.def_obj.word_dict.get_all_hidden_words()
            faulty_examples = check_for_hidden_words_presence_in_custom_examples(examples=self.def_obj.word_dict['custom_examples']['german'],
                                                                                            hidden_words=all_word_variants)
        self.beispiel.clear()
        self.beispiel2.clear()
        # TODO save here automaticly or by hitting the save button?
        self.def_obj.word_dict.save_word_dict()

        if faulty_examples:
            self.launch_no_hidden_words_in_beispiel_de_dialog(faulty_examples)

        self.update_text_view()        

    def format_selection(self, operation: str) -> None:
        for index in self.dict_tree_view.selectedIndexes():
            if not index.data() or not index.column():
                # ignore if it's in front of a branche or it's a key
                continue
            print(f'formatting {index.data()}')
            text, address = self.model.get_dict_address(index)
            # add to anki
            if operation == 'bookmark':
                # create a simple dict that holds the def block
                bookmarked_def_block = self.def_obj.word_dict.get_block_from_address(address)
                note_id, already_in_anki = self.def_obj.ankify_def_block_example(def_block=bookmarked_def_block)
                # add anki id if note is not already in anki
                if not already_in_anki:
                    text = wrap_text_in_tag_with_attr(text=text, tag_name='span', attr_name='data-anki-note-id', attr_value=note_id)
                
            text = format_html(text, operation)
            self.def_obj.word_dict.update_dict(text, address)

            # update_model
            self.model.setData(index, text)
            # self.model.dataChanged.emit(index, index) # signal already emmited in setData 
        self.def_obj.word_dict.save_word_dict()
        self.update_text_view()

    def restore_discarded(self) -> None:
        operation = lambda elem: remove_html_wrapping(elem, unwrap='red_strikthrough')
        self.def_obj.word_dict.recursivly_operate_on_last_lvl(operation)

        self.refresh_all()

    def refresh_all(self):
        # update whole model
        # NOT WORKING
        # self.dict_tree_view.hide()
        # self.model.beginResetModel()
        # headers = ["Type", "Content"]
        # self.model = TreeModel(headers, self.def_obj.word_dict['content'])
        # self.model.dataChanged.emit(QModelIndex(), QModelIndex())
        # self.model.endResetModel()
        # self.dict_tree_view.show()
        # self.dict_tree_view.update()
        # self.dict_tree_view.expandAll()

        self.dict_tree_view.deleteLater() # lets Qt knows it needs to delete this widget from the GUI
        
        self.construct_model()
        
        del self.dict_tree_view
        
        self.update_text_view()
        
        self.dict_tree_view = DictEditorWidget(self.model, parent = self)
        self.dict_tree_view.move(700, 5)
        self.dict_tree_view.resize(690, 635)
        self.dict_tree_view.show()

    def refresh_dict(self, index) -> None:
        text, address = self.model.get_dict_address(index)
        self.def_obj.word_dict.update_dict(text, address)
        self.update_text_view()

    def update_text_view(self) -> None:
        self.def_obj.defined_html = self.def_obj.render_html()
        self.text_view.clear()
        self.text_view.insertHtml(self.def_obj.defined_html)
        self.text_view.moveCursor(QTextCursor.MoveOperation.Start)
        self.show()

    def expend_window_to_edit_dict(self) -> None:
        self.parent().expand_definition_window_animation()
        self.dict_tree_view.expandAll()
        self.dict_tree_view.show()

    def fill_def_window(self) -> None:
        if self.def_obj.word_query.beispiel_de:
            self.beispiel.insert(self.def_obj.word_query.beispiel_de)

        if self.def_obj.word_query.beispiel_en:
            self.beispiel2.insert(self.def_obj.word_query.beispiel_en)

        self.text_view.setFont(NORMAL_FONT)
        self.text_view.insertHtml(self.def_obj.defined_html)
        self.text_view.moveCursor(QTextCursor.MoveOperation.Start)

        if self.def_obj.word_dict['requested'] == 'duden':
            self.du_pons_switch.setChecked(True)
        elif self.def_obj.word_dict['requested'] == 'pons':
            self.du_pons_switch.setChecked(False)
        else:
            self.du_pons_switch.setEnabled(False)

    def highlight_selection(self) -> None:
        logger.info("highlight_selection")
        color_format = QTextCharFormat()
        color = QColor(3, 155, 224)
        color = QColor(int(220*1.15), int(212*1.15), int(39*1.15))
        color_format.setForeground(color)
        self.text_view.textCursor().mergeCharFormat(color_format)

    def send_examples_to_anki(self) -> None:

        self.def_obj.ankify_custom_examples()

    def save_definition(self) -> None:
        logger.info("save_definition")

        # Force hide is the only button function we need now
        # self.switch_highlight_button_action(new_action='highlight')

        _, beispiel_de, beispiel_en, tag = self.get_def_window_content()

        faulty_examples = quizify_and_save(dict_data_path=DICT_DATA_PATH,
                                            word_dict=self.def_obj.word_dict,
                                            saving_word=self.def_obj.word_query.saving_word,
                                            beispiel_de=beispiel_de,
                                            beispiel_en=beispiel_en,
                                            tag=tag)

        if faulty_examples:
            self.launch_no_hidden_words_in_beispiel_de_dialog(faulty_examples)

    def launch_no_hidden_words_in_beispiel_de_dialog(self, faulty_examples) -> None:
        faulty_examples = [str(x+1) for x in faulty_examples]
        faulty_examples = ', '.join(faulty_examples)
        logger.info("launch_no_hidden_words_in_beispiel_de_dialog")
        choice = QMessageBox.information(self, "Attention a la vache",
                                    f"none of the words to hide are detected in your custom german example(s) {faulty_examples}. \n"
                                    "Please select the word you want to hide in quiz mode manually, hit Force Hide and save again",
                                    QMessageBox.Ok)
        
        # Force hide is the only button function we need now
        # if choice == QMessageBox.Ok:
        #     self.switch_highlight_button_action(new_action='hide')

    # Force hide is the only button function we need now
    # def switch_highlight_button_action(self, new_action) -> None:
    #     if new_action=='hide':
    #         if self.highlight_button.text() != 'Force Hide':
    #             self.highlight_button.setText('Force Hide')
    #             try:
    #                 # button not connected to anything on the first run
    #                 self.highlight_button.clicked.disconnect()
    #             except TypeError:
    #                 pass
    #             self.highlight_button.clicked.connect(self.force_hide)
    #             self.show()
    #     elif new_action=='highlight':
    #         if self.highlight_button.text() != 'Highlight':
    #             self.highlight_button.setText('Highlight')
    #             self.highlight_button.clicked.disconnect()
    #             self.highlight_button.clicked.connect(self.highlight_selection)
    #             self.show()
    #     else: 
    #         raise RuntimeError(f'Keyword {new_action} not recognized')
    
    def force_hide(self) -> None:
        '''add selected word to  hidden words in dict file'''
        # DONE (1) desactivate button if no selection
        logger.info("force_hide")
        # DONE (1) add manually hidden words to dict_file
        selected_text2hide = self.text_view.textCursor().selectedText() or self.beispiel.selectedText()

        self.def_obj.add_word_to_hidden_list(selected_text2hide)

        self.update_text_view()
        
        self.def_obj.word_dict.save_word_dict()
        notification.notify(title='Word added to hidden words',
                            message=selected_text2hide,
                            timeout=5)

    def get_def_window_content(self) -> tuple[str, str, str, Literal['Studium', '']]:
        beispiel_de = self.beispiel.text()
        beispiel_en = self.beispiel2.text()
        beispiel_de = beispiel_de.replace('- ', '– ')
        beispiel_en = beispiel_en.replace('- ', '– ')
        custom_html_from_qt = self.text_view.toHtml()
        tag = ''
        return custom_html_from_qt, beispiel_de, beispiel_en, tag


class LineEdit(QLineEdit):
    # workaround to keep selection in focus for force_hide method
    # but we've lost the blinking cursor, no big deal
    def focusOutEvent(self, e) -> None:
        start = self.selectionStart()
        length = self.selectionLength()
        super().focusOutEvent(e)
        self.setSelection(start, length)

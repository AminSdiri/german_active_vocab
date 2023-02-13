import sys
from typing import Literal
from plyer import notification

from PyQt5.QtWidgets import (QPushButton, QWidget, QLineEdit, QTextEdit, QCheckBox, QMessageBox)
from PyQt5.QtGui import (QTextCharFormat,
                         QTextCursor,
                         QColor)
from SavingToQuiz import quizify_and_save
from EditDictModelView import DictEditorWidget, TreeModel
from utils import remove_html_wrapping, set_up_logger, format_html
from settings import (DICT_DATA_PATH,
                      NORMAL_FONT)

logger = set_up_logger(__name__)

# plemplem, herumwirbeln 3tatek error

# TODO (1) separate Def-Obj Model operations from View 
# custom example li savitou mel pons dict zeda mawjoud fel kelma me duden (prolet).
# 7aja zaboura 3alekher ama fama risque mta3 conflit

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

        self.txt_cont = QTextEdit(self)
        self.txt_cont.move(5, 5)
        self.txt_cont.resize(690, 545)
        self.txt_cont.setReadOnly(True)

        self.save_to_stud = QCheckBox('Studium', self)
        self.save_to_stud.move(5, 645)
        
        # if code is being tested, the Return button have the "Pass Test" fonctionality
        # Do NOT load pytest anywhere outside test files for this to work
        self.return_button = QPushButton('Return' if "pytest" not in sys.modules else "Pass Test", self)
        self.return_button.move(105, 645)
        self.return_button.resize(80, 30)

        self.highlight_button = QPushButton('Force Hide', self)
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

    def construct_model(self, def_obj):
        self.def_obj = def_obj
        dict_content = def_obj.dict_dict.get_dict_content()
        self.model = TreeModel(headers=["Type", "Content"],
                               data=dict_content)
        self.model.dataChanged.connect(self.refresh_dict)
        self.dict_tree_view.setModel(self.model)

    def def_window_connect_buttons(self):
        self.highlight_button.clicked.connect(self.force_hide)
        self.anki_button.clicked.connect(self.send_to_anki)
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

    def format_selection(self, operation: str) -> None:
        for index in self.dict_tree_view.selectedIndexes():
            if not index.data() or not index.column():
                # ignore if it's in front of a branche or it's a key
                continue
            print(f'formatting {index.data()}')
            text, address = self.model.get_dict_address(index)
            text = format_html(text, operation)
            # add to anki
            if operation == 'bookmark':
                # create a simple dict that holds the def block
                bookmarked_def_block = self.def_obj.dict_dict.get_block_from_address(address)
                self.def_obj.ankify(def_block=bookmarked_def_block)
                
            self.def_obj.dict_dict.update_dict(text, address)

            # update_model
            self.model.setData(index, text)
            # self.model.dataChanged.emit(index, index) # signal already emmited in setData 
        self.update_text_view()

    def restore_discarded(self) -> None:
        operation = lambda elem: remove_html_wrapping(elem, unwrap='red_strikthrough')
        self.def_obj.dict_dict.recursivly_operate_on_last_lvl(operation)

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

        # TODO reuse construct_model method?
        self.dict_tree_view.deleteLater() # lets Qt knows it needs to delete this widget from the GUI
        
        headers = ["Type", "Content"]
        dict_content = self.def_obj.dict_dict.get_dict_content()
        self.model = TreeModel(headers=headers,
                               data=dict_content)
        
        del self.dict_tree_view
        
        self.update_text_view()
        
        self.dict_tree_view = DictEditorWidget(self.model, parent = self)
        self.dict_tree_view.move(700, 5)
        self.dict_tree_view.resize(690, 635)
        self.dict_tree_view.show()

    def refresh_dict(self, index) -> None:
        text, address = self.model.get_dict_address(index)
        self.def_obj.dict_dict.update_dict(text, address)

    def update_text_view(self) -> None:
        defined_html = self.def_obj.re_render_html()
        self.txt_cont.clear()
        self.txt_cont.insertHtml(defined_html)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)
        self.show()

    def expend_window_to_edit_dict(self) -> None:
        self.parent().expand_definition_window_animation()
        self.dict_tree_view.expandAll()
        self.dict_tree_view.show()

    def fill_def_window(self, def_obj) -> None:
        if def_obj.word_query.beispiel_de:
            self.beispiel.insert(def_obj.word_query.beispiel_de)

        if def_obj.word_query.beispiel_en:
            self.beispiel2.insert(def_obj.word_query.beispiel_en)

        self.txt_cont.setFont(NORMAL_FONT)
        self.txt_cont.insertHtml(def_obj.defined_html)
        self.txt_cont.moveCursor(QTextCursor.MoveOperation.Start)

    def highlight_selection(self) -> None:
        logger.info("highlight_selection")
        color_format = QTextCharFormat()
        color = QColor(3, 155, 224)
        color = QColor(int(220*1.15), int(212*1.15), int(39*1.15))
        color_format.setForeground(color)
        self.txt_cont.textCursor().mergeCharFormat(color_format)

    def send_to_anki(self) -> None:

        _, german_phrase, english_translation, _ = self.get_def_window_content()

        self.def_obj.ankify(german_phrase, english_translation)

    def save_definition(self) -> None:
        logger.info("save_definition")

        # Force hide is the only button function we need now
        # self.switch_highlight_button_action(new_action='highlight')

        custom_html_from_qt, beispiel_de, beispiel_en, tag = self.get_def_window_content()

        faulty_examples = quizify_and_save(dict_data_path=DICT_DATA_PATH,
                                            dict_dict=self.def_obj.dict_dict,
                                            dict_saving_word=self.def_obj.word_query.dict_saving_word,
                                            qt_html_content=custom_html_from_qt,
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
        # TODO (1) desactivate button if no selection
        logger.info("force_hide")
        # DONE (1) add manually hidden words to dict_file
        selected_text2hide = self.txt_cont.textCursor().selectedText() or self.beispiel.selectedText()

        self.def_obj.add_word_to_hidden_list(selected_text2hide)

        self.update_text_view()
        
        notification.notify(title='Word added to hidden words',
                            message=selected_text2hide,
                            timeout=5)

    def get_def_window_content(self) -> tuple[str, str, str, Literal['Studium', '']]:
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
    def focusOutEvent(self, e) -> None:
        start = self.selectionStart()
        length = self.selectionLength()
        super().focusOutEvent(e)
        self.setSelection(start, length)

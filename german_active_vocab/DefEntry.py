from dataclasses import dataclass, field
from pathlib import Path
import re
from datetime import datetime, timedelta
from argparse import Namespace
from collections import Counter
from PyQt5.QtCore import pyqtSignal, QWaitCondition

from bs4.builder import HTML
from GetDict.GenerateDict import standart_dict
from RenderHTML.RenderingHTML import render_html
from PushToAnki import Anki
from settings import ANKI_CONFIG, DICT_DATA_PATH

from utils import (sanitize_word, set_up_logger)

logger = set_up_logger(__name__)

# TODO (4) type-hinting in every function
# TODO (4) positional args vs keyword args
# DONE (0)* create dict_dict class that inherit form dict and have all dict operations
# TODO (0) rename dict_dict to word_dict

class WordDict(dict):    
    def get_dict_content(self):
        translate = 'translate' in self['requested']
        if translate:
            dict_content = self[f'content_{self["requested"].replace("translate_", "")}']
        elif self['requested'] == 'duden':
            dict_content = self['content_du']
        elif self['requested'] == 'pons':
            dict_content = self['content_pons']
        return dict_content

    def get_dict_slice_from_adress(self, address: list) -> dict | list:
        # validate address
        dict_slice = self.get_dict_content()
        for idx, entry in enumerate(address):
            # BUG when header is bookmarked then discarded
            try:
                if idx == len(address)-1:
                    if isinstance(dict_slice[entry], str):
                        return dict_slice
                    else:
                        return dict_slice[entry]
                else:
                    dict_slice = dict_slice[entry]
            except KeyError:
                raise KeyError(f"{entry} not in dict. Invalid Address: {address}")
            except TypeError: 
                raise TypeError('list indices must be integers or slices, not str')

    def update_dict(self, text, address: list) -> None:
        dict_slice = self.get_dict_slice_from_adress(address)
        if isinstance(dict_slice[address[-1]], str):
            dict_slice[address[-1]] = text
        else:
            raise RuntimeError('dict elemt is not str')

    def extract_definition_and_examples(self, address) -> tuple[str, str]:
        bookmarked_address = address[:(address.index('def_blocks')+1+1)]
        bookmarked_def_block = self.get_dict_slice_from_adress(bookmarked_address)
        bookmarked_def_block = bookmarked_def_block.copy() # we're not modifing dict_dict
        if isinstance(bookmarked_def_block, dict):
            if isinstance(address[-1], int):
                # case of only one example is bookmarked in a list of examples
                bookmarked_def_block[address[-2]] = bookmarked_def_block[address[-2]][address[-1]]

            definition_1 = bookmarked_def_block.get('definition', '')
            definition_2 = bookmarked_def_block.get('sense', '')
            if definition_1 and definition_2:
                logger.warning('Loss of Information! Both a definition and sense found, only one will be sent to Anki!!')
            definition = definition_1 or definition_2

            # DONE (2) change after standerising dicts
            example = bookmarked_def_block.get('example', '')
            return definition, example
        else:
            raise RuntimeError('Case not taken into account')

    def get_definitions_from_dict_dict(self, info='definition') -> list[str]:
        definitions_list: list[str] = []
        for big_section in self['content']:
            if "word_subclass" not in big_section:
                # it's a dict from duden
                continue
            for small_section in big_section["word_subclass"]:
                # lenna fama style(umg..), grammatical use, 

                for def_block in small_section["def_blocks"]:
                    # lenna fama definitions w examples

                    for h3_key,h3_value in def_block.items():
                        if h3_key == info:
                            if isinstance(h3_value, list):
                                definitions_list += h3_value
                            else:
                                definitions_list.append(h3_value)
                        else:
                            print(f'Hint: you can also get {h3_key} from the dict')

        return definitions_list

    def extract_synonymes_in_html_format(self) -> str:
        if 'synonymes' in self:
            synonymes = self['synonymes']
            syns_list_of_strings = [', '.join(syns) for syns in synonymes]
            synonymes = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in syns_list_of_strings]) + '</ul>'
        else:
            synonymes = ''
        return synonymes

    def append_new_examples_in_dict_dict(self, beispiel_de, beispiel_en):
        if beispiel_de:
            if 'custom_examples' in self:
                # update custom examples list in dict_dict
                self['custom_examples']['german'].append(beispiel_de)
                if not beispiel_en:
                    beispiel_en = '#'*len(beispiel_de)
                self['custom_examples']['english'].append(beispiel_en)

                _ = self._prevent_duplicating_examples()
            else:
                # create custom examples list in dict_dict
                self['custom_examples'] = {}
                self['custom_examples']['german'] = [beispiel_de]
                if not beispiel_en:
                    beispiel_en = '#'*len(beispiel_de)
                self['custom_examples']['english'] = [beispiel_en]
        
        return self

    def _prevent_duplicating_examples(self):
        '''get duplicated elements indexes in german examples.
        delete the elements having this index in both german and english examples
        (supposing they are parallels)'''
        # TODO (4) change custom example entery to be dict of translations (key=german_example, value = english_translation) to avoid this non-sense


        # only values that appears more than once
        german_examples = self['custom_examples']['german']
        duplicates_list = Counter(german_examples) - Counter(set(german_examples))

        res = {}
        for index, elem in enumerate(german_examples):
            if elem in duplicates_list:
                item = res.get(elem)
                if item:
                    item.append(index)
                else:
                    res[elem] = [index]

        # keep first occurence
        indexes_to_delete = []
        for _, values in res.items():
            indexes_to_delete += values[1:]

        indexes_to_delete.sort(reverse=True)

        for index in indexes_to_delete:
            del self['custom_examples']['german'][index]
            del self['custom_examples']['english'][index]
        
        return self
    
    def recursivly_operate_on_last_lvl(self, operation: callable):
        # most easily readable way to recursivly operate on a nested dict
        # https://stackoverflow.com/questions/55704719/python-replace-values-in-nested-dictionary
        # TODO (2) generalize this function to use for dict operations
        # DONE (0)* integrate this properly in word_dict
        
        def operate_on_dict(dict_object, operation: callable):
            new_dict = {}
            for key, value in dict_object.items():
                if isinstance(value, dict):
                    value = operate_on_dict(value, operation)
                elif isinstance(value, list):
                    value = operate_on_list(value, operation)
                elif isinstance(value, str):
                    value = operation(value)
                new_dict[key] = value
            return new_dict


        def operate_on_list(list_object, operation: callable):
            new_list = []
            for elem in list_object:
                if isinstance(elem, list):
                    elem = operate_on_list(elem, operation)
                elif isinstance(elem, dict):
                    elem = operate_on_dict(elem, operation)
                elif isinstance(elem, str):
                    elem = operation(elem)
                new_list.append(elem)
            return new_list
        
        word_dict =  self.copy()
        word_dict = operate_on_dict(word_dict, operation)
        self.clear()
        self.update(word_dict)


@dataclass
class WordQuery():
    input_word: str
    cl_args: Namespace
    search_word: str = ''
    cache_saving_word: str = ''
    dict_saving_word: str = ''
    ignore_cache: bool = False
    ignore_dict: bool = False
    translate_fr: bool = False
    translate_en: bool = False
    get_from_duden: bool = False

    beispiel_de: str = ''
    beispiel_en: str = ''

    def __post_init__(self) -> None:
        '''process input'''
        if ' new_dict' in self.input_word:
            self.ignore_dict = True
            self.input_word = self.input_word.replace(' new_dict', '')
        else:
            self.ignore_dict = False

        if ' new_cache' in self.input_word:
            self.ignore_cache = True
            self.input_word = self.input_word.replace(' new_cache', '')
        else:
            self.ignore_cache = False

        # search_word and translate-info
        if ' fr' in self.input_word:
            self.translate_fr = True
            self.search_word = self.input_word.replace(' fr', '')
        elif ' en' in self.input_word:
            self.translate_en = True
            self.search_word = self.input_word.replace(' en', '')
        elif ' du' in self.input_word:
            self.get_from_duden = True
            self.search_word = self.input_word.replace(' du', '')
        else:
            self.search_word = self.input_word
        self.search_word = self.search_word.lower().strip()
        self.dict_saving_word = sanitize_word(self.search_word)

        # saving word
        if self.translate_fr:
            self.cache_saving_word = self.search_word + '_fr'
        elif self.translate_en:
            self.cache_saving_word = self.search_word + '_en'
        elif self.get_from_duden:
            self.cache_saving_word = self.search_word + '_du'
        else:
            self.cache_saving_word = self.search_word
        self.cache_saving_word = sanitize_word(self.cache_saving_word)
        
        if self.cl_args and self.cl_args.ger:
            self.beispiel_de = self.cl_args.ger.replace("//QUOTE", "'").replace("//DOUBLEQUOTE", '"').strip()
                
        if self.cl_args and self.cl_args.eng :
            self.beispiel_en = self.cl_args.eng.replace("//QUOTE", "'").replace("//DOUBLEQUOTE", '"').strip()

@dataclass
class DefEntry():
    word_query: WordQuery
    message_box_content_carrier: pyqtSignal
    wait_for_usr: QWaitCondition
    beispiel_de: str = ''
    beispiel_en: str = ''

    dict_dict: dict = field(default_factory=dict)
    dict_dict_path: Path = ''

    defined_html: HTML = ''

    def __post_init__(self) -> None:

        self._log_word_in_wordlist_history()

        dict_dict = standart_dict(self.word_query,
                                self.message_box_content_carrier,
                                self.wait_for_usr)
        
        self.dict_dict = WordDict(dict_dict)
 
        self.defined_html = render_html(dict_dict=self.dict_dict)
    

    def re_render_html(self) -> str:
        self.defined_html = render_html(dict_dict=self.dict_dict)
        return self.defined_html


    def _log_word_in_wordlist_history(self) -> None:
        # TODO (1) update to with open
        now = datetime.now() - timedelta(hours=3)

        logger.info("log_word_in_wordlist_history")
        # TODO (2) Pylint: Using open without explicitly specifying an encoding
        f = open(DICT_DATA_PATH / 'Wordlist.txt', "a+")
        fileend = f.tell()
        f.seek(0)
        historyfile = f.read()
        f.seek(fileend)
        word_count = (historyfile.count('\n'+self.word_query.search_word+', ')
                    + historyfile.count('\n'+self.word_query.search_word+' ')
                    + historyfile.count('\n'+self.word_query.search_word+'\n'))
        f.write(f'\n{self.word_query.search_word}, {str(word_count)}, {now.strftime("%d.%m.%y")}')
        f.close()

    def wrap_words_to_learn_in_clozes(self, german_phrase: str) -> str:
        # TODO (0)* update
        logger.info("wrap_words_to_learn_in_clozes")
        
        hidden_words_list = self.dict_dict['hidden_words_list']
        # TODO (1) STRUCT before saving dict and maybe after adding hidden words manually
        hidden_words_list = list(set(hidden_words_list))

        front_with_cloze_wrapping = german_phrase

        for w in hidden_words_list:
            front_with_cloze_wrapping = self._wrap_in_clozes(front_with_cloze_wrapping, w)

        return front_with_cloze_wrapping

    def _wrap_in_clozes(self, text: str, word_to_wrap: str) -> str:
        ' wrap word_to_wrap between {{c1:: and }} '
        logger.info("wrap_in_clozes")

        # DONE (1) salla7ha zeda fel blassa lokhra
        word_pattern = f'((^)|(?<=[^a-zA-ZäöüßÄÖÜẞ])){word_to_wrap}((?=[^a-zA-ZäöüßÄÖÜẞ])|($))'
        try:
            quiz_text = re.sub(word_pattern, f'{{{{c1::{word_to_wrap}}}}}', text)
        except re.error:
            quiz_text = text
            logger.error(f'error by hiding {word_to_wrap}. '
                        'Word may contains reserved Regex charactar')

        return quiz_text

    def ankify(self, german_phrase: str, english_translation: str = '', definitions_html=None) -> None:
        front_with_cloze_wrapping = self.wrap_words_to_learn_in_clozes(german_phrase)

        if definitions_html is None:
            definitions_list = self.dict_dict.get_definitions_from_dict_dict(info='definition')
            definitions_html = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in definitions_list]) + '</ul>'

        synonymes_html = self.dict_dict.extract_synonymes_in_html_format()

        with Anki(base=ANKI_CONFIG['base'], profile=ANKI_CONFIG['profile']) as a:
            a.add_notes_single(cloze=front_with_cloze_wrapping,
                                hint1=synonymes_html,
                                hint2=english_translation,
                                hint3=definitions_html,
                                answer_extra=self.search_word,
                                tags='',
                                model=ANKI_CONFIG['model'],
                                deck=ANKI_CONFIG['deck'],
                                overwrite_notes=ANKI_CONFIG['overwrite'])

    def add_word_to_hidden_list(self, selected_text2hide) -> None:
        if 'forced_hidden_words' in self.dict_dict:
            self.dict_dict['forced_hidden_words'].append(selected_text2hide)
        else:
            self.dict_dict['forced_hidden_words']= [selected_text2hide]

        logger.debug(f'forced word2hide: {selected_text2hide}')
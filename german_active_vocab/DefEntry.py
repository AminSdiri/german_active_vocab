from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from datetime import datetime, timedelta

from bs4.builder import HTML
from GetDict.GenerateDict import extract_synonymes_in_html_format, get_definitions_from_dict_dict, standart_dict
from RenderHTML.RenderingHTML import render_html
from PushToAnki import Anki
from settings import ANKI_CONFIG, DICT_DATA_PATH

from utils import (sanitize_word, set_up_logger)

logger = set_up_logger(__name__)

# TODO (4) type-hinting in every function
# TODO (4) positional args vs keyword args


@dataclass
class DefEntry():
    # TODO(0) STRUCT hiya nafs'ha lclass mta3 search_input
    input_word: str
    search_word: str = ''
    saving_word: str = ''
    beispiel_de: str = ''
    beispiel_en: str = ''
    _ignore_cache: bool = False
    _ignore_dict: bool = False
    translate2fr: bool = False
    translate2en: bool = False
    get_from_duden: bool = False

    dict_dict: dict = field(default_factory=dict)
    dict_dict_path: Path = ''

    defined_html: HTML = ''
    # duden_synonyms: list = field(default_factory=list)
    # hidden_words_list: list = field(default_factory=list)

    def __post_init__(self):

        self._process_input()

        self._log_word_in_wordlist_history()

        (self.dict_dict,
         self.dict_dict_path) = standart_dict(self.saving_word,
                                self.translate2fr,
                                self.translate2en,
                                self.get_from_duden,
                                self.search_word,
                                self._ignore_cache,
                                self._ignore_dict)

        logger.info(f'Words to hide: {self.dict_dict["hidden_words_list"]}')
 
        self.defined_html = render_html(dict_dict=self.dict_dict)
    
    def get_dict_slice_from_adress(self, address: list):
        # validate address
        dict_slice = self.dict_dict['content']
        for idx, entry in enumerate(address):
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

    def extract_definition_and_examples(self, address):
        if self.dict_dict['source'] == 'pons':
            bookmarked_address = address[:(address.index('def_blocks')+1+1)]
        elif self.dict_dict['source'] == 'duden':
            # TODO change after standerising dicts
            bookmarked_address = address[:2]
        bookmarked_def_block = self.get_dict_slice_from_adress(bookmarked_address)
        bookmarked_def_block = bookmarked_def_block.copy() # we're not modifing dict_dict
        if isinstance(bookmarked_def_block, dict):
            if isinstance(address[-1], int):
                # case of only one example is bookmarked
                bookmarked_def_block[address[-2]] = bookmarked_def_block[address[-2]][address[-1]]
            if 'definition' in bookmarked_def_block:
                definition = bookmarked_def_block['definition']
            elif 'sense' in bookmarked_def_block:
                definition = bookmarked_def_block['sense']
            else:
                definition = ''
            # TODO change after standerising dicts
            example = bookmarked_def_block['example'] if 'example' in bookmarked_def_block else bookmarked_def_block['Beispiele']
            return definition, example
        else:
            raise RuntimeError('Case not taken into account')

    def update_dict(self, text, address: list):
        dict_slice = self.get_dict_slice_from_adress(address)
        if isinstance(dict_slice[address[-1]], str):
            dict_slice[address[-1]] = text
        else:
            raise RuntimeError('dict elemt is not str')

    def re_render_html(self):
        self.defined_html = render_html(dict_dict=self.dict_dict)
        return self.defined_html

    def _process_input(self):
        if ' new_dict' in self.input_word:
            self._ignore_dict = True
            self.input_word = self.input_word.replace(' new_dict', '')
        else:
            self._ignore_dict = False

        if ' new_cache' in self.input_word:
            self._ignore_cache = True
            self.input_word = self.input_word.replace(' new_cache', '')
        else:
            self._ignore_cache = False

        # search_word and translate-info
        if ' fr' in self.input_word:
            self.translate2fr = True
            self.search_word = self.input_word.replace(' fr', '')
        elif ' en' in self.input_word:
            self.translate2en = True
            self.search_word = self.input_word.replace(' en', '')
        elif ' du' in self.input_word:
            self.get_from_duden = True
            self.search_word = self.input_word.replace(' du', '')
        else:
            self.search_word = self.input_word
        self.search_word = self.search_word.lower()

        # saving word
        if self.translate2fr:
            self.saving_word = self.search_word + '_fr'
        elif self.translate2en:
            self.saving_word = self.search_word + '_en'
        elif self.get_from_duden:
            self.saving_word = self.search_word + '_du'
        else:
            self.saving_word = self.search_word
        self.saving_word = sanitize_word(self.saving_word)

        nbargin = len(sys.argv) - 1
        
        if nbargin <2:
            self.beispiel_de = ''
            self.beispiel_en = ''
        elif nbargin == 2:
            self.beispiel_de = sys.argv[2].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')
            self.beispiel_en = ''
        elif nbargin == 3 :
            self.beispiel_de = sys.argv[2].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')
            self.beispiel_en = sys.argv[3].replace(
                "//QUOTE", "'").replace("//DOUBLEQUOTE", '"')
        else :
            raise RuntimeError('Number of argument exceeds 3')

    def _log_word_in_wordlist_history(self):
        # TODO (1) update to with open
        now = datetime.now() - timedelta(hours=3)

        logger.info("log_word_in_wordlist_history")
        f = open(DICT_DATA_PATH / 'Wordlist.txt', "a+")
        fileend = f.tell()
        f.seek(0)
        historyfile = f.read()
        f.seek(fileend)
        word_count = (historyfile.count('\n'+self.input_word+', ')
                    + historyfile.count('\n'+self.input_word+' ')
                    + historyfile.count('\n'+self.input_word+'\n'))
        f.write(f'\n{self.input_word}, {str(word_count)}, {now.strftime("%d.%m.%y")}')
        f.close()

    def wrap_words_to_learn_in_clozes(self, german_phrase):
        logger.info("wrap_words_to_learn_in_clozes")
        
        hidden_words_list = self.dict_dict['hidden_words_list']
        # TODO STRUCT before saving dict and maybe after adding hidden words manually
        hidden_words_list = list(set(hidden_words_list))

        front_with_cloze_wrapping = german_phrase

        for w in hidden_words_list:
            front_with_cloze_wrapping = self._wrap_in_clozes(front_with_cloze_wrapping, w)

        return front_with_cloze_wrapping

    def _wrap_in_clozes(self, text, word_to_wrap):
        ' wrap word_to_wrap between {{c1:: and }} '
        logger.info("wrap_in_clozes")

        # TODO salla7ha zeda fel blassa lokhra
        word_pattern = f'((^)|(?<=[^a-zA-Z])){word_to_wrap}((?=[^a-zA-Z])|($))'
        try:
            quiz_text = re.sub(word_pattern, f'{{{{c1::{word_to_wrap}}}}}', text)
        except re.error:
            quiz_text = text
            logger.error(f'error by hiding {word_to_wrap}. '
                        'Word may contains reserved Regex charactar')

        return quiz_text

    def ankify(self, german_phrase, english_translation='', definitions_html=None):
        front_with_cloze_wrapping = self.wrap_words_to_learn_in_clozes(german_phrase)

        if definitions_html is None:
            definitions_list = get_definitions_from_dict_dict(self.dict_dict, info='definition')
            definitions_html = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in definitions_list]) + '</ul>'

        synonymes_html = extract_synonymes_in_html_format(self.dict_dict)

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

    def add_word_to_hidden_list(self, selected_text2hide):
        if selected_text2hide in self.dict_dict['hidden_words_list']:
            logger.warning('selected word is already in hidden words list, choose another one')
        self.dict_dict['hidden_words_list'].append(selected_text2hide)

        logger.debug(f'word2hide: {selected_text2hide}')
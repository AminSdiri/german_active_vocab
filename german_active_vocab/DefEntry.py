from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Dict   # , field
from bs4.builder import HTML
from GetDict.GenerateDict import extract_synonymes_in_html, get_definitions_from_dict_dict, standart_dict
from RenderingHTML import render_html
from PushToAnki import Anki
from SavingToQuiz import wrap_words_to_learn_in_clozes
from settings import anki_cfg

from utils import (log_word_in_wordlist_history, replace_umlauts, set_up_logger)

logger = set_up_logger(__name__)

# TODO (4) type-hinting in every function
# TODO (4) positional args vs keyword args


@dataclass
class DefEntry():
    # TODO(0) STRUCT hiya nafs'ha lclass mta3 search_input
    search_word: str
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

        log_word_in_wordlist_history(self.search_word)

        self.process_input(self.search_word)

        (self.dict_dict,
         self.dict_dict_path) = standart_dict(self.saving_word,
                                self.translate2fr,
                                self.translate2en,
                                self.get_from_duden,
                                self.search_word,
                                self._ignore_cache,
                                self._ignore_dict)

        translate = self.translate2fr or self.translate2en

        self.defined_html = render_html(dict_dict=self.dict_dict,
                                        word=self.search_word,
                                        translate=translate,
                                        get_from_duden=self.get_from_duden)

    def process_input(self, input_word):
        if ' new_dict' in input_word:
            self._ignore_dict = True
            input_word = input_word.replace(' new_dict', '')
        else:
            self._ignore_dict = False

        if ' new_cache' in input_word:
            self._ignore_cache = True
            input_word = input_word.replace(' new_cache', '')
        else:
            self._ignore_cache = False

        # search_word and translate-info
        if ' fr' in input_word:
            self.translate2fr = True
            self.search_word = input_word.replace(' fr', '')
        elif ' en' in input_word:
            self.translate2en = True
            self.search_word = input_word.replace(' en', '')
        elif ' du' in input_word:
            self.get_from_duden = True
            self.search_word = input_word.replace(' du', '')
        self.search_word = self.search_word.lower()

        # saving word
        if self.translate2fr:
            self.saving_word = self.search_word + '_fr'
        elif self.translate2en:
            self.saving_word = self.search_word + '_en'
        elif self.get_from_duden:
            self.saving_word = self.search_word + '_du'
        self.saving_word = replace_umlauts(self.saving_word)

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

    def ankify(self, german_phrase, english_translation):
        front_with_cloze_wrapping = wrap_words_to_learn_in_clozes(german_phrase, self.dict_dict, self.dict_dict_path)

        definitions_list = get_definitions_from_dict_dict(self.dict_dict, info='definition')
        definitions_html = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in definitions_list]) + '</ul>'

        synonymes_html = extract_synonymes_in_html(self.dict_dict)

        with Anki(base=anki_cfg['base'], profile=anki_cfg['profile']) as a:
            a.add_notes_single(cloze=front_with_cloze_wrapping,
                                hint1=synonymes_html,
                                hint2=english_translation,
                                hint3=definitions_html,
                                answer_extra=self.search_word,
                                tags='',
                                model=anki_cfg['model'],
                                deck=anki_cfg['deck'],
                                overwrite_notes=anki_cfg['overwrite'])

    def add_word_to_hidden_list(self, selected_text2hide):
        if selected_text2hide in self.dict_dict['hidden_words_list']:
            logger.warning('selected word is already in hidden words list, choose another one')
        self.dict_dict['hidden_words_list'].append(selected_text2hide)

        logger.debug(f'word2hide: {selected_text2hide}')
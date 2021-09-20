from dataclasses import dataclass, field
from bs4.builder import HTML
from pathlib import Path
from ParsingData.ParsingData import standart_dict
from RenderingHTML import get_seen_word_info, render_html

from utils import (log_word_in_wordlist_history, set_up_logger,
                   replace_umlauts)

dict_data_path = Path.home() / 'Dictionnary'
dict_src_path = Path.home() / 'Dokumente' / 'active_vocabulary' / 'src'

logger = set_up_logger(__name__)

# TODO (4) use a database instead of files to save
# standarized dicts, raw Json, raw htmls

# TODO (4) type-hinting in every function

# TODO (4) positional variables ywaliw bel esm fel les fct lkol


@dataclass
class DefEntry():
    word: str
    beispiel_de: str = ''
    beispiel_en: str = ''
    checkbox_en: bool = False
    checkbox_fr: bool = False
    translate2fr: bool = False
    translate2en: bool = False
    get_from_duden: bool = False
    defined_html: HTML = ''
    # duden_synonyms: list = field(default_factory=list)
    # words_to_hide: list = field(default_factory=list)

    def __post_init__(self):

        self.process_input()

        log_word_in_wordlist_history(self.word)

        translate = self.translate2fr or self.translate2en

        (self.dict_dict,
         self.dict_dict_path,
         _found_in_pons,
         _found_in_duden) = standart_dict(self.saving_word,
                                          translate,
                                          self.translate2fr,
                                          self.translate2en,
                                          self.get_from_duden,
                                          self.word,
                                          self._ignore_cache)

        word_info = get_seen_word_info(self.word)

        self.defined_html = render_html(self.dict_dict,
                                        word_info,
                                        translate,
                                        _found_in_pons,
                                        self.get_from_duden,
                                        _found_in_duden)

    def process_input(self):
        logger.info("process_input")

        if ' new' in self.word:
            self._ignore_cache = True
            self.word = self.word.replace(' new', '')
        else:
            self._ignore_cache = False

        if ' fr' in self.word or self.checkbox_fr:
            self.translate2fr = True
            self.word = self.word.replace(' fr', '')
            self.saving_word = replace_umlauts(self.word) + '_fr'
        elif ' en' in self.word or self.checkbox_en:
            self.translate2en = True
            self.word = self.word.replace(' en', '')
            self.saving_word = replace_umlauts(self.word) + '_en'
        elif ' du' in self.word:
            self.get_from_duden = True
            self.word = self.word.replace(' du', '')
            self.saving_word = replace_umlauts(self.word) + '_du'
        else:
            self.saving_word = replace_umlauts(self.word)

        self.word = self.word.lower()

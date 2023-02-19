from dataclasses import dataclass, field
import json
from pathlib import Path
from datetime import datetime, timedelta
from argparse import Namespace
from collections import Counter
from PyQt5.QtCore import pyqtSignal, QWaitCondition

from bs4.builder import HTML
from GetDict.GenerateDict import extract_custom_examples_from_html, standart_dict
from RenderHTML.RenderingHTML import render_html
from PushToAnki import Anki
from GetDict.HiddenWordsList import treat_words_to_hide
from GetDict.ParsingSoup import parse_anki_attribute, wrap_text_in_tag_with_attr
from settings import ANKI_CONFIG, DICT_DATA_PATH
from itertools import zip_longest

from utils import (replace_umlauts_1, sanitize_word, set_up_logger, write_str_to_file)

logger = set_up_logger(__name__)

# TODO (4) type-hinting in every function
# TODO (4) positional args vs keyword args
# DONE (0)* create word_dict class that inherit form dict and have all dict operations
# DONE (0) rename word_dict to word_dict
# TODO (2) add ability to delete and modify custom examples from DictView
# DONE (0) gray out force hide button if no word is selected in TextView
# DONE (0) replace (umgangssprachlich) in duden_syn with umg with pons styling or group them like duden?


class WordDict(dict):
    def __init__(self, word_dict, saving_word):
        super().__init__(word_dict) 
        self.word_dict_path = DICT_DATA_PATH / 'word_dicts' / f'{saving_word}_dict.json'

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

    def get_block_from_address(self, address) -> tuple[str, str]:
        bookmarked_address = address[:(address.index('def_blocks')+1+1)]
        bookmarked_def_block = self.get_dict_slice_from_adress(bookmarked_address)
        bookmarked_def_block = bookmarked_def_block.copy() # we're not modifing word_dict

        if not isinstance(bookmarked_def_block, dict):
            raise RuntimeError('Case not taken into account')

        if isinstance(address[-1], int):
            # case of only one example is bookmarked in a list of examples
            bookmarked_def_block[address[-2]] = bookmarked_def_block[address[-2]][address[-1]]

        # get other propreties in dict higher levels
        other_properties = {}
        dict_slice = self.get_dict_content()
        for entry in bookmarked_address:
            dict_slice = dict_slice[entry]
            if entry == 'def_blocks':
                break
            if not isinstance(dict_slice, dict):
                continue
            other_properties.update({key: value for key, value in dict_slice.items() 
                                    if isinstance(value, str|list|int) and key not in ('word_subclass', 'def_blocks')})
        if 'forced_hidden_words' in self:
            other_properties['hidden_words_list'] = list(set(other_properties['hidden_words_list'] + self['forced_hidden_words']))
        
        bookmarked_def_block.update(other_properties)
        return bookmarked_def_block

    def get_definitions_from_word_dict(self, info='definition') -> list[str]:
        definitions_list: list[str] = []
        for big_section in self.get_dict_content():
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

    def append_new_examples_in_word_dict(self, beispiel_de, beispiel_en):
        _ = self._prevent_duplicating_examples()
        if beispiel_de:
            if 'custom_examples' in self:
                # update custom examples list in word_dict
                if beispiel_de in self['custom_examples']['german']:
                    # ignore if example already in word_dict
                    return self
                self['custom_examples']['german'].append(beispiel_de)
                if not beispiel_en:
                    beispiel_en = '#'*len(beispiel_de)
                self['custom_examples']['english'].append(beispiel_en)

            else:
                # create custom examples list in word_dict
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

    def get_all_hidden_words(self) -> tuple[list, dict[str, str]]:
        logger.info("extract all hidden_words and secondary_words")

        word_dict_content = self.get_dict_content()
        all_word_variants = []
        all_secondary_words = {}

        for rom_level_dict in word_dict_content:
            all_word_variants += rom_level_dict['hidden_words_list']
            all_secondary_words.update(rom_level_dict['secondary_words_to_hide'])

        # add forced_hidden_words and remove duplicates
        if 'forced_hidden_words' in self:
            all_word_variants = list(set(all_word_variants + self['forced_hidden_words']))

        return all_word_variants, all_secondary_words

    def save_word_dict(self):
        write_str_to_file(self.word_dict_path, json.dumps(self), overwrite=True)


@dataclass
class WordQuery():
    input_word: str
    cl_args: Namespace
    search_word: str = ''
    saving_word: str = ''
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
        self.saving_word = sanitize_word(self.search_word)

        # # saving word
        # if self.translate_fr:
        #     self.cache_saving_word = self.search_word + '_fr'
        # elif self.translate_en:
        #     self.cache_saving_word = self.search_word + '_en'
        # elif self.get_from_duden:
        #     self.cache_saving_word = self.search_word + '_du'
        # else:
        #     self.cache_saving_word = self.search_word
        # self.cache_saving_word = sanitize_word(self.cache_saving_word)
        
        if self.cl_args and self.cl_args.ger:
            self.beispiel_de = self.cl_args.ger.replace("//QUOTE", "'").replace("//DOUBLEQUOTE", '"').strip()
                
        if self.cl_args and self.cl_args.eng :
            self.beispiel_en = self.cl_args.eng.replace("//QUOTE", "'").replace("//DOUBLEQUOTE", '"').strip()

@dataclass
class DefEntry():
    word_query: WordQuery
    message_box_content_carrier: pyqtSignal
    wait_for_usr: QWaitCondition

    word_dict: WordDict = field(default_factory=dict)
    word_dict_path: Path = ''

    defined_html: HTML = ''

    def __post_init__(self) -> None:

        self._log_word_in_wordlist_history()

        word_dict = standart_dict(self.word_query,
                                self.message_box_content_carrier,
                                self.wait_for_usr)
        
        self.word_dict = WordDict(word_dict, saving_word=self.word_query.saving_word)

        # temporary, move custom examples from html to json
        # TODO (0)* loop over all html files and get rid of all html extraction related code. htnl will be only rendered
        german_examples, english_examples = extract_custom_examples_from_html(search_word=self.word_dict['search_word'],
                                                                                    saving_word=self.word_query.saving_word,
                                                                                    old_saving_word=replace_umlauts_1(self.word_query.search_word))
        for german_example, english_example in zip_longest(german_examples, english_examples):
            self.word_dict = self.word_dict.append_new_examples_in_word_dict(german_example, english_example)
        
        # otherwise we'll get an error in rendering, move to better place after getting rid of html dependency
        if 'custom_examples' not in self.word_dict:
            self.word_dict['custom_examples'] = {}
            self.word_dict['custom_examples']['german'] = []
            self.word_dict['custom_examples']['english'] = []
 
        self.defined_html = render_html(word_dict=self.word_dict)
    

    def re_render_html(self) -> str:
        self.defined_html = render_html(word_dict=self.word_dict)
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

    def ankify_custom_examples(self) -> None:
        '''if user wants to capture the custom examples than we should only provide the german phrase
        and optionally it's english translation, all the definitions and synonymes will be automaticly extracted'''

        # get definitions
        definitions_list = self.word_dict.get_definitions_from_word_dict(info='definition')
        definitions_html = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in definitions_list]) + '</ul>'

        synonymes_html = self.word_dict.extract_synonymes_in_html_format()
        
        words_to_hide, secondary_words = self.word_dict.get_all_hidden_words()

        for idx, german_phrase in enumerate(self.word_dict['custom_examples']['german']):
            inner_text, note_id, already_in_anki = parse_anki_attribute(german_phrase)
            front_with_cloze_wrapping = treat_words_to_hide(inner_text, words_to_hide, secondary_words, treatement='cloze')

            try:
                english_translation = self.word_dict['custom_examples']['english'][idx]
            except IndexError:
                english_translation = '#'*len(german_phrase)
                self.word_dict['custom_examples']['english'].append(english_translation)
                self.word_dict.save_word_dict()

            note_content = {'cloze': front_with_cloze_wrapping,
                            'hint1': synonymes_html,
                            'hint2': english_translation,
                            'hint3': definitions_html,
                            'answer_extra': self.word_dict['search_word']}

            with Anki(base=ANKI_CONFIG['base'], profile=ANKI_CONFIG['profile']) as a:
                if not already_in_anki:
                    note_id = a.add_anki_note(note_content,
                                        tags='',
                                        model=ANKI_CONFIG['model'],
                                        deck=ANKI_CONFIG['deck'],
                                        overwrite_notes=ANKI_CONFIG['overwrite'])
                else:
                    a.update_anki_note(note_content,
                                tags='',
                                model=ANKI_CONFIG['model'],
                                note_id=note_id)
            
            # add node_id to example data attribute to track it and update its anki note when needed
            if not already_in_anki and note_id:
                german_phrase = wrap_text_in_tag_with_attr(text=german_phrase, tag_name='span', attr_name='data-anki-note-id', attr_value=note_id)
                self.word_dict['custom_examples']['german'][idx] = german_phrase
                self.word_dict.save_word_dict()

    def ankify_def_block_example(self, def_block) -> None:
        '''
        If the user capture an example from the word_dict, only the corresponding definition will be extracted, 
        and the words_to_hide for it's rom level'''

        # get definitions
        definition_1 = def_block.get('definition', '')
        definition_2 = def_block.get('sense', '')
        if definition_1 and definition_2:
            logger.error('Loss of Information! Both a definition and sense found, only one will be sent to Anki!!')
        definitions_html = definition_1 or definition_2

        # transform german_phrase
        german_phrase = def_block.get('example', '')
        inner_text, note_id, already_in_anki = parse_anki_attribute(german_phrase)
        words_to_hide = def_block.get('hidden_words_list', {})
        secondary_words = def_block.get('secondary_words', {})
        front_with_cloze_wrapping = treat_words_to_hide(inner_text, words_to_hide, secondary_words, treatement='cloze')

        synonymes_html = self.word_dict.extract_synonymes_in_html_format()

        english_translation = ''

        note_content = {'cloze': front_with_cloze_wrapping,
                        'hint1': synonymes_html,
                        'hint2': english_translation,
                        'hint3': definitions_html,
                        'answer_extra': self.word_dict['search_word']}

        with Anki(base=ANKI_CONFIG['base'], profile=ANKI_CONFIG['profile']) as a:
            if not already_in_anki:
                note_id = a.add_anki_note(note_content,
                                    tags='',
                                    model=ANKI_CONFIG['model'],
                                    deck=ANKI_CONFIG['deck'],
                                    overwrite_notes=ANKI_CONFIG['overwrite'])
            else:
                a.update_anki_note(note_content,
                            tags='',
                            model=ANKI_CONFIG['model'],
                            note_id=note_id)
                
        return note_id, already_in_anki


    def add_word_to_hidden_list(self, selected_text2hide) -> None:
        if 'forced_hidden_words' in self.word_dict:
            self.word_dict['forced_hidden_words'].append(selected_text2hide)
        else:
            self.word_dict['forced_hidden_words']= [selected_text2hide]

        logger.debug(f'forced word2hide: {selected_text2hide}')
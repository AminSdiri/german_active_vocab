import json
from pathlib import Path
from bs4 import BeautifulSoup as bs
import ast
from collections import Counter
import pandas as pd
from PyQt5.QtCore import QMutex
from typing import Any
from PyQt5.QtCore import pyqtSignal, QWaitCondition

from GetDict.GetData import get_word_from_source
from GetDict.ParsingJson import construct_dict_content_from_json
from GetDict.ParsingSoup import (construct_dict_content_from_soup, create_synonyms_list,
                                     get_word_freq_from_soup)
from GetDict.HiddenWordsList import generate_hidden_words_list
from utils import fix_html_with_custom_example, remove_html_wrapping
from utils import (get_cache,
                   read_str_from_file,
                   set_up_logger, write_str_to_file)
from settings import DICT_DATA_PATH

logger = set_up_logger(__name__)

# You can set the python.analysis.diagnosticMode to workspace rather than its default value of openFilesOnly to check for error without opening files
# TODO (2) STRUCT convert to class? (OOP vs Functional)

def standart_dict(saving_word: str, translate2fr: bool, translate2en: bool,
                  get_from_duden: bool, search_word: str, ignore_cache: bool, ignore_dict: bool,
                  message_box_content_carrier: pyqtSignal, wait_for_usr: QWaitCondition):
    
    # BUG (2) too many args
    dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{saving_word}_standerised.json'

    if not (ignore_cache or ignore_dict):
        dict_cache_found, _error_reading_json, dict_dict = _read_dict_from_file(dict_dict_path)
        if dict_cache_found and not _error_reading_json:
            # temporary
            if 'requested' not in dict_dict:
                dict_dict['requested'] = dict_dict['source']
            if 'search_word' not in dict_dict:
                dict_dict['search_word'] = search_word
            # end temporary
            return dict_dict, dict_dict_path 

    (found_in_pons_duden,
    _pons_json,
    _duden_soup,
    _duden_syn_soup) = get_word_from_source(translate2fr,
                                            translate2en,
                                            get_from_duden,
                                            search_word,
                                            saving_word,
                                            ignore_cache)

    # TODO (0)* STRUCT use the same dict structures for both pons and duden
    
    translate = translate2fr or translate2en

    if get_from_duden:
        dict_dict = _standart_duden_dict(found_in_pons_duden,
                                        _duden_soup,
                                        _duden_syn_soup,
                                        search_word)
        dict_dict['requested'] = 'duden'

    elif found_in_pons_duden[0]:
        dict_dict = _standart_pons_dict(_pons_json,
                                        _duden_syn_soup,
                                        search_word,
                                        translate,
                                        _duden_soup,
                                        message_box_content_carrier,
                                        wait_for_usr)
        dict_dict['requested'] = 'pons'

    elif not translate:
        dict_dict = _standart_duden_dict(found_in_pons_duden,
                                        _duden_soup,
                                        _duden_syn_soup,
                                        search_word)
        if dict_dict:
            dict_dict['requested'] = 'pons'
        else:
            # word is not found anywhere
            dict_dict['requested'] = 'pons'
            dict_dict['source'] = 'NotFound'
            dict_dict['content'] = []
            dict_dict['hidden_words_list'] = []

    # FIXED (0) dict_dict is list for translate
    dict_dict['search_word'] = search_word

    return dict_dict, dict_dict_path

def _read_dict_from_file(dict_dict_path: Path):
    logger.debug('Looking for dict cache')
    dict_dict: dict
    dict_cache_found: bool
    dict_string, pons_dict_cache_found = get_cache(dict_dict_path)
    if pons_dict_cache_found:
        dict_cache_found = True
        try:
            dict_dict = ast.literal_eval(dict_string)
            error_reading_json = False
        except SyntaxError:
            logger.warning('dict file is not readable!')
            dict_dict = {}
            error_reading_json = True
    else:
        dict_cache_found = False
        error_reading_json = None
        dict_dict = {}
    
    return dict_cache_found, error_reading_json, dict_dict

def _standart_pons_dict(_pons_json, _duden_syn_soup, word, translate,
                       _duden_soup, message_box_content_carrier: pyqtSignal,
                       wait_for_usr: QWaitCondition) -> dict[str, Any]:
    '''
    standarize json file and save it before rendering to allow filtering of words, blocks, properties
    in power mode (new mode)

    parseable properties are
    - wordclass: Verb, noun, adj ..
    - prop for verbes (z.B: warte.. auf)
    - gen for nouns (der, die, das)
    - syns
    - defs
    - beispiele
    - Verwendung (Umg, tech etc)
    '''

    logger.info("standerize_dict")

    if not translate and len(_pons_json) == 1:
        logger.info(f'language: {_pons_json[0]["lang"]}')

        dict_dict = {'content': construct_dict_content_from_json(_pons_json[0]["hits"], translate, word),
                     'synonymes': _add_synonymes_from_duden(_duden_syn_soup),
                     'custom_examples': {
                         'german': [],
                         'english': []},
                     'word_freq' : get_word_freq_from_soup(_duden_soup),
                     'hidden_words_list': [],
                     'source': 'pons'
                     }

        (dict_dict['custom_examples']['german'], 
         dict_dict['custom_examples']['english']) = _extract_custom_examples_from_html(word)
        dict_dict['hidden_words_list'], dict_dict['secondary_words_to_hide']=generate_hidden_words_list(dict_dict['content'])

    elif translate and len(_pons_json) == 1:
        logger.info(f'language: {_pons_json[0]["lang"]}')

        dict_dict = {'lang': _pons_json[0]["lang"],
                      'content': construct_dict_content_from_json(_pons_json[0]["hits"], translate, word)}
    elif translate and len(_pons_json) == 2:
        # resolve language translation confusion by asking the user

        message_box_dict = prepare_message_box_content(_pons_json, word)
        # open message box from the main thread
        message_box_content_carrier.emit(message_box_dict)

        # recieve response
        mutex = QMutex()
        mutex.lock()
        wait_for_usr.wait(mutex)
        mutex.unlock()
        print('resume code')
        global CLICKED_BUTTON

        if CLICKED_BUTTON[0]:
            json_data = _pons_json[0]["hits"]
            dict_dict_content = construct_dict_content_from_json(json_data, translate, word)
            dict_dict = {
                'lang': _pons_json[0]['lang'],
                'content': dict_dict_content
                }
        elif CLICKED_BUTTON[1]:
            json_data = _pons_json[1]["hits"]
            dict_dict_content = construct_dict_content_from_json(json_data, translate, word)
            dict_dict = {
                'lang': _pons_json[1]['lang'],
                'content': dict_dict_content
                }
        else:
            raise RuntimeError('how can this happen')

        del CLICKED_BUTTON

    else:
        raise RuntimeError(
            'json API response is expected to be of length 1 '
            'or only for translations 2')

    return dict_dict

def prepare_message_box_content(_pons_json, word) -> dict[str, str]:
    _languages = [_pons_json[0]["lang"], _pons_json[1]["lang"]]
    mother_language = _languages[0] if _languages[0] != 'de' else _pons_json[1]["lang"]
    if _languages[0]=='de':
        mother_language = 'an english' if _languages[1]=='en' else 'a french'
        zero_to_one_str = 'De -> En' if _languages[1]=='en' else 'De -> Fr'
        one_to_zero_str = 'En -> De' if _languages[1]=='en' else 'Fr -> De'
    else:
        mother_language = 'an english' if _languages[0]=='en' else 'a french'
        zero_to_one_str = 'De -> En' if _languages[0]=='en' else 'De -> Fr'
        one_to_zero_str = 'En -> De' if _languages[0]=='en' else 'Fr -> De'

    message_box_dict = {'text': "Confused.. I need you help??",
                            'title': "Choice of translation",
                            'informative_text': f'"{word}" is both a german and {mother_language} word. Please choose the translation direction',
                            'yes_button_text': zero_to_one_str,
                            'no_button_text': one_to_zero_str}
                        
    return message_box_dict

def _standart_duden_dict(found_in_pons_duden, _duden_soup, _duden_syn_soup, word) -> dict[str, Any]:

    if found_in_pons_duden[1]:

        duden_dict = {'custom_examples': {'german': [],
                                            'english': []},
                        'content': construct_dict_content_from_soup(_duden_soup),
                        'synonymes': _add_synonymes_from_duden(_duden_syn_soup),
                        'hidden_words_list': [],
                        'secondary_words_to_hide': {},
                        'source': 'duden',
                        'word_freq' : get_word_freq_from_soup(_duden_soup)}

        (duden_dict['custom_examples']['german'], 
         duden_dict['custom_examples']['english']) = _extract_custom_examples_from_html(word)

        duden_dict['hidden_words_list'], duden_dict['secondary_words_to_hide'] = generate_hidden_words_list(duden_dict)

    else:
        duden_dict = {}

    return duden_dict
    
def _extract_custom_examples_from_html(word: str) -> tuple[list[str], list[str]]:
    '''
    Temporary function:
    save custom examples list from the old version html in dict_dict
    '''
    # TODO (2) run in loop to update dicts and then delete
    old_german_examples: list[str] = []
    old_englisch_examples: list[str] = []
    wordlist_df = pd.read_csv(DICT_DATA_PATH / 'wordlist.csv')
    wordlist_df.set_index('Word', inplace=True)
    word_is_already_saved = word in wordlist_df.index
    if not word_is_already_saved:
        return old_german_examples, old_englisch_examples

    old_html_path = DICT_DATA_PATH / 'html' / f'{word}.html'
    old_html_str = read_str_from_file(old_html_path)
    old_html_str = fix_html_with_custom_example(old_html_str)
    old_html_soup = bs(old_html_str, 'lxml')

    # lkolou deja fi class=custom_examples
    ce_begin = old_html_soup.find("b", string="Eigenes Beispiel:")
    if ce_begin:
        custom_example_de_soup = ce_begin.findNext('i')
        while custom_example_de_soup:
            old_german_examples.append(custom_example_de_soup.string.replace('&nbsp;', '').replace('\xa0', ''))
            custom_example_de_soup = custom_example_de_soup.findNext('i')
    else:
        return old_german_examples, old_englisch_examples

    ce_englisch_begin = ce_begin.findNext('b', string="Auf Englisch:")
    if ce_englisch_begin:
        custom_example_en_soup = ce_englisch_begin.findNext('i')
        while custom_example_en_soup:
            old_englisch_examples.append(custom_example_en_soup.string.replace('&nbsp;', '').replace('\xa0', ''))
            custom_example_en_soup = custom_example_en_soup.findNext('i')
    
    old_german_examples = old_german_examples[:-len(old_englisch_examples)]

    # DONE (1) BUG should return list
    assert isinstance(old_german_examples, list)

    return old_german_examples, old_englisch_examples

def _add_synonymes_from_duden(_duden_syn_soup) -> list[list[str]]:
    if not _duden_syn_soup:
        return []

    try:
        synonyms_list = create_synonyms_list(_duden_syn_soup)
        return synonyms_list
    except TypeError:
        # logger.warning('Type Error in create_synonyms_list >> Check it!')
        raise TypeError('Type Error in create_synonyms_list >> Check it!')

def get_definitions_from_dict_dict(dict_dict, info='definition') -> list[str]:
    definitions_list: list[str] = []
    for big_section in dict_dict['content']:
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
             
def extract_synonymes_in_html_format(dict_dict) -> str:
    if 'synonymes' in dict_dict:
        synonymes = dict_dict['synonymes']
        syns_list_of_strings = [', '.join(syns) for syns in synonymes]
        synonymes = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in syns_list_of_strings]) + '</ul>'
    else:
        synonymes = ''
    return synonymes


def _prevent_duplicating_examples(dict_dict):
    '''get duplicated elements indexes in german examples.
    delete the elements having this index in both german and english examples
    (supposing they are parallels)'''
    # TODO (4) change custom example entery to be dict of translations (key=german_example, value = english_translation) to avoid this non-sense


    # only values that appears more than once
    german_examples = dict_dict['custom_examples']['german']
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
        del dict_dict['custom_examples']['german'][index]
        del dict_dict['custom_examples']['english'][index]

    return dict_dict

def append_new_examples_in_dict_dict(beispiel_de, beispiel_en, dict_dict):
    if beispiel_de:
        # update custom examples list in dict_dict
        dict_dict['custom_examples']['german'].append(beispiel_de)
        if not beispiel_en:
            beispiel_en = '#'*len(beispiel_de)
        dict_dict['custom_examples']['english'].append(beispiel_en)

        dict_dict = _prevent_duplicating_examples(dict_dict)
    
    return dict_dict


def create_dict_for_manually_added_words() -> dict[str, Any]:
    # dict is not built -> word not found anywhere but html "written" manually
    # BUG (2) this allows only one example to persist for manually written defs 
    # -> TODO if manually added dict already exist append new examples to that dict else create new one like here
    dict_dict = {}
    dict_dict['source'] = 'manual'
    dict_dict['custom_examples'] = {}
    dict_dict['custom_examples']['german'] = []
    dict_dict['custom_examples']['english'] = []
    dict_dict['hidden_words_list'] = []

    return dict_dict


def update_hidden_words_in_dict(selected_text2hide, saving_word):
    dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{saving_word}_standerised.json'
    dict_cache_found, _, dict_dict = _read_dict_from_file(dict_dict_path)
    if dict_cache_found:
        if selected_text2hide in dict_dict['hidden_words_list']:
            raise RuntimeError('selected word is already in hidden words list')
        dict_dict['hidden_words_list'].append(selected_text2hide)
        write_str_to_file(dict_dict_path, json.dumps(dict_dict), overwrite=True)
    else:
        raise RuntimeError('dict for quized word not found')




# most easily readable way to recursivly operate on a nested dict
# https://stackoverflow.com/questions/55704719/python-replace-values-in-nested-dictionary
# TODO (2) generalize this function to use for dict operations
def dict_replace_value(dict_object):
    new_dict = {}
    for key, value in dict_object.items():
        if isinstance(value, dict):
            value = dict_replace_value(value)
        elif isinstance(value, list):
            value = list_replace_value(value)
        elif isinstance(value, str):
            if value.startswith('<s'):
                value = remove_html_wrapping(value, unwrap='red_strikthrough')
        new_dict[key] = value
    return new_dict


def list_replace_value(list_object):
    new_list = []
    for elem in list_object:
        if isinstance(elem, list):
            elem = list_replace_value(elem)
        elif isinstance(elem, dict):
            elem = dict_replace_value(elem)
        elif isinstance(elem, str):
            if elem.startswith('<s'):
                elem = remove_html_wrapping(elem, unwrap='red_strikthrough')
        new_list.append(elem)
    return new_list

def get_value_from_dict_if_exists(keys, dictionnary) -> str:
    for key in keys:
        if key in dictionnary:
            return dictionnary[key]
    return ''

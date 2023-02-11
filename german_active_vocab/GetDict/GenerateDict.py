import json
import os
from bs4 import BeautifulSoup as bs
import pandas as pd
from PyQt5.QtCore import QMutex
from typing import Any
from PyQt5.QtCore import pyqtSignal, QWaitCondition

from GetDict.GetData import get_duden_soup, get_json_from_pons_api
from GetDict.ParsingJson import construct_dict_content_from_json
from GetDict.ParsingSoup import (construct_dict_content_from_soup, create_synonyms_list,
                                     get_word_freq_from_soup)
from utils import fix_html_with_custom_example, remove_from_str, remove_html_wrapping
from utils import (get_cache,
                   read_str_from_file,
                   set_up_logger, write_str_to_file)
from settings import DICT_DATA_PATH

logger = set_up_logger(__name__)

# You can set the python.analysis.diagnosticMode to workspace rather than its default value of openFilesOnly to check for error without opening files
# TODO (2) STRUCT convert to class? (OOP vs Functional)
# DONE (0)* STRUCT use the same dict structures for both pons and duden

def standart_dict(word_query,
                  message_box_content_carrier: pyqtSignal,
                  wait_for_usr: QWaitCondition):
    '''
    dict keys: 
      - search_word
      - custom_examples
      - requested
      - content_pons
      - content_du
      - content_fr/fr-de/de-fr
      - content_en/en-de/de-en
      - word_freq
      - synonymes
      - forced_hidden_words
      - forced_hidden_secondary_words
    
    standarize json file and save it before rendering to allow
    filtering of words, blocks, properties in power mode (new mode)

    parseable properties are
    - wordclass: Verb, noun, adj ..
    - prop for verbes (z.B: warte.. auf)
    - gen for nouns (der, die, das)
    - syns
    - defs
    - beispiele
    - Verwendung (Umg, tech etc)
    '''

    # BUG (2) too many args

    # DONE if dict dont'exist at all, the creation of the dict should not include any key that will be tested on
    # because I'll assume that if the key exist and it's value is empty that it couldn't be fetched 
    
    # looking up cache is necessary if I want to keep a persistant custom example list and the user customizations
    # ignore_dict is risky
    # TODO check if the dict gets saved after every update (maybe should be a class that calls a save method after every update)
    dict_exist = False
    # if not ignore_dict:
    dict_cache_found, _error_reading_json, dict_dict = _read_dict_from_file(word_query.dict_saving_word)
    # temporary (look for an old dict file)
    if not dict_cache_found:
        dict_cache_found, _error_reading_json, dict_dict = _read_dict_from_file(word_query.dict_saving_word, old=True)
    dict_exist = dict_cache_found and not _error_reading_json
    if dict_exist and 'search_word' not in dict_dict: # temporary
        dict_dict['search_word'] = word_query.search_word
    

    if not dict_exist:
        dict_dict = _create_empty_dict(word_query.search_word)
    
    translate = word_query.translate_fr or word_query.translate_en

    # DONE (1) STRUCT use one unified decision tree for all functions
    if translate:
        # check if dict already cached and have the translation data,
        # otherwise update it if it lacks the translation data
        # or create it if doesnt'exist and then update it.

        lang = 'fr' * word_query.translate_fr + 'en' * word_query.translate_en
        
        if f'content_{lang}' in dict_dict:
            _update_files(dict_dict, word_query.dict_saving_word)
            dict_dict['requested'] = f'translate_{lang}'
            return dict_dict
        if f'content_{lang}-de' in dict_dict:
            requested = _prompt_user_for_lang(search_word=dict_dict['search_word'],
                                            message_box_content_carrier=message_box_content_carrier,
                                            wait_for_usr=wait_for_usr,
                                            lang_0='de',
                                            lang_1=lang)
            dict_dict['requested'] = f'translate_{requested}' 
            _update_files(dict_dict, word_query.dict_saving_word)
            return dict_dict
        
        dict_dict = _add_dict_content(dict_dict=dict_dict,
                                        cache_saving_word=word_query.cache_saving_word,
                                        ignore_cache=word_query.ignore_cache,
                                        message_box_content_carrier=message_box_content_carrier,
                                        wait_for_usr=wait_for_usr,
                                        source=f'translate_{lang}')
        _update_files(dict_dict, word_query.dict_saving_word)
        return dict_dict

    if word_query.get_from_duden:
        if 'content_du' in dict_dict:
            _update_files(dict_dict, word_query.dict_saving_word)
            dict_dict['requested'] = 'duden'
            return dict_dict

        dict_dict = _add_dict_content(dict_dict=dict_dict,
                                    cache_saving_word=word_query.cache_saving_word,
                                    ignore_cache=word_query.ignore_cache,
                                    message_box_content_carrier=message_box_content_carrier,
                                    wait_for_usr=wait_for_usr,
                                    source='duden')
        _update_files(dict_dict, word_query.dict_saving_word)
        return dict_dict
    
    if 'content_pons' in dict_dict:
        _update_files(dict_dict, word_query.dict_saving_word)
        dict_dict['requested'] = 'pons'
        return dict_dict

    dict_dict = _add_dict_content(dict_dict=dict_dict,
                                cache_saving_word=word_query.cache_saving_word,
                                ignore_cache=word_query.ignore_cache,
                                message_box_content_carrier=message_box_content_carrier,
                                wait_for_usr=wait_for_usr,
                                source='pons')
    _update_files(dict_dict, word_query.dict_saving_word)
    return dict_dict

def _create_empty_dict(search_word):
    dict_dict = {'search_word': search_word}
    return dict_dict

def _add_dict_content(dict_dict, cache_saving_word, ignore_cache, message_box_content_carrier, wait_for_usr, source: str):
    if 'translate' in source:
        _pons_json = get_json_from_pons_api(search_word=dict_dict['search_word'],
                                            filename=cache_saving_word,
                                            translate_en='en' in source,
                                            translate_fr='fr' in source,
                                            ignore_cache=ignore_cache)

        if _pons_json:
            if len(_pons_json) == 1:
                lang = _pons_json[0]["lang"]
                dict_dict.update({
                    'requested' : source,
                    f'content_{lang}': construct_dict_content_from_json(_pons_json[0]["hits"],
                                                                        translate=True,
                                                                        search_word=dict_dict['search_word'])})
                return dict_dict
            elif len(_pons_json) == 2:
                lang_0 = _pons_json[0]["lang"]
                lang_1 = _pons_json[1]["lang"]
                requested = _prompt_user_for_lang(search_word=dict_dict['search_word'],
                                                 message_box_content_carrier=message_box_content_carrier,
                                                 wait_for_usr=wait_for_usr,
                                                 lang_0=lang_0,
                                                 lang_1=lang_1)
                dict_dict.update({
                    'requested': f'translate_{requested}' ,
                    f'content_{lang_0}-{lang_1}':  construct_dict_content_from_json(_pons_json[0]["hits"],
                                                                                    translate=True,
                                                                                    search_word=dict_dict['search_word']),
                    f'content_{lang_1}-{lang_0}':  construct_dict_content_from_json(_pons_json[1]["hits"],
                                                                                    translate=True,
                                                                                    search_word=dict_dict['search_word'])
                        })
                
                return dict_dict
            else:
                raise RuntimeError('json API response is expected to be of length 1 or only for translations 2')  
        else:
            lang = source.replace('translate_')
            dict_dict.update({f'content_{lang}': ''})
            dict_dict['requested'] = source
            return dict_dict

    if source in ('duden', 'pons'):
        pons_json = get_json_from_pons_api(search_word=dict_dict['search_word'],
                                            filename=cache_saving_word,
                                            ignore_cache=ignore_cache)
        # getting root headword
        duden_search_word = _get_rootword(search_word=dict_dict['search_word'],
                                         pons_json=pons_json)

        duden_soup = get_duden_soup(duden_search_word,
                                    cache_saving_word,
                                    ignore_cache,
                                    'dictionnary')

        duden_syn_soup = get_duden_soup(duden_search_word,
                                            cache_saving_word,
                                            ignore_cache,
                                            'synonymes')
        
        # TODO only run function if key does not exist
        dict_dict = _update_dict_without_overwriting(dict_dict,
                                                    key='content_pons',
                                                    value=construct_dict_content_from_json(pons_json[0]["hits"],
                                                                                            search_word=dict_dict['search_word']))
        dict_dict = _update_dict_without_overwriting(dict_dict,
                                                    key='content_du',
                                                    value=construct_dict_content_from_soup(duden_soup))
        dict_dict = _update_dict_without_overwriting(dict_dict,
                                                    key='synonymes',
                                                    value=_add_synonymes_from_duden(duden_syn_soup))
        dict_dict = _update_dict_without_overwriting(dict_dict,
                                                    key='word_freq',
                                                    value=get_word_freq_from_soup(duden_soup))

        german_examples, english_examples = _extract_custom_examples_from_html(word=dict_dict['search_word'])
        dict_dict = _update_dict_without_overwriting(dict_dict,
                                                    key='custom_examples',
                                                    value={})
        dict_dict['custom_examples'] = _update_dict_without_overwriting(dict_dict['custom_examples'],
                                                    key='german',
                                                    value=german_examples)
        dict_dict['custom_examples'] = _update_dict_without_overwriting(dict_dict['custom_examples'],
                                                                        key='english',
                                                                        value=english_examples)

        dict_dict['requested'] = source

        return dict_dict

def _update_files(dict_dict, dict_saving_word):
    ''' temporary function
    Moving away from using html files and put everything in one dict file (json format).'''
    if 'updated' not in dict_dict:
        try:
            del dict_dict['content']
        except KeyError:
            pass
        dict_dict['updated'] = 'unified dicts 09.02'
        dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{dict_saving_word}_dict.json'
        write_str_to_file(dict_dict_path, json.dumps(dict_dict), overwrite=True)
        dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{dict_saving_word}_standerised.json'
        try:
            os.remove(dict_dict_path)
        except FileNotFoundError:
            pass
        old_html_path = DICT_DATA_PATH / 'html' / f'{dict_saving_word}.html'
        try:
            os.remove(old_html_path)
        except FileNotFoundError:
            pass
        old_html_path = DICT_DATA_PATH / 'html' / f'{dict_saving_word}.quiz.html'
        try:
            os.remove(old_html_path)
        except FileNotFoundError:
            pass

    if 'hidden_words_list' in dict_dict:
        del dict_dict['hidden_words_list']
        del dict_dict['secondary_words_to_hide']
        dict_dict['updated'] = 'split hidden words 11.02'
        dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{dict_saving_word}_dict.json'
        write_str_to_file(dict_dict_path, json.dumps(dict_dict), overwrite=True)
    else:
        dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{dict_saving_word}_dict.json'
        write_str_to_file(dict_dict_path, json.dumps(dict_dict), overwrite=True)

def _update_dict_without_overwriting(dict_dict, key, value):
    if key not in dict_dict:
        dict_dict[key] = value
    return dict_dict

def _get_rootword(search_word: str, pons_json):
    if pons_json:
        try:
            duden_search_word = pons_json[0]['hits'][0]['roms'][0]['headword']
            duden_search_word = remove_from_str(duden_search_word, [b'\xcc\xa3', b'\xcc\xb1', b'\xc2\xb7'])
        except KeyError:
            duden_search_word = search_word
    else:
        duden_search_word = search_word
    return duden_search_word

def _prompt_user_for_lang(search_word: str, message_box_content_carrier, wait_for_usr, lang_0: str, lang_1: str) -> str:
    ## resolve language translation confusion by prompting the user from a QMessageBox
    message_box_dict = _prepare_message_box_content(search_word, lang_0, lang_1)
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
        lang = f'{lang_0}-{lang_1}'
    elif CLICKED_BUTTON[1]:
        lang = f'{lang_1}-{lang_0}'
    else:
        raise RuntimeError('how can this happen')

    del CLICKED_BUTTON

    return lang

def _read_dict_from_file(saving_word: str, old=False):
    if not old:
        dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{saving_word}_dict.json'
    else:
        dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{saving_word}_standerised.json'

    logger.debug('Looking for dict cache')
    dict_dict: dict
    dict_cache_found: bool
    dict_string, pons_dict_cache_found = get_cache(dict_dict_path)
    if pons_dict_cache_found:
        dict_cache_found = True
        try:
            # dict_dict = ast.literal_eval(dict_string) # gives me malformed string for "machen"
            dict_dict = json.loads(dict_string)
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


def _prepare_message_box_content(word: str, lang_0: str, lang_1: str) -> dict[str, str]:
    mother_language = lang_0 if lang_0 != 'de' else lang_1
    if lang_0=='de':
        mother_language = 'an english' if lang_1=='en' else 'a french'
        zero_to_one_str = 'De -> En' if lang_1=='en' else 'De -> Fr'
        one_to_zero_str = 'En -> De' if lang_1=='en' else 'Fr -> De'
    else:
        mother_language = 'an english' if lang_0=='en' else 'a french'
        zero_to_one_str = 'De -> En' if lang_0=='en' else 'De -> Fr'
        one_to_zero_str = 'En -> De' if lang_0=='en' else 'Fr -> De'

    message_box_dict = {'text': "Confused.. I need you help??",
                        'title': "Choice of translation",
                        'informative_text': f'"{word}" is both a german and {mother_language} word. Please choose the translation direction',
                        'yes_button_text': zero_to_one_str,
                        'no_button_text': one_to_zero_str}
                        
    return message_box_dict
    
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
    try:
        old_html_str = read_str_from_file(old_html_path)
    except FileNotFoundError:
        return old_german_examples, old_englisch_examples
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

    # FIXED (1) BUG should return list
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

def create_dict_for_manually_added_words() -> dict[str, Any]:
    # dict is not built -> word not found anywhere but html "written" manually
    # BUG (2) this allows only one example to persist for manually written defs 
    # -> TODO if manually added dict already exist append new examples to that dict else create new one like here
    dict_dict = {}
    dict_dict['source'] = 'manual'
    dict_dict['custom_examples'] = {}
    dict_dict['custom_examples']['german'] = []
    dict_dict['custom_examples']['english'] = []
    dict_dict['forced_hidden_words'] = []

    return dict_dict


def update_hidden_words_in_dict(selected_text2hide, saving_word) -> None:
    dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{saving_word}_standerised.json'
    dict_cache_found, _, dict_dict = _read_dict_from_file(saving_word)
    if dict_cache_found:
        if selected_text2hide in dict_dict['forced_hidden_words']:
            raise RuntimeError('selected word is already in hidden words list')
        dict_dict['forced_hidden_words'].append(selected_text2hide)
        write_str_to_file(dict_dict_path, json.dumps(dict_dict), overwrite=True)
    else:
        raise RuntimeError('dict for quized word not found')


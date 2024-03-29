import json
from PyQt5.QtCore import QMutex
from typing import Any
from PyQt5.QtCore import pyqtSignal, QWaitCondition

from GetDict.GetData import get_duden_soup, get_json_from_pons_api
from GetDict.ParsingJson import construct_dict_content_from_json
from GetDict.ParsingSoup import (construct_dict_content_from_soup, create_synonyms_list,
                                     get_word_freq_from_soup)
from utils import remove_from_str, replace_umlauts_1
from utils import (get_cache,
                   set_up_logger, write_str_to_file)
from settings import DICT_DATA_PATH

logger = set_up_logger(__name__)

# You can set the python.analysis.diagnosticMode to workspace rather than its default value of openFilesOnly to check for error without opening files
# TODO (2) STRUCT convert to class? (OOP vs Functional)
# DONE (0) STRUCT use the same dict structures for both pons and duden
# TODO (6) Umschweife not found in duden but it's there -> update: the owrd is there but there's no definition section
# BUG (0) if the website is not reachable, the returned soup will be empty and the algo will not look it up again 

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

    def _create_empty_dict(search_word, german_examples: list = None, english_examples: list = None):
        word_dict = {'search_word': search_word}
        if german_examples is not None:
            word_dict['custom_examples'] = {}
            word_dict['custom_examples']['german'] = german_examples
            word_dict['custom_examples']['english'] = []
        if english_examples is not None:
            word_dict['custom_examples']['english'] = english_examples
        return word_dict

    def _add_dict_content(word_dict, saving_word, ignore_cache, message_box_content_carrier, wait_for_usr, source: str):
        if 'translate' in source:
            _pons_json, status_code = get_json_from_pons_api(search_word=word_dict['search_word'],
                                                filename=saving_word+source.replace('translate', ''),
                                                translate_en='en' in source,
                                                translate_fr='fr' in source,
                                                ignore_cache=ignore_cache)

            # schnappen en ta3tik erreur puisque fama content_de ama translate_en
            if _pons_json:
                if len(_pons_json) == 1:
                    # lang = _pons_json[0]["lang"] # schnappen en ta3tik erreur puisque fama content_de ama translate_en
                    lang = source.replace('translate_', '')
                    word_dict.update({
                        'requested' : source,
                        f'content_{lang}': construct_dict_content_from_json(_pons_json[0]["hits"],
                                                                            translate=True,
                                                                            search_word=word_dict['search_word'])})
                    return word_dict
                elif len(_pons_json) == 2:
                    lang_0 = _pons_json[0]["lang"]
                    lang_1 = _pons_json[1]["lang"]
                    requested = _prompt_user_for_lang(search_word=word_dict['search_word'],
                                                    message_box_content_carrier=message_box_content_carrier,
                                                    wait_for_usr=wait_for_usr,
                                                    lang_0=lang_0,
                                                    lang_1=lang_1)
                    word_dict.update({
                        'requested': f'translate_{requested}' ,
                        f'content_{lang_0}-{lang_1}':  construct_dict_content_from_json(_pons_json[0]["hits"],
                                                                                        translate=True,
                                                                                        search_word=word_dict['search_word']),
                        f'content_{lang_1}-{lang_0}':  construct_dict_content_from_json(_pons_json[1]["hits"],
                                                                                        translate=True,
                                                                                        search_word=word_dict['search_word'])
                            })
                    
                    return word_dict
                else:
                    raise RuntimeError('json API response is expected to be of length 1 or only for translations 2')  
            elif status_code not in (404, 403, 500, 503): # those are connexion problems, the word may be in pons after retry
                lang = source.replace('translate_', '')
                word_dict.update({f'content_{lang}': ''})
                word_dict['requested'] = source
                return word_dict
            else:
                word_dict['requested'] = source
                # inform the user he should retry if content_lang is not there
                return word_dict 

        if source in ('duden', 'pons'):
            pons_json, status_code = get_json_from_pons_api(search_word=word_dict['search_word'],
                                                filename=saving_word,
                                                ignore_cache=ignore_cache)
            # getting root headword
            duden_search_word = _get_rootword(search_word=word_dict['search_word'],
                                            pons_json=pons_json)

            duden_soup = get_duden_soup(duden_search_word,
                                        saving_word+'_du',
                                        ignore_cache,
                                        'dictionnary')

            duden_syn_soup = get_duden_soup(duden_search_word,
                                                saving_word+'_du_syn',
                                                ignore_cache,
                                                'synonymes')

            # TODO only run function if key does not exist
            json_data = pons_json[0]["hits"] if pons_json else ''
            word_dict = _update_dict_without_overwriting(word_dict,
                                                        key='content_pons',
                                                        value=construct_dict_content_from_json(json_data,
                                                                                                search_word=word_dict['search_word']))
            word_dict = _update_dict_without_overwriting(word_dict,
                                                        key='content_du',
                                                        value=construct_dict_content_from_soup(duden_soup))
            word_dict = _update_dict_without_overwriting(word_dict,
                                                        key='synonymes',
                                                        value= create_synonyms_list(duden_syn_soup))
            word_dict = _update_dict_without_overwriting(word_dict,
                                                        key='word_freq',
                                                        value=get_word_freq_from_soup(duden_soup))

            word_dict['requested'] = source

            return word_dict

    def _update_files(word_dict, saving_word, old_saving_word):
        ''' temporary function
        Moving away from using html files and put everything in one dict file (json format).'''
        if 'updated' not in word_dict:
            try:
                del word_dict['content']
            except KeyError:
                pass
            word_dict['updated'] = 'unified dicts 09.02'
            save_word_dict(word_dict, saving_word)

        if 'hidden_words_list' in word_dict:
            del word_dict['hidden_words_list']
            try:
                del word_dict['secondary_words_to_hide']
            except KeyError:
                pass
            word_dict['updated'] = 'split hidden words 11.02'
            word_dict_path = DICT_DATA_PATH / 'word_dicts' / f'{saving_word}_dict.json'
            write_str_to_file(word_dict_path, json.dumps(word_dict), overwrite=True)
        else:
            word_dict_path = DICT_DATA_PATH / 'word_dicts' / f'{saving_word}_dict.json'
            write_str_to_file(word_dict_path, json.dumps(word_dict), overwrite=True)

    def save_word_dict(word_dict, saving_word):
        word_dict_path = DICT_DATA_PATH / 'word_dicts' / f'{saving_word}_dict.json'
        write_str_to_file(word_dict_path, json.dumps(word_dict), overwrite=True)

    def _update_dict_without_overwriting(word_dict, key, value):
        if key not in word_dict:
            word_dict[key] = value
        return word_dict

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

    dict_exist = False
    # if not ignore_dict:
    dict_cache_found, _error_reading_json, word_dict = _read_dict_from_file(word_query.saving_word)
    # temporary (look for an old dict file)
    if not dict_cache_found:
        dict_cache_found, _error_reading_json, word_dict = _read_dict_from_file(word_query.saving_word, old=True)
    # temporary (look for an old dict file with old filename)
    if not dict_cache_found:
        dict_cache_found, _error_reading_json, word_dict = _read_dict_from_file(replace_umlauts_1(word_query.search_word), old=True)
    dict_exist = dict_cache_found and not _error_reading_json
    if dict_exist and 'search_word' not in word_dict: # temporary
        word_dict['search_word'] = word_query.search_word

    update_synonymes_format(word_dict)

    if not dict_exist:
        word_dict = _create_empty_dict(word_query.search_word)

    if dict_exist and (word_query.ignore_cache or word_query.ignore_dict):
        word_dict = _create_empty_dict(word_query.search_word,
                                       german_examples=word_dict['custom_examples']['german'],
                                       english_examples=word_dict['custom_examples']['english'])
    
    translate = word_query.translate_fr or word_query.translate_en

    # DONE (1) STRUCT use one unified decision tree for all functions
    if translate:
        # check if dict already cached and have the translation data,
        # otherwise update it if it lacks the translation data
        # or create it if doesnt'exist and then update it.

        lang = 'fr' * word_query.translate_fr + 'en' * word_query.translate_en
        
        if f'content_{lang}' in word_dict:
            _update_files(word_dict, word_query.saving_word, replace_umlauts_1(word_query.search_word))
            word_dict['requested'] = f'translate_{lang}'
            return word_dict
        if f'content_{lang}-de' in word_dict:
            requested = _prompt_user_for_lang(search_word=word_dict['search_word'],
                                            message_box_content_carrier=message_box_content_carrier,
                                            wait_for_usr=wait_for_usr,
                                            lang_0='de',
                                            lang_1=lang)
            word_dict['requested'] = f'translate_{requested}' 
            _update_files(word_dict, word_query.saving_word, replace_umlauts_1(word_query.search_word))
            return word_dict
        
        word_dict = _add_dict_content(word_dict=word_dict,
                                        saving_word=word_query.saving_word,
                                        ignore_cache=word_query.ignore_cache,
                                        message_box_content_carrier=message_box_content_carrier,
                                        wait_for_usr=wait_for_usr,
                                        source=f'translate_{lang}')
        _update_files(word_dict, word_query.saving_word, replace_umlauts_1(word_query.search_word))
        return word_dict

    if word_query.get_from_duden:
        if 'content_du' in word_dict:
            _update_files(word_dict, word_query.saving_word, replace_umlauts_1(word_query.search_word))
            word_dict['requested'] = 'duden'
            return word_dict

        word_dict = _add_dict_content(word_dict=word_dict,
                                    saving_word=word_query.saving_word,
                                    ignore_cache=word_query.ignore_cache,
                                    message_box_content_carrier=message_box_content_carrier,
                                    wait_for_usr=wait_for_usr,
                                    source='duden')
        _update_files(word_dict, word_query.saving_word, replace_umlauts_1(word_query.search_word))
        return word_dict
    
    if 'content_pons' in word_dict:
        _update_files(word_dict, word_query.saving_word, replace_umlauts_1(word_query.search_word))
        word_dict['requested'] = 'pons'
        return word_dict

    word_dict = _add_dict_content(word_dict=word_dict,
                                saving_word=word_query.saving_word,
                                ignore_cache=word_query.ignore_cache,
                                message_box_content_carrier=message_box_content_carrier,
                                wait_for_usr=wait_for_usr,
                                source='pons')
    _update_files(word_dict, word_query.saving_word, replace_umlauts_1(word_query.search_word))
    return word_dict

def update_synonymes_format(word_dict):
    # temporary, update synonymes format, delete after all word_dicts are modified after 19.02.23
    if 'synonymes' not in word_dict:
        return
    
    word_dict['synonymes'] = [
        [syn.replace('(', '<acronym title="usage">')\
            .replace(')', '</acronym>')\
            .replace('umgangssprachlich', 'umg')\
            .replace('landschaftlich', 'land')
                for syn in syn_sublist] for syn_sublist in word_dict['synonymes']]

def create_dict_for_manually_added_words() -> dict[str, Any]:
    # dict is not built -> word not found anywhere but html "written" manually
    # BUG (2) this allows only one example to persist for manually written defs 
    # -> TODO if manually added dict already exist append new examples to that dict else create new one like here
    word_dict = {}
    word_dict['source'] = 'manual'
    word_dict['custom_examples'] = {}
    word_dict['custom_examples']['german'] = []
    word_dict['custom_examples']['english'] = []
    word_dict['forced_hidden_words'] = []

    return word_dict

def _read_dict_from_file(saving_word: str, old=False):
    if not old:
        word_dict_path = DICT_DATA_PATH / 'word_dicts' / f'{saving_word}_dict.json'
    else:
        word_dict_path = DICT_DATA_PATH / 'word_dicts' / f'{saving_word}_standerised.json'

    logger.debug('Looking for dict cache')
    word_dict: dict
    dict_cache_found: bool
    dict_string, pons_dict_cache_found = get_cache(word_dict_path)
    if pons_dict_cache_found:
        dict_cache_found = True
        try:
            # word_dict = ast.literal_eval(dict_string) # gives me malformed string for "machen"
            word_dict = json.loads(dict_string)
            error_reading_json = False
        except SyntaxError:
            logger.warning('dict file is not readable!')
            word_dict = {}
            error_reading_json = True
    else:
        dict_cache_found = False
        error_reading_json = None
        word_dict = {}
    
    return dict_cache_found, error_reading_json, word_dict
    
def update_hidden_words_in_dict(selected_text2hide, saving_word) -> None:
    word_dict_path = DICT_DATA_PATH / 'word_dicts' / f'{saving_word}_standerised.json'
    dict_cache_found, _, word_dict = _read_dict_from_file(saving_word)
    if dict_cache_found:
        if selected_text2hide in word_dict['forced_hidden_words']:
            raise RuntimeError('selected word is already in hidden words list')
        word_dict['forced_hidden_words'].append(selected_text2hide)
        write_str_to_file(word_dict_path, json.dumps(word_dict), overwrite=True)
    else:
        raise RuntimeError('dict for quized word not found')


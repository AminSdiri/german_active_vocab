import json
import pandas as pd
from bs4 import BeautifulSoup as bs
import ast
from collections import Counter

from GetDict.GetData import get_word_from_source
from GetDict.ParsingJson import construct_dict_from_json
from GetDict.ParsingSoup import (create_synonyms_list,
                                     get_word_freq_from_soup,
                                     parse_duden_html_to_dict)
from GetDict.HiddenWordsList import generate_hidden_words_list
from utils import fix_html_with_custom_example
from utils import (get_cache,
                   read_str_from_file,
                   set_up_logger, write_str_to_file)
from settings import DICT_DATA_PATH

logger = set_up_logger(__name__)

# TODO STRUCT (1) BUG dicts saved from duden are not the same as those saved from Pons!! (different outer structure)

def standart_dict(saving_word, translate2fr, translate2en,
                  get_from_duden, search_word, ignore_cache, ignore_dict):
    
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

    # TODO STRUCT (1) baddalha el fonction tbadel struct dict twalli standarisee
    
    translate = translate2fr or translate2en

    if get_from_duden:
        dict_dict = _standart_duden_dict(found_in_pons_duden,
                                        _duden_soup,
                                        _duden_syn_soup,
                                        search_word,
                                        dict_dict_path)
        dict_dict['requested'] = 'duden'

    elif found_in_pons_duden[0]:
        dict_dict = _standart_pons_dict(_pons_json,
                                        _duden_syn_soup,
                                        search_word,
                                        translate,
                                        _duden_soup)
        if isinstance(dict_dict, dict):
            dict_dict['requested'] = 'pons'

    elif not translate:
        dict_dict = _standart_duden_dict(found_in_pons_duden,
                                        _duden_soup,
                                        _duden_syn_soup,
                                        search_word,
                                        dict_dict_path)
        dict_dict['requested'] = 'pons'

    else:
        dict_dict = {}
        dict_dict['requested'] = 'pons'
        dict_dict['source'] = 'NotFound'
    
    # BUG (0) dict_dict is list for translate
    dict_dict['search_word'] = search_word

    return dict_dict, dict_dict_path

def _read_dict_from_file(dict_dict_path):
    logger.debug('Looking for dict cache')
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
                       _duden_soup):
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

        dict_dict = {'content': construct_dict_from_json(_pons_json[0]["hits"], translate, word),
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
        dict_dict['hidden_words_list']=generate_hidden_words_list(dict_dict['content'])

    elif translate and len(_pons_json) == 1:
        logger.info(f'language: {_pons_json[0]["lang"]}')
        json_data = _pons_json[0]["hits"]
        dict_dict = construct_dict_from_json(json_data, translate, word)

        dict_dict = [{'lang': _pons_json[0]["lang"],
                      'content': dict_dict}
                    ]
    elif translate and len(_pons_json) == 2:
        logger.info(f'language: {_pons_json[0]["lang"]}')
        json_data_1 = _pons_json[0]["hits"]
        dict_dict_1 = construct_dict_from_json(json_data_1, translate, word)

        json_data_2 = _pons_json[1]["hits"]
        dict_dict_2 = construct_dict_from_json(json_data_2, translate, word)

        # language=json_data[0]['lang']
        dict_dict = [
            {'lang': _pons_json[0]['lang'],
                'content': dict_dict_1},
            {'lang': _pons_json[1]['lang'],
                'content': dict_dict_2}
                ]
    else:
        raise RuntimeError(
            'json API response is expected to be of length 1 '
            'or only for translations 2')

    return dict_dict

def _standart_duden_dict(found_in_pons_duden, _duden_soup, _duden_syn_soup,
                         word):

    if found_in_pons_duden[1]:

        duden_dict = parse_duden_html_to_dict(_duden_soup)

        duden_dict["synonymes"] = _add_synonymes_from_duden(_duden_syn_soup)

        (duden_dict['custom_examples']['german'], 
         duden_dict['custom_examples']['english']) = _extract_custom_examples_from_html(word)

        duden_dict['hidden_words_list'] = generate_hidden_words_list(duden_dict)

        duden_dict['source'] = 'duden'

    else:
        duden_dict = {}

    return duden_dict
    
def _extract_custom_examples_from_html(word):
    '''
    Temporary function:
    save custom examples list from the old version html in dict_dict
    '''
    # TODO (2) run in loop and then delete here
    old_german_examples = []
    old_englisch_examples = []
    df = pd.read_csv(DICT_DATA_PATH / 'wordlist.csv')
    df.set_index('Word', inplace=True)
    word_is_already_saved = word in df.index
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

def _add_synonymes_from_duden(_duden_syn_soup):
    if not _duden_syn_soup:
        return []

    try:
        synonyms_list = create_synonyms_list(_duden_syn_soup)
        return synonyms_list
    except TypeError:
        # logger.warning('Type Error in create_synonyms_list >> Check it!')
        raise RuntimeError('Type Error in create_synonyms_list >> Check it!')

def get_definitions_from_dict_dict(dict_dict, info='definition'):
    definitions_list = []
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
             
def extract_synonymes_in_html_format(dict_dict):
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


def create_dict_for_manually_added_words():
    # dict is not built -> word not found anywhere but html "written" manually
    # BUG (2) this allows only one example to persist for manually written defs 
    # -> TODO if manually added dict already exist append new examples to that dict else create new one like here
    dict_dict = dict()
    dict_dict['source'] = 'manual'
    dict_dict['custom_examples'] = dict()
    dict_dict['custom_examples']['german'] = []
    dict_dict['custom_examples']['english'] = []
    dict_dict['hidden_words_list'] = []

    return dict_dict


def update_hidden_words_in_dict(selected_text2hide, saving_word):
    dict_dict_path = DICT_DATA_PATH / 'dict_dicts' / f'{saving_word}_standerised.json'
    dict_cache_found, _, _, dict_dict = _read_dict_from_file(dict_dict_path)
    if dict_cache_found:
        if selected_text2hide in dict_dict['hidden_words_list']:
            raise RuntimeError('selected word is already in hidden words list')
        dict_dict['hidden_words_list'].append(selected_text2hide)
        write_str_to_file(dict_dict_path, json.dumps(dict_dict), overwrite=True)
    else:
        raise RuntimeError('dict for quized word not found')
import json
import pandas as pd
from bs4 import BeautifulSoup as bs
import ast

from GetData import get_word_from_source
from ParsingData.ParsingJson import parse_json_data
from ParsingData.ParsingSoup import (create_synonyms_list,
                                     get_word_freq_from_soup,
                                     parse_duden_html_to_dict)
from utils import fix_html_with_custom_example
from utils import (get_cache,
                   read_str_from_file,
                   set_up_logger, write_str_to_file)
from settings import dict_data_path

logger = set_up_logger(__name__)


def standart_dict(saving_word, translate, translate2fr, translate2en,
                  get_from_duden, word, ignore_cache, ignore_dict):
    
    if not (ignore_cache or ignore_dict):
        dict_dict_path, dict_cache_found, error_reading_json, _found_in_pons, _found_in_duden, dict_dict = read_dict_from_file(saving_word, get_from_duden)
        if dict_cache_found and not error_reading_json:
            return dict_dict, dict_dict_path, _found_in_pons, _found_in_duden 

    (_pons_json,
        _found_in_pons,
        _duden_soup,
        _found_in_duden,
        _duden_syn_soup,
        _syns_found_in_duden) = get_word_from_source(translate2fr,
                                                     translate2en,
                                                     get_from_duden,
                                                     word,
                                                     saving_word,
                                                     ignore_cache)

    if get_from_duden:
        dict_dict = standart_duden_dict(_found_in_duden,
                                        _duden_soup,
                                        _duden_syn_soup,
                                        _syns_found_in_duden,
                                        word,
                                        dict_dict_path)

    elif _found_in_pons:
        dict_dict = standart_pons_dict(_pons_json,
                                        dict_dict_path,
                                        _duden_syn_soup,
                                        _syns_found_in_duden,
                                        word,
                                        translate,
                                        _duden_soup,
                                        _found_in_duden)

    elif not translate:
        dict_dict = standart_duden_dict(
            _found_in_duden,
            _duden_soup,
            _duden_syn_soup,
            _syns_found_in_duden,
            word,
            dict_dict_path)

    else:
        dict_dict = {}

    return dict_dict, dict_dict_path, _found_in_pons, _found_in_duden

def read_dict_from_file(saving_word, get_from_duden):
    # pons or duden depending on the saving word (vorübergehend)

    # TODO STRUCT (1) baddalha el fonction tbadel struct dict twalli standarisee w source pons wala duden mawjoud fel key

    logger.debug('Looking for pons dict cache')
    if not get_from_duden:
        dict_dict_path = dict_data_path / 'dict_dicts' / f'{saving_word}_standerised.json'
        dict_string, pons_dict_cache_found = get_cache(dict_dict_path)
        if pons_dict_cache_found:
            dict_cache_found = True
            # FIXED
            # if dict_string == 'null':
            #     _found_in_pons = None
            #     _found_in_duden = None
            #     error_reading_json = True
            #     dict_dict = {}
            #     # fixedBUG (1) find out when and where it happens
            #     logger.warning('dict string is null! (dict damaged somewhere')
            #     return dict_dict_path, dict_cache_found, error_reading_json, _found_in_pons, _found_in_duden, dict_dict
            _found_in_pons = True
            _found_in_duden = None
            try:
                dict_dict = ast.literal_eval(dict_string)
                error_reading_json = False
            except SyntaxError:
                logger.warning('dict file is not readable!')
                dict_dict = {}
                error_reading_json = True
            # vorübergehend ekteb source fel dict w 3al fichier
            if 'wortart' in dict_dict:
                _found_in_pons = None
                _found_in_duden = True
                dict_dict['source'] = 'duden'
                write_str_to_file(dict_dict_path, json.dumps(dict_dict))
            return dict_dict_path, dict_cache_found, error_reading_json, _found_in_pons, _found_in_duden, dict_dict

    if get_from_duden or not pons_dict_cache_found:
        saving_word_du = saving_word + '_du'
        dict_dict_path = dict_data_path / 'dict_dicts' / f'{saving_word_du}_standerised.json'
        dict_string, duden_dict_cache_found = get_cache(dict_dict_path)
        if duden_dict_cache_found:
            dict_cache_found = True
            _found_in_pons = None if get_from_duden else False
            _found_in_duden = True
            try:
                dict_dict = ast.literal_eval(dict_string)
                error_reading_json = False
            except SyntaxError:
                logger.warning('dict file is not readable!')
                dict_dict = {}
                error_reading_json = True    
            return dict_dict_path, dict_cache_found, error_reading_json, _found_in_pons, _found_in_duden, dict_dict

        else:
            dict_dict_path = dict_data_path / 'dict_dicts' / f'{saving_word}_standerised.json'
            dict_cache_found = False
            _found_in_pons = False
            _found_in_duden = False
            error_reading_json = None
            dict_dict = {}
            return dict_dict_path, dict_cache_found, error_reading_json, _found_in_pons, _found_in_duden, dict_dict


def standart_pons_dict(_pons_json, dict_dict_path,
                       _duden_syn_soup, _syns_found_in_duden, word, translate,
                       _duden_soup,
                       _found_in_duden):
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
        json_data = _pons_json[0]["hits"]
        dict_dict = parse_json_data(json_data, translate, word)

        dict_dict = {'content': dict_dict,
                     'synonymes': [],
                     'custom_examples': {
                         'german': [],
                         'english': []
                     }
                     }

        if _found_in_duden:
            word_freq = get_word_freq_from_soup(_duden_soup)
        else:
            word_freq = -1

        dict_dict['word_freq'] = word_freq

    elif translate and len(_pons_json) == 1:
        logger.info(f'language: {_pons_json[0]["lang"]}')
        json_data = _pons_json[0]["hits"]
        dict_dict = parse_json_data(json_data, translate, word)

        dict_dict = [
            {'lang': '',
                'content': dict_dict}
        ]
    elif translate and len(_pons_json) == 2:
        logger.info(f'language: {_pons_json[0]["lang"]}')
        json_data_1 = _pons_json[0]["hits"]
        dict_dict_1 = parse_json_data(json_data_1, translate, word)

        json_data_2 = _pons_json[1]["hits"]
        dict_dict_2 = parse_json_data(json_data_2, translate, word)

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

    if not translate:
        dict_dict = add_synonymes_from_duden(
            dict_dict, _duden_syn_soup, _syns_found_in_duden)
        dict_dict = extract_custom_examples_from_html_to_dict(
            dict_dict, word)

    # save dict_dict
    write_str_to_file(dict_dict_path, json.dumps(dict_dict))

    return dict_dict


def standart_duden_dict(_found_in_duden, _duden_soup, _duden_syn_soup,
                        _syns_found_in_duden, word, dict_dict_path):

    if _found_in_duden:

        duden_dict = parse_duden_html_to_dict(_duden_soup)

        duden_dict = add_synonymes_from_duden(
            duden_dict, _duden_syn_soup, _syns_found_in_duden)

        duden_dict = extract_custom_examples_from_html_to_dict(
            duden_dict, word)

        # save dict_dict
        write_str_to_file(dict_dict_path, json.dumps(duden_dict))

    else:
        duden_dict = {}

    return duden_dict


def extract_custom_examples_from_html_to_dict(dict_dict, word):
    '''
    Temporary function:
    save custom examples list from the old version html in dict_dict
    '''

    beispiel_list_de = dict_dict['custom_examples']['german']
    beispiel_list_en = dict_dict['custom_examples']['english']
    df = pd.read_csv(dict_data_path / 'wordlist.csv')
    df.set_index('Word', inplace=True)
    word_is_already_saved = word in df.index
    if word_is_already_saved:
        old_html_path = dict_data_path / 'html' / f'{word}.html'
        old_html_str = read_str_from_file(old_html_path)

        alt_beispiel_de, alt_beispiel_en = get_custom_example_from_html(
            old_html_str)
        if alt_beispiel_de:
            beispiel_list_de.append(alt_beispiel_de)
        if alt_beispiel_en:
            beispiel_list_en.append(alt_beispiel_en)

    return dict_dict


def add_synonymes_from_duden(dict_dict, _duden_syn_soup, _syns_found_in_duden):
    if not _syns_found_in_duden:
        return dict_dict

    try:
        synonyms_list = create_synonyms_list(_duden_syn_soup)
        dict_dict["synonymes"] = synonyms_list
    except TypeError:
        logger.warning(
            'Type Error in create_synonyms_list >> Check it!')

    return dict_dict


def get_custom_example_from_html(old_html_str):
    old_html_str = fix_html_with_custom_example(old_html_str)
    old_html_soup = bs(old_html_str, 'lxml')

    ce_begin = old_html_soup.find("b", string="Eigenes Beispiel:")
    if ce_begin:
        custum_exemple_de_soup = ce_begin.findNext('i')
        alt_beispiele_de = custum_exemple_de_soup.string.replace('&nbsp;', '')
    else:
        alt_beispiele_de = ''
        alt_beispiele_en = ''
        return alt_beispiele_de, alt_beispiele_en

    ce_englisch_begin = ce_begin.findNext('b', string="Auf Englisch:")
    if ce_englisch_begin:
        custum_exemple_en_soup = ce_englisch_begin.findNext('i')
        alt_beispiele_en = custum_exemple_en_soup.string.replace('&nbsp;', '')
    else:
        alt_beispiele_en = ''

    alt_beispiele_de = alt_beispiele_de.replace('\xa0', '')
    alt_beispiele_en = alt_beispiele_en.replace('\xa0', '')

    return alt_beispiele_de, alt_beispiele_en

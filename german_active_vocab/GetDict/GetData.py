from plyer import notification
import requests
import json
import time
from urllib import request, error
from bs4 import BeautifulSoup as bs
from http.client import InvalidURL

from utils import (get_cache,
                   read_str_from_file,
                   remove_from_str,
                   replace_umlauts_2,
                   set_up_logger,
                   write_str_to_file)
from settings import DICT_DATA_PATH

logger = set_up_logger(__name__)

# TODO implement proper search for duden https://github.com/radomirbosak/duden/blob/master/duden/search.py
# TODO update dict "source" value if examples are manually given by user

def get_word_from_source(translate2fr, translate2en, get_from_duden,
                         word, saving_word, ignore_cache):

    logger.info("get_word_from_source")
    translate = translate2fr or translate2en
    found_in_pons_duden = [None, None]

    # Pons data
    if get_from_duden:
        pons_json = ''
        _found_in_pons = None
    else:
        pons_json, _found_in_pons = _get_json_from_pons_api(word,
                                                            saving_word,
                                                            translate2en,
                                                            translate2fr,
                                                            ignore_cache)
        found_in_pons_duden[0] = _found_in_pons


    if translate:
        duden_soup = ''
        duden_syn_soup = ''
        return (found_in_pons_duden, pons_json, duden_soup, duden_syn_soup)

    # getting root headword
    if _found_in_pons:
        try:
            duden_search_word = pons_json[0]['hits'][0]['roms'][0]['headword']
            duden_search_word = remove_from_str(duden_search_word, [b'\xcc\xa3', b'\xcc\xb1', b'\xc2\xb7'])
        except KeyError:
            duden_search_word = word
    else:
        duden_search_word = word

    (duden_soup, _found_in_duden) = _get_duden_soup(duden_search_word,
                                                    saving_word,
                                                    ignore_cache,
                                                    'dictionnary')
    found_in_pons_duden[1] = _found_in_duden

    duden_syn_soup, _ = _get_duden_soup(duden_search_word,
                                        saving_word,
                                        ignore_cache,
                                        'synonymes')

    return (found_in_pons_duden, pons_json, duden_soup, duden_syn_soup)


def _get_duden_soup(word, filename, ignore_cache, duden_source):
    # TODO find better way to request word from duden
    # example schleife is not found in duden but it's there under
    # https://www.duden.de/rechtschreibung/Schleife_Schlinge_Kurve_Schlaufe 
    
    logger.debug('Looking in Duden cache')
    filename = filename if '_du' in filename else f'{filename}_du'
    if duden_source == 'synonymes':
        filename += '_syn'
    cache_path = DICT_DATA_PATH / 'cache' / filename
    duden_html, duden_cache_found = get_cache(cache_path)

    if duden_cache_found and not ignore_cache:
        logger.debug('Reading Word from Duden Cache')
        duden_soup = bs(duden_html, 'html.parser')
        found_in_duden = True
        return duden_soup, found_in_duden

    logger.info('Online searching for Word in Duden')

    url_uppercase, url_lowercase = _make_duden_url(word, duden_source)
    found_in_duden, duden_html, http_code = _get_html_from_duden(url_lowercase)
    if http_code == 404:
        found_in_duden, duden_html, http_code = _get_html_from_duden(url_uppercase)

    if found_in_duden:
        duden_soup = _duden_html_to_soup(duden_source, duden_html)
        write_str_to_file(DICT_DATA_PATH / 'cache' / filename, str(duden_soup))
    else:
        duden_soup = ''

    return duden_soup, found_in_duden

def _duden_html_to_soup(duden_source, duden_html):
    if duden_source == 'dictionnary':
        duden_soup = bs(duden_html, 'html.parser')
        duden_soup = duden_soup.find_all('article', role='article')
        if len(duden_soup) != 1:
            raise RuntimeError(
                    'duden_soup result have a length different than 1')
        else:
            duden_soup = duden_soup[0]

    elif duden_source == 'synonymes':
        duden_soup = bs(duden_html, 'html.parser')
        duden_soup = duden_soup.find_all('div', id="andere-woerter")
        if len(duden_soup) != 1:
            raise RuntimeError(
                    'duden_soup result have a length different than 1')
        else:
            duden_soup = duden_soup[0]
    return duden_soup

def _get_html_from_duden(url_lowercase):
    found_in_duden = False
    http_code = 0
    try:
        with request.urlopen(url_lowercase) as response:
            # use whatever encoding as per the webpage
            duden_html = response.read().decode('utf-8')
        logger.debug('got Duden Html (lower)')
        found_in_duden = True
        http_code =200

    except InvalidURL:
        logger.error(f'{url_lowercase} '
                        'words containing spaces in german to german ',
                        'are not allowed, did you wanted a translation?')
    except request.HTTPError as e:
        http_code = e.code
        if http_code == 404:
            logger.warning(f"{url_lowercase} is not found")
            duden_html = '404 Wort nicht gefunden'
        elif http_code == 503:
            logger.warning(f'{url_lowercase} '
                           'base webservices are not available')
            pass
        else:
            logger.warning('http error', e)
            duden_html = 'Error 500'
    except error.URLError:
        logger.error('certificate verify failed: '
                     'unable to get local issuer certificate')
        duden_html = 'No certificate installed'
    return found_in_duden, duden_html, http_code

def _make_duden_url(word, duden_source):
    if duden_source == 'dictionnary':
        url_uppercase = (f'https://www.duden.de/rechtschreibung/{replace_umlauts_2(word).capitalize()}')
        url_lowercase = (f'https://www.duden.de/rechtschreibung/{replace_umlauts_2(word).lower()}')
    elif duden_source == 'synonymes':
        url_uppercase = (f'https://www.duden.de/synonyme/{replace_umlauts_2(word).capitalize()}')
        url_lowercase = (f'https://www.duden.de/synonyme/{replace_umlauts_2(word).lower()}')
    else:
        raise RuntimeError('Duden source should be either "dictionnary" or '
                           '"synonymes". '
                           f'Instead {duden_source} is passed')
                           
    return url_uppercase, url_lowercase


def _get_json_from_pons_api(word, filename: str, translate2en,
                           translate2fr, ignore_cache):
    logger.debug('Looking in Pons cache')
    cache_path = DICT_DATA_PATH / 'cache' / filename
    json_file, json_cache_found = get_cache(cache_path)

    if json_cache_found and not ignore_cache:
        logger.debug('Reading Word from Pons Cache')
        json_data = json.loads(json_file)
        status_code = 200
        return json_data, status_code == 200

    logger.info('Online searching for Word in Pons')
    status_code = 0
    while True:
        if translate2en:
            url = "https://api.pons.com/v1/dictionary?l=deen&q="
        elif translate2fr:
            url = "https://api.pons.com/v1/dictionary?l=defr&q="
        else:
            url = "https://api.pons.com/v1/dictionary?l=dedx&q="
        url += word
        logger.debug(f'URL: {url}')
        try:
            # TODO (1) save API secret as envirement var
            # Please consider using your own API (it's free)
            # this one is limited to 1000 request per month
            # (https://en.pons.com/open_dict/public_api/secret)
            api_path = DICT_DATA_PATH / 'PONS_API'
            api_secret = read_str_from_file(api_path)
            api_secret = api_secret.replace('\n', '')

            raw_data = requests.get(url, headers={"X-Secret": api_secret})

            status_code = raw_data.status_code
            if status_code == 200:
                message = 'OK'
            elif status_code == 204:
                message = 'no results for this word could be found'
            elif status_code == 404:
                message = 'The dictionary does not exist'
            elif status_code == 403:
                message = 'The access to the dictionary is not allowed'
            elif status_code == 500:
                message = 'An internal server error has occurred'
            elif status_code == 503:
                message = 'The daily limit has been reached'

            if status_code == 200:
                logger.debug('got Json from Pons')
                json_data = raw_data.json()
                write_str_to_file(DICT_DATA_PATH / 'cache' /
                                  filename, json.dumps(json_data))
            else:
                logger.warning(
                    f'Status Code: {str(status_code)} {message}')
                json_data = ''

            return json_data, status_code == 200

        except requests.exceptions.ConnectionError:
            notification.notify(title='No Connection to Mutter',
                                message='Retrying in 10s',
                                timeout=5)
            logger.warning('No connection to Mutter, retying in 10s')
            time.sleep(10)
            continue

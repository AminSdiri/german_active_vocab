from plyer import notification
import requests
import json
import time
from urllib import request, error
from bs4 import BeautifulSoup as bs
from http.client import InvalidURL

from utils import (get_cache,
                   read_str_from_file,
                   replace_umlauts_2,
                   set_up_logger,
                   write_str_to_file)
from settings import DICT_DATA_PATH

logger = set_up_logger(__name__)

# TODO (1) implement proper search for duden https://github.com/radomirbosak/duden/blob/master/duden/search.py
# TODO (1) update dict "source" value if examples are manually given by user


def get_duden_soup(word, filename, ignore_cache, duden_source):
    # TODO (1) find better way to request word from duden
    # example schleife is not found in duden but it's there under
    # https://www.duden.de/rechtschreibung/Schleife_Schlinge_Kurve_Schlaufe 
    
    logger.debug('Looking in Duden cache')
    filename = filename if '_du' in filename else f'{filename}_du'
    filename = f'{filename}_syn' if duden_source == 'synonymes' else filename
    cache_path = DICT_DATA_PATH / 'cache' / filename
    duden_html, duden_cache_found = get_cache(cache_path)

    if duden_cache_found and not ignore_cache:
        logger.debug('Reading Word from Duden Cache')
        duden_soup = bs(duden_html, 'html.parser')
        return duden_soup

    logger.info('Online searching for Word in Duden')

    url_uppercase, url_lowercase = _make_duden_url(word, duden_source)
    found_in_duden, duden_html, http_code = _get_html_from_duden(url_lowercase)
    if http_code == 404:
        found_in_duden, duden_html, http_code = _get_html_from_duden(url_uppercase)

    if found_in_duden:
        duden_soup = _duden_html_to_soup(duden_source, duden_html)
        write_str_to_file(DICT_DATA_PATH / 'cache' / filename, str(duden_soup), overwrite=True)
    else:
        duden_soup = ''

    return duden_soup

def _duden_html_to_soup(duden_source, duden_html) -> bs:
    if duden_source == 'dictionnary':
        duden_soup = bs(duden_html, 'html.parser')
        duden_soup = duden_soup.find_all('article', role='article')
        if len(duden_soup) == 1:
            duden_soup = duden_soup[0]
        else:
            raise RuntimeError('duden_soup result have a length different than 1')

    if duden_source == 'synonymes':
        duden_soup = bs(duden_html, 'html.parser')
        duden_soup = duden_soup.find_all('div', id="andere-woerter")
        if len(duden_soup) == 1:
            duden_soup = duden_soup[0]
        else:
            raise RuntimeError('duden_soup result have a length different than 1')

    return duden_soup

def _get_html_from_duden(url_string):
    found_in_duden = False
    duden_html = None
    http_code = 0
    try:
        with request.urlopen(url_string) as response:
            # use whatever encoding as per the webpage
            duden_html = response.read().decode('utf-8')
        logger.debug('got Duden HTML')
        found_in_duden = True
        http_code =200

    except InvalidURL:
        logger.error(f'{url_string}. words containing spaces in german to german ',
                        'are not allowed, did you wanted a translation?')
    except request.HTTPError as http_error:
        http_code: int = http_error.code
        if http_code == 404:
            logger.warning(f"{url_string} is not found")
        elif http_code == 503:
            logger.warning(f'{url_string} '
                           'base webservices are not available')
        else:
            logger.warning('http error', http_code)
    except error.URLError:
        logger.error('certificate verify failed: '
                     'unable to get local issuer certificate')

    return found_in_duden, duden_html, http_code

def _make_duden_url(word: str, duden_source) -> tuple[str, str]:
    if duden_source == 'dictionnary':
        url_uppercase = (f'https://www.duden.de/rechtschreibung/{replace_umlauts_2(word).capitalize()}')
        url_lowercase = (f'https://www.duden.de/rechtschreibung/{replace_umlauts_2(word).lower()}')
    elif duden_source == 'synonymes':
        url_uppercase = (f'https://www.duden.de/synonyme/{replace_umlauts_2(word).capitalize()}')
        url_lowercase = (f'https://www.duden.de/synonyme/{replace_umlauts_2(word).lower()}')
    else:
        raise RuntimeError('Duden source should be either "dictionnary" or "synonymes". '
                           f'Instead {duden_source} is passed')
                           
    return url_uppercase, url_lowercase


def get_json_from_pons_api(search_word: str,
                            filename: str,
                            ignore_cache: bool,
                            translate_en: bool = False,
                            translate_fr: bool = False):
    logger.debug('Looking in Pons cache')
    cache_path = DICT_DATA_PATH / 'cache' / filename
    json_file, json_cache_found = get_cache(cache_path)

    if json_cache_found and not ignore_cache:
        logger.debug('Reading Word from Pons Cache')
        json_data = json.loads(json_file)
        return json_data

    logger.info('Online searching for Word in Pons')
    status_code = 0
    while True:
        if translate_en:
            url = "https://api.pons.com/v1/dictionary?l=deen&q="
        elif translate_fr:
            url = "https://api.pons.com/v1/dictionary?l=defr&q="
        else:
            url = "https://api.pons.com/v1/dictionary?l=dedx&q="
        url += search_word
        logger.debug(f'URL: {url}')
        try:
            # TODO (1) save API secret as envirement var
            # Please consider using your own API (it's free)
            # this one is limited to 1000 request per month
            # (https://en.pons.com/open_dict/public_api/secret)
            api_path = DICT_DATA_PATH / 'PONS_API'
            api_secret = read_str_from_file(api_path)
            api_secret = api_secret.replace('\n', '')
            
            # TODO (2) Pylint Missing timeout argument for method 'requests.get' can cause your program to hang indefinitely
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
                write_str_to_file(DICT_DATA_PATH / 'cache' / filename, json.dumps(json_data), overwrite=True)
            else:
                logger.warning(
                    f'Status Code: {str(status_code)} {message}')
                json_data = ''

            return json_data

        except requests.exceptions.ConnectionError:
            notification.notify(title='No Connection to Mutter',
                                message='Retrying in 5s',
                                timeout=3)
            logger.warning('No connection to Mutter, retying in 10s')
            time.sleep(5)
            continue

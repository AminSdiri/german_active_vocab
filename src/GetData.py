from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import subprocess
from bs4.builder import HTML
import requests
import json
import time
from pathlib import Path
import urllib.request
from bs4 import BeautifulSoup as bs

from DudenProc import (
    create_synonyms_list,
    extract_def_section_from_duden)
from ProcessData import (
    append_word_seen_info,
    correct_num_indentation,
    create_translation_table,
    format_html,
    format_titel_html,
    treat_def_part)
from WordProcessing import update_words2hide

dict_path = Path.home() / 'Dictionnary'

# set up logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())  # .setFormatter(formatter)
logger.setLevel(logging.INFO)  # Levels: debug, info, warning, error, critical
formatter = logging.Formatter(
    '%(levelname)8s -- %(name)-15s line %(lineno)-4s: %(message)s')
logger.handlers[0].setFormatter(formatter)

# TODO use a database instead of files to save standarized Json and raw Json


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
    debug_mode: bool = False
    defined_html: HTML = ''
    duden_synonyms: list = field(default_factory=list)
    words2hide: list = field(default_factory=list)

    def __post_init__(self):

        self.process_input()

        self.log_word_in_wordlist_history()

        self.get_word_from_source()

    def process_input(self):
        logger.info("process_input")

        if self.word == 'debug':
            self.debug_mode = True
        if ' fr' in self.word or self.checkbox_fr:
            self.translate2fr = 1
            self.word = self.word.replace(' fr', '')
        if ' en' in self.word or self.checkbox_en:
            self.translate2en = 1
            self.word = self.word.replace(' en', '')
        if ' du' in self.word:
            self.get_from_duden = 1
            self.word = self.word.replace(' du', '')

        self.word = self.word.lower()

    def log_word_in_wordlist_history(self):
        now = datetime.now() - timedelta(hours=3)

        logger.info("log_word_in_wordlist_history")
        f = open(dict_path / 'Wordlist.txt', "a+")
        fileend = f.tell()
        f.seek(0)
        historyfile = f.read()
        f.seek(fileend)
        word_count = (historyfile.count('\n'+self.word+', ')
                      + historyfile.count('\n'+self.word+' ')
                      + historyfile.count('\n'+self.word+'\n'))
        f.write('\n'+self.word+', '+str(word_count) +
                ', '+now.strftime("%d.%m.%y"))
        f.close()

    def get_word_from_source(self):
        logger.info("get_word_from_source")
        translate = self.translate2fr or self.translate2en
        not_getting_from_pons = 0

        if self.translate2en:
            filename = replace_umlauts(self.word) + '_en'
        elif self.translate2fr:
            filename = replace_umlauts(self.word) + '_fr'
        else:
            filename = replace_umlauts(self.word)

        if (self.debug_mode):
            logger.debug('------------------Debug Mode------------------')
            with open(dict_path / 'debug.txt') as json_file:
                json_data = json.load(json_file)
        else:
            # Pons data
            json_data, status_code = self.get_json_from_pons_api(filename)

            if not translate:
                duden_soup, found_in_duden = self.get_duden_soup(filename)

                if self.get_from_duden:
                    if found_in_duden:
                        processed_html_duden = self.process_duden_data(
                            duden_soup)
                        self.defined_html = processed_html_duden
                    else:
                        self.defined_html = '<div align="center"><font size="5"'
                        ' face="Arial Black">Wort nicht gefunden '
                        ' in Duden</font></div>'
                        self.duden_synonyms = ''
                    return
            else:
                duden_soup = ''
                self.duden_synonyms = []

            if status_code != 200:
                if not translate:
                    if found_in_duden:
                        processed_html_duden = self.process_duden_data(
                            duden_soup)
                        self.defined_html = processed_html_duden
                    else:
                        self.defined_html = '<div align="center"><font size="5"'
                        ' face="Arial Black">Wort nicht gefunden '
                        'weder in Pons nor in Duden</font></div>'
                        self.duden_synonyms = ''
                else:
                    self.defined_html = '<div align="center"><font size="5" '
                    'face="Arial Black">Übersetzung '
                    'nicht gefunden in Pons</font></div>'
                not_getting_from_pons = 1

        if not not_getting_from_pons:
            self.convert_json2Html(json_data, translate, duden_soup)

        # return (not_getting_from_pons, json_data, duden_soup,
        #         self.defined_html, self.duden_synonyms, self.words2hide,
        #          translate)

    def get_json_from_pons_api(self, filename):
        logger.debug('Looking in Pons cache')
        json_file, json_cache_found = get_cache(filename)

        if json_cache_found:
            logger.debug('Reading Word from Pons Cache')
            json_data = json.loads(json_file)
            status_code = 200
            return json_data, status_code

        logger.info('Online searching for Word in Pms')
        status_code = 0
        pons_data_fetched = 0
        while not pons_data_fetched:
            logger.info('Online searching for Word in Pons')
            if self.translate2en:
                url = "https://api.pons.com/v1/dictionary?l=deen&q="
            elif self.translate2fr:
                url = "https://api.pons.com/v1/dictionary?l=defr&q="
            else:
                url = "https://api.pons.com/v1/dictionary?l=dedx&q="
            url += self.word
            logger.debug(f'URL: {url}')
            try:
                # TODO save API secret as envirement var
                api_path = Path.home() / 'PONS_API'
                with open(api_path, 'r') as api_file:
                    api_secret = api_file.read()
                api_secret = api_secret.replace('\n', '')
                # put your api-key from pons here
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
                    raw_data = raw_data.json()

                    with open(dict_path / 'Json' / filename, 'w') as outfile:
                        json.dump(raw_data, outfile)

                else:
                    logger.info(f'Status Code: {str(status_code)} {message}')
                    json_data = ''
                    return json_data, status_code

                pons_data_fetched = 1
            except requests.exceptions.ConnectionError:
                subprocess.Popen(
                    ['notify-send', 'No Connection to Mutter',
                     'Retrying in 10s'])
                logger.warning('No connection to Mutter, retying in 10s')
                time.sleep(10)
                continue

        json_data = json.loads(raw_data)
        return json_data, status_code

    def convert_json2Html(self, json_data, translate, soup):
        # TODO change function structure to render html from json using
        # a template.html
        # TODO use CSS file to format the rendred html
        logger.info("convert_json2Html")
        self.defined_html = bs('<html><body><p></p></body></html>', 'lxml')
        # trennbar = 0
        self.words_to_hide = self.word.split()

        if len(json_data) == 1:
            logger.info(f'language: {json_data[0]["lang"]}')
            json_data = json_data[0]["hits"]
        else:
            raise RuntimeError(
                'json API respense is expected to be of length 1')

        for rom_level in json_data:
            is_first_word_case = 1
            for arab_level in rom_level["roms"]:
                headword = arab_level["headword"]
                if 'wordclass' in arab_level:
                    wordclass = arab_level["wordclass"]
                else:
                    wordclass = 'Unknown'
                full_headword = arab_level["headword_full"]

                if full_headword != '':

                    self.words_to_hide = update_words2hide(
                        full_headword, self.words_to_hide)

                    full_headword = format_titel_html(
                        full_headword, is_first_word_case)
                    self.defined_html.body.append(full_headword.body.p)

                    is_first_word_case = 0

                for definition_block in arab_level["arabs"]:
                    block_number = definition_block["header"]
                    (indented_block_number,
                     self.defined_html, ignore) = correct_num_indentation(
                        block_number, self.defined_html)
                    if ignore:
                        continue
                    self.defined_html.body.append(indented_block_number)

                    previous_is_expl = 0
                    was_gra_here = 0
                    is_previous_gra = 0
                    content = definition_block["translations"]
                    if translate:
                        data_corpus = ''
                        for definition_part in content:
                            (self.defined_html,
                             data_corpus) = create_translation_table(
                                self.defined_html, definition_part,
                                data_corpus)
                    else:
                        for definition_part in content:
                            data_corpus = definition_part["source"]
                            if data_corpus != '':
                                for element in bs(data_corpus, 'lxml').body:
                                    if element is not None:
                                        (is_previous_gra,
                                         previous_is_expl,
                                         was_gra_here,
                                         self.defined_html) = treat_def_part(
                                            element,
                                            is_previous_gra,
                                            previous_is_expl,
                                            was_gra_here,
                                            self.defined_html)

        if not translate:
            self.defined_html = format_html(self.defined_html)

        if not translate:
            try:
                self.duden_synonyms = create_synonyms_list(soup)
                syn_part = ('<p><hr><font size="6" color="#ffb84d">'
                            'Synonyme</font><ul>')  # face
                for item in self.duden_synonyms:
                    syn_part += '<li>'+item+'</li>'
                syn_part += '</ul></p>'
                syn_soup = bs(syn_part, 'lxml')
                self.defined_html.body.append(syn_soup.body)
            except TypeError:
                self.duden_synonyms = ('<p><hr><font size="4" color="#ffb84d">'
                                       'Synonyme zu ' + self.word +
                                       ' in duden nicht gefunden</font><ul>')
        else:
            self.duden_synonyms = ''

        self.defined_html = append_word_seen_info(self.word, self.defined_html)

        self.defined_html.smooth()
        self.defined_html = str(self.defined_html)

        # TODO uncomment this block when restructuring
        # if word != 'machen':
        #     raise RuntimeError('still debugging,
        #                         no search allowed other than "machen"')
        # with open(dict_path / 'Last_innocent_html.html', 'r') as f:
        #     last_html = f.read()
        # assert last_html == defined_html

        with open(dict_path / 'Last_innocent_html.html', 'w') as f:
            f.write(self.defined_html)

        return self.words_to_hide, self.duden_synonyms, self.defined_html

    def get_duden_soup(self, filename):
        logger.debug('Looking in Duden cache')
        duden_html, duden_cache_found = get_cache(filename+'_duden')

        if duden_cache_found:
            logger.debug('Reading Word from Duden Cache')
            duden_soup = bs(duden_html, 'html.parser')
            found_in_duden = 1
            return duden_soup, found_in_duden

        logger.info('Online searching for Word in Duden')

        url_uppercase = ('https://www.duden.de/rechtschreibung/' +
                         replace_umlauts(self.word).capitalize())
        url_lowercase = ('https://www.duden.de/rechtschreibung/' +
                         replace_umlauts(self.word).lower())

        try_upper = 0

        try:
            with urllib.request.urlopen(url_lowercase) as response:
                # use whatever encoding as per the webpage
                duden_html = response.read().decode('utf-8')
            logger.debug('got Duden Html (lower)')

            with open(dict_path / 'Json' / (filename +
                                            '_duden'), 'w') as outfile:
                outfile.write(str(duden_html))
            found_in_duden = 1
        except urllib.error.URLError:
            logger.error('certificate verify failed: '
                         'unable to get local issuer certificate')
            duden_html = 'No certificate installed'
            found_in_duden = 0
        except urllib.request.HTTPError as e:
            found_in_duden = 0
            if e.code == 404:
                logger.warning(f"{url_lowercase} is not found")
                duden_html = 'Wort nicht gefunden'
                try_upper = 1
            elif e.code == 503:
                logger.warning(f'{url_lowercase} '
                               'base webservices are not available')
                pass
            else:
                logger.warning('http error', e)
                duden_html = 'Error 500'

        if try_upper:
            try:
                with urllib.request.urlopen(url_uppercase) as response:
                    # use whatever encoding as per the webpage
                    duden_html = response.read().decode('utf-8')
                logger.debug('got Duden Html (Upper)')
                with open(dict_path / 'Json' / (filename +
                                                '_duden'), 'w') as outfile:
                    outfile.write(str(duden_html))
                found_in_duden = 1
            except urllib.error.URLError:
                found_in_duden = 0
                logger.error('certificate verify failed: '
                             'unable to get local issuer certificate')
                duden_html = 'No certificate installed'
            except urllib.request.HTTPError as e:
                found_in_duden = 0
                if e.code == 404:
                    logger.warning(f"{url_uppercase} is not found")
                    duden_html = 'Wort nicht gefunden'
                elif e.code == 503:
                    logger.warning(f'{url_uppercase} '
                                   'base webservices are not available')
                    pass
                else:
                    logger.warning('http error', e)
                    duden_html = 'Error 500'

        duden_soup = bs(duden_html, 'html.parser')
        return duden_soup, found_in_duden

    def process_duden_data(self, soup):
        logger.info("process_duden_data")
        duden_list = extract_def_section_from_duden(soup)
        processed_html_duden = ('<div><font size="6" face="Arial Black">' +
                                self.word +
                                '</font></div><p>' +
                                duden_list +
                                '</p><br>(Wort von Duden gefunden)</p>')
        self.duden_synonyms = create_synonyms_list(soup)
        if self.duden_synonyms is not None:
            syn_part = (
                '<p><hr><font size="6" color="#ffb84d">Synonyme</font><ul>'
            )  # face
            for item in self.duden_synonyms:
                syn_part += '<li>'+item+'</li>'
            syn_part += '</ul></p>'
            processed_html_duden += syn_part
        return processed_html_duden


def get_cache(filename):
    try:
        cache_path = dict_path / 'Json' / (filename)
        with open(cache_path, 'r') as cache_file:
            cache_file_content = cache_file.read()
        cache_found = 1
        logger.info('Cached file found')
    except FileNotFoundError:
        logger.debug(f'No cached file found in {cache_path}')
        cache_found = 0
        cache_file_content = ''
    return cache_file_content, cache_found


def replace_umlauts(word):
    normalized_word = word.replace("ü", "ue")\
        .replace("ö", "oe")\
        .replace("ä", "ae")\
        .replace("ß", "sz")
    return normalized_word

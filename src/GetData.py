from dataclasses import dataclass, field
from datetime import datetime, timedelta
import subprocess
from bs4.builder import HTML
import pandas as pd
import requests
import json
import time
from pathlib import Path
from urllib import request, error
from bs4 import BeautifulSoup as bs
from jinja2 import Environment, PackageLoader, Template

from DudenProc import (
    create_synonyms_list,
    extract_def_section_from_duden)
from ProcessData import (
    append_word_seen_info_toHtml,
    correct_num_indentation,
    create_translation_table,
    format_html,
    format_titel_html,
    treat_def_part,
    treat_def_part_new)
from WordProcessing import update_words_to_hide
from utils import set_up_logger

dict_path = Path.home() / 'Dictionnary'

logger = set_up_logger(__name__)

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
    defined_html: HTML = ''
    duden_synonyms: list = field(default_factory=list)
    words_to_hide: list = field(default_factory=list)

    def __post_init__(self):

        self.process_input()

        self.log_word_in_wordlist_history()

        self.get_word_from_source()

        if self.get_from_duden:
            self.generate_duden_html()
            return

        translate = self.translate2fr or self.translate2en

        if not self._found_in_pons:
            if not translate:
                self.generate_duden_html()
            else:
                with open('src/templates/not_found_pons_translation.html') as f:
                    tmpl = Template(f.read())
                self.defined_html = tmpl.render(word=self.word)
            return

        self.standerize_dict(translate)

        self.add_synonymes_from_duden(translate)

        word_info = self.get_seen_word_info()

        with open('standerised.json', 'w') as f:
            f.write(str(json.dumps(self.dict_dict)))

        # TODO save dict_dict
        if translate:
            self.render_html_from_dict('translation')
        else:
            self.render_html_from_dict('definition', word_info)

        return self.words_to_hide, self.duden_synonyms, self.defined_html

    def get_seen_word_info(self):
        df = pd.read_csv(dict_path / 'wordlist.csv')
        df.set_index('Word', inplace=True)
        word_is_already_saved = self.word in df.index
        word_info = {'word': self.word}
        if word_is_already_saved:
            word_info["Previous_date"] = df.loc[self.word, "Previous_date"]
            word_info["Next_date"] = df.loc[self.word, "Next_date"]
        return word_info

    def add_synonymes_from_duden(self, translate):
        if not translate:
            try:
                synonyms_list = create_synonyms_list(self._duden_soup)
                self.dict_dict["synonymes"] = synonyms_list
            except TypeError:
                logger.warning('Type Error in create_synonyms_list >> Check it!')

    def standerize_dict(self, translate):
        logger.info("standerize_dict")

        self.words_to_hide = self.word.split()

        if not translate and len(self._pons_json) == 1:
            logger.info(f'language: {self._pons_json[0]["lang"]}')
            json_data = self._pons_json[0]["hits"]
            self.parse_json_data(json_data, translate)
        elif translate and len(self._pons_json) == 1:
            logger.info(f'language: {self._pons_json[0]["lang"]}')
            json_data = self._pons_json[0]["hits"]
            self.parse_json_data(json_data, translate)
            self.dict_dict = [
                {'lang': json_data[0]['lang'],
                 'content': self.dict_dict},
            ]
        elif translate and len(self._pons_json) == 2:
            logger.info(f'language: {self._pons_json[0]["lang"]}')
            json_data_1 = self._pons_json[0]["hits"]
            self.parse_json_data(json_data_1, translate)
            json_data_2 = self._pons_json[1]["hits"]
            self.parse_json_data(json_data_2, translate)
            # language=json_data[0]['lang']
            self.dict_dict = [
                {'lang': self._pons_json[0]['lang'],
                 'content': self.dict_dict_1},
                {'lang': self._pons_json[1]['lang'],
                 'content': self.dict_dict_2}
            ]
        else:
            raise RuntimeError(
                'json API respense is expected to be of length 1 or only for translations 2')

    def generate_duden_html(self):
        if self._found_in_duden:
            processed_html_duden = self.process_duden_data(
                self._duden_soup)
            self.defined_html = processed_html_duden
            self.defined_html = bs(self.defined_html, 'lxml')
            self.defined_html = append_word_seen_info_toHtml(
                self.word, self.defined_html)
            self.defined_html.smooth()
            self.defined_html = str(self.defined_html)
        else:
            with open('src/templates/not_found_pons_duden.html') as f:
                tmpl = Template(f.read())
            self.defined_html = tmpl.render(word=self.word)
            self.duden_synonyms = ''

    def process_input(self):
        logger.info("process_input")

        if ' fr' in self.word or self.checkbox_fr:
            self.translate2fr = True
            self.word = self.word.replace(' fr', '')
        elif ' en' in self.word or self.checkbox_en:
            self.translate2en = True
            self.word = self.word.replace(' en', '')
        elif ' du' in self.word:
            self.get_from_duden = True
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

        if self.translate2en:
            filename = replace_umlauts(self.word) + '_en'
        elif self.translate2fr:
            filename = replace_umlauts(self.word) + '_fr'
        else:
            filename = replace_umlauts(self.word)

        # Pons data
        self._pons_json, self._found_in_pons = self.get_json_from_pons_api(
            filename)

        # Duden data
        if not translate:
            self._duden_soup, self._found_in_duden = self.get_duden_soup(
                filename+'_duden')
        else:
            self._duden_soup = ''
            self._found_in_duden = False

    def get_json_from_pons_api(self, filename: str):
        logger.debug('Looking in Pons cache')
        json_file, json_cache_found = get_cache(filename)

        if json_cache_found:
            logger.debug('Reading Word from Pons Cache')
            json_data = json.loads(json_file)
            status_code = 200
            return json_data, status_code

        logger.info('Online searching for Word in Pons')
        status_code = 0
        while True:
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
                    json_data = raw_data.json()

                    with open(dict_path / 'Json' / filename, 'w') as outfile:
                        json.dump(json_data, outfile)
                else:
                    logger.warning(
                        f'Status Code: {str(status_code)} {message}')
                    json_data = ''

                return json_data, status_code == 200

            except requests.exceptions.ConnectionError:
                subprocess.Popen(
                    ['notify-send', 'No Connection to Mutter',
                     'Retrying in 10s'])
                logger.warning('No connection to Mutter, retying in 10s')
                time.sleep(10)
                continue

    def render_html_from_dict(self, html_type: str, word_info={}):
        env = Environment(
            loader=PackageLoader("tests", "templates"),
            # autoescape=select_autoescape(["html", "xml"]),
        )

        env.filters["is_list"] = is_list
        if html_type == 'definition':
            env.filters["treat_class"] = treat_class_def
            path_str = 'src/templates/definition.html'
            with open(path_str) as f:
                tmpl = env.from_string(f.read())
                self.defined_html = tmpl.render(
                    dict_dict=self.dict_dict,
                    word_info=word_info)
        elif html_type == 'translation':
            env.filters["treat_class"] = treat_class_trans
            path_str = 'src/templates/translation.html'
            with open(path_str) as f:
                tmpl = env.from_string(f.read())
                self.defined_html = tmpl.render(
                    lang_dict=self.dict_dict)

        with open(dict_path / 'renderd_innocent_html.html', 'w') as f:
            f.write(self.defined_html)

        classes = [value
                   for element in bs(self.defined_html, "html.parser").find_all(class_=True)
                   for value in element["class"]]

        print('classes: ', set(classes))

    def parse_json_data(self, json_data, translate):
        '''
        convert json_data to standerized dict

        standerized dict structure:
        {
            'content':
            [   # ROMS
                {
                    'headword': '',
                    'wordclass': '',  # verb/adjektiv/name/adverb
                    'flexion': '',  # [present, präteritum, perfekt]
                    'genus': '',  # der/die/das
                    ...
                    'word_subclass':
                    [   # ARABS
                        {
                            'verbclass': '',  # with_obj/without_obj
                            ...
                            'def_blocks':
                            [   # BLOCKS
                                {
                                    'header_num': '',   # 1. /2. ...
                                    'grammatical_construction': '',  # jd macht jemanden
                                    'definition': '',
                                    'example': '',  # []
                                    'rhetoric': ''  # pejorativ...
                                    'style': '',  # gebrauch
                                    # BUG "style": "<acronym title=\"synonym\">\u2248</acronym> entbl\u00f6\u00dfen"
                                    ...
                                },
                                {..}, ..
                            ]
                        },
                        {..}, ..
                    ]
                },
                {..}, ..
            ],
            'synonymes': [],
            'custom_examples':
                {
                    'german': [],
                    'english': []
                }
        }
        '''

        dict_dict = [None] * len(json_data)

        for rom_idx, rom_level in enumerate(json_data):
            if "roms" in rom_level:
                dict_dict[rom_idx] = dict()
                dict_dict[rom_idx]["word_subclass"] = [
                    None] * len(rom_level["roms"])
                for arab_idx, arab_level in enumerate(rom_level["roms"]):
                    dict_dict[rom_idx]["word_subclass"][arab_idx] = dict()

                    headword = arab_level["headword"]
                    headword = remove_from_str(
                        headword, [b'\xcc\xa3', b'\xcc\xb1', b'\xc2\xb7'])
                    self.update_rom_lvl_entry(
                        dict_dict, rom_idx, 'headword', headword)

                    wordclass = arab_level["wordclass"] if 'wordclass' in arab_level else ''
                    self.update_rom_lvl_entry(
                        dict_dict, rom_idx, 'wordclass', wordclass)

                    full_headword = arab_level["headword_full"]
                    if full_headword != '':
                        headword_soup = bs(full_headword, 'lxml')
                        for element in headword_soup.find_all(class_=True):
                            key_class = element["class"]
                            if len(key_class) == 1:
                                key_class = key_class[0]
                            else:
                                raise Exception
                            if key_class == 'separator':
                                # ignoring classes could be done hear or in treat_class() fct
                                continue
                            if key_class in ['headword', 'wordclass', 'flexion', 'genus']:
                                value = ''.join(str(x)
                                                for x in element.contents)
                                self.update_rom_lvl_entry(
                                    dict_dict, rom_idx, key_class, value)
                            elif key_class in dict_dict[rom_idx]["word_subclass"][arab_idx]:
                                continue
                            else:
                                if len(dict_dict[rom_idx]["word_subclass"][arab_idx]) > 1:
                                    logger.warning(
                                        f'subclass entry already have a key: {dict_dict[rom_idx]["word_subclass"][arab_idx].keys()}')
                                # exemple (style: 'inf') isn't supposed to be appended here sondern, it have to go to it's children
                                value = ''.join(str(x)
                                                for x in element.contents)
                                dict_dict[rom_idx]["word_subclass"][arab_idx][key_class] = value

                        # TODO words_to_hide gets dict_dict entries
                        self.words_to_hide = update_words_to_hide(
                            full_headword, self.words_to_hide)

                    dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'] = [
                    ]
                    def_idx = 0
                    for definition_block in arab_level["arabs"]:
                        dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'].append(
                            dict())

                        block_number = definition_block["header"]
                        if ('Zusammen- oder Getrenntschreibung' in block_number or
                            'Zusammenschreibung' in block_number or
                                'Getrennt' in block_number):
                            continue

                        dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx]["header_num"] = block_number

                        gra_was_in_block = False
                        previous_class = ''
                        content = definition_block["translations"]
                        if translate:
                            data_corpus = ''
                            for definition_part in content:
                                datasource = definition_part["source"]
                                datatarget = definition_part["target"]
                                self.add_to_dict_dict(
                                    dict_dict, rom_idx, arab_idx, 'source', def_idx, datasource)
                                self.add_to_dict_dict(
                                    dict_dict, rom_idx, arab_idx, 'target', def_idx, datatarget)
                        else:
                            for definition_part in content:
                                data_corpus = definition_part["source"]
                                source_soup = bs(data_corpus, 'lxml')
                                for element in source_soup.find_all(class_=True):
                                    key_class = element["class"]
                                    if len(key_class) == 1:
                                        key_class = key_class[0]
                                    else:
                                        raise Exception
                                    source_content = ''.join(
                                        str(x) for x in element.contents)
                                    if (previous_class == 'grammatical_construction' or previous_class == 'idiom_proverb') and not (key_class == 'grammatical_construction' or key_class == 'idiom_proverb'):
                                        gra_was_in_block = True
                                    if ((previous_class == 'example' and key_class != 'example') or
                                            (gra_was_in_block and (key_class == 'grammatical_construction' or key_class == 'idiom_proverb'))):
                                        def_idx += 1
                                        dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'].append(
                                            dict())
                                        dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx]["header_num"] = ''
                                    previous_class = key_class
                                    self.add_to_dict_dict(
                                        dict_dict, rom_idx, arab_idx, key_class, def_idx, source_content)
                        def_idx += 1

            elif "source" in rom_level:
                gra_was_in_block = False
                previous_class = ''
                def_idx = 0
                data_corpus = rom_level["source"]

                dict_dict[rom_idx] = dict()
                dict_dict[rom_idx]["word_subclass"] = [None]
                arab_idx = 0
                dict_dict[rom_idx]["word_subclass"][arab_idx] = dict()
                dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'] = [
                    None]
                dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx] = dict(
                )

                source_soup = bs(data_corpus, 'lxml')
                for element in source_soup.find_all(class_=True):
                    key_class = element["class"]
                    if len(key_class) == 1:
                        key_class = key_class[0]
                    else:
                        raise Exception
                    source_content = ''.join(
                        str(x) for x in element.contents)
                    if (previous_class == 'grammatical_construction' or previous_class == 'idiom_proverb') and not (key_class == 'grammatical_construction' or key_class == 'idiom_proverb'):
                        gra_was_in_block = True
                    if ((previous_class == 'example' and key_class != 'example') or
                            (gra_was_in_block and (key_class == 'grammatical_construction' or key_class == 'idiom_proverb'))):
                        def_idx += 1
                        dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'].append(
                            dict())
                        dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx]["header_num"] = ''
                    previous_class = key_class
                    self.add_to_dict_dict(
                        dict_dict, rom_idx, arab_idx, key_class, def_idx, source_content)
            else:
                raise KeyError(
                    '"roms" or (in the worst case) "source" key is expected"')

        if translate:
            if hasattr(self, 'dict_dict'):
                self.dict_dict_1 = self.dict_dict
                self.dict_dict_2 = dict_dict
                self.dict_dict = ''
            else:
                self.dict_dict = dict_dict
        else:
            self.dict_dict = {'content': dict_dict,
                              'synonymes': [],
                              'custom_examples': {
                                    'german': [],
                                    'english': []
                                }
                              }

    def add_to_dict_dict(self, dict_dict, rom_idx, arab_idx, key_class, def_idx, source_content):
        if key_class in dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx]:
            # raise Exception(f'{key_class} element cannot be overwritten')
            if not isinstance(dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx][key_class], list):
                dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx][key_class] = [
                    dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx][key_class]]
            dict_dict[rom_idx]["word_subclass"][arab_idx]['def_blocks'][def_idx][key_class].append(
                source_content)
        else:
            dict_dict[rom_idx]["word_subclass"][arab_idx][
                'def_blocks'][def_idx][key_class] = source_content

    def update_rom_lvl_entry(self, dict_dict, rom_idx, key, value):
        if key in dict_dict[rom_idx]:
            logger.debug(
                f'Key: {key}\nOld value: {dict_dict[rom_idx][key]}\nNew value: {value}')
            if dict_dict[rom_idx][key] == '':
                dict_dict[rom_idx][key] = value
        else:
            dict_dict[rom_idx][key] = value

    def get_duden_soup(self, filename):
        logger.debug('Looking in Duden cache')
        duden_html, duden_cache_found = get_cache(filename)

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
            with request.urlopen(url_lowercase) as response:
                # use whatever encoding as per the webpage
                duden_html = response.read().decode('utf-8')
            logger.debug('got Duden Html (lower)')

            with open(dict_path / 'Json' / filename, 'w') as outfile:
                outfile.write(str(duden_html))
            found_in_duden = 1
        except request.HTTPError as e:
            found_in_duden = 0
            if e.code == 404:
                logger.warning(f"{url_lowercase} is not found")
                duden_html = '404 Wort nicht gefunden'
                try_upper = 1
            elif e.code == 503:
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
            found_in_duden = 0

        if try_upper:
            try:
                with request.urlopen(url_uppercase) as response:
                    # use whatever encoding as per the webpage
                    duden_html = response.read().decode('utf-8')
                logger.debug('got Duden Html (Upper)')
                with open(dict_path / 'Json' / filename, 'w') as outfile:
                    outfile.write(str(duden_html))
                found_in_duden = 1
            except request.HTTPError as e:
                found_in_duden = 0
                if e.code == 404:
                    logger.warning(f"{url_uppercase} is not found")
                    duden_html = '404 Wort nicht gefunden'
                elif e.code == 503:
                    logger.warning(f'{url_uppercase} '
                                   'base webservices are not available')
                    pass
                else:
                    logger.warning('http error', e)
                    duden_html = 'Error 500'
            except error.URLError:
                found_in_duden = 0
                logger.error('certificate verify failed: '
                             'unable to get local issuer certificate')
                duden_html = 'No certificate installed'

        duden_soup = bs(duden_html, 'html.parser')
        return duden_soup, found_in_duden

    def process_duden_data(self, soup):
        logger.info("process_duden_data")
        duden_list = extract_def_section_from_duden(soup)
        # TODO: generate json file from duden_html
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


def remove_from_str(string: str, substrings: list):
    string = string.encode(encoding='UTF-8', errors='strict')
    for substring in substrings:
        string = string.replace(substring, b'')
    return string.decode('utf-8')


def is_list(value):
    return isinstance(value, list)


def treat_class_def(value, class_name, previous_class_name, previous_class_value):
    '''workaround because of css21'''
    logger.info(f"treating class: {class_name}")

    # Nomen

    if class_name == 'wordclass':
        if value == 'noun':
            value = 'Nomen'
        # Ignoring
        return ''

    # bs_class = 'wrdclass'
    # # try:
    # titel_word = headword_full.find(**{"class": "wordclass"})
    # if not(titel_word is None or titel_word.contents == []):
    #     titel_word.wrap(headword_full.new_tag(bs_class))
    #     if is_first_word_case:
    #         titel_word.insert_before(headword_full.new_tag('br'))
    #     titel_word.insert_before(headword_full.new_tag('br'))
    #     titel_word.insert_before('\xa0•\xa0')
    #     headword_full.find(bs_class)['size'] = 5
    #     headword_full.find(bs_class)['face'] = 'Arial'
    #     headword_full.find(bs_class).name = 'font'

    if class_name == 'flexion':
        value = '[' + value[1:] if value[0] == '<' else value
        value = value[:-1] if value[-1] == '>' else value
        # value = value.replace('&lt;', '[')\
        #              .replace('&gt;', ']')\
        #              .replace('<', '[')\
        #              .replace('>', ']')
        return value

    # bs_class = 'conj'
    # # try:
    # titel_word = headword_full.find(**{"class": "flexion"})
    # if not(titel_word is None):
    #     titel_word.wrap(headword_full.new_tag(bs_class))
    #     headword_full.find(bs_class)['size'] = 4
    #     headword_full.find(bs_class)['face'] = 'Arial'
    #     if not is_first_word_case:
    #         headword_full.find(bs_class).decompose()
    #     else:
    #         headword_full.find(bs_class).name = 'font'
    #         titel_word.wrap(headword_full.new_tag('b'))

    if class_name == 'genus':
        if value == 'der':
            value = '<font color="#0099cc">' + value + '</font>'
        elif value == 'die':
            value = '<font color="#ff99ff">' + value + '</font>'
        elif value == 'das':
            value = '<font color="#d24dff">' + value + '</font>'
        return value

    # bs_class = 'gen'
    # # try:
    # titel_word = headword_full.find(**{"class": "genus"})
    # if not(titel_word is None):
    #     titel_word.wrap(headword_full.new_tag(bs_class))
    #     headword_full.find(bs_class)['size'] = 5
    #     headword_full.find(bs_class)['face'] = 'Arial'
    #     if not is_first_word_case:
    #         headword_full.find(bs_class).decompose()
    #     else:
    #         headword_full.find(bs_class).name = 'font'
    #         titel_word.wrap(headword_full.new_tag('b'))

    if class_name == 'verbclass':
        value = value.replace('with SICH', 'mit sich')\
                     .replace('with obj', 'mit obj')\
                     .replace('without obj', 'ohne obj')
        return value

    # bs_class = 'vrbclass'
    # # try:
    # titel_word = headword_full.find(**{"class": "verbclass"})
    # if not(titel_word is None):
    #     titel_word.wrap(headword_full.new_tag(bs_class))
    #     headword_full.find(bs_class)['size'] = 5
    #     headword_full.find(bs_class)['face'] = 'Arial'
    #     headword_full.find(bs_class).name = 'font'
    # # except:
    # #     pass

    if class_name == 'header_num':
        value = '\xa0\xa0\xa0\xa0' + value
        if len(value) > 10:
            # TODO long headers probably contains def or another important element,
            # treat it the right was when constructing th dict_dict
            value = '<font color="#ffff00">' + value + \
                ' (Warning)' + '</font>' + '<br>\xa0\xa0\xa0\xa0'
        if 'Zusammenschreibung' in value:
            value = ''
        return value

    if class_name == 'grammatical_construction':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0ⓖ ' + value
        else:
            value = 'ⓖ ' + value
        value += '\xa0'
        return value

    if class_name == 'idiom_proverb':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0ⓖ ' + value
        else:
            value = 'ⓖ ' + value
        value += '\xa0'
        return value

    if class_name == 'synonym':
        value = '≈ ' + value
        return value

    if class_name == 'opposition':
        value = '≠ ' + value
        return value

    if class_name == 'definition':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0' + value
        value += '\xa0'
        return value

    if class_name == 'sense':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0' + value
        value += '\xa0'
        return value

    if class_name == 'example':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0' + value
        return value

    if class_name == 'restriction':
        value += '\xa0'
        return value

    if class_name == 'style':
        value = value.replace('>inf', '>umg')
        return value

    if class_name == 'case':
        # ignoring because already exists in grammatical_construction
        return ''

    if class_name == 'rhetoric':
        # pejorativ...
        return value

    logger.warning(f"Class: {class_name} not treated!")
    return value


def treat_class_trans(value, class_name, previous_class_name, previous_class_value):
    '''workaround because of css21'''
    # TODO ken source feha class w target mafihech, wrapi target fel class mta3 source zeda

    logger.info(f"treating class: {class_name}")

    # TODO ken source fih headword na7eha l'class w khali lkelma

    if class_name == 'source':
        # TODO this treatement should be before standerised json
        soup = bs(value, 'lxml')
        headword = soup.find_all(**{"class": "headword"})
        if headword:
            for elem in headword:
                elem.unwrap()
            soup.html.unwrap()
            soup.body.unwrap()
            value = str(soup)
        return value

    if class_name == 'wordclass':
        if value == 'noun':
            value = 'Nomen'
        # Ignoring
        return ''

    if class_name == 'flexion':
        value = '[' + value[1:] if value[0] == '<' else value
        value = value[:-1] if value[-1] == '>' else value
        return value

    if class_name == 'genus':
        if value == 'der':
            value = '<font color="#0099cc">' + value + '</font>'
        elif value == 'die':
            value = '<font color="#ff99ff">' + value + '</font>'
        elif value == 'das':
            value = '<font color="#d24dff">' + value + '</font>'
        return value

    if class_name == 'verbclass':
        value = value.replace('with SICH', 'mit sich')\
                     .replace('with obj', 'mit obj')\
                     .replace('without obj', 'ohne obj')
        return value

    if class_name == 'header_num':
        value = '\xa0\xa0\xa0\xa0' + value
        if 'Zusammenschreibung' in value:
            value = ''
        return value

    if class_name == 'grammatical_construction':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0ⓖ ' + value
        else:
            value = 'ⓖ ' + value
        value += '\xa0'
        return value

    if class_name == 'idiom_proverb':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0ⓖ ' + value
        else:
            value = 'ⓖ ' + value
        value += '\xa0'
        return value

    if class_name == 'synonym':
        value = '≈ ' + value
        return value

    if class_name == 'opposition':
        value = '≠ ' + value
        return value

    if class_name == 'definition':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0' + value
        value += '\xa0'
        return value

    if class_name == 'sense':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0' + value
        value += '\xa0'
        return value

    if class_name == 'example':
        if previous_class_name != 'header_num':
            value = '<br>\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0' + value
        return value

    if class_name == 'restriction':
        value += '\xa0'
        return value

    if class_name == 'style':
        value = value.replace('>inf', '>umg')
        return value

    if class_name == 'case':
        # ignoring because already exists in grammatical_construction
        return ''

    if class_name == 'rhetoric':
        # pejorativ...
        return value

    logger.warning(f"Class: {class_name} not treated!")
    return value


def replace_umlauts(word: str):
    """[summary]

    Args:
        word (str): [description]

    Returns:
        [str]: strings without Umlaut
    """
    normalized_word = word.replace("ü", "ue")\
        .replace("ö", "oe")\
        .replace("ä", "ae")\
        .replace("ß", "sz")
    return normalized_word

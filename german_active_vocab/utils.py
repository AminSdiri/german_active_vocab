from datetime import datetime, timedelta
import logging
from logging import Logger
import os
from pathlib import Path
import string
import pandas as pd
from bs4 import BeautifulSoup as bs
from plyer import notification
import argparse

# from autologging import TRACE

from settings import DICT_DATA_PATH


def set_up_logger(logger_name, level=logging.INFO) -> Logger:

    # TODO (5) remove to reset level to INFO
    # Levels: debug, info, warning, error, critical
    # level = TRACE
    # level = logging.DEBUG
    level = logging.INFO

    logger_obj = logging.getLogger(logger_name)
    logger_obj.addHandler(logging.StreamHandler())
    logger_obj.setLevel(level)
    formatter = logging.Formatter(
        '%(levelname)8s -- %(asctime)s -- %(name)-15s.%(funcName)-40s line %(lineno)-4s: %(message)s')
    logger_obj.handlers[0].setFormatter(formatter)
    return logger_obj


logger = set_up_logger(__name__)

def get_command_line_args() -> "Namespace":
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--word')
    parser.add_argument('-g', '--ger')
    parser.add_argument('-e', '--eng')
    args = parser.parse_args()
    return args

# TODO (2) auto-logging 
# def wrap(pre, post):
# 	""" Wrapper """
# 	def decorate(func):
# 		""" Decorator """
# 		def call(*args, **kwargs):
# 			""" Actual wrapping """
# 			pre(func)
# 			result = func(*args, **kwargs)
# 			post(func)
# 			return result
# 		return call
# 	return decorate

# def entering(func):
# 	""" Pre function logging """
# 	logger.debug("Entered %s", func.__name__)

# def exiting(func):
# 	""" Post function logging """
# 	logger.debug("Exited  %s", func.__name__)

# @wrap(entering, exiting)

# or @traced(logger)


def get_cache(cache_path) -> tuple[str, bool]:
    try:
        cache_file_content = read_str_from_file(cache_path)
        cache_found = True
        logger.info('Cached file found')
    except FileNotFoundError:
        logger.debug(f'No cached file found in {cache_path}')
        cache_found = False
        cache_file_content = ''
    return cache_file_content, cache_found


def sanitize_word(word: str) -> str:
    """
    Sanitize unicode word for use as filename
    Ascii letters and underscore are kept unchanged.
    Other characters, umlauts for example are replaced with "-u{charccode}-" string.
    """
    allowed_chars = string.ascii_letters + "_"

    def sanitize_char(char: str) -> str:
        if char in allowed_chars:
            return char
        return "-u" + str(ord(char)) + "-"

    return "".join(sanitize_char(char) for char in word)


def replace_umlauts_1(word: str) -> str:
    # temporary
    """for duden links

    Args:
        word (str): [description]

    Returns:
        [str]: strings without Umlaut
    """
    normalized_word = word.replace("ü", "ue")\
                        .replace("ö", "oe")\
                        .replace("ä", "ae")\
                        .replace("ß", "ss")
    return normalized_word


def replace_umlauts_2(word: str) -> str:
    """for duden links

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

def ignore_headers(quiz_text: str) -> tuple[list[int], int]:
    logger.info("create_ignore_list")
    quiz_list = bs(quiz_text, "lxml").find_all('p')
    nb_parts = len(quiz_list)
    ignore_list = [1]*len(quiz_list)
    for index, _ in enumerate(quiz_list):
        quiz_list_lvl2 = quiz_list[index].find_all('span')
        for item in quiz_list_lvl2:
            contain_example = 'italic' in item['style']
            if contain_example:
                ignore_list[index] = 0
                continue
        if quiz_list[index].find_all('i'):
            ignore_list[index] = 0
    # logger.debug('Indexes to Ignore', ignore_list)
    return ignore_list, nb_parts

def remove_from_str(text: str, substrings: list):
    # DONE (1) use with long replace chains
    text = text.encode(encoding='UTF-8', errors='strict')
    for substring in substrings:
        text = text.replace(substring, b'')
    return text.decode('utf-8')

def read_dataframe_from_file(parts=False) -> pd.DataFrame:
    filename = 'wordlist.csv' if not parts else 'wordpart_list.csv'
    df = pd.read_csv(DICT_DATA_PATH / filename)
    indexname = 'Word' if not parts else 'Wordpart'
    df.set_index(indexname, inplace=True)
    df['Next_date'] = pd.to_datetime(df['Next_date'])
    df['Created'] = pd.to_datetime(df['Created'])
    df['Previous_date'] = pd.to_datetime(df['Previous_date'])
    return df

def update_dataframe_file(word, quiz_text, full_text) -> None:
    logger.info("update dataframe file")

    quiz_parts = bs(quiz_text, "lxml").find_all('p')
    full_parts = bs(full_text, "lxml").find_all('p')
    assert len(quiz_parts) == len(full_parts)

    ignore_list, nb_parts = ignore_headers(quiz_text)
    logger.debug(f'Ignore List: {ignore_list}')

    # TODO (3) STRUCT minimize reading and writing to disk?
    wordlist_df = read_dataframe_from_file(parts=False)
    wordlist_df.loc[word, 'Focused'] = 1
    wordlist_df.to_csv(DICT_DATA_PATH / 'wordlist.csv')

    general_EF = wordlist_df.loc[word, 'EF_score']

    focus_df = read_dataframe_from_file(parts=True)
    now = datetime.now() - timedelta(hours=3)
    for k in range(0, nb_parts):
        wordpart = word+' '+str(k)
        focus_df.loc[wordpart, "Word"] = word
        focus_df.loc[wordpart, "Repetitions"] = 0
        focus_df.loc[wordpart, "EF_score"] = general_EF
        focus_df.loc[wordpart, "Interval"] = 6
        focus_df.loc[wordpart, "Previous_date"] = now
        focus_df.loc[wordpart, "Created"] = now
        # insixdays = now + timedelta(days=6)
        focus_df.loc[wordpart, "Next_date"] = now # insixdays
        focus_df.loc[wordpart, "Part"] = k
        focus_df.loc[wordpart, "Ignore"] = ignore_list[k]
    focus_df.to_csv(DICT_DATA_PATH / 'wordpart_list.csv')

    notification.notify(title=f'"{word}"',
                            message='Added to Focus Mode',
                            timeout=2)
    logger.info(f'{word} switched to Focus Mode')

def fix_html_with_custom_example(html_text: str) -> str:
    # TODO (5) Vorübergehend, delete after all htmls are updated
    # TODO (2) run in loop and then delete here
    logger.info("fix_html_with_custom_example")

    html_text = html_text.replace('</body></html><br><br>',
                                  '<br><p style=" margin-top:12px; '
                                  'margin-bottom:12px; margin-left:0px; '
                                  'margin-right:0px; -qt-block-indent:0; '
                                  'text-indent:0px;">')
    if html_text[-4:] == '</i>':
        html_text += '</p></body></html>'

    return html_text

def read_text_from_files(word: str) -> tuple[str, str]:
    quiz_file_path = DICT_DATA_PATH / 'html' / f'{word}.quiz.html'
    quiz_text = read_str_from_file(quiz_file_path)

    full_file_path = DICT_DATA_PATH / 'html' / f'{word}.html'
    full_text = read_str_from_file(full_file_path)

    full_text = fix_html_with_custom_example(full_text)
    write_str_to_file(full_file_path, full_text, overwrite=True)

    quiz_text = fix_html_with_custom_example(quiz_text)
    write_str_to_file(quiz_file_path, quiz_text, overwrite=True)

    return full_text, quiz_text

def read_str_from_file(path: Path) -> str:
    # word (path.stem) is sanitized before therefore not needed
    # path_str = sanitize_word(str(path))
    # path = Path(path_str)
    # try:
    with open(path, 'r', encoding="utf8") as file:
        file_string = file.read()
    # clashes with cache reading
    # except FileNotFoundError:
    #     logger.error(f'Path not Found: "{path}"')
    #     file_string = ''

    return file_string


def write_str_to_file(path: Path, content: str, overwrite=False, notification_list: list = None) -> None:
    # TODO (3) Overwrite files?, in which case I want to do that
    # in which case I want to reset DF entries
    # path_str = str(path)
    # path = Path(path_str)

    # Prevent unintentional overwriting
    if os.path.exists(path) and not overwrite:
        notification.notify(title='Overwriting is not allowed',
                            message=f'Path: {path} exists',
                            timeout=20)
        raise RuntimeError(f'Path "{path}" exists and overwriting is not allowed')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    if notification_list:
        notification.notify(title=notification_list[0],
                            message='\n'.join(notification_list[1:]),
                            timeout=5)

    # TODO (4) add try, except and notify

    # try:
    #     %%%%%%%%%%%%%
    # except:
    #     logger.error('Error writing')
    #     # notify
    #     pass


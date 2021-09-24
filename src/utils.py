from datetime import datetime, timedelta
import logging
from pathlib import Path
import subprocess

dict_data_path = Path.home() / 'Dictionnary'


def set_up_logger(logger_name, level=logging.INFO):

    # TODO (4) remove to reset level to INFO
    level = logging.WARNING

    logger = logging.getLogger(logger_name)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(level)
    # Levels: debug, info, warning, error, critical
    formatter = logging.Formatter(
        '%(levelname)8s -- %(name)-15s line %(lineno)-4s: %(message)s')
    logger.handlers[0].setFormatter(formatter)
    return logger


logger = set_up_logger(__name__)


def get_cache(cache_path):
    try:
        cache_file_content = read_str_from_file(cache_path)

        cache_found = 1
        logger.info('Cached file found')
    except FileNotFoundError:
        logger.debug(f'No cached file found in {cache_path}')
        cache_found = 0
        cache_file_content = ''
    return cache_file_content, cache_found


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
        .replace("ß", "ss")
    return normalized_word


def replace_umlauts_2(word: str):
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


def remove_from_str(string: str, substrings: list):
    # DONE (1) use with long replace chains
    string = string.encode(encoding='UTF-8', errors='strict')
    for substring in substrings:
        string = string.replace(substring, b'')
    return string.decode('utf-8')


def log_word_in_wordlist_history(word):
    now = datetime.now() - timedelta(hours=3)

    logger.info("log_word_in_wordlist_history")
    f = open(dict_data_path / 'Wordlist.txt', "a+")
    fileend = f.tell()
    f.seek(0)
    historyfile = f.read()
    f.seek(fileend)
    word_count = (historyfile.count('\n'+word+', ')
                  + historyfile.count('\n'+word+' ')
                  + historyfile.count('\n'+word+'\n'))
    f.write(f'\n{word}, {str(word_count)}, {now.strftime("%d.%m.%y")}')
    f.close()


def read_str_from_file(path: Path):
    path_str = replace_umlauts(str(path))
    path = Path(path_str)
    with open(path, 'r') as file:
        file_string = file.read()

    return file_string


def write_str_to_file(path: Path, string: str, notification=[]):
    path_str = replace_umlauts(str(path))
    path = Path(path_str)
    with open(path, 'w') as f:
        f.write(string)
    if notification:
        notification_command = ['notify-send'] + notification
        subprocess.Popen(notification_command)

    # TODO (4) add try, except and notify

    # try:
    #     %%%%%%%%%%%%%
    # except:
    #     logger.error('Error writing')
    #     # subprocess.Popen(['notify-send', 'Error writing'])
    #     pass

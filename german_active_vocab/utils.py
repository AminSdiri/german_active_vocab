from datetime import datetime, timedelta
import logging
from pathlib import Path
from plyer import notification

from settings import dict_data_path


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
        cache_found = True
        logger.info('Cached file found')
    except FileNotFoundError:
        logger.debug(f'No cached file found in {cache_path}')
        cache_found = False
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


def write_str_to_file(path: Path, string: str, notification_list=[]):
    # TODO (3) Overwrite files?, in which case I want to do that
    # in which case I want to reset DF entries
    path_str = replace_umlauts(str(path))
    path = Path(path_str)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(string)
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

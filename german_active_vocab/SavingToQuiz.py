from datetime import datetime, timedelta
import re
import pandas as pd
from bs4 import BeautifulSoup as bs

from GetDict.GenerateDict import create_dict_for_manually_added_words
from utils import set_up_logger
from settings import JINJA_ENVIRONEMENT

logger = set_up_logger(__name__)

# DONE (0) hide der, die, das, den, dem .. before nouns

def quizify_and_save(dict_data_path, beispiel_de,
                      beispiel_en, tag, word_dict: "WordDict",
                      saving_word):
    # TODO (1) fix this function
    '''
    Now we have a unified dict that the user can change directly! 
    Dielemma: if customising html in QtTextEdit Window is allowed,
    we cant use word_dict to generate quiz file without "übertragung"
    of changes from html to word_dict so quiz file is generated from the html.

    if a word is searched and it's already saved, in quiz mode it's retrieved
    from the saved html to show also the customisations made by the user
    before.
    here it's not even the case, only the information that the word is already
    saved is shown but the html is reconstructed again from word_dict.
    this is a "middle priority" bug

    but then we can't use all the exotic options behind word_dict
    (see new features allowed by dict dict), so every change to html file
    should be mirrored in word_dict (this is a TODO) it complicated for me
    so for now just generate the quiz file from the definition file rendered
    from word_dict (previous direct customisations to the definition html
    will be lost)
    and only allow for persitant custom examples (through word_dict)
    and because older entries with custom example dosnt' have word_dict
    we will retrive them using bs and add them to word_dict

    so big flow (for now, only current changes to html will be saved):
    - generate html (TODO including custom examples already in word_dict)
    - allow user to customize it
    - if user add new exemple and save (this function):
    - get custom examples fron saved html file in lists if theres's no
    word_dict cache, else get it from word_dict
    - append new custom examples
    - save the new list in word_dict
    - destroy the custom examples section in html and generate them again
    - include the custum examples list in html again
    - save the html
    '''

    word = word_dict['search_word']
    words_df = pd.read_csv(dict_data_path / 'wordlist.csv')
    words_df.set_index('Word', inplace=True)
    word_is_already_saved = word in words_df.index
    
    ####  old code ####
    # removing '\n' elements
    # qt_html_content = "".join(line.strip() for line in qt_html_content.split("\n"))
    # qt_html_content_soup = bs(qt_html_content, 'lxml')
    # if word_is_already_saved:
    #     qt_html_content_soup = _remove_custom_section_from_html(qt_html_content_soup)
    #     qt_html_content_soup = _remove_word_last_seen_section(qt_html_content_soup)

    if not word_is_already_saved:
        _add_word_to_words_df(dict_data_path, word, tag, words_df)

    if not beispiel_de and beispiel_en:
        raise RuntimeError('no no no no no, NO Beispiel_en without Beispiel_de, no.')

    if not word_dict:
        word_dict = create_dict_for_manually_added_words()

    word_dict = word_dict.append_new_examples_in_word_dict(beispiel_de, beispiel_en)
    # check if one of the words will get hidden in the custom german examples -> otherwise ask the user manually to select it
    # DONE (-1) kamel 3al old custom examples
    if 'custom_examples' in word_dict:
        all_word_variants, _ = word_dict.get_all_hidden_words()
        no_hidden_words_in_example = check_for_hidden_words_presence_in_custom_examples(examples=word_dict['custom_examples']['german'],
                                                                                        hidden_words=all_word_variants)

    # TODO (2) when it's not ok to overwrite?
    word_dict.save_word_dict()

    # if word_dict['custom_examples']['german']:
    #     custom_section_soup = _create_custom_section(word_dict)
    #     qt_html_content_soup.body.insert(len(qt_html_content_soup.body.contents), custom_section_soup.body.p)

    # qt_html_content = str(qt_html_content_soup)

    # TODO (3) after mirroring the changes made in the html to word_dict,
    # create_quiz_html will create a quiz_dict instead from word_dict and
    # render the html from it

    logger.info(f'{word} gespeichert')

    return no_hidden_words_in_example


def _add_word_to_words_df(dict_data_path, word, tag, words_df):
    # TODO (3) add reps for the same day like Anki
    words_df.loc[word, "Repetitions"] = 0
    words_df.loc[word, "EF_score"] = 2.5
    words_df.loc[word, "Interval"] = 1
    now = datetime.now() - timedelta(hours=3)
    words_df.loc[word, "Previous_date"] = now
    words_df.loc[word, "Created"] = now
    words_df.loc[word, "Next_date"] = now
    words_df.loc[word, "Tag"] = tag
    words_df.to_csv(dict_data_path / 'wordlist.csv')

def check_for_hidden_words_presence_in_custom_examples(examples: list, hidden_words:list):
    no_hidden_words_in_example = []
    for example_index, example_phrase in enumerate(examples):
        if not any(x in example_phrase for x in hidden_words):
            logger.warning(f'no words to hide in: {example_phrase}')
            logger.warning(f'hidden_words_list: {hidden_words}')
            no_hidden_words_in_example.append(example_index)
    return no_hidden_words_in_example

def hide_text(text, word_to_hide):
    # TODO (3) delete when moved to rendering html
    logger.info("hide_text")

    word_length = len(word_to_hide)

    hide_pattern = f'((^)|(?<=[^a-zA-ZäöüßÄÖÜẞ])){word_to_hide}((?=[^a-zA-ZäöüßÄÖÜẞ])|($))'
    try:
        quiz_text = re.sub(hide_pattern, word_length*'_', text)
    except re.error:
        quiz_text = text
        logger.error(f'error by hiding {word_to_hide}. '
                     'Word maybe contains reserved Regex charactar')

    return quiz_text

from datetime import datetime, timedelta
import json
import re
import pandas as pd
from bs4 import BeautifulSoup as bs
from collections import Counter

from WordProcessing import (hide_text, wrap_in_clozes,
                            generate_hidden_words_list)
from utils import set_up_logger, write_str_to_file
from settings import jinja_env

logger = set_up_logger(__name__)

# TODO (1) hide der, die, das, den, dem .. before nouns

def create_quiz_html(html_res, hidden_words_list):
    logger.info("create_quiz_html")
    clean_html = html_res

    clean_html_soup = bs(clean_html, 'lxml')

    # remove headwords
    clean_html_soup= remove_headwords(clean_html_soup)

    clean_html_soup= lock_definitions(clean_html_soup)

    clean_html = str(clean_html_soup)

    for w in hidden_words_list:
        clean_html = hide_text(clean_html, w)

    # repl_dict = {}
    # for w in hidden_words_list:
    #     repl_dict[w] = len(w)*'_'
    #     repl_dict[w.capitalize()] = len(w)*'_'
    # def helper(dic, match):
    #     word = match.group(0)
    #     return dic.get(word, word)
    # clean_html = word_re.sub(partial(helper, repl_dict), clean_html)

    clean_html_soup = bs(clean_html, 'lxml')
    clean_html_soup= unlock_definitions(clean_html_soup)

    clean_html_soup= remove_triangles(clean_html_soup)

    clean_html = str(clean_html_soup)

    return clean_html

def remove_triangles(clean_html_soup):
    for elem in clean_html_soup.find_all():
        if elem.string:
            if '▶' in elem.string:
                elem.string.replace_with(
                    re.sub('[a-zA-ZäöüßÄÖÜẞ]', '_', elem.string))
    
    return clean_html_soup

def unlock_definitions(clean_html_soup):
    '''remove dummy encoding in bold elements'''
    bold_elements = clean_html_soup.body.find_all(
        'span', style=re.compile('font-weight:600'))
    for elem in bold_elements:
        if elem.string:
            elem.string.replace_with(elem.string.replace('.:.', ''))
        else:
            for e in elem:
                if e.string:
                    e.string.replace_with(e.string.replace('.:.', ''))

    return clean_html_soup

def lock_definitions(clean_html_soup):
    '''do not hide words in the definitions (in bold)'''
    bold_elements = clean_html_soup.body.find_all(
        'span', style=re.compile('font-weight:600'))
    # dummy encoding to prevent words from being replaced
    for elem in bold_elements:
        if elem.string:
            elem.string.replace_with('.:.'.join([c for c in elem.string]))
        else:
            for e in elem:
                if e.string:
                    e.string.replace_with('.:.'.join([c for c in e.string]))
        
    return clean_html_soup


def remove_headwords(clean_html_soup):
    headwords = clean_html_soup.find_all("h1")
    if headwords:
        for headword in headwords:
            headword.decompose()

    return clean_html_soup


def wrap_words_to_learn_in_clozes(german_phrase, dict_dict):
    logger.info("wrap_words_to_learn_in_clozes")

    # TODO STRUCT (3) check your logic, only one case is always true?
    if 'hidden_words_list' not in dict_dict:
        hidden_words_list = generate_hidden_words_list(dict_dict)
    else:
        hidden_words_list = dict_dict['hidden_words_list']

    # Dupes make function wrap word twice
    hidden_words_list = list(set(hidden_words_list))

    front_with_cloze_wrapping = german_phrase

    for w in hidden_words_list:
        front_with_cloze_wrapping = wrap_in_clozes(front_with_cloze_wrapping, w)

    return front_with_cloze_wrapping

def save_from_def_mode(dict_data_path, word, custom_html_from_qt, beispiel_de,
                      beispiel_en, tag, dict_dict,
                      dict_dict_path):
    '''
    Dielemma: if customising html in QtTextEdit Window is allowed,
    we cant use dict_dict to generate quiz file without "übertragung"
    of changes from html to dict_dict so quiz file is generated from the html.

    if a word is searched and it's already saved, in quiz mode it's retrieved
    from the saved html to show also the customisations made by the user
    before.
    here it's not even the case, only the information that the word is already
    saved is shown but the html is reconstructed again from dict_dict.
    this is a "middle priority" bug

    but then we can't use all the exotic options behind dict_dict
    (see new features allowed by dict dict), so every change to html file
    should be mirrored in dict_dict (this is a TODO) it complicated for me
    so for now just generate the quiz file from the definition file rendered
    from dict_dict (previous direct customisations to the definition html
    will be lost)
    and only allow for persitant custom examples (through dict_dict)
    and because older entries with custom example dosnt' have dict_dict
    we will retrive them using bs and add them to dict_dict

    so big flow (for now, only current changes to html will be saved):
    - generate html (TODO including custom examples already in dict_dict)
    - allow user to customize it
    - if user add new exemple and save (this function):
    - get custom examples fron saved html file in lists if theres's no
    dict_dict cache, else get it from dict_dict
    - append new custom examples
    - save the new list in dict_dict
    - destroy the custom examples section in html and generate them again
    - include the custum examples list in html again
    - save the html
    '''

    # removing '\n' elements
    custom_html_from_qt = "".join(line.strip() for line in custom_html_from_qt.split("\n"))
    custom_qt_soup = bs(custom_html_from_qt, 'lxml')

    df = pd.read_csv(dict_data_path / 'wordlist.csv')
    df.set_index('Word', inplace=True)
    word_is_already_saved = word in df.index
    
    if word_is_already_saved:
        # destroy Custom_examples section
        ce_begin = custom_qt_soup.find("span", string="Eigenes Beispiel:")
        if ce_begin:
            ce_begin.parent.decompose()

        # destroy "word last seen" section
        last_seen_begin = custom_qt_soup.find(
            "span", string=re.compile("Last seen on"))
        if last_seen_begin:
            if last_seen_begin.parent.previous_sibling.name == 'hr':
                last_seen_begin.parent.previous_sibling.decompose()
            last_seen_begin.parent.decompose()

    else:
        # TODO (3) add reps for the same day like Anki
        df.loc[word, "Repetitions"] = 0
        df.loc[word, "EF_score"] = 2.5
        df.loc[word, "Interval"] = 1
        now = datetime.now() - timedelta(hours=3)
        df.loc[word, "Previous_date"] = now
        df.loc[word, "Created"] = now
        df.loc[word, "Next_date"] = now
        df.loc[word, "Tag"] = tag
        df.to_csv(dict_data_path / 'wordlist.csv')

    if not beispiel_de and beispiel_en:
        raise RuntimeError('no no no no no, NO Beispiel_en without Beispiel_de, no.')

    if dict_dict:
        if not 'source' in dict_dict:
            # TODO STRUCT (2) zid'ha meli yetsna3 dict moch lenna
            if '_du' in dict_dict_path.stem:
                dict_dict['source'] = 'duden'
            else:
                dict_dict['source'] = 'pons'
        if not 'hidden_words_list' in dict_dict:
            hidden_words_list = generate_hidden_words_list(dict_dict)
            dict_dict['hidden_words_list'] = hidden_words_list
        else:
            hidden_words_list = dict_dict['hidden_words_list']
    else:
        # dict is not built -> word not found anywhere but html "written" manually
        # BUG (2) this allows only one example to persist for manually written defs 
        # -> TODO if manually added dict already exist append new examples to that dict else create new one like here
        dict_dict = dict()
        dict_dict['source'] = 'manual'
        dict_dict['custom_examples'] = dict()
        dict_dict['custom_examples']['german'] = []
        dict_dict['custom_examples']['english'] = []
        hidden_words_list = []
        dict_dict['hidden_words_list'] = hidden_words_list

    # word found in pons or duden
    dict_dict = append_new_examples_in_dict_dict(beispiel_de, beispiel_en, dict_dict)

    dict_dict = prevent_duplicating_examples(dict_dict)

    write_str_to_file(dict_dict_path, json.dumps(dict_dict))

    # generate new custom_examples html section (if examples exist)
    if dict_dict['custom_examples']['german']:
        tmpl = jinja_env.get_template('custom_examples_section.html')
        custom_section_html = tmpl.render(dict_dict=dict_dict)

        custom_section_html = "".join(line.strip()
                                      for line
                                      in custom_section_html.split("\n"))

        # insert the custom examples list in html again
        custom_section_soup = bs(custom_section_html, 'lxml')
        custom_qt_soup.body.insert(
            len(custom_qt_soup.body.contents), custom_section_soup.body.p)

    custom_html_from_qt = str(custom_qt_soup)

    # TODO (3) after mirroring the changes made in the html to dict_dict,
    # create_quiz_html will create a quiz_dict instead from dict_dict and
    # render the html from it

    clean_html = create_quiz_html(custom_html_from_qt, hidden_words_list)

    # check if one of the words will get hidden in the custom german examples -> otherwise ask the user manually to select it
    # DONE (-1) kamel 3al old custom examples
    no_hidden_words_in_example = check_for_hidden_words_presence_in_custom_examples(dict_dict, hidden_words_list)

    # custom_qt_html = custom_qt_html.replace('.:.', '')
    # clean_html = clean_html.replace('.:.', '')

    # insert custom examples properly
    # TODO (1) when do I need fix_html_with_custom_example?
    # remove it when it's redundant
    # custom_qt_html = fix_html_with_custom_example(custom_qt_html)
    # clean_html = fix_html_with_custom_example(clean_html)

    write_str_to_file(dict_data_path / 'html' / f'{word}.html', custom_html_from_qt,
                      notification_list=[f'{word} gespeichert!'])
    write_str_to_file(dict_data_path / 'html' /f'{word}.quiz.html', clean_html)
    logger.info(f'{word} gespeichert')

    return no_hidden_words_in_example

def prevent_duplicating_examples(dict_dict):
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

    print(res)

    # keep first occurence
    indexes_to_delete = []
    for _, values in res.items():
        indexes_to_delete += values[1:]

    indexes_to_delete.sort(reverse=True)

    for index in indexes_to_delete:
        del dict_dict['custom_examples']['german'][index]
        del dict_dict['custom_examples']['english'][index]

    return dict_dict

def check_for_hidden_words_presence_in_custom_examples(dict_dict, hidden_words_list):
    no_hidden_words_in_example = []
    for example_index, example_phrase in enumerate(dict_dict['custom_examples']['german']):
        if not any(x in example_phrase for x in hidden_words_list):
            logger.warning(f'no words to hide in: {example_phrase}')
            logger.warning(f'hidden_words_list: {hidden_words_list}')
            no_hidden_words_in_example.append(example_index)
    return no_hidden_words_in_example

def append_new_examples_in_dict_dict(beispiel_de, beispiel_en, dict_dict):
    if beispiel_de:
        # update custom examples list in dict_dict
        dict_dict['custom_examples']['german'].append(beispiel_de)
        if not beispiel_en:
            beispiel_en = '#'*len(beispiel_de)
        dict_dict['custom_examples']['english'].append(beispiel_en)
    
    return dict_dict

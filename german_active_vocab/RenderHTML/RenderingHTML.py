import time
from jinja2 import UndefinedError
import pandas as pd
from bs4 import BeautifulSoup as bs
from typing import Any
from GetDict.HiddenWordsList import treat_words_to_hide

from utils import set_up_logger
from settings import DICT_DATA_PATH, JINJA_ENVIRONEMENT

logger = set_up_logger(__name__)

# DONE (1) color words to hide and secondary words also in custom examples
# TODO (2) LOOK&FEEL fama dl, Definition list, Supports the standard block attributes fel PyQT HTML esta3melha le def blocks bech yabdew alignee 3al isar.
# https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dl?retiredLocale=de

def render_html(word_dict: dict[str, Any], mode='full') -> str:
    # translate > get from duden > found in pons > found in duden > not found
    # DONE (1) STRUCT use one unified decision tree for all functions

    # background-color (from pyqt darktheme styling) = #2D2D2D

    # color_palette_dict = {
    #     # Main Primary color
    #     'primary_0': "#FFFF00",
    #     'primary_1': "#FFFF99",
    #     'primary_2': "#FFFF67",
    #     'primary_3': "#CFCF00",
    #     'primary_4': "#9E9E00",
    #     # Main Secondary color (1)
    #     'secondary_1_0': "#AAFF00",
    #     'secondary_1_1': "#DDFF99",
    #     'secondary_1_2': "#CCFF67",
    #     'secondary_1_3': "#81C200",
    #     'secondary_1_4': "#629300",
    #     # Main Secondary color (2)
    #     'secondary_2_0': "#FFD300",
    #     'secondary_2_1': "#FFED99",
    #     'secondary_2_2': "#FFE567",
    #     'secondary_2_3': "#CFAC00",
    #     'secondary_2_4': "#9E8300"

    # }

    color_palette_dict = {
        # Main Primary color
        'primary_0': "#DCFABC",
        'primary_1': "#F2FEE5",
        'primary_2': "#E7FCD1",
        'primary_3': "#D1F7A7",
        'primary_4': "#C5F393",
        # Main Secondary color (1)
        'secondary_1_0': "#B4EFCF",
        'secondary_1_1': "#E3FCEE",
        'secondary_1_2': "#CCF6E0",
        'secondary_1_3': "#9CE6BE",
        'secondary_1_4': "#84DAAC",
        # Main Secondary color (2)
        'secondary_2_0': "#F6FEBF",
        'secondary_2_1': "#FBFFE5",
        'secondary_2_2': "#F9FED3",
        'secondary_2_3': "#F2FDAC",
        'secondary_2_4': "#EFFC98"

    }

    JINJA_ENVIRONEMENT.filters["is_list"] = is_list
    if mode == 'full':
        JINJA_ENVIRONEMENT.filters["treat_hidden_words"] = highlight_words_to_hide
    elif mode == 'quiz':
        JINJA_ENVIRONEMENT.filters["treat_hidden_words"] = hide_words_to_hide
    else:
        raise RuntimeError
        
    word_info = get_saved_seen_word_info(word_dict['search_word'])

    dict_content = word_dict.get_dict_content()
    all_words_to_hide, all_secondary_words = word_dict.get_all_hidden_words()

    if 'translate' in word_dict['requested']:
        if dict_content:
            JINJA_ENVIRONEMENT.filters["treat_class"] = treat_class_trans
            tmpl = JINJA_ENVIRONEMENT.get_template('translation.html.j2')
            defined_html = tmpl.render(dict_content=dict_content, 
                                    word_dict=word_dict,
                                    all_words_to_hide=all_words_to_hide,
                                    all_secondary_words=all_secondary_words,
                                    mode=mode)
        else:
            tmpl = JINJA_ENVIRONEMENT.get_template('not_found_pons_translation.html.j2')
            defined_html = tmpl.render(word=word_info["word"])
        return defined_html

    if dict_content:
        JINJA_ENVIRONEMENT.filters["treat_class"] = treat_class_def
        tmpl = JINJA_ENVIRONEMENT.get_template('definition_pons.html.j2')
        # DONE (1)* make the rendering faster (it takes 2.2s for machen pons to render!)
        # probably because of the big list of words to hide
        start = time.time()
        defined_html = tmpl.render(word_dict=word_dict,
                                   dict_content=dict_content,
                                   all_words_to_hide=all_words_to_hide,
                                   all_secondary_words=all_secondary_words,
                                   word_info=word_info,
                                   col_pal=color_palette_dict,
                                   mode=mode)
        print('The rendering ran for', time.time() - start)
    else:
        tmpl = JINJA_ENVIRONEMENT.get_template('not_found.html.j2')
        defined_html = tmpl.render(word=word_info["word"], source=word_dict['requested'].capitalize())

    # trim_vlocks and lstrip_blocks are not enoughs?
    defined_html = "".join(line.strip()
                           for line in defined_html.split("\n"))

    # classes = [value for element in
    #            bs(defined_html, "html.parser").find_all(class_=True)
    #            for value in element["class"]]

    # print('classes: ', set(classes))

    return defined_html

def get_saved_seen_word_info(word: str) -> dict[str, Any]:
    df = pd.read_csv(DICT_DATA_PATH / 'wordlist.csv')
    df.set_index('Word', inplace=True)
    word_is_already_saved = word in df.index
    word_info = {'word': word}
    if word_is_already_saved:
        word_info["Previous_date"] = df.loc[word, "Previous_date"]
        word_info["Next_date"] = df.loc[word, "Next_date"]

    return word_info

def is_list(value) -> bool:
    return isinstance(value, list)

def treat_class_def(value, class_name, previous_class_name,
                    previous_class_value) -> str:
    '''workaround because of css21'''
    logger.debug(f"treating class: {class_name}")

    # ignoring can be also done here (by class, before rendering)

    # ignore striked values
    if isinstance(value, str):
        if value.startswith('<s'):
            return ''

    # value = value.strip()

    if class_name == 'headword':
        return value

    if class_name == 'wordclass':
        if value == 'noun':
            value = 'Nomen'
        # Ignoring
        return ''

    if class_name == 'flexion':
        value = '[' + value[1:] if value[0] == '<' else value
        value = value[:-1] + ']' if value[-1] == '>' else value
        return value

    if class_name == 'genus':
        if value == 'der':
            value = '<font color="#0099cc">' + value + '</font>'
        elif value == 'die':
            value = '<font color="#ff99ff">' + value + '</font>'
        elif value == 'das':
            value = '<font color="#d24dff">' + value + '</font>'
        return value

    if class_name == 'word_freq':
        if value > 0:
            value = '▰' * value + '▱' * (5 - value)
            value = '<br>' + '&nbsp;'*4 + 'Häufigkeit: ' + value
        elif value == -1:
            value = ''
        return value

    if class_name == 'verbclass':
        value = value.replace('with SICH', 'mit sich')\
                     .replace('with ', 'mit ')\
                     .replace('without ', 'ohne ')
        return value

    if class_name == 'phonetics':
        # ignoring
        return ''

    if class_name == 'header_num':
        value = '&nbsp;'*4 + value
        value = value.replace('Phrases:', '')
        if len(value) > 32:
            value = f'<font color="#ff5131">{value} (Warning)</font><br>' + '&nbsp;'*4
        if 'Zusammenschreibung' in value:
            value = ''
        value = f'<b>{value}</b>'
        return value

    # grammar

    if class_name == 'grammatical_construction':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*8 + 'ⓖ ' + value
        else:
            value = 'ⓖ ' + value
        value += '&nbsp;'
        return value

    if class_name == 'case':
        # ignoring because already exists in grammatical_construction
        # return ''
        return value

    if class_name == 'auxiliary_verb':
        # +sein ...
        return value

    if class_name == 'idiom_proverb':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*8 + 'ⓤ ' + value
        else:
            value = 'ⓤ ' + value
        value += '&nbsp;'
        return value

    if class_name == 'info':
        # no pl...
        return value

    if class_name == 'feminine':
        # Sünder -> Sünderin
        # doesn't get hidden without extra processing, don't need it
        return ''

    if class_name == 'object-case':
        # zu -> +Dat
        return value

    if class_name == 'full_collocation':
        # "ebenso gern" by "ebenso" for example
        value += '&nbsp;'
        return value

    # references ? probably useless for us => ignoring

    if class_name == 'indirect_reference_RQ':
        # zu, zu
        value += '&nbsp;'
        return ''

    if class_name == 'indirect_reference_OTHER':
        # zu, --> zu
        value += '&nbsp;'
        return ''

    # definitions

    if class_name == 'definition':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*8 + value
        value += '&nbsp;'
        return value

    if class_name == 'sense':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*8 + value
        value += '&nbsp;'
        return value

    if class_name == 'Wendungen_Redensarten_Sprichwoerter':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*8 + value
        if previous_class_name == 'example':
            value = '<br>' + value
        value += '&nbsp;'
        return value

    if class_name == 'reference_qualification':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*8 + value
        value += '&nbsp;'
        return value

    if class_name == 'synonym':
        value = '≈ ' + value
        return value

    if class_name == 'opposition':
        value = '≠ ' + value
        return value

    # example

    if class_name == 'example':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*16 + value
        return value

    # usage

    if class_name == 'restriction':
        value += '&nbsp;'
        return value

    if class_name == 'style':
        value = value.replace('>inf', '>umg')
        return value

    if class_name == 'rhetoric':
        # pejorativ...
        return value

    if class_name == 'topic':
        # PHYS...
        # TODO (4) text is in Tag <acronym> so capitalize will not reach content
        # value = value.lower().capitalize()
        return value

    if class_name == 'region':
        # SGer...
        return value

    if class_name == 'etymology':
        # (yidd)...
        return value

    if class_name == 'age':
        # veralt...
        return value

    logger.warning(f"Class: {class_name} not treated!")
    # unknown classes will be colored
    value = f'<acronym title="{class_name}">' + value + '</acronym>'
    value = '<font color="#ff5131">' + value + '</font>'
    return value


def treat_class_trans(value, class_name, previous_class_name,
                      previous_class_value) -> str:
    '''workaround because of css21'''
    # TODO (3) wrap target in the same class as source

    logger.debug(f"treating class: {class_name}")

    # base color: #4ae08c

    if class_name == 'source':
        # TODO (2) STRUCT this treatement should be done before standerised json
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
            value = '<font color="#4EAAD7">' + value + '</font>'
        elif value == 'die':
            value = '<font color="#FF7854">' + value + '</font>'
        elif value == 'das':
            value = '<font color="#FFB054">' + value + '</font>'
        return value

    if class_name == 'verbclass':
        value = value.replace('with SICH', 'mit sich')\
                     .replace('with obj', 'mit obj')\
                     .replace('without obj', 'ohne obj')
        return value

    if class_name == 'header_num':
        value = '&nbsp;'*4 + value
        value = value.replace('Phrases:', '')
        if 'Zusammenschreibung' in value:
            value = ''
        return value

    if class_name == 'synonym':
        value = '≈ ' + value
        return value

    if class_name == 'opposition':
        value = '≠ ' + value
        return value

    if class_name == 'restriction':
        value += '&nbsp;'
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


def treat_class_du(value, class_name, previous_class_name,
                   previous_class_value) -> str:
    '''workaround because of css21'''
    logger.debug(f"treating class: {class_name}")
    # TODO (1)* delete after moving everything to treat_class
    # TODO (1) all the html formatting shoud be here or in the jinja templates (example <font color=)

    # ignore striked values
    if isinstance(value, str):
        if value.startswith('<s'):
            return ''

    # value = value.strip()

    if class_name == 'headword':
        return value

    if class_name == 'wortart':
        if value == 'noun':
            value = 'Nomen'
        # Ignoring
        return value

    if class_name == 'word_freq':
        if value > 0:
            value = '▰' * value + '▱' * (5 - value)
        elif value == -1:
            value = ''
        value = '<br>' + '&nbsp;'*4 + 'Häufigkeit: ' + value
        return value

    if class_name == 'genus':
        if value == 'der':
            value = '<font color="#0099cc">' + value + '</font>'
        elif value == 'die':
            value = '<font color="#ff99ff">' + value + '</font>'
        elif value == 'das':
            value = '<font color="#d24dff">' + value + '</font>'
        return value

    # if class_name == 'verbclass':
    #     value = value.replace('with SICH', 'mit sich')\
    #                  .replace('with obj', 'mit obj')\
    #                  .replace('without obj', 'ohne obj')
    #     return value

    if class_name == 'header':
        value = '&nbsp;'*4 + value.replace(' ', '&nbsp;')
        return value

    if class_name == 'Grammatik':
        if previous_class_name != 'header':
            value = '<br>' + '&nbsp;'*8 + 'ⓖ ' + value
        else:
            value = 'ⓖ ' + value
        value += '&nbsp;'
        return value

    if class_name == 'idiom_proverb':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*8 + 'ⓤ ' + value
        else:
            value = 'ⓤ ' + value
        value += '&nbsp;'
        return value

    # if class_name == 'synonym':
    #     value = '≈ ' + value
    #     return value

    # if class_name == 'opposition':
    #     value = '≠ ' + value
    #     return value

    if class_name == 'definition':
        if previous_class_name != 'header':
            value = '<br>' + '&nbsp;'*8 + value
        value += '&nbsp;'
        return value

    # if class_name == 'Wendungen, Redensarten, Sprichwörter':
    #     value = '<br>' + '&nbsp;'*16 + value
    #     if (previous_class_name != 'Wendungen, Redensarten, Sprichwörter'
    #             and previous_class_name != 'header'):
    #         value = '<br>' + value
    #     return value

    # if class_name == 'sense':
    #     if previous_class_name != 'header_num':
    #         value = '<br>' + '&nbsp;'*8 + value
    #     value += '&nbsp;'
    #     return value

    if class_name == 'Beispiele':
        value = '<br>' + '&nbsp;'*16 + value
        return value

    if class_name == 'Beispiel':
        value = '<br>' + '&nbsp;'*16 + value
        return value

    # if class_name == 'restriction':
    #     value += '&nbsp;'
    #     return value

    if class_name == 'Gebrauch':
        value = value.replace('>inf', '>umg')
        return value

    # if class_name == 'case':
    #     # ignoring because already exists in grammatical_construction
    #     # return ''
    #     return value

    # if class_name == 'rhetoric':
    #     # pejorativ...
    #     return value

    logger.warning(f"Class: {class_name} not treated!")
    # unknown classes will be colored
    if isinstance(value, list):
        print(value)
    value = f'<acronym title="{class_name}">{value}</acronym>'
    value = f'<font color="#ffff00">{value}</font>'
    return value

def highlight_words_to_hide(value, class_name, words_to_hide: list, secondary_words: dict, forced_word_to_hide: list) -> str:
    ''' highlight words to hide (subtile color) for full html'''
    if not value:
        return value

    # no highlighting in headers and definitions
    if class_name in ('headword', 'flexion', 'definition', 'sense'):
        return value

    # combine user words to hide with automaticaly generated words to hide
    try:
        words_to_hide = list(set(words_to_hide + forced_word_to_hide))
    except UndefinedError: # 'DefEntry.DictDict object' has no attribute 'forced_hidden_words'
        pass
    
    value = treat_words_to_hide(value, words_to_hide, secondary_words, treatement='highlight')

    return value

def hide_words_to_hide(value, class_name, words_to_hide, secondary_words, forced_word_to_hide: list) -> str:
    ''' hide words to hide for quiz html'''

    if not value:
        return value

    # no replacing in definitions
    if class_name in ('definition', 'sense'):
        return value

    # Remove triangles (search word in another wordclass, noun from verb for example)
    if '▶' in value:
        return ''

    # combine user words to hide with automaticaly generated words to hide
    try:
        words_to_hide = list(set(words_to_hide + forced_word_to_hide))
    except UndefinedError: # 'DefEntry.DictDict object' has no attribute 'forced_hidden_words'
        pass

    value = treat_words_to_hide(value, words_to_hide, secondary_words, treatement='hide')

    return value


# # Lookup decision tree #
    #     if translate:
    #     dict_content = word_dict[f'content_{word_dict["requested"].replace("translate_", "")}']
    #     if word_dict:
    #         defined_html = render_html_from_dict('translation', dict_content, word_dict)
    #     else:
    #         tmpl = JINJA_ENVIRONEMENT.get_template('not_found_pons_translation.html.j2')
    #         defined_html = tmpl.render(word=word_info["word"])
    #     return defined_html

    # if word_dict['requested'] == 'duden':
    #     if word_dict['source'] == 'duden':
    #         # todo (0)* get ride of this after standarizing dicts
    #         defined_html = render_html_from_dict('pons', word_dict, word_info)
    #     else:
    #         tmpl = JINJA_ENVIRONEMENT.get_template('not_found_duden.html.j2')
    #         defined_html = tmpl.render(word=word_info["word"])
    #     return defined_html

    # if word_dict['source'] == 'pons':
    #     defined_html = render_html_from_dict('pons', word_dict, word_info)
    # elif word_dict['source'] == 'duden':
    #     defined_html = render_html_from_dict('duden', word_dict, word_info)
    # else:
    #     tmpl = JINJA_ENVIRONEMENT.get_template('not_found_pons_duden.html.j2')
    #     defined_html = tmpl.render(word=word_info["word"])

    # return defined_html

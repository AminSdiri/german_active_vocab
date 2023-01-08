import pandas as pd
from bs4 import BeautifulSoup as bs

from utils import (set_up_logger,
                   write_str_to_file)
from settings import dict_data_path, jinja_env

logger = set_up_logger(__name__)


def render_html(dict_dict, word_info, translate,
                get_from_duden):
    # get from duden > found in pons > not translate > else
    # TODO STRUCT (1) use one unified decision tree for all functions

    source = dict_dict['source']
    if translate:
        if source == 'pons':
            defined_html = render_html_from_dict('translation', dict_dict)
        else:
            tmpl = jinja_env.get_template('not_found_pons_translation.html')
            defined_html = tmpl.render(word=word_info["word"])
        return defined_html

    if get_from_duden:
        if source == 'duden':
            defined_html = render_html_from_dict('duden', dict_dict, word_info)
        else:
            tmpl = jinja_env.get_template('not_found_duden.html')
            defined_html = tmpl.render(word=word_info["word"])
        return defined_html
    
    if source == 'pons':
        defined_html = render_html_from_dict('definition', dict_dict, word_info)
    elif source == 'duden':
        defined_html = render_html_from_dict('duden', dict_dict, word_info)
    else:
        tmpl = jinja_env.get_template('not_found_pons_duden.html')
        defined_html = tmpl.render(word=word_info["word"])

    return defined_html


def render_html_from_dict(html_type: str, dict_dict, word_info={}):

    # background-color (from pyqt darktheme styling) = #2D2D2D
    color_palette_dict = {
        # Main Primary color
        'primary_0': "#FFFF00",
        'primary_1': "#FFFF99",
        'primary_2': "#FFFF67",
        'primary_3': "#CFCF00",
        'primary_4': "#9E9E00",
        # Main Secondary color (1)
        'secondary_1_0': "#AAFF00",
        'secondary_1_1': "#DDFF99",
        'secondary_1_2': "#CCFF67",
        'secondary_1_3': "#81C200",
        'secondary_1_4': "#629300",
        # Main Secondary color (2)
        'secondary_2_0': "#FFD300",
        'secondary_2_1': "#FFED99",
        'secondary_2_2': "#FFE567",
        'secondary_2_3': "#CFAC00",
        'secondary_2_4': "#9E8300"

    }

    jinja_env.filters["is_list"] = is_list
    if html_type == 'definition':
        jinja_env.filters["treat_class"] = treat_class_def
        tmpl = jinja_env.get_template('definition.html')
        defined_html = tmpl.render(dict_dict=dict_dict,
                                   word_info=word_info,
                                   col_pal=color_palette_dict)
    elif html_type == 'translation':
        jinja_env.filters["treat_class"] = treat_class_trans
        tmpl = jinja_env.get_template('translation.html')
        defined_html = tmpl.render(lang_dict=dict_dict)
    elif html_type == 'duden':
        jinja_env.filters["treat_class"] = treat_class_du
        tmpl = jinja_env.get_template('definition_du.html')
        defined_html = tmpl.render(du_dict=dict_dict,
                                   word_info=word_info)

    # trim_vlocks and lstrip_blocks are not enoughs?
    defined_html = "".join(line.strip()
                           for line in defined_html.split("\n"))

    write_str_to_file(
        dict_data_path / 'rendered_html_b4_qt.html', defined_html, overwrite=True)

    # classes = [value for element in
    #            bs(defined_html, "html.parser").find_all(class_=True)
    #            for value in element["class"]]

    # print('classes: ', set(classes))

    return defined_html


def is_list(value):
    return isinstance(value, list)


def treat_class_def(value, class_name, previous_class_name,
                    previous_class_value):
    '''workaround because of css21'''
    logger.info(f"treating class: {class_name}")

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
        if len(value) > 30:
            value = '<font color="#ff5131">' + value + \
                ' (Warning)' + '</font>' + '<br>' + '&nbsp;'*4
        # ignoring can be also done here
        if 'Zusammenschreibung' in value:
            value = ''
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
                      previous_class_value):
    '''workaround because of css21'''
    # TODO (3) wrap target in the same class as source

    logger.info(f"treating class: {class_name}")

    # base color: #4ae08c

    if class_name == 'source':
        # TODO  STRUCT (2) this treatement should be done before standerised json
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
                   previous_class_value):
    '''workaround because of css21'''
    logger.info(f"treating class: {class_name}")

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

    if class_name == 'Wendungen, Redensarten, Sprichwörter':
        value = '<br>' + '&nbsp;'*16 + value
        if (previous_class_name != 'Wendungen, Redensarten, Sprichwörter'
                and previous_class_name != 'header'):
            value = '<br>' + value
        return value

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


def get_seen_word_info(word):
    df = pd.read_csv(dict_data_path / 'wordlist.csv')
    df.set_index('Word', inplace=True)
    word_is_already_saved = word in df.index
    word_info = {'word': word}
    if word_is_already_saved:
        word_info["Previous_date"] = df.loc[word, "Previous_date"]
        word_info["Next_date"] = df.loc[word, "Next_date"]
    return word_info

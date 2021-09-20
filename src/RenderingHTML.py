import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup as bs
from jinja2 import Environment, PackageLoader, Template

from utils import (read_str_from_file, set_up_logger,
                   write_str_to_file)

dict_data_path = Path.home() / 'Dictionnary'
dict_src_path = Path.home() / 'Dokumente' / 'active_vocabulary' / 'src'

logger = set_up_logger(__name__)


def render_html(dict_dict, word_info, translate, _found_in_pons,
                get_from_duden, _found_in_duden):
    # get from duden > found in pons > not translate > else
    if translate:
        if _found_in_pons:
            defined_html = render_html_from_dict(
                'translation', dict_dict)
        else:
            tmpl_string = read_str_from_file(
                dict_src_path / 'templates/not_found_pons_translation.html')
            tmpl = Template(tmpl_string)
            defined_html = tmpl.render(word=word_info["word"])
    elif get_from_duden:
        if _found_in_duden:
            defined_html = render_html_from_dict(
                'duden', dict_dict, word_info)
        else:
            tmpl_string = read_str_from_file(
                dict_src_path / 'templates/not_found_duden.html')
            tmpl = Template(tmpl_string)
            defined_html = tmpl.render(word=word_info["word"])
    else:
        if _found_in_pons:
            defined_html = render_html_from_dict(
                'definition', dict_dict, word_info)
        else:
            if _found_in_duden:
                defined_html = render_html_from_dict(
                    'duden', dict_dict, word_info)
            else:
                tmpl_string = read_str_from_file(
                    dict_src_path / 'templates/not_found_pons_duden.html')
                tmpl = Template(tmpl_string)
                defined_html = tmpl.render(word=word_info["word"])

    return defined_html


def render_html_from_dict(html_type: str, dict_dict, word_info={}):
    env = Environment(
        loader=PackageLoader("tests", "templates"),
        trim_blocks=True,
        lstrip_blocks=True
        # autoescape=select_autoescape(["html", "xml"]),
    )

    env.filters["is_list"] = is_list
    if html_type == 'definition':
        env.filters["treat_class"] = treat_class_def
        path_str = dict_src_path / 'templates/definition.html'
        tmpl_string = read_str_from_file(path_str)
        tmpl = env.from_string(tmpl_string)
        defined_html = tmpl.render(
            dict_dict=dict_dict,
            word_info=word_info)
    elif html_type == 'translation':
        env.filters["treat_class"] = treat_class_trans
        path_str = dict_src_path / 'templates/translation.html'
        tmpl_string = read_str_from_file(path_str)
        tmpl = env.from_string(tmpl_string)
        defined_html = tmpl.render(
            lang_dict=dict_dict)
    elif html_type == 'duden':
        env.filters["treat_class"] = treat_class_du
        path_str = dict_src_path / 'templates/definition_du.html'
        tmpl_string = read_str_from_file(path_str)
        tmpl = env.from_string(tmpl_string)
        defined_html = tmpl.render(
            du_dict=dict_dict,
            word_info=word_info)

    # trim_vlocks and lstrip_blocks are not enoughs?
    defined_html = "".join(line.strip()
                           for line in defined_html.split("\n"))

    write_str_to_file(
        dict_data_path / 'renderd_innocent_html.html', defined_html)

    classes = [value
               for element in
               bs(defined_html, "html.parser").find_all(class_=True)
               for value in element["class"]]

    print('classes: ', set(classes))

    return defined_html


def is_list(value):
    return isinstance(value, list)


def treat_class_def(value, class_name, previous_class_name,
                    previous_class_value):
    '''workaround because of css21'''
    logger.info(f"treating class: {class_name}")

    value = value.strip()

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

    if class_name == 'verbclass':
        value = value.replace('with SICH', 'mit sich')\
                     .replace('with obj', 'mit obj')\
                     .replace('without obj', 'ohne obj')
        return value

    if class_name == 'header_num':
        value = '&nbsp;'*4 + value
        if len(value) > 30:
            value = '<font color="#ffff00">' + value + \
                ' (Warning)' + '</font>' + '<br>' + '&nbsp;'*4
        if 'Zusammenschreibung' in value:
            value = ''
        return value

    if class_name == 'grammatical_construction':
        if previous_class_name != 'header_num':
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

    if class_name == 'synonym':
        value = '≈ ' + value
        return value

    if class_name == 'opposition':
        value = '≠ ' + value
        return value

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

    if class_name == 'example':
        if previous_class_name != 'header_num':
            value = '<br>' + '&nbsp;'*16 + value
        return value

    if class_name == 'restriction':
        value += '&nbsp;'
        return value

    if class_name == 'style':
        value = value.replace('>inf', '>umg')
        return value

    if class_name == 'case':
        # ignoring because already exists in grammatical_construction
        # return ''
        return value

    if class_name == 'rhetoric':
        # pejorativ...
        return value

    logger.warning(f"Class: {class_name} not treated!")
    # unknown classes will be colored
    value = f'<acronym title="{class_name}">' + value + '</acronym>'
    value = '<font color="#ffff00">' + value + '</font>'
    return value


def treat_class_trans(value, class_name, previous_class_name,
                      previous_class_value):
    '''workaround because of css21'''
    # TODO (2) ken source feha class w target mafihech
    # wrapi target fel class mta3 source zeda

    logger.info(f"treating class: {class_name}")

    if class_name == 'source':
        # TODO (2) this treatement should be done before standerised json
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
        value = '&nbsp;'*4 + value
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
            value = '▰' * value
        elif value == -1:
            value = ''
        value = '<br>' + value
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
    value = f'<acronym title="{class_name}">' + value + '</acronym>'
    value = '<font color="#ffff00">' + value + '</font>'
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

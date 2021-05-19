import logging
import pandas as pd
from bs4 import BeautifulSoup as bs
from WordProcessing import create_quiz_html
from pathlib import Path

dict_path = Path.home() / 'Dictionnary'

# set up logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())  # .setFormatter(formatter)
logger.setLevel(logging.INFO)  # Levels: debug, info, warning, error, critical
formatter = logging.Formatter(
    '%(levelname)8s -- %(name)-15s line %(lineno)-4s: %(message)s')
logger.handlers[0].setFormatter(formatter)


def format_html(defined_html):
    logger.info("format_html")
    bs_class = 'gc'
    titel_word = defined_html.find_all(**{"class": "grammatical_construction"})
    if not(titel_word is None):
        for elem in titel_word:
            logger.debug('gc insert')
            # try:
            previous_sb = elem.previous_sibling.name
            # except:
            #     previous_sb = ''
            if previous_sb != 'header_num':
                elem.insert_before(defined_html.new_tag('br'))
                elem.insert_before('\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0ⓖ ')
            else:
                elem.insert_before('ⓖ ')
            elem.insert_after('\xa0')

    bs_class = 'ip'
    titel_word = defined_html.find_all(**{"class": "idiom_proverb"})
    for elem in titel_word:
        if not(elem is None):
            logger.debug('ip insert')
            prev_seb = elem.previous_sibling
            if not(prev_seb is None):
                is_previous_header = (prev_seb.name == 'header_num')
            else:
                logger.debug('No name for previous element')
                is_previous_header = 0
            if not is_previous_header:
                elem.insert_before(defined_html.new_tag('br'))
                elem.insert_before('\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0ⓤ ')
            else:
                elem.insert_before('ⓤ ')
            elem.insert_after('\xa0')

    bs_class = 'syn'
    titel_word = defined_html.find_all(**{"class": "synonym"})
    if not(titel_word is None):
        for elem in titel_word:
            logger.debug('syn insert')
            elem.wrap(defined_html.new_tag('b'))

    bs_class = 'ant'
    titel_word = defined_html.find_all(**{"class": "opposition"})
    if not(titel_word is None):
        for elem in titel_word:
            logger.debug('ant insert')
            elem.insert_before(defined_html.new_tag('br'))
            elem.wrap(defined_html.new_tag('b'))

    bs_class = 'def'
    titel_word = defined_html.find_all(**{"class": "definition"})
    if not(titel_word is None):
        for elem in titel_word:
            logger.debug('def insert')
            try:
                no_header_before = elem.previous_sibling.name != 'header_num'
            except AttributeError:
                no_header_before = 1
            if no_header_before:
                elem.insert_before(defined_html.new_tag('br'))
                elem.insert_before('\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0')
            elem.insert_after('\xa0')
            elem.wrap(defined_html.new_tag('b'))

    bs_class = 'sense'
    titel_word = defined_html.find_all(**{"class": "sense"})
    if not(titel_word is None):
        for elem in titel_word:
            logger.debug('sense insert')
            if elem.previous_sibling.name != 'header_num':
                elem.insert_before(defined_html.new_tag('br'))
            elem.insert_before('\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0')
            elem.wrap(defined_html.new_tag('b'))

    bs_class = 'exp'
    titel_word = defined_html.find_all(**{"class": "example"})
    if not(titel_word is None):
        for elem in titel_word:
            logger.debug('exp insert')
            elem.insert_before(defined_html.new_tag('br'))
            elem.wrap(defined_html.new_tag('i'))
            elem.insert_before(
                '\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0'
                '\xa0\xa0\xa0\xa0\xa0\xa0\xa0')

    bs_class = 'ut'
    titel_word = defined_html.find_all(**{"class": "restriction"})
    for elem in titel_word:
        if not(elem is None):
            logger.debug('util insert')
            elem.string.insert_after('\xa0')
            elem.wrap(defined_html.new_tag(bs_class))['color'] = '#cfff70'
            elem.parent.name = 'font'

    bs_class = 'umg'
    titel_word = defined_html.find_all(**{"title": "informal"})
    for elem in titel_word:
        if not(elem is None):
            logger.debug('umg insert')
            elem.string.insert_after('\xa0')
            elem.wrap(defined_html.new_tag(bs_class))['color'] = '#cfff70'
            elem.parent.name = 'font'

    return(defined_html)


def format_titel_html(headword_full, is_first_word_case):
    logger.info("format_titel_html")

    headword_full = headword_full.encode(encoding='UTF-8', errors='strict')\
        .replace(b'\xcc\xa3', b'').replace(b'\xcc\xb1', b'').decode('utf-8')
    headword_full = headword_full.replace(
        '<span class="separator">·</span>', '')\
        .replace('&lt;', '[')\
        .replace('&gt;', ']')
    headword_full = bs(headword_full, "lxml")

    bs_class = 'gen'
    # try:
    titel_word = headword_full.find(**{"class": "genus"})
    if not(titel_word is None):
        titel_word.wrap(headword_full.new_tag(bs_class))
        headword_full.find(bs_class)['size'] = 5
        headword_full.find(bs_class)['face'] = 'Arial'
        if not is_first_word_case:
            headword_full.find(bs_class).decompose()
        else:
            headword_full.find(bs_class).name = 'font'
            titel_word.wrap(headword_full.new_tag('b'))
    # except:
    #     pass

    bs_class = 'bigtitel'
    try:
        titel_word = headword_full.p.find(text=True, recursive=False)
    except AttributeError:
        titel_word = headword_full.body.find(text=True, recursive=False)
    titel_word.wrap(headword_full.new_tag(bs_class))
    headword_full.find(bs_class)['size'] = 6
    headword_full.find(bs_class)['face'] = 'Arial Black'
    if not is_first_word_case:
        headword_full.find(bs_class).decompose()
    else:
        headword_full.find(bs_class).name = 'font'

    bs_class = 'conj'
    # try:
    titel_word = headword_full.find(**{"class": "flexion"})
    if not(titel_word is None):
        titel_word.wrap(headword_full.new_tag(bs_class))
        headword_full.find(bs_class)['size'] = 4
        headword_full.find(bs_class)['face'] = 'Arial'
        if not is_first_word_case:
            headword_full.find(bs_class).decompose()
        else:
            headword_full.find(bs_class).name = 'font'
            titel_word.wrap(headword_full.new_tag('b'))
    # except:
    #     pass

    bs_class = 'wrdclass'
    # try:
    titel_word = headword_full.find(**{"class": "wordclass"})
    if not(titel_word is None or titel_word.contents == []):
        titel_word.wrap(headword_full.new_tag(bs_class))
        if is_first_word_case:
            titel_word.insert_before(headword_full.new_tag('br'))
        titel_word.insert_before(headword_full.new_tag('br'))
        titel_word.insert_before('\xa0•\xa0')
        headword_full.find(bs_class)['size'] = 5
        headword_full.find(bs_class)['face'] = 'Arial'
        headword_full.find(bs_class).name = 'font'
    # except:
    #     pass

    bs_class = 'vrbclass'
    # try:
    titel_word = headword_full.find(**{"class": "verbclass"})
    if not(titel_word is None):
        titel_word.wrap(headword_full.new_tag(bs_class))
        headword_full.find(bs_class)['size'] = 5
        headword_full.find(bs_class)['face'] = 'Arial'
        headword_full.find(bs_class).name = 'font'
    # except:
    #     pass

    is_p_in_titel = headword_full.find('p')
    if is_p_in_titel is None:
        footnote = headword_full.body
        new_ol = headword_full.new_tag("p")
        for content in reversed(footnote.contents):
            new_ol.insert(0, content.extract())
        footnote.append(new_ol)
    else:
        pass

    return headword_full


def create_translation_table(defined_html, definition_part, data_corpus):
    datasource = definition_part["source"]
    datatarget = definition_part["target"]
    logger.debug('DataSource: '+datasource)
    logger.debug('DataTarget: '+datatarget)
    if datasource != '' and datatarget != '':
        data_corpus += ('<table width="700" border="1"'
                        ' rules="rows"><tr><td width='
                        '"350">'
                        + datasource +
                        '</td><td width="350">' +
                        datatarget + '</td></tr>'
                        '</table>')  # <th> zeda fama
    logger.debug('data_corpus: '+data_corpus)
    for element in bs(data_corpus, 'lxml').body:
        if element is not None:
            defined_html.body.append(element)

    return defined_html, data_corpus


def correct_num_indentation(block_number, defined_html):
    ignore = 0
    block_number = block_number.replace('Phrases:', '')
    if ('Zusammen- oder Getrenntschreibung' in block_number or
        'Zusammenschreibung' in block_number or
            'Getrennt' in block_number):
        ignore = 1
    if block_number == '':
        indented_block_number = bs(
            '\xa0\xa0\xa0\xa0\xa0\xa0\xa0', 'lxml').body.p
    else:
        indented_block_number = bs(
            '\xa0\xa0\xa0\xa0' + block_number, 'lxml').body.p
    try:
        indented_block_number.string.wrap(
            defined_html.new_tag('header_num'))
    except AttributeError:
        try:
            indented_block_number.p.contents[0].wrap(
                defined_html.new_tag('header_num'))
        except AttributeError:
            indented_block_number.contents[0].wrap(
                defined_html.new_tag('header_num'))
    return indented_block_number, defined_html, ignore


def append_word_seen_info(word, defined_html):
    df = pd.read_csv(dict_path / 'wordlist.csv')
    tata = df[df["Word"] == word]
    if tata.size != 0:
        df.set_index('Word', inplace=True)
        rev_str = ('<br><br><font size="3" face="Courier New">Last seen on '
                   + df.loc[word, "Previous_date"] + ', next revision on '
                   + df.loc[word, "Next_date"] + '</font>')
        rev_bs = bs(rev_str, 'lxml').font
        defined_html.body.append(rev_bs)
    return defined_html


def treat_def_part(element, is_previous_gra, previous_is_expl,
                   was_gra_here, defined_html):
    # try:
    current_is_expl = (
        element["class"] == ['example'])
    is_current_gra = (
        element["class"] == [
            'idiom_proverb'] or
        element["class"] == [
            'grammatical_construction'])
    # except:
    #     is_current_an_example = 0
    if (is_previous_gra and
            not is_current_gra):
        was_gra_here = 1
    if ((not current_is_expl and
        previous_is_expl) or
        (was_gra_here and
            is_current_gra)):
        logger.debug(
            'separating gr in '
            'new paragraph')
        element.wrap(
            defined_html.new_tag('p'))
        defined_html.body.append(
            element.parent)
    else:
        defined_html.find_all(
            'p')[-1].append(element)
    previous_is_expl = current_is_expl
    is_previous_gra = is_current_gra

    return is_previous_gra, previous_is_expl, was_gra_here, defined_html


def standarize_json(json_data, translate):
    # to allow filtering of words, parts in power mode
    # TODO standarize json file before parsing and assign it as Def attribute
    # parseable properties are
    # - wordclass: Verb, noun, adj ..
    # - prop for verbes (z.B: warte.. auf)
    # - gen for nouns (der, die, das)
    # - syns
    # - defs
    # - beispiele
    # - Verwendung (Umg, tech etc)
    logger.info("standarize_json")
    defined_html = bs('<html><body><p></p></body></html>', 'lxml')

    standarized_json = [{}]
    standarized_json[0]['lang'] = ''
    standarized_json[0]['hits'] = []
    standarized_json[0]['hits'].append({})
    standarized_json[0]['hits'][0]['type'] = ''
    standarized_json[0]['hits'][0]['opendict'] = False
    standarized_json[0]['hits'][0]['roms'] = []
    standarized_json[0]['hits'][0]['roms'].append({})
    standarized_json[0]['hits'][0]['roms'][0]['headword'] = ''  # get this
    # and this and extract gender..
    standarized_json[0]['hits'][0]['roms'][0]['headword_full'] = ''
    standarized_json[0]['hits'][0]['roms'][0]['wordclass'] = ''  # and this
    standarized_json[0]['hits'][0]['roms'][0]['arabs'] = []
    standarized_json[0]['hits'][0]['roms'][0]['arabs'].append({})
    # and this
    standarized_json[0]['hits'][0]['roms'][0]['arabs'][0]['header'] = ''
    standarized_json[0]['hits'][0]['roms'][0]['arabs'][0]['translations'] = []
    standarized_json[0]['hits'][0]['roms'][0]['arabs'][0]['translations'].append({})
    # and this
    standarized_json[0]['hits'][0]['roms'][0]['arabs'][0]['translations'][0]['source'] = ''
    # and this
    standarized_json[0]['hits'][0]['roms'][0]['arabs'][0]['translations'][0]['target'] = ''

    return json_data

    for key, value in json_data.items():
        if isinstance(value, list):
            pass

    if len(json_data) == 1:
        logger.info(f'language: {json_data[0]["lang"]}')
        json_data = json_data[0]["hits"]
    else:
        raise RuntimeError('json API response is expected to be of length 1')

    for j in range(0, len(json_data)):  # j tetbadel m3a lkelma
        try:
            k_range = range(0, len(json_data[j]["roms"]))
        except KeyError:
            logger.warning('no k index warning')
            k_range = range(0, 1)
        for k in k_range:  # k tetbadel m3a mit/ohne_object/sich...
            try:
                raw_titel = json_data[j]["roms"][k]["headword_full"]
            except KeyError:
                logger.warning('no headword warning')
                json_data[j]["roms"][k]["headword_full"] = ''
            try:
                l_range = range(
                    0, len(json_data[j]["roms"][k]["arabs"]))
            except KeyError:
                logger.warning('no l index warning')
                l_range = range(0, 1)
            for l in l_range:
                # headerexist = 0
                # header_raw_is_full = 0
                # no_header = 0
                try:
                    rd_header = json_data[j]["roms"][k][
                        "arabs"][l]["header"]
                except KeyError:
                    try:
                        rd_header = json_data[j]["header"]
                        logger.warning('no arabs header index warning')
                    except KeyError:
                        logger.warning('no header index warning')
                        rd_header = ''
                        pass

                previous_is_expl = 0
                was_gra_here = 0
                is_previous_gra = 0
                try:
                    m_range = range(
                        0, len(json_data[j]["roms"][k]["arabs"]
                               [l]["translations"]))
                except KeyError:
                    logger.warning('no m index warning')
                    m_range = range(0, 1)
                if translate:
                    data_corpus = ''
                    for m in m_range:
                        logger.debug(f'm: {m}')
                        try:
                            datasource = json_data[j]["roms"][k][
                                "arabs"][l]["translations"][m]["source"]
                            datatarget = json_data[j]["roms"][k][
                                "arabs"][l]["translations"][m]["target"]
                            logger.debug('DataSource: '+datasource)
                            logger.debug('DataTarget: '+datatarget)
                            if datasource != '' and datatarget != '':
                                data_corpus += ('<table width="700" border="1"'
                                                ' rules="rows"><tr><td width='
                                                '"350">'
                                                + datasource +
                                                '</td><td width="350">' +
                                                datatarget + '</td></tr>'
                                                '</table>')  # <th> zeda fama
                        except KeyError:
                            logger.warning(
                                'no translation target index warning')
                            datasource = json_data[j]["source"]
                            datatarget = json_data[j]["target"]
                            logger.debug(datasource)
                            if datasource != '' and datatarget != '':
                                data_corpus += ('<table width="700" border="1" rules="rows"><tr><td width="350">'
                                                + datasource + '</td><td width="350">' + datatarget + '</td></tr></table>')   # <th> zeda fama
                    logger.debug('data_corpus: '+data_corpus)
                    for element in bs(data_corpus, 'lxml').body:
                        if element is not None:
                            defined_html.body.append(element)
                else:
                    for m in m_range:
                        try:
                            data_corpus = json_data[j]["roms"][k][
                                "arabs"][l]["translations"][m]["source"]
                            if data_corpus != '':
                                for element in bs(data_corpus, 'lxml').body:
                                    if element is not None:
                                        # try:
                                        current_is_expl = (
                                            element["class"] == ['example'])
                                        is_current_gra = (
                                            element["class"] == [
                                                'idiom_proverb'] or
                                            element["class"] == [
                                                'grammatical_construction'])
                                        # except:
                                        #     is_current_an_example = 0
                                        if (is_previous_gra and
                                                not is_current_gra):
                                            was_gra_here = 1
                                        if ((not current_is_expl and
                                            previous_is_expl) or
                                            (was_gra_here and
                                                is_current_gra)):
                                            logger.debug(
                                                'separating gr in '
                                                'new paragraph')
                                            element.wrap(
                                                defined_html.new_tag('p'))
                                            defined_html.body.append(
                                                element.parent)
                                        else:
                                            defined_html.find_all(
                                                'p')[-1].append(element)
                                        previous_is_expl = current_is_expl
                                        is_previous_gra = is_current_gra
                        except KeyError:
                            logger.warning('no translations index warning')
                            for element in bs(json_data[j]["source"], 'lxml').body:
                                if element is not None:
                                    defined_html.find_all(
                                        'p')[-1].append(element)


# def convert_json2Html_old(word, json_data, translate, soup):
#     logger.info("convert_json2Html")
#     defined_html = bs('<html><body><p></p></body></html>', 'lxml')
#     # trennbar = 0
#     words2hide = word.split()

#     if len(json_data) == 1:
#         logger.info(f'language: {json_data[0]["lang"]}')
#         json_data = json_data[0]["hits"]
#     else:
#         raise RuntimeError('json API respense is expected to be of length 1')

#     for j in range(0, len(json_data)):  # j tetbadel m3a lkelma
#         try:
#             k_range = range(0, len(json_data[j]["roms"]))
#         except KeyError:
#             logger.warning('no k index warning')
#             k_range = range(0, 1)
#         for k in k_range:  # k tetbadel m3a mit/ohne_object/sich...
#             try:
#                 raw_titel = json_data[j]["roms"][k]["headword_full"]
#             except KeyError:
#                 raw_titel = ''
#                 logger.warning('no headword warning')
#             logger.debug(f'j: {j}')
#             logger.debug(f'k: {k}')
#             if raw_titel != '':
#                 raw_titel, words2hide = format_titel_html(
#                     raw_titel, words2hide, k)
#                 defined_html.body.append(raw_titel.body.p)
#             try:
#                 l_range = range(
#                     0, len(json_data[j]["roms"][k]["arabs"]))
#             except KeyError:
#                 logger.warning('no l index warning')
#                 l_range = range(0, 1)
#             for l in l_range:
#                 # headerexist = 0
#                 # header_raw_is_full = 0
#                 # no_header = 0
#                 try:
#                     rd_header = json_data[j]["roms"][k][
#                         "arabs"][l]["header"]
#                 except KeyError:
#                     try:
#                         rd_header = json_data[j]["header"]
#                         logger.warning('no arabs header index warning')
#                     except KeyError:
#                         logger.warning('no header index warning')
#                         rd_header = ''
#                         pass
#                 rd_header = rd_header.replace('Phrases:', '')
#                 if ('Zusammen- oder Getrenntschreibung' in rd_header or
#                     'Zusammenschreibung' in rd_header or
#                         'Getrennt' in rd_header):
#                     continue
#                 if rd_header == '':
#                     bs_header = bs(
#                         '\xa0\xa0\xa0\xa0\xa0\xa0\xa0', 'lxml').body.p
#                 else:
#                     bs_header = bs('\xa0\xa0\xa0\xa0' +
#                                    rd_header, 'lxml').body.p
#                     # headerexist = 1
#                 try:
#                     bs_header.string.wrap(
#                         defined_html.new_tag('header_num'))
#                 except AttributeError:
#                     try:
#                         bs_header.p.contents[0].wrap(
#                             defined_html.new_tag('header_num'))
#                     except AttributeError:
#                         bs_header.contents[0].wrap(
#                             defined_html.new_tag('header_num'))
#                 defined_html.body.append(bs_header)
#                 previous_is_expl = 0
#                 was_gra_here = 0
#                 is_previous_gra = 0
#                 try:
#                     m_range = range(
#                         0, len(json_data[j]["roms"][k]["arabs"]
#                                [l]["translations"]))
#                 except KeyError:
#                     logger.warning('no m index warning')
#                     m_range = range(0, 1)
#                 if translate:
#                     data_corpus = ''
#                     for m in m_range:
#                         logger.debug(f'm: {m}')
#                         try:
#                             datasource = json_data[j]["roms"][k][
#                                 "arabs"][l]["translations"][m]["source"]
#                             datatarget = json_data[j]["roms"][k][
#                                 "arabs"][l]["translations"][m]["target"]
#                             logger.debug('DataSource: '+datasource)
#                             logger.debug('DataTarget: '+datatarget)
#                             if datasource != '' and datatarget != '':
#                                 data_corpus += ('<table width="700" border="1"'
#                                                 ' rules="rows"><tr><td width='
#                                                 '"350">'
#                                                 + datasource +
#                                                 '</td><td width="350">' +
#                                                 datatarget + '</td></tr>'
#                                                 '</table>')  # <th> zeda fama
#                         except KeyError:
#                             logger.warning(
#                                 'no translation target index warning')
#                             datasource = json_data[j]["source"]
#                             datatarget = json_data[j]["target"]
#                             logger.debug(datasource)
#                             if datasource != '' and datatarget != '':
#                                 data_corpus += ('<table width="700" border="1" rules="rows"><tr><td width="350">'
#                                                 + datasource + '</td><td width="350">' + datatarget + '</td></tr></table>')   # <th> zeda fama
#                     logger.debug('data_corpus: '+data_corpus)
#                     for element in bs(data_corpus, 'lxml').body:
#                         if element is not None:
#                             defined_html.body.append(element)
#                 else:
#                     for m in m_range:
#                         try:
#                             data_corpus = json_data[j]["roms"][k][
#                                 "arabs"][l]["translations"][m]["source"]
#                             if data_corpus != '':
#                                 for element in bs(data_corpus, 'lxml').body:
#                                     if element is not None:
#                                         # try:
#                                         current_is_expl = (
#                                             element["class"] == ['example'])
#                                         is_current_gra = (
#                                             element["class"] == [
#                                                 'idiom_proverb'] or
#                                             element["class"] == [
#                                                 'grammatical_construction'])
#                                         # except:
#                                         #     is_current_an_example = 0
#                                         if (is_previous_gra and
#                                                 not is_current_gra):
#                                             was_gra_here = 1
#                                         if ((not current_is_expl and
#                                             previous_is_expl) or
#                                             (was_gra_here and
#                                                 is_current_gra)):
#                                             logger.debug(
#                                                 'separating gr in '
#                                                 'new paragraph')
#                                             element.wrap(
#                                                 defined_html.new_tag('p'))
#                                             defined_html.body.append(
#                                                 element.parent)
#                                         else:
#                                             defined_html.find_all(
#                                                 'p')[-1].append(element)
#                                         previous_is_expl = current_is_expl
#                                         is_previous_gra = is_current_gra
#                         except KeyError:
#                             logger.warning('no translations index warning')
#                             for element in bs(json_data[j]["source"], 'lxml').body:
#                                 if element is not None:
#                                     defined_html.find_all(
#                                         'p')[-1].append(element)

#     if not translate:
#         defined_html = format_html(defined_html)

#     if not translate:
#         try:
#             duden_synonyms = synonyms(soup)
#             syn_part = ('<p><hr><font size="6" color="#ffb84d">'
#                         'Synonyme</font><ul>')  # face
#             for item in duden_synonyms:
#                 syn_part += '<li>'+item+'</li>'
#             syn_part += '</ul></p>'
#             rev_bs = bs(syn_part, 'lxml')
#             defined_html.body.append(rev_bs.body)
#         except TypeError:
#             duden_synonyms = '<p><hr><font size="4" color="#ffb84d">Synonyme zu ' + \
#                 word + ' nicht gefunden</font><ul>'
#     else:
#         duden_synonyms = ''

#     df = pd.read_csv(dict_path / 'wordlist.csv')
#     tata = df[df["Word"] == word]
#     if tata.size != 0:
#         df.set_index('Word', inplace=True)
#         rev_str = ('<br><br><font size="3" face="Courier New">Last seen on '
#                    + df.loc[word, "Previous_date"] + ', next revision on '
#                    + df.loc[word, "Next_date"] + '</font>')
#         rev_bs = bs(rev_str, 'lxml').font
#         defined_html.body.append(rev_bs)
#     defined_html.smooth()
#     defined_html = str(defined_html)
#     f = open(dict_path / 'Last_innocent_html.html', 'w')
#     f.write(defined_html)
#     f.close()
#     return words2hide, duden_synonyms, defined_html


def save_function(dict_path, word, defined_user_html, beispiel_de,
                  beispiel_en, tag, words_2_hide, now):
    df = pd.read_csv(dict_path / 'wordlist.csv')
    tata = df[df["Word"] == word]
    df.set_index('Word', inplace=True)
    if tata.size != 0:
        defined_user_html = defined_user_html\
            .replace('Last seen on '+df.loc[word, "Previous_date"]
                     + ', next revision on '+df.loc[word, "Next_date"], '')
    else:
        # TODO add reps for the same day like Anki
        df.loc[word, "Repetitions"] = 0
        df.loc[word, "EF_score"] = 2.5
        df.loc[word, "Interval"] = 1
        df.loc[word, "Previous_date"] = now.strftime("%d.%m.%y")
        df.loc[word, "Created"] = now.strftime("%d.%m.%y")
        df.loc[word, "Next_date"] = now.strftime("%d.%m.%y")
        df.loc[word, "Tag"] = tag
        df.to_csv(dict_path / 'wordlist.csv')

    clean_html = create_quiz_html(defined_user_html, words_2_hide)
    if not beispiel_de == '' and beispiel_en == '':
        clean_beispiel_de = create_quiz_html(beispiel_de, words_2_hide)
        clean_html += ('<br><br><b>Eigenes Beispiel:</b><br><i>&nbsp;'
                       '&nbsp;&nbsp;&nbsp;' + clean_beispiel_de+'</i>')
        defined_user_html += ('<br><br><b>Eigenes Beispiel:</b><br><i>'
                              '&nbsp;&nbsp;&nbsp;&nbsp;' +
                              beispiel_de+'</i>')
    elif not beispiel_de == '' and not beispiel_en == '':
        clean_beispiel_de = create_quiz_html(beispiel_de, words_2_hide)
        clean_html += ('<br><br><b>Eigenes Beispiel:</b><br><i>&nbsp;'
                       '&nbsp;&nbsp;&nbsp;' + clean_beispiel_de +
                       '</i><br><b>Auf Englisch:</b><br><i>&nbsp;'
                       '&nbsp;&nbsp;&nbsp;' + beispiel_en + '</i>')
        defined_user_html += ('<br><br><b>Eigenes Beispiel:</b><br><i>'
                              '&nbsp;&nbsp;&nbsp;&nbsp;' + beispiel_de
                              + '</i><br><b>Auf Englisch:</b><br><i>'
                              '&nbsp;&nbsp;&nbsp;&nbsp;' + beispiel_en
                              + '</i>')
    elif beispiel_de == '' and not beispiel_en == '':
        clean_html += ('<br><br><b>Auf Englisch:</b><br><i>&nbsp;&nbsp;'
                       '&nbsp;&nbsp;' + beispiel_en+'</i>')
        defined_user_html += ('<br><br><b>Auf Englisch:</b><br><i>''&nbsp;'
                              '&nbsp;&nbsp;&nbsp;' + beispiel_en + '</i>')
    defined_user_html = defined_user_html.replace('.:.', '')
    clean_html = clean_html.replace('.:.', '')
    # try:
    with open(dict_path / (word+'.html'), 'w') as f:
        f.write(defined_user_html)

    with open(dict_path / (word+'.quiz.html'), 'w') as f:
        f.write(clean_html)
    # subprocess.Popen(['notify-send', word + ' gespeichert!'])
    logger.info(word + 'gespeichert')
    # except:
    #     logger.error('Error writing' + word)
    #     subprocess.Popen(['notify-send', 'Error writing' + word])
    #     pass

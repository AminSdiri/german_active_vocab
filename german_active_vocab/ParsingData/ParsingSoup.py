from bs4 import BeautifulSoup as bs

from utils import set_up_logger

logger = set_up_logger(__name__)


def parse_duden_html_to_dict(_duden_soup):
    '''
    convert duden_html to standerized dict

    standerized dict structure:
    {
        'headword': '',
        'wordclass': '',  # verb/adjektiv/name/adverb
        'häfigkeit': '----',  # von '-' bis '-----'
        'genus': '',  # der/die/das
        ...
        'synonymes': [],
        'custom_examples':
            {
                'german': [],
                'english': []
            }
        'words_variants': []
        'content':  [   # ARABS (1. 2. ...)
                        [   # BLOCKS (a. b. ...)
                                {
                                    'header_num': '',   # 1.a. .. 2. ...
                                    'grammatical_construction': '',  # jd macht etw
                                    'definition': '',
                                    'example': '',  # []
                                    'rhetoric': ''  # pejorativ...
                                    'style': '',  # gebrauch
                                    ...
                                },
                                {..}, ..
                        ],
                        [..],
                    ]
    }
    '''
    (headword,
     wortart,
     word_freq,
     bedeutung_soup) = extract_parts_from_dudensoup(_duden_soup)

    duden_dict = dict()
    duden_dict['headword'] = headword
    duden_dict['wortart'] = wortart
    duden_dict['word_freq'] = word_freq
    duden_dict['custom_examples'] = {'german': [],
                                     'english': []}

    if bedeutung_soup is not None:
        duden_dict["content"] = populate_content_entry(bedeutung_soup)
    else:
        logger.warning('duden_soup is empty!, try other variant of the word'
                       ' (exp: stehenbleiben -> stehen_bleiben)')
        duden_dict["content"] = {}

    return duden_dict


def populate_content_entry(bedeutung_soup):
    try:
        fst_lvl_li_children = [x for x in bedeutung_soup.ol.contents
                               if x.name == 'li']

    except AttributeError:
        # for z.B. schrumpeln
        dict_content = [None]
        dict_content[0] = [None]
        dict_content[0][0] = dict()
        snd_lvl_dict = dict_content[0][0]
        snd_lvl_dict['header'] = ''
        parse_child(bedeutung_soup, snd_lvl_dict)
        return dict_content

    # TODO (3) use recursive function like recursivly_extract?
    # only if you notice if sometimes there is more than 2 levels
    if not fst_lvl_li_children:
        dict_content = [None]
        dict_content[0] = [None]
        dict_content[0][0] = dict()
        snd_lvl_dict = dict_content[0][0]
        snd_lvl_dict['header'] = ''
        parse_child(bedeutung_soup, snd_lvl_dict)
        return dict_content

    len_arabs = len(fst_lvl_li_children)
    dict_content = [None] * len_arabs

    for fst_lvl_num, fst_lvl_child in enumerate(fst_lvl_li_children):
        ol_section = fst_lvl_child.find('ol')
        if ol_section is None:
            if fst_lvl_child.name == 'li':
                dict_content[fst_lvl_num] = [None]
                dict_content[fst_lvl_num][0] = dict()
                snd_lvl_dict = dict_content[fst_lvl_num][0]

                snd_lvl_dict['header'] = get_header_num(fst_lvl_num,
                                                        len_arabs=len_arabs)

                parse_child(fst_lvl_child, snd_lvl_dict)
            else:
                raise RuntimeError('li Tag expected. '
                                   f'got {fst_lvl_child.name} instead')
        else:
            snd_lvl_li_children = [child
                                   for child in ol_section.contents
                                   if child.name == 'li']
            dict_content[fst_lvl_num] = [
                None] * len(snd_lvl_li_children)
            for snd_lvl_num, snd_lvl_child in enumerate(snd_lvl_li_children):
                dict_content[fst_lvl_num][snd_lvl_num] = dict()
                snd_lvl_dict = dict_content[fst_lvl_num][snd_lvl_num]

                snd_lvl_dict['header'] = get_header_num(fst_lvl_num,
                                                        snd_lvl_num=snd_lvl_num,
                                                        len_arabs=len_arabs,
                                                        len_letters=len(
                                                            snd_lvl_li_children))
                parse_child(snd_lvl_child, snd_lvl_dict)

    return dict_content


def get_header_num(fst_lvl_num, snd_lvl_num=0, len_arabs=0, len_letters=0):

    if len_arabs > 1 and len_letters > 1:
        snd_lvl_ltr = chr(97 + snd_lvl_num)
        if snd_lvl_num == 0:
            header_num = f'{fst_lvl_num+1}. a) '
        else:
            header_num = f'    {snd_lvl_ltr}) '

    elif len_arabs > 1:
        header_num = f'{fst_lvl_num+1}. '
    else:
        header_num = ''

    return header_num


def parse_child(second_lvl_child, second_lvl_dict):
    for element in second_lvl_child.contents:
        p_tag = False
        try:
            element_class_name = element['class'][0]
        except KeyError:
            p_tag = element.name == 'p'
        except TypeError:
            continue

        if element_class_name == 'enumeration__text' or p_tag:
            second_lvl_dict['definition'] = element.text
        elif element_class_name == 'note':
            key_name = element.find('dt', class_='note__title').text
            second_lvl_dict[key_name] = [
                elem.text for elem in element.dd.find_all('li')]
        elif element_class_name == 'tuple':
            key_name = element.find('dt', class_='tuple__key').text
            second_lvl_dict[key_name] = element.find(
                'dd', class_='tuple__val').text
        else:
            logger.warning(f'Class {element_class_name} is not '
                           '"enumeration__text" or "note" or "tuple".')
            pass
            # raise RuntimeError(f'Class {element_class_name} is not '
            #                    '"enumeration__text" or "note" or "tuple".')


def process_data_corpus(data_corpus):
    '''
    (For pons json content)
    return dict: {class_name: class_content
                  class_name2: ... ,
                  }

    3 cases:
        only one entry:
            - <span ...> ... </span>
        split this in 2 different entry:
            - <span ...> ... </span> <span ...> ... </span>
        only one entry, unwrap the class inside:
            - <span ...> ... <span ...> ... </span> .. </span>

    '''
    source_soup = bs(data_corpus, 'lxml')

    try:
        naked_text = source_soup.body.findChild('p').find(text=True)
    except AttributeError:
        naked_text = ''

    corpus_list_of_dicts = [{
        'class_name': 'NO_CLASS',
        'class_content': naked_text,
    }]

    for element in source_soup.find_all(class_=True):
        key_class = element["class"]
        if len(key_class) == 1:
            key_class = key_class[0]
        else:
            raise ValueError('Element have more than one class')

        # ignoring cant be done here also
        # headword sometime in the 'source' entry
        if key_class == 'headword':
            continue

        if element.parent is None:
            # because it's already deleted
            logger.info(
                f'subclass {element["class"]} tag already deleted')
            continue

        if element.parent.name not in ['body', 'p']:
            logger.info(f'found subclass {key_class} '
                        f'inside {element.parent.name} \n'
                        f'source_soup: {data_corpus}.\n'
                        'Passing')
            continue

        if element.findChildren(class_=True):
            for child_element in element.findChildren(class_=True):
                logger.info(f'dissolving subclass {child_element["class"]} '
                            f'tag inside {key_class} \n'
                            f'source_soup: {data_corpus}.')
                child_element.unwrap()

        source_content = ''.join(
            str(x) for x in element.contents)

        corpus_list_of_dicts.append({
            'class_name': key_class,
            'class_content': source_content
        })

    return corpus_list_of_dicts


def extract_parts_from_dudensoup(soup):
    logger.info("extract_def_section_from_duden")
    # approximate = True

    headword = get_headword_from_soup(soup)

    wortart = get_wordclass_from_soup(soup)

    # DONE (1) add word usage frequency to pons dict
    word_freq = get_word_freq_from_soup(soup)

    bedeutung_soup = get_meaning_section_from_soup(soup)

    return headword, wortart, word_freq, bedeutung_soup


def get_meaning_section_from_soup(soup):
    bedeutung_soup = None
    bedeutung_soup = soup.find('div', id="bedeutungen")
    if bedeutung_soup is None:
        bedeutung_soup = soup.find('div', id="bedeutung")
    return bedeutung_soup


def get_headword_from_soup(soup):
    h1_titles = soup.find_all('h1')
    if len(h1_titles) == 1:
        headword = h1_titles[0].span.text.replace('\xad', '')
    else:
        raise RuntimeError('Found none or more than one h1 tag in duden HTML')
    return headword


def get_word_freq_from_soup(soup):
    # getting Häufigkeit
    """
            Return word frequency:

            0 - least frequent
            5 - most frequent
            """
    h1_titles = soup.find_all('h1')

    headword_sieblings_iterator = h1_titles[0].parent.next_siblings
    for sib in headword_sieblings_iterator:
        try:
            tag_name = sib.name
        except AttributeError:
            tag_name = ""
        if tag_name == 'dl':
            if 'Häufigkeit' in sib.dt.contents[0].string:
                word_freq = len(sib.dd.div.span.string)
                break
        elif tag_name == 'div':
            logger.warning(
                "reached the end of header section without finding wortart")
            word_freq = -1
            break
    return word_freq


def get_wordclass_from_soup(soup):
    h1_titles = soup.find_all('h1')
    headword_sieblings_iterator = h1_titles[0].parent.next_siblings
    for sib in headword_sieblings_iterator:
        try:
            tag_name = sib.name
        except AttributeError:
            tag_name = ""
        if tag_name == 'dl':
            if 'Wortart' in sib.dt.contents[0].string:
                wortart = sib.dd.string
                break
        elif tag_name == 'div':
            logger.warning(
                "reached the end of header section without finding wortart")
            wortart = ''
            break
    return wortart


def create_synonyms_list(soup):
    logger.info("create_synonyms_list")
    # approximate = True

    syn_section = []
    logger.debug('fetching Synonyme section')
    if soup.name == 'div':
        syn_section = soup
    else:
        syn_section = soup.find('div', id="andere-woerter")
    if not syn_section:
        raise RuntimeError('synonymes section not Found in Duden')

    xerox_elements = [x for x in syn_section.contents if x.name == 'div']

    syn_list_of_lists = []

    for xerox_element in xerox_elements:
        if xerox_element['class'][0] == 'xerox':
            syn_list = []
            usage = ''
            for xerox_group in xerox_element.contents:
                if xerox_group.name == 'ul':
                    syn_sublist = xerox_group.find_all('li')
                    syn_sublist = [syn_elem.text for syn_elem in syn_sublist]
                    if usage:
                        syn_sublist = [
                            f'{syn} ({usage})' for syn in syn_sublist]
                    syn_list += syn_sublist
                elif xerox_group.name == 'h3':
                    usage = xerox_group.text
        syn_list_of_lists.append(syn_list)

    # section = copy.copy(section)
    # if section.header:
    #     section.header.extract()
    #     return recursively_extract(section, maxdepth=2,
    #                                exfun=lambda x: x.text.strip())

    return syn_list_of_lists


def recursively_extract(node, exfun, maxdepth=2):
    logger.debug("recursively_extract")
    if node.name in ['ol', 'ul']:
        li_list = node
    else:
        li_list = node.ol or node.ul
    if li_list and maxdepth:
        return [recursively_extract(li, exfun, maxdepth=(maxdepth - 1))
                for li in li_list.find_all('li', recursive=False)]
    return exfun(node)

# def search(word, exact=True, return_words=True):
#     """
#     Search for a word 'word' in duden

#     """
#     url = SEARCH_URL_FORM.format(word=word)
#     response = requests.get(url)
#     soup = bs(response.text, 'html.parser')
#     main_sec = soup.find('section', id='block-duden-tiles-0')

#     if main_sec is None:
#         return []

#     a_tags = [h2.a for h2 in main_sec.find_all('h2')]

#     urlnames = [a['href'].split('/')[-1]
#                 for a in a_tags
#                 if (not exact) or word in get_search_link_variants(a.text)]
#     if return_words:
#         return [get(urlname) for urlname in urlnames]
#     else:
#         return urlnames

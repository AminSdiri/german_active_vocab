from bs4 import BeautifulSoup as bs
from .HiddenWordsList import generate_hidden_words_list

from utils import set_up_logger

logger = set_up_logger(__name__)

'''
    duden dict structure:
    {
        'headword': '',
        'wordclass': '',  # verb/adjektiv/name/adverb
        'häufigkeit': '----',  # von '-' bis '-----'
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
                                'Wendugen, ..' : [] lezmha processing
                                'example': '',  # [] rod'ha dima list
                                'style': '',  # gebrauch
                                ...
                            },
                            {..}, ..
                        ],
                        [..],
                    ]
    }
'''

#TODO (1) unwrap Wendungen_Redensarten_Sprichwoerter

def construct_dict_content_from_soup(_duden_soup):
    if not _duden_soup:
        return []
    
    (headword,
    wortart,
    bedeutung_soup) = extract_parts_from_dudensoup(_duden_soup)
    if bedeutung_soup is None:
        logger.warning('duden_soup is empty!, try other variant of the word'
                       ' (exp: stehenbleiben -> stehen_bleiben)')
        dict_content = []
        return dict_content

    # Initialize dict content
    dict_content = [None]

    # Initialize rom level dict
    dict_content[0] = {}
    rom_level_dict = dict_content[0]

    rom_level_dict["headword"] = headword 
    rom_level_dict["wordclass"] = wortart # TODO (0)* get genus from here and (flexions from pons?) 

    try:
        fst_lvl_li_children = [x for x in bedeutung_soup.ol.contents
                               if x.name == 'li']

    except AttributeError:
        # for z.B. schrumpeln
        
        # Initialize arab level dict
        rom_level_dict["word_subclass"] = [None]
        arab_idx = 0
        rom_level_dict["word_subclass"][arab_idx] = {}
        arab_level_dict = rom_level_dict["word_subclass"][arab_idx]

        # Initialize def_blocks level dict
        arab_level_dict['def_blocks'] = [None]
        def_idx = 0
        arab_level_dict['def_blocks'][def_idx] = {}
        def_block = arab_level_dict['def_blocks'][def_idx]

        # fill def block
        def_block['header_num'] = ''
        def_block = parse_child(bedeutung_soup, def_block)

        dict_content = generate_hidden_words_list(dict_content)
        
        return dict_content

    # TODO (4) use recursive function like recursivly_extract?
    # only if you notice if sometimes there is more than 2 levels
    if not fst_lvl_li_children:
        # Initialize arab level dict
        rom_level_dict["word_subclass"] = [None]
        arab_idx = 0
        rom_level_dict["word_subclass"][arab_idx] = {}
        arab_level_dict = rom_level_dict["word_subclass"][arab_idx]

        # Initialize def_blocks level dict
        arab_level_dict['def_blocks'] = [None]
        def_idx = 0
        arab_level_dict['def_blocks'][def_idx] = {}
        def_block = arab_level_dict['def_blocks'][def_idx]

        # fill def block
        def_block['header_num'] = ''
        def_block = parse_child(bedeutung_soup, def_block)

        dict_content = generate_hidden_words_list(dict_content)

        return dict_content


    len_arabs = len(fst_lvl_li_children)
    rom_level_dict["word_subclass"] = [None]*len_arabs

    for fst_lvl_num, fst_lvl_child in enumerate(fst_lvl_li_children):
        ol_section = fst_lvl_child.find('ol')

        # Initialize arab level dict, fst_lvl === arabs , scd_lvl == defidxs
        rom_level_dict["word_subclass"][fst_lvl_num] = {}
        arab_level_dict = rom_level_dict["word_subclass"][fst_lvl_num]

        if ol_section is None:
            if fst_lvl_child.name == 'li':

                # Initialize def_blocks level dict
                arab_level_dict['def_blocks'] = [None]
                def_idx = 0
                arab_level_dict['def_blocks'][def_idx] = {}
                def_block = arab_level_dict['def_blocks'][def_idx]

                # fill def block
                def_block['header_num'] = get_header_num(fst_lvl_num,
                                                        len_arabs=len_arabs)
                def_block = parse_child(fst_lvl_child, def_block)
            else:
                raise RuntimeError(f'li Tag expected. got {fst_lvl_child.name} instead')
        else:
            snd_lvl_li_children = [child
                                   for child in ol_section.contents
                                   if child.name == 'li']

            arab_level_dict['def_blocks'] = [None] * len(snd_lvl_li_children)
            
            for snd_lvl_num, snd_lvl_child in enumerate(snd_lvl_li_children):
                # Initialize def_blocks level dict
                arab_level_dict['def_blocks'][snd_lvl_num] = {}  # Initializing dict before gives weird pointer behaviour
                def_block = arab_level_dict['def_blocks'][snd_lvl_num]

                def_block['header_num'] = get_header_num(fst_lvl_num,
                                                        snd_lvl_num=snd_lvl_num,
                                                        len_arabs=len_arabs,
                                                        len_letters=len(snd_lvl_li_children))
                def_block = parse_child(snd_lvl_child, def_block)

    dict_content = generate_hidden_words_list(dict_content)
    
    return dict_content


def get_header_num(fst_lvl_num, snd_lvl_num=0, len_arabs=0, len_letters=0) -> str:

    if len_arabs > 1 and len_letters > 1:
        snd_lvl_ltr = chr(97 + snd_lvl_num)
        if snd_lvl_num == 0:
            header_num = f'{fst_lvl_num+1}. a) '
        else:
            # header_num = f'    {snd_lvl_ltr}) '
            header_num = f'{snd_lvl_ltr}) '
    elif len_arabs > 1:
        header_num = f'{fst_lvl_num+1}. '
    else:
        header_num = ''

    return header_num


def parse_child(second_lvl_child, def_block: dict[str, str|list]):
    for element in second_lvl_child.contents:
        p_tag = False
        try:
            element_class_name = element['class'][0]
        except KeyError:
            p_tag = element.name == 'p'
        except TypeError:
            continue

        if element_class_name == 'enumeration__text' or p_tag:
            def_block['definition'] = element.text
        elif element_class_name == 'note':
            class_name = element.find('dt', class_='note__title').text
            class_name = standarize_item_names(class_name)
            def_block[class_name] = [elem.text for elem in element.dd.find_all('li')]
        elif element_class_name == 'tuple':
            class_name = element.find('dt', class_='tuple__key').text
            class_name = standarize_item_names(class_name)
            def_block[class_name] = element.find('dd', class_='tuple__val').text
        else:
            logger.warning(f'Class {element_class_name} is not '
                           '"enumeration__text" or "note" or "tuple".')
            # raise RuntimeError(f'Class {element_class_name} is not '
            #                    '"enumeration__text" or "note" or "tuple".')

    return def_block

def standarize_item_names(class_name):
    class_name = class_name.replace('Beispiele', 'example')\
                            .replace('Beispiel', 'example')\
                            .replace('Gebrauch', 'style')\
                            .replace('Grammatik', 'grammatical_construction')\
                            .replace('Wendungen, Redensarten, Sprichwörter',
                                     'Wendungen_Redensarten_Sprichwoerter')
                            
    return class_name


def extract_classes_names_and_content(data_corpus: str) -> list[dict[str,str]]:
    '''
    (For pons json content)
    return list of dicts: [
                            {"class_name": class_name,
                            "class_content": class_content
                            },
                            {"class_name2": class_name2,
                            "class_content2": class_content2
                            },
                            ...
                            ]

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
        class_name = element["class"]
        if len(class_name) == 1:
            class_name = class_name[0]
        else:
            raise ValueError('Element have more than one class')

        # ignoring cant be done here also
        # headword sometime in the 'source' entry
        if class_name == 'headword':
            continue

        if element.parent is None:
            # because it's already deleted
            logger.debug(f'subclass {element["class"]} tag already deleted')
            continue

        if element.parent.name not in ['body', 'p']:
            logger.debug(f'found subclass {class_name} '
                        f'inside {element.parent.name} \n'
                        f'source_soup: {data_corpus}.\n'
                        'Passing')
            continue

        if element.findChildren(class_=True):
            for child_element in element.findChildren(class_=True):
                logger.debug(f'dissolving subclass {child_element["class"]} '
                            f'tag inside {class_name} \n'
                            f'source_soup: {data_corpus}.')
                child_element.unwrap()

        source_content = ''.join(str(x) for x in element.contents)

        corpus_list_of_dicts.append({
            'class_name': class_name,
            'class_content': source_content
        })

    return corpus_list_of_dicts


def extract_parts_from_dudensoup(soup: bs):
    logger.info("extract_def_section_from_duden")
    # approximate = True

    headword = get_headword_from_soup(soup)

    wortart = get_wordclass_from_soup(soup)

    # DONE (1) add word usage frequency to pons dict

    bedeutung_soup = get_meaning_section_from_soup(soup)

    return headword, wortart, bedeutung_soup


def get_meaning_section_from_soup(soup: bs):
    bedeutung_soup = None
    bedeutung_soup = soup.find('div', id="bedeutungen")
    if bedeutung_soup is None:
        bedeutung_soup = soup.find('div', id="bedeutung")
    return bedeutung_soup


def get_headword_from_soup(soup: bs) -> str:
    h1_titles = soup.find_all('h1')
    if len(h1_titles) == 1:
        headword: str = h1_titles[0].span.text.replace('\xad', '')
    else:
        raise RuntimeError('Found none or more than one h1 tag in duden HTML')
    return headword


def get_word_freq_from_soup(soup) -> int:
    # getting Häufigkeit
    """
            Return word frequency:

            0 - least frequent
            5 - most frequent
            """
    
    if not soup:
        word_freq = -1
        return word_freq
        
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
                return word_freq
        # elif tag_name == 'div':
        #     logger.warning(
        #         "reached the end of header section without finding wortart")
        #     word_freq = -1
        #     break

    word_freq = -1
    return word_freq


def get_wordclass_from_soup(soup: bs) -> str:
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
                return wortart
        # elif tag_name == 'div':
        #     logger.warning(
        #         "reached the end of header section without finding wortart")
        #     wortart = ''
        #     break
    wortart = ''
    return wortart


def create_synonyms_list(soup: bs) -> list[list[str]]:
    logger.info("create_synonyms_list")
    # approximate = True

    logger.debug('fetching Synonyme section')
    if soup.name == 'div':
        syn_section = soup
    else:
        syn_section = soup.find('div', id="andere-woerter")

    xerox_elements = [x for x in syn_section.contents if x.name == 'div']

    syn_list_of_lists: list[list[str]] = []

    for xerox_element in xerox_elements:
        if xerox_element['class'][0] == 'xerox':
            syn_list: list[str] = []
            usage: str = ''
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

def wrap_text_in_tag_with_attr(text, tag_name, attr_name, attr_value):
    return f'<{tag_name} {attr_name}="{attr_value}">{text}</{tag_name}>'

def parse_anki_attribute(text):
    '''
    "this is an example" -> "this is an example", None
    "this <b>is</b> an example" -> "this <b>is</b> an example", None
    "<span data-anki-note-id='123'>this <b>is</b> an example</span>" -> "this <b>is</b> an example", "123"
    "<style color="F054525" data-anki-note-id='123'>this <b>is</b> an example</style>" -> "this <b>is</b> an example", "123"
    '''
    
    soup = bs(text, 'html.parser')

    # check if the text is have already the data-anki-note-id attribute
    elements_with_attr = soup.find(lambda tag: tag.has_attr('data-anki-note-id'))
    if not elements_with_attr:
        return text, None, False

    # get the data-anki-note-id value
    note_id = elements_with_attr['data-anki-note-id']
    note_id = int(note_id)

    # extract the contents of the tag containing data-* attribute and convert them to string
    contents = elements_with_attr.contents
    inner_text = ''.join([str(content) for content in contents])

    already_in_anki = True
    
    return inner_text, note_id, already_in_anki

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


def format_html(text: str, operation) -> str:
    if text.startswith('<s') and operation == 'discard':
        return text
    
    if text.startswith('<s') and operation == 'bookmark':
        text = remove_html_wrapping(text, unwrap= 'red_strikthrough')
        text = wrap_html(text, style='lime')
        return text
    
    if text.startswith('<font') and operation == 'discard':
        text = remove_html_wrapping(text, unwrap= 'lime')
        text = wrap_html(text, style='red_strikthrough')
        return text
    
    if text.startswith('<font') and operation == 'bookmark':
        return text
    
    if operation == 'discard':
        text = wrap_html(text, style='red_strikthrough')
        return text
    
    if operation == 'bookmark':
        text = wrap_html(text, style='lime')
        return text
    
    raise RuntimeError(f'wrap to {operation} not executed')

def wrap_html(text: str, style :str) -> str:
    if style == 'red_strikthrough':
        text=wrap_text_in_tag_with_attr(text=text, tag_name='s', attr_name='style', attr_value='color:Tomato')
        # text=f'<s style="color:Tomato;">{text}</s>'
        return text
    
    if style == 'lime':
        text=f'<font color="Lime">{text}</font>'
        return text
    
    raise RuntimeError(f'wrap to {style} not executed')

def remove_html_wrapping(text: str, unwrap: str) -> str:
    if not text.startswith('<s'):
        return text
        
    if unwrap == 'red_strikthrough':
        return text.replace('<s style="color:Tomato">','').replace('</s>', '') 
    if unwrap == 'lime':
        # BUG (2) ken fama deja font fi dict original yetna7a rodbelek
        return text.replace('<font color="Lime">','').replace('</font>', '')
        # text.replace("<font style='color:Lime'>",'').replace('</font>', '')
    raise RuntimeError(f'unwrapping {unwrap} not executed')


import logging
from pathlib import Path
import copy


# set up logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())  # .setFormatter(formatter)
logger.setLevel(logging.INFO)  # Levels: debug, info, warning, error, critical
formatter = logging.Formatter(
    '%(levelname)8s -- %(name)-15s line %(lineno)-4s: %(message)s')
logger.handlers[0].setFormatter(formatter)

dict_path = Path.home() / 'Dictionnary'


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


def create_synonyms_list(soup):
    logger.info("synonyms")
    # approximate = True
    # name = 'Synonyme zu'
    syn_section = None
    logger.debug('fetching Synonyme section')
    syn_section = soup.findAll('div', id="synonyme")
    if len(syn_section) == 0:
        logger.warning("Synonyme section not found")
        return None
    if len(syn_section) > 1:
        logger.warning("found more than 1 synonyme section!")
    else:
        logger.debug("synonyme section found")
        section = syn_section[0]
    section = copy.copy(section)
    if section.header:
        section.header.extract()
        return recursively_extract(section, maxdepth=2,
                                   exfun=lambda x: x.text.strip())


def extract_def_section_from_duden(soup):
    logger.info("duden_bedeutung")
    # approximate = True
    bedeutung_section = None
    bedeutung_section = soup.find('div', id="bedeutungen")
    if bedeutung_section is None:
        bedeutung_section = soup.find('div', id="bedeutung")
        bedeutung_section = str(bedeutung_section.p)
        return bedeutung_section
    bedeutung_section = str(bedeutung_section.ol)
    return bedeutung_section
    syn_section = syn_section[0]
    Bd_list = syn_section.ol.findAll("li")
    Bedeutung = []
    Beispiel = []
    for x in Bd_list:
        Bedeutung.append(
            x.find(**{"class": "enumeration__text"}).text.replace("\n", ""))
        Beispiel.append(
            x.find(**{"class": "note__list"}).text.replace("\n", ""))
    return Bedeutung, Beispiel

# TODO add word usage frequency
    ''' def frequency(self):
            """
            Return word frequency:

            0 - least frequent
            5 - most frequent
            """
            try:
                pos_div = self._section_main_get_node(
                    'Häufigkeit:', use_label = False)
                return pos_div.strong.text.count('▮')
            except AttributeError:
                return None
                '''


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

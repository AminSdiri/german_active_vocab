import logging
import re
# from functools import partial

from utils import set_up_logger

logger = set_up_logger(__name__, level=logging.WARNING)

word_re = re.compile(r'\b[a-zA-Z]+\b')


def fix_html_with_custom_example(html_text):
    # TODO (4) Vorübergehend, delete after all htmls are updated
    logger.info("fix_html_with_custom_example")

    html_text = html_text.replace('</body></html><br><br>',
                                  '<br><p style=" margin-top:12px; '
                                  'margin-bottom:12px; margin-left:0px; '
                                  'margin-right:0px; -qt-block-indent:0; '
                                  'text-indent:0px;">')
    if html_text[-4:] == '</i>':
        html_text += '</p></body></html>'

    return html_text


def hide_text(text, word_to_hide):
    logger.info("hide_text")

    word_length = len(word_to_hide)

    hide_pattern = f'(?<=[^a-zA-Z]){word_to_hide}(?=[^a-zA-Z])'
    try:
        quiz_text = re.sub(hide_pattern, word_length*'_', text)
    except re.error:
        quiz_text = text
        logger.error(f'error by hiding {word_to_hide}. '
                     'Word maybe contains reserved Regex charactar')

    return quiz_text


def find_all(a_str, sub):
    logger.info("find_all")
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)  # use start += 1 to find overlapping matches


def update_words_to_hide(dict_dict):
    # TODO (3) clean up
    logger.info("extract_words_to_hide")
    word_variants = []

    for rom_idx in range(len(dict_dict['content'])):
        if 'headword' in dict_dict['content'][rom_idx]:
            headword = dict_dict['content'][rom_idx]['headword']
        else:
            headword = ''
        if 'wordclass' in dict_dict['content'][rom_idx]:
            wordclass = dict_dict['content'][rom_idx]['wordclass']
        else:
            wordclass = ''
        if 'flexion' in dict_dict['content'][rom_idx]:
            flexion = dict_dict['content'][rom_idx]['flexion']
            flexion = flexion.replace('<', '').replace('>', '')
            flexion_list = flexion.split(', ')
        else:
            flexion_list = []
        if 'genus' in dict_dict['content'][rom_idx]:
            genus = dict_dict['content'][rom_idx]['genus']
        else:
            genus = ''

        if headword == '':
            return word_variants

        word_variants.append(headword)

        if wordclass == 'verb':
            if flexion_list:
                logger.debug('Verb')
                base_word = headword
                conjugations = flexion_list
                if len(conjugations) == 3:
                    try:
                        prateritum = conjugations[1].split()
                    except IndexError:
                        prateritum = [base_word[:-2]+'te']
                    try:
                        perfekt = conjugations[2].split()
                    except IndexError:
                        # perfekt = ['hat', base_word[:-2]+'t']
                        perfekt = ['hat', 'ge'+base_word[:-2]+'t']
                elif len(conjugations) == 2:
                    try:
                        prateritum = conjugations[0].split()
                    except IndexError:
                        prateritum = [base_word[:-2]+'te']
                    try:
                        perfekt = conjugations[1].split()
                    except IndexError:
                        # perfekt = ['hat', base_word[:-2]+'t']
                        perfekt = ['hat', 'ge'+base_word[:-2]+'t']
                if len(prateritum) == 2:
                    logger.debug('trennbar')
                    # trennbar = 1
                    word_variants += conjugations[0].split()
                    trenn_wort = prateritum[1]
                    lentrennwort = len(trenn_wort)
                    word_variants.append(base_word[lentrennwort:])
                    word_variants.append(
                        trenn_wort+'zu'+base_word[lentrennwort:])
                    word_variants.append(base_word[lentrennwort:-1])
                    word_variants.append(base_word[lentrennwort:-2]+'t')
                    word_variants.append(base_word[lentrennwort:-2])
                    word_variants.append(base_word[:-1])
                    word_variants.append(base_word[:-2]+'t')
                    word_variants.append(base_word[:-2])
                    word_variants.append(conjugations[0][:-2]+'t')
                    word_variants.append(conjugations[0][:-2])
                    word_variants.append(prateritum[0]+'t')
                    if prateritum[0][-1] == 'e':
                        word_variants.append(prateritum[0]+'n')
                    else:
                        word_variants.append(prateritum[0]+'en')
                    word_variants.append(prateritum[0]+'st')
                    word_variants.append(prateritum[0]+'t')
                    word_variants.append(prateritum[0])
                    word_variants.append(perfekt[1])
                    word_variants.append(perfekt[1]+'e')
                    word_variants.append(perfekt[1]+'es')
                    word_variants.append(perfekt[1]+'er')
                elif base_word[0:2] == 'ab':
                    logger.debug('false trennbar')
                    word_variants += conjugations[0].split()
                    word_variants.append('ab')
                    word_variants.append(base_word[2:-1])
                    word_variants.append(base_word[2:-2]+'t')
                    word_variants.append(base_word[2:-1]+'t')
                    word_variants.append(base_word[2:-2])
                    word_variants.append(base_word[2:-2]+'st')
                    word_variants.append(base_word[2:-1]+'st')
                    word_variants.append(prateritum[0]+'t')
                    if prateritum[0][-1] == 'e':
                        word_variants.append(prateritum[0]+'n')
                    else:
                        word_variants.append(prateritum[0]+'en')
                    word_variants.append(prateritum[0]+'st')
                    word_variants.append(prateritum[0]+'t')
                    word_variants.append(prateritum[0])
                    word_variants.append(perfekt[1])
                    word_variants.append('ab'+'ge'+base_word[2:-1]+'t')
                else:
                    logger.debug('einfach')
                    word_variants += conjugations[0].split()
                    word_variants.append(base_word)
                    word_variants.append(base_word[:-1])
                    word_variants.append(base_word[:-1]+'e')
                    word_variants.append(conjugations[0][:-2])
                    word_variants.append(conjugations[0][:-2]+'t')
                    word_variants.append(conjugations[0][:-2]+'et')
                    word_variants.append(base_word[:-2]+'t')
                    word_variants.append(base_word[:-2]+'et')
                    word_variants.append(base_word[:-1]+'t')
                    word_variants.append(base_word[:-1]+'et')
                    word_variants.append(prateritum[0])
                    word_variants.append(prateritum[0]+'st')
                    word_variants.append(prateritum[0]+'t')
                    word_variants.append(prateritum[0]+'n')
                    word_variants.append(base_word+'d')
                    try:
                        word_variants.append(perfekt[1])
                    except IndexError:
                        word_variants.append('ge'+base_word[:-2]+'t')
                        word_variants.append('ge'+base_word[:-1]+'t')
            else:
                logger.debug('without flexion')
                base_word = headword
                word_variants.append(base_word)
                word_variants.append(base_word[:-1])
                word_variants.append(base_word[:-1]+'e')
                word_variants.append(base_word[:-2])
                word_variants.append(base_word[:-2]+'e')
                word_variants.append(base_word[:-1]+'est')
                word_variants.append(base_word[:-2]+'st')
                word_variants.append(base_word[:-2]+'t')
                word_variants.append(base_word[:-2]+'et')
                word_variants.append(base_word[:-1]+'t')
                word_variants.append(base_word[:-1]+'et')
                word_variants.append(base_word[:-2]+'te')
                word_variants.append(base_word[:-2]+'test')
                word_variants.append(base_word[:-2]+'tet')
                word_variants.append(base_word[:-2]+'ten')
                word_variants.append(base_word[:-1]+'te')
                word_variants.append(base_word[:-1]+'test')
                word_variants.append(base_word[:-1]+'tet')
                word_variants.append(base_word[:-1]+'ten')
                word_variants.append('ge'+base_word[:-2]+'t')
                word_variants.append('ge'+base_word[:-1]+'t')
        else:
            if flexion_list:
                # base_word = cleaner_raw_titel.split(":")
                # logger.debug(base_word)
                # try:
                #     plural = flexion_list[1]
                #     wrdrr = plural
                #     word_variants += flexion_list
                # except IndexError:
                #     conjugations = base_word[0].split()
                #     if (conjugations[0] == 'der' or
                #         conjugations[0] == 'die' or
                #             conjugations[0] == 'das'):
                #         wrdrr = conjugations[1].replace('·', '').replace('', '')
                #     else:
                #         wrdrr = conjugations[0].replace('·', '').replace('', '')
                #     word_variants.append(wrdrr)

                word_variants.append(headword+'e')
                word_variants.append(headword+'en')
                word_variants.append(headword+'er')
                word_variants.append(headword+'em')
                word_variants.append(headword+'es')
                word_variants.append(headword+'n')
                word_variants.append(headword+'r')
                word_variants.append(headword+'m')
                word_variants.append(headword+'s')
                # conjugations = base_word[0].split()
                # if conjugations[0] == 'der' or conjugations[0] == 'die' or conjugations[0] == 'das':
                #     wrdrr = conjugations[1].replace('·', '').replace('', '')
                # else:
                #     wrdrr = conjugations[0].replace('·', '').replace('', '')
            # else:
                # word_variants += cleaner_raw_titel.split()
                # logger.debug(word_variants)
                # if (word_variants[0] == 'der' or
                #     word_variants[0] == 'die' or
                #         word_variants[0] == 'das'):
                #     wrdrr = word_variants[1].replace('·', '').replace('', '')
                # else:
                #     wrdrr = word_variants[0].replace('·', '').replace('', '')

            word_variants.append(headword+'e')
            word_variants.append(headword+'en')
            word_variants.append(headword+'er')
            word_variants.append(headword+'em')
            word_variants.append(headword+'es')
            word_variants.append(headword+'n')
            word_variants.append(headword+'r')
            word_variants.append(headword+'m')
            word_variants.append(headword+'s')

        # workaround to ignore words containing special chars
        # words_to_hide = [elem for elem in words_to_hide if all(
        #     c.isalnum() for c in elem)]
        word_variants = list(set(word_variants))

    return word_variants

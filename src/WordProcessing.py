import logging
import re
from functools import partial

from utils import set_up_logger

logger = set_up_logger(__name__, level=logging.WARNING)

word_re = re.compile(r'\b[a-zA-Z]+\b')


def fix_html_with_custom_example(html_text):
    # Vorübergehend
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


def reclassify(stri, wrd1, wrd2):
    logger.info("reclassify")
    idx = list(find_all(stri, wrd1))
    for k in idx:
        indlist = list(find_all(stri, wrd2))
        lastbr = [i for n, i in enumerate(indlist) if i > k][0]
        stri = stri[:lastbr]+'<br>'+stri[lastbr+len(wrd2):]
        stri = stri[:k]+wrd2+stri[k:]
    return stri


def reverse_between_words(stri, wrd1, wrd2, wrd21):
    logger.info("reverse_between_words")
    inds1 = list(find_all(stri, wrd1))
    inds2 = list(find_all(stri, wrd2))
    count = 0
    inds2new = []

    if len(inds1) == 0 or len(inds2) == 0:
        return stri

    for k in range(0, len(inds1)):
        while inds2[count] < inds1[k]:
            count += 1
        inds2new.append(inds2[count])
    inds2 = inds2new
    assert len(inds1) == len(inds2)

    stri2 = stri[0:inds1[0]]
    for k in range(1, len(inds1)):
        stri2 += (wrd1
                  + stri[inds2[k-1]-1:(inds1[k-1] + len(wrd1)-1):-1]
                  + stri[inds2[k-1]:inds1[k]])

    stri2 += (wrd1
              + stri[inds2[k]-1:(inds1[k]+len(wrd1)-1):-1]
              + stri[inds2[k]:])

    return stri2


def delete_between_words(stri, wrd1, wrd2, wrd21):
    logger.info("delete_between_words")
    inds1 = list(find_all(stri, wrd1))
    inds2 = list(find_all(stri, wrd2))
    if len(inds1) == 0 or len(inds2) == 0:
        return stri
    if len(inds1) != len(inds2):
        inds2 = list(find_all(stri, wrd21))
    stri2 = stri[0:inds1[0]]
    k = 0
    for k in range(1, len(inds1)):
        stri2 += wrd1+stri[inds2[k-1]:inds1[k]]
    stri2 += wrd1+stri[inds2[k]:]
    return stri2


def delete_between_words2(stri, wrd1, wrd2, wrd21):
    logger.info("delete_between_words2")
    # lastinddeleted = 0
    k = 0
    idx2 = 0
    while stri.find(wrd1, 0) != -1 & k < 10:
        idx1 = stri.find(wrd1, 0)
        idx2 = stri.find(wrd2, idx1)
        idx21 = stri.find(wrd21, idx1)
        if idx2 == -1 and idx21 == -1:
            return stri
        if idx2 < idx21 and idx2 != -1:
            stri = stri[:idx1]+stri[idx2+len(wrd2):]
        else:
            stri = stri[:idx1]+stri[idx21:]
        k = k+1
    return stri


def delete_between_words3(stri, wrd1, wrd2, wrd21):
    logger.info("delete_between_words3")
    lastinddeleted = 0
    k = 0
    while stri.find(wrd2, lastinddeleted) != -1 & k < 10:
        idx1 = stri.find(wrd1, lastinddeleted)
        idx2 = stri.find(wrd2, lastinddeleted)
        # idx21 = stri.find(wrd21, lastinddeleted)
        if idx2 == -1:
            return stri
        stri = stri[:idx1]+stri[idx2:]
        ind21list = list(list(find_all(stri, wrd21)))
        # try:
        lastinddeleted = [i for n, i in enumerate(
            ind21list) if i > idx2][0]

        # except:
        #     return stri
        k = k+1
    return stri


def delete_part_containing(stri, wrd, delim1, delim2):
    logger.info("delete_part_containing")
    wrd_idx = idx1 = stri.find(wrd)
    firstidx = 0
    bigk = 0
    # maxk = len(stri)
    while stri.find(wrd, firstidx) > 0 and bigk < 10:
        bigk = bigk+1
        found = 0
        k = 0
        wrd_idx = stri.find(wrd, firstidx)
        idx2 = 0
        idx1 = 0
        while found == 0:
            if stri[wrd_idx+k] == delim2:
                idx2 = wrd_idx+k
                found = 1
            k = k+1
            if k == 5:
                firstidx = wrd_idx+1
                break
        if k == 5:
            continue
        found = 0
        k = 0
        while found == 0:
            if stri[wrd_idx-k] == delim1:
                idx1 = wrd_idx-k
                found = 1
            k = k+1
            if k == 50:
                firstidx = wrd_idx+1
                break
        if k == 50:
            continue
        stri = stri[:idx1+len(wrd)]+stri[idx2+1:]
    return stri


def delete_after_words(stri, wrd1, wrd2):
    logger.info("delete_after_words")
    inds1 = list(find_all(stri, wrd1))
    inds2 = list(find_all(stri, wrd2))
    if len(inds1) > 0:
        if wrd2 == 'end':
            stri = stri[:inds1[0]]
            return stri
        stri2 = stri[0:inds1[0]]
        for k in range(0, len(inds2)):
            if inds2[k] > inds1[0]:
                stri2 += 'Name: '+stri[inds2[k]:]
                return stri2
        return stri
    return stri


def create_quiz_html(html_res, words_to_hide):
    logger.info("create_quiz_html")
    clean_html = html_res

    clean_html = reverse_between_words(
        clean_html, '<span style=" font-weight:600;">', '</span>', '<br />')
    capitalized_words_to_hide = [x.capitalize() for x in words_to_hide]
    words_to_hide += capitalized_words_to_hide

    for w in words_to_hide:
        clean_html = hide_text(clean_html, w)

    repl_dict = {}
    for w in words_to_hide:
        repl_dict[w] = len(w)*'_'
        repl_dict[w.capitalize()] = len(w)*'_'

    def helper(dic, match):
        word = match.group(0)
        return dic.get(word, word)

    clean_html = delete_between_words(
        clean_html,
        '<font size="6"><font size="6">',
        '<span class="wordclass">', '<br>')
    clean_html = delete_between_words2(
        clean_html,
        '<span style=" font-family:\'Arial Black\'; font-size:xx-large;">',
        '<br />', '</p>')
    clean_html = word_re.sub(partial(helper, repl_dict), clean_html)
    inds = list(find_all(clean_html, '▶'))
    for k in range(len(inds)):
        clean_html = delete_after_words(clean_html, '▶', '<')
    clean_html = reverse_between_words(
        clean_html, '<span style=" font-weight:600;">', '</span>', '<br />')
    return clean_html


def update_words_to_hide(full_headword, words_to_hide):
    # TODO rewrite. Dummy coding, return a lot of junk and f*cks up html file
    logger.info("extract_words_to_hide")

    full_headword = full_headword.encode(encoding='UTF-8', errors='strict')\
        .replace(b'\xcc\xa3', b'').replace(b'\xcc\xb1', b'').decode('utf-8')

    cleaner_raw_titel = delete_after_words(
        full_headword, '<span class="wordclass">', 'end')
    cleaner_raw_titel = cleaner_raw_titel\
        .replace('<span class="separator">·</span>', '')\
        .replace('<span class="flexion">&lt;', ':')\
        .replace('&gt;</span> <span class="wordclass">', ':')\
        .replace('<acronym title="verb">VERB</acronym>', '')\
        .replace('<acronym title="without object">ohne OBJ</acronym>', '')\
        .replace('<span class="verbclass">', '')\
        .replace('</span>', '')\
        .replace('<span class="wordclass">PREP', '')\
        .replace('<span class="object-case">', '')\
        .replace('ạ', 'a')\
        .replace('&lt;', ':')\
        .replace('&gt;', ':')\
        .replace('', '')
    cleaner_raw_titel = delete_between_words(cleaner_raw_titel, '<', '>', '>')
    cleaner_raw_titel = cleaner_raw_titel.replace('>', ' ').replace('<', ' ')
    cleaner_raw_titel = cleaner_raw_titel.replace('1', ' ').replace(
        '2', ' ').replace('3', ' ').replace('0', ' ')
    logger.debug('Raw Title: '+full_headword)
    if full_headword == '':
        return []
    if 'VERB' in full_headword or 'verb' in full_headword:
        if ':' in cleaner_raw_titel:
            logger.debug('Verb')
            base_words = cleaner_raw_titel.split(":")
            conjugations = base_words[1].split(", ")
            base_word = base_words[0].replace(' ', '')
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
                word_variants = conjugations[0].split()
                trenn_wort = prateritum[1]
                lentrennwort = len(trenn_wort)
                word_variants.append(base_word[lentrennwort:])
                word_variants.append(trenn_wort+'zu'+base_word[lentrennwort:])
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
                word_variants = conjugations[0].split()
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
                word_variants = conjugations[0].split()
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
            base_word = cleaner_raw_titel.replace(' ', '')
            word_variants = [base_word]
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
        cleaner_raw_titel = delete_between_words(
            cleaner_raw_titel, '<', '>', '>')
        cleaner_raw_titel = cleaner_raw_titel.replace(', ', ' ')\
            .replace('>', ' ')\
            .replace('<', ' ')\
            .replace('der ', ' ')\
            .replace('die ', ' ')\
            .replace('das ', ' ')
        if ':' in cleaner_raw_titel:
            base_word = cleaner_raw_titel.split(":")
            logger.debug(base_word)
            if ',' in base_word[1]:
                flexion = base_word[1].split(",")
            else:
                flexion = base_word[1].split()
            logger.debug(flexion)
            try:
                plural = flexion[1]
                wrdrr = plural
                word_variants = flexion
            except IndexError:
                conjugations = base_word[0].split()
                if (conjugations[0] == 'der' or
                    conjugations[0] == 'die' or
                        conjugations[0] == 'das'):
                    wrdrr = conjugations[1].replace('·', '').replace('', '')
                else:
                    wrdrr = conjugations[0].replace('·', '').replace('', '')
                word_variants = [wrdrr]
            word_variants.append(wrdrr+'e')
            word_variants.append(wrdrr+'en')
            word_variants.append(wrdrr+'er')
            word_variants.append(wrdrr+'em')
            word_variants.append(wrdrr+'es')
            word_variants.append(wrdrr+'n')
            word_variants.append(wrdrr+'r')
            word_variants.append(wrdrr+'m')
            word_variants.append(wrdrr+'s')
            conjugations = base_word[0].split()
            if conjugations[0] == 'der' or conjugations[0] == 'die' or conjugations[0] == 'das':
                wrdrr = conjugations[1].replace('·', '').replace('', '')
            else:
                wrdrr = conjugations[0].replace('·', '').replace('', '')
        else:
            word_variants = cleaner_raw_titel.split()
            logger.debug(word_variants)
            logger.debug(cleaner_raw_titel)
            if (word_variants[0] == 'der' or
                word_variants[0] == 'die' or
                    word_variants[0] == 'das'):
                wrdrr = word_variants[1].replace('·', '').replace('', '')
            else:
                wrdrr = word_variants[0].replace('·', '').replace('', '')
        word_variants.append(wrdrr+'e')
        word_variants.append(wrdrr+'en')
        word_variants.append(wrdrr+'er')
        word_variants.append(wrdrr+'em')
        word_variants.append(wrdrr+'es')
        word_variants.append(wrdrr+'n')
        word_variants.append(wrdrr+'r')
        word_variants.append(wrdrr+'m')
        word_variants.append(wrdrr+'s')
        word_variants.append(wrdrr)

    words_to_hide = words_to_hide + word_variants
    # workaround to ignore words containing special chars
    words_to_hide = [elem for elem in words_to_hide if all(
        c.isalnum() for c in elem)]
    return words_to_hide

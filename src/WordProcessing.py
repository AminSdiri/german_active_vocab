import logging
import re
from functools import partial

from utils import set_up_logger

logger = set_up_logger(__name__, level=logging.WARNING)

word_re = re.compile(r'\b[a-zA-Z]+\b')


def hide_text(quiz_text, selected_text2hide):
    logger.info("hide_text")
    quiz_text = quiz_text\
        .replace(' '+selected_text2hide+' ',
                 ' '+len(selected_text2hide)*'_'+' ')\
        .replace('>'+selected_text2hide+' ',
                 '>'+len(selected_text2hide)*'_'+' ')\
        .replace(' '+selected_text2hide+'<',
                 ' '+len(selected_text2hide)*'_'+'<')\
        .replace('>'+selected_text2hide+'<',
                 '>'+len(selected_text2hide)*'_'+'<')\
        .replace(' '+selected_text2hide+'\xa0',
                 ' '+len(selected_text2hide)*'_'+'\xa0')\
        .replace(' '+selected_text2hide+', ',
                 ' '+len(selected_text2hide)*'_'+', ')\
        .replace(' '+selected_text2hide+'.',
                 ' '+len(selected_text2hide)*'_'+'.')\
        .replace(' '+selected_text2hide+'&',
                 ' '+len(selected_text2hide)*'_'+'&')\
        .replace(';'+selected_text2hide+' ',
                 ';'+len(selected_text2hide)*'_'+' ')\
        .replace(' '+selected_text2hide+'?',
                 ' '+len(selected_text2hide)*'_'+'?')\
        .replace(';'+selected_text2hide+', ',
                 '<'+len(selected_text2hide)*'_'+', ')\
        .replace(' '+selected_text2hide+'!',
                 ' '+len(selected_text2hide)*'_'+'!')\
        .replace(' '+selected_text2hide+'\\',
                 ' '+len(selected_text2hide)*'_'+'\\')
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


def create_quiz_html(html_res, words2hide):
    logger.info("create_quiz_html")
    clean_html = html_res
    clean_html = reverse_between_words(
        clean_html, '<span style=" font-weight:600;">', '</span>', '<br />')
    capitalized_words2hide = [x.capitalize() for x in words2hide]
    words2hide += capitalized_words2hide
    for w in words2hide:
        clean_html = clean_html.replace(' '+w+' ', ' '+len(w)*'_'+' ')\
                               .replace('>'+w+' ', '>'+len(w)*'_'+' ')\
                               .replace(' '+w+'<', ' '+len(w)*'_'+'<')\
                               .replace('>'+w+'<', '>'+len(w)*'_'+'<')\
                               .replace(' '+w+', ', ' '+len(w)*'_'+', ')\
                               .replace(' '+w+'.', ' '+len(w)*'_'+'.')\
                               .replace(' '+w+'&', ' '+len(w)*'_'+'&')\
                               .replace(';'+w+' ', ';'+len(w)*'_'+' ')\
                               .replace(' '+w+'?', ' '+len(w)*'_'+'?')\
                               .replace(';'+w+', ', '<'+len(w)*'_'+', ')\
                               .replace(' '+w+'!', ' '+len(w)*'_'+'!')
    repl_dict = {}
    for w in words2hide:
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


def update_words2hide(full_headword, words2hide):
    logger.info("extract_words2hide")

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
            raw_word = cleaner_raw_titel.split(":")
            words = raw_word[1].split(", ")
            raw_word = raw_word[0].replace(' ', '')
            indiv_words = words[0].split()
            # try:
            prateritum = words[1].split()
            # except:
            #     prateritum = [raw_word[:-2]+'te']
            # try:
            rest_words = words[2].split()
            # except:
            #     rest_words = ['hat', raw_word[:-2]+'t']
            #     rest_words = ['hat', 'ge'+raw_word[:-2]+'t']
            if len(prateritum) == 2:
                logger.debug('trennbar')
                # trennbar = 1
                trenn_wort = prateritum[1]
                lentrennwort = len(trenn_wort)
                indiv_words.append(raw_word[lentrennwort:])
                indiv_words.append(trenn_wort+'zu'+raw_word[lentrennwort:])
                indiv_words.append(raw_word[lentrennwort:-1])
                indiv_words.append(raw_word[lentrennwort:-2]+'t')
                indiv_words.append(raw_word[lentrennwort:-2])
                indiv_words.append(raw_word[:-1])
                indiv_words.append(raw_word[:-2]+'t')
                indiv_words.append(raw_word[:-2])
                indiv_words.append(words[0][:-2]+'t')
                indiv_words.append(words[0][:-2])
                indiv_words.append(prateritum[0]+'t')
                if prateritum[0][-1] == 'e':
                    indiv_words.append(prateritum[0]+'n')
                else:
                    indiv_words.append(prateritum[0]+'en')
                indiv_words.append(prateritum[0]+'st')
                indiv_words.append(prateritum[0]+'t')
                indiv_words.append(prateritum[0])
                indiv_words.append(rest_words[1])
                indiv_words.append(rest_words[1]+'e')
                indiv_words.append(rest_words[1]+'es')
                indiv_words.append(rest_words[1]+'er')
            elif raw_word[0:2] == 'ab':
                logger.debug('false trennbar')
                indiv_words = words[0].split()
                indiv_words.append('ab')
                indiv_words.append(raw_word[2:-1])
                indiv_words.append(raw_word[2:-2]+'t')
                indiv_words.append(raw_word[2:-1]+'t')
                indiv_words.append(raw_word[2:-2])
                indiv_words.append(raw_word[2:-2]+'st')
                indiv_words.append(raw_word[2:-1]+'st')
                indiv_words.append(prateritum[0]+'t')
                if prateritum[0][-1] == 'e':
                    indiv_words.append(prateritum[0]+'n')
                else:
                    indiv_words.append(prateritum[0]+'en')
                indiv_words.append(prateritum[0]+'st')
                indiv_words.append(prateritum[0]+'t')
                indiv_words.append(prateritum[0])
                indiv_words.append(rest_words[1])
                indiv_words.append('ab'+'ge'+raw_word[2:-1]+'t')
            else:
                logger.debug('einfach')
                indiv_words = words[0].split()
                indiv_words.append(raw_word)
                indiv_words.append(raw_word[:-1])
                indiv_words.append(raw_word[:-1]+'e')
                indiv_words.append(words[0][:-2])
                indiv_words.append(words[0][:-2]+'t')
                indiv_words.append(words[0][:-2]+'et')
                indiv_words.append(raw_word[:-2]+'t')
                indiv_words.append(raw_word[:-2]+'et')
                indiv_words.append(raw_word[:-1]+'t')
                indiv_words.append(raw_word[:-1]+'et')
                indiv_words.append(prateritum[0])
                indiv_words.append(prateritum[0]+'st')
                indiv_words.append(prateritum[0]+'t')
                indiv_words.append(prateritum[0]+'n')
                indiv_words.append(raw_word+'d')
                # try:
                indiv_words.append(rest_words[1])
                # except:
                #     indiv_words.append('ge'+raw_word[:-2]+'t')
                #     indiv_words.append('ge'+raw_word[:-1]+'t')
        else:
            logger.debug('without flexion')
            raw_word = cleaner_raw_titel.replace(' ', '')
            indiv_words = [raw_word]
            indiv_words.append(raw_word[:-1])
            indiv_words.append(raw_word[:-1]+'e')
            indiv_words.append(raw_word[:-2])
            indiv_words.append(raw_word[:-2]+'e')
            indiv_words.append(raw_word[:-1]+'est')
            indiv_words.append(raw_word[:-2]+'st')
            indiv_words.append(raw_word[:-2]+'t')
            indiv_words.append(raw_word[:-2]+'et')
            indiv_words.append(raw_word[:-1]+'t')
            indiv_words.append(raw_word[:-1]+'et')
            indiv_words.append(raw_word[:-2]+'te')
            indiv_words.append(raw_word[:-2]+'test')
            indiv_words.append(raw_word[:-2]+'tet')
            indiv_words.append(raw_word[:-2]+'ten')
            indiv_words.append(raw_word[:-1]+'te')
            indiv_words.append(raw_word[:-1]+'test')
            indiv_words.append(raw_word[:-1]+'tet')
            indiv_words.append(raw_word[:-1]+'ten')
            indiv_words.append('ge'+raw_word[:-2]+'t')
            indiv_words.append('ge'+raw_word[:-1]+'t')
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
            raw_word = cleaner_raw_titel.split(":")
            logger.debug(raw_word)
            if ',' in raw_word[1]:
                flexion = raw_word[1].split(",")
            else:
                flexion = raw_word[1].split()
            logger.debug(flexion)
            try:
                plural = flexion[1]
                wrdrr = plural
                indiv_words = flexion
            except IndexError:
                words = raw_word[0].split()
                if (words[0] == 'der' or
                    words[0] == 'die' or
                        words[0] == 'das'):
                    wrdrr = words[1].replace('·', '').replace('', '')
                else:
                    wrdrr = words[0].replace('·', '').replace('', '')
                indiv_words = [wrdrr]
            indiv_words.append(wrdrr+'e')
            indiv_words.append(wrdrr+'en')
            indiv_words.append(wrdrr+'er')
            indiv_words.append(wrdrr+'em')
            indiv_words.append(wrdrr+'es')
            indiv_words.append(wrdrr+'n')
            indiv_words.append(wrdrr+'r')
            indiv_words.append(wrdrr+'m')
            indiv_words.append(wrdrr+'s')
            words = raw_word[0].split()
            if words[0] == 'der' or words[0] == 'die' or words[0] == 'das':
                wrdrr = words[1].replace('·', '').replace('', '')
            else:
                wrdrr = words[0].replace('·', '').replace('', '')
        else:
            indiv_words = cleaner_raw_titel.split()
            logger.debug(indiv_words)
            logger.debug(cleaner_raw_titel)
            if (indiv_words[0] == 'der' or
                indiv_words[0] == 'die' or
                    indiv_words[0] == 'das'):
                wrdrr = indiv_words[1].replace('·', '').replace('', '')
            else:
                wrdrr = indiv_words[0].replace('·', '').replace('', '')
        indiv_words.append(wrdrr+'e')
        indiv_words.append(wrdrr+'en')
        indiv_words.append(wrdrr+'er')
        indiv_words.append(wrdrr+'em')
        indiv_words.append(wrdrr+'es')
        indiv_words.append(wrdrr+'n')
        indiv_words.append(wrdrr+'r')
        indiv_words.append(wrdrr+'m')
        indiv_words.append(wrdrr+'s')
        indiv_words.append(wrdrr)

    words2hide = words2hide + indiv_words
    return words2hide

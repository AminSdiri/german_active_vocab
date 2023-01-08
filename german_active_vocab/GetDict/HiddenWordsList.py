from utils import set_up_logger

logger = set_up_logger(__name__)

def generate_hidden_words_list(dict_dict_content):
    # TODO (3) clean up
    logger.info("extract_hidden_words_list")
    word_variants = []

    for rom_idx in range(len(dict_dict_content)):
        headword = _get_prop_from_dict(dict_dict_content, rom_idx,looking_for='headword')
        wordclass = _get_prop_from_dict(dict_dict_content, rom_idx,looking_for='wordclass')
        genus = _get_prop_from_dict(dict_dict_content, rom_idx,looking_for='genus')
        flexions = _get_prop_from_dict(dict_dict_content, rom_idx,looking_for='flexion')
        flexions = flexions.replace('<', '').replace('>', '')
        if flexions:
            flexion_list = flexions.split(', ')
        else:
            flexion_list = []

        if headword == '':
            return word_variants

        word_variants.append(headword)

        if wordclass == 'verb':
            word_variants = _get_verb_flexions(word_variants, headword, flexion_list)
        else:
            word_variants = _other_than_verb_flexions(word_variants, headword, flexion_list)

        # workaround to ignore words containing special chars
        # hidden_words_list = [elem for elem in hidden_words_list if all(
        #     c.isalnum() for c in elem)]

        capitalized_word_variants = [x.capitalize() for x in word_variants]
        word_variants += capitalized_word_variants

        # remove duplicates
        word_variants = list(set(word_variants))

        logger.debug(f'Word variants:\n{word_variants}')

    return word_variants

def _get_prop_from_dict(dict_dict_content, rom_idx, looking_for):
    dict_level = dict_dict_content[rom_idx]
    if looking_for in dict_level:
        prop = dict_level[looking_for]
    else:
        prop = ''
    return prop

def _other_than_verb_flexions(word_variants, headword, flexion_list):
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
                #         wrdrr = conjugations[1].replace('·', '')
                #     else:
                #         wrdrr = conjugations[0].replace('·', '')
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
                # if (conjugations[0] == 'der'
                #       or conjugations[0] == 'die'
                #       or conjugations[0] == 'das'):
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

    # TODO (1) feminine cases 
    word_variants.append(headword+'e')
    word_variants.append(headword+'en')
    word_variants.append(headword+'er')
    word_variants.append(headword+'em')
    word_variants.append(headword+'es')
    word_variants.append(headword+'n')
    word_variants.append(headword+'r')
    word_variants.append(headword+'m')
    word_variants.append(headword+'s')

    return word_variants

def _get_verb_flexions(word_variants, headword, conjugations):
    if conjugations:
        logger.debug('Verb')
        base_word = headword
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
        else:
            prateritum = base_word
            perfekt = base_word
                    # reinziehen [ziehst, rein, zog rein, hat/ist reingezogen]
                    # from pons -_-
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
            word_variants.append(base_word[:-2]) # imperativ
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
    
    return word_variants
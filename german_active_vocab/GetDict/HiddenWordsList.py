from utils import set_up_logger

logger = set_up_logger(__name__)

def generate_hidden_words_list(dict_dict_content) -> tuple[list, dict[str, str]]:
    # TODO (3) clean up
    logger.info("extract_hidden_words_list")
    all_word_variants = []
    all_secondary_words = {}

    # TODO (1) every rom (header) should have a separate hidden_words list (example: for "Tisch", "auf" would be hidden because of "auftischen")
    for rom_idx in range(len(dict_dict_content)):
        headword = _get_prop_from_dict(dict_dict_content, rom_idx, looking_for='headword')
        wordclass = _get_prop_from_dict(dict_dict_content, rom_idx, looking_for='wordclass')
        genus = _get_prop_from_dict(dict_dict_content, rom_idx, looking_for='genus')
        flexions_str = _get_prop_from_dict(dict_dict_content, rom_idx, looking_for='flexion')
        flexions_str = flexions_str.replace('<', '').replace('>', '').replace('[', '').replace(']', '')
        if flexions_str:
            flexions = flexions_str.split(', ')
        else:
            flexions = []

        if headword == '':
            return [], {}

        if wordclass == 'verb':
            word_variants = _get_verb_flexions(headword, flexions)
            secondary_words = {}
        elif wordclass == 'noun':
            # TODO (1) make it also work for duden (wortart: substantiv, maskulin), standarize dict structs
            word_variants, secondary_words = _get_noun_flexions(headword, flexions, genus)
        else:
            word_variants = _other_than_verb_flexions(headword, flexions)
            secondary_words = {}

        # workaround to ignore words containing special chars
        # hidden_words_list = [elem for elem in hidden_words_list if all(c.isalnum() for c in elem)]

        # Add capitalized words
        capitalized_word_variants = [x.capitalize() for x in word_variants]
        word_variants += capitalized_word_variants

        # capitalize from 2nd char if first char is (
        capitalized_secondary_words = {k.capitalize(): v.capitalize() if v[0]!='(' else '('+v[1:].capitalize() for k,v in secondary_words.items()}
        secondary_words.update(capitalized_secondary_words)

        # append to persistant list, this keep a commun list for all headwords (not the best but easier)
        all_word_variants += word_variants
        all_secondary_words.update(secondary_words)

        logger.debug(f'Word variants:\n{word_variants}')
    
    # remove duplicates
    all_word_variants = list(set(all_word_variants))

    return all_word_variants, all_secondary_words

def _get_prop_from_dict(dict_dict_content: list, rom_idx: int, looking_for: str) -> str:
    if isinstance(dict_dict_content, dict):
        # dict from duden case (temporary)
        dict_level = dict_dict_content
    else:
        dict_level = dict_dict_content[rom_idx]
    if looking_for in dict_level:
        # temporary to fix flexion in saved dicts
        if looking_for == 'flexion':
            dict_level[looking_for] = dict_level[looking_for].replace('<', '[').replace('>', ']')
        # end temporary
        prop = dict_level[looking_for]
    else:
        prop = ''
    return prop

def _get_noun_flexions(headword: str, flexions: list, genus: str) -> tuple[list, dict[str, str]]:
    word_variants = [headword]
    if flexions:
        try:
            word_variants.append(flexions[1]) # plural
        except IndexError:
            pass
        word_variants = _add_normal_declinations(headword, word_variants)
    else:
        word_variants = _add_normal_declinations(headword, word_variants)

    # in case of nouns, the gender of a noun should be also hidden so that the user also learn it. 
    # secondary words get hidden (just articles for now) only if it comes before the noun to not give a clue about the gender,
    secondary_words = _construct_secondary_words(genus)

    return word_variants, secondary_words

def _construct_secondary_words(genus: str) -> dict[str, str]:
    # DONE (0) combine [ein, mein, dein, sein, ihr, unser, euer, kein, dies, jed, welch, all] with
    # the endings list ['', e, er, en ...] to get all secondary words and mark only the endings.
    base = ['ein', 'mein', 'dein', 'sein', 'ihr', 'unser', 'euer', 'kein', 'dies', 'jed', 'welch', 'all']
    secondary_words= {}

    if genus == 'der':
        defined_articles = ['der', 'den', 'dem',  'des']
        endings = ['', 'er', 'en', 'em', 'es']
    elif genus == 'die':
        defined_articles = ['die', 'der']
        endings = ['e', 'er', 'en']
    elif genus == 'das':
        defined_articles = ['das', 'dem',  'des']
        endings = ['', 'es', 'er', 'em']
    else:
        raise RuntimeError('Article should be der, die or das.')

    secondary_words = {key: f'({key})' for key in defined_articles}
    # before we used if ending else key to not put () if empty but we need them
    combined_base_endings = {key+ending: f'{key}({ending})' for ending in endings for key in base}
    secondary_words.update(combined_base_endings)

    return secondary_words
    
def _other_than_verb_flexions(headword: str, flexions: list) -> list:
    # TODO (2) add all cases 
    word_variants =[headword]
    if flexions:   # TODO (4) which flexions 
        word_variants = _add_normal_declinations(headword, word_variants)

    else:
        word_variants = _add_normal_declinations(headword, word_variants)

    return word_variants

def _add_normal_declinations(headword: str, word_variants: list) -> list:
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

def _get_verb_flexions(headword: str, conjugations: list) -> list:
    word_variants =[headword]
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

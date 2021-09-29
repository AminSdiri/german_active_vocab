from ParsingData.ParsingSoup import process_data_corpus

from utils import (remove_from_str,
                   set_up_logger)

logger = set_up_logger(__name__)


def parse_json_data(json_data, translate, word):
    '''
    convert json_data to standerized dict

    standerized dict structure:
    {
        'content':
        [   # ROMS
            {
                'headword': '',
                'wordclass': '',  # verb/adjektiv/name/adverb
                'flexion': '',  # [present, präteritum, perfekt]
                'genus': '',  # der/die/das
                ...
                'word_subclass':
                [   # ARABS
                    {
                        'verbclass': '',  # with_obj/without_obj
                        ...
                        'def_blocks':
                        [   # BLOCKS
                            {
                                'header_num': '',   # 1. /2. ...
                                'grammatical_construction': '',  # jd macht etw
                                'definition': '',
                                'example': '',  # []
                                'rhetoric': ''  # pejorativ...
                                'style': '',  # gebrauch
                                ...
                            },collapse all vscode
                            {..}, ..
                        ]
                    },
                    {..}, ..
                ]
            },
            {..}, ..
        ],
        'synonymes': [],
        'custom_examples':
            {
                'german': [],
                'english': []
            }
        'words_variants': []
    }
    '''

    dict_dict = [None] * len(json_data)

    for rom_idx, rom_level_json in enumerate(json_data):
        if "roms" in rom_level_json:
            dict_dict[rom_idx] = dict()
            rom_level_dict = dict_dict[rom_idx]
            rom_level_dict["word_subclass"] = [
                None] * len(rom_level_json["roms"])
            for arab_idx, arab_level_json in enumerate(rom_level_json["roms"]):
                rom_level_dict["word_subclass"][arab_idx] = dict()
                arab_level_dict = rom_level_dict["word_subclass"][arab_idx]

                # headword
                headword = arab_level_json["headword"]
                headword = remove_from_str(
                    headword, [b'\xcc\xa3', b'\xcc\xb1', b'\xc2\xb7'])
                rom_level_dict = update_dict_w_ignoring(
                    rom_level_dict, 'headword', headword)

                # wordclass
                if 'wordclass' in arab_level_json:
                    wordclass = arab_level_json["wordclass"]
                else:
                    wordclass = ''
                rom_level_dict = update_dict_w_ignoring(
                    rom_level_dict, 'wordclass', wordclass)

                # extract everything from full_headword into dict items
                full_headword = arab_level_json["headword_full"]
                (rom_level_dict,
                 arab_level_dict) = populate_rom_and_arab_level_dict(
                    full_headword, rom_level_dict, arab_level_dict)

                arab_level_dict['def_blocks'] = []
                def_idx = 0
                for definition_block in arab_level_json["arabs"]:

                    block_number = definition_block["header"]

                    if ('Zusammen- oder Getrenntschreibung' in block_number
                        or 'Zusammenschreibung' in block_number
                            or 'Getrennt' in block_number
                            or 'Großschreibung' in block_number):
                        # ignoring can be also done here
                        continue

                    arab_level_dict['def_blocks'].append(dict())
                    def_block_dict = arab_level_dict['def_blocks'][def_idx]
                    block_number_list_of_dicts = process_data_corpus(
                        block_number)
                    # header_number sometime contains other elements (style..)
                    # putting those in sibling entries
                    for element in block_number_list_of_dicts:
                        if element["class_name"] == 'NO_CLASS':
                            def_block_dict["header_num"] = element["class_content"]
                        else:
                            key_class = element["class_name"]
                            source_content = element["class_content"]
                            def_block_dict = update_dict_w_appending(
                                def_block_dict, key_class, source_content)

                    gra_was_in_block = False
                    previous_class = ''
                    source_and_target_dicts = definition_block["translations"]
                    if translate:
                        for definition_part in source_and_target_dicts:
                            datasource = definition_part["source"]
                            datatarget = definition_part["target"]
                            def_block_dict = update_dict_w_appending(
                                def_block_dict, 'source', datasource)
                            def_block_dict = update_dict_w_appending(
                                def_block_dict, 'target', datatarget)
                    else:
                        for definition_part in source_and_target_dicts:
                            data_corpus = definition_part["source"]
                            corpus_list_of_dicts = process_data_corpus(
                                data_corpus)
                            for element in corpus_list_of_dicts:
                                key_class = element["class_name"]
                                source_content = element["class_content"]

                                if key_class == 'NO_CLASS':
                                    if source_content:
                                        logger.info('Naked Text found!\n'
                                                    f': {source_content}')
                                    continue

                                (def_block_dict,
                                    previous_class,
                                    gra_was_in_block,
                                    def_idx) = process_def_block_separation(
                                    arab_level_dict,
                                    previous_class,
                                    key_class,
                                    def_idx,
                                    gra_was_in_block)

                                def_block_dict = update_dict_w_appending(
                                    def_block_dict, key_class, source_content)
                    def_idx += 1

        elif "source" in rom_level_json:
            gra_was_in_block = False
            previous_class = ''
            def_idx = 0
            data_corpus = rom_level_json["source"]

            dict_dict[rom_idx] = dict()
            rom_level_dict = dict_dict[rom_idx]
            rom_level_dict["headword"] = word
            rom_level_dict["word_subclass"] = [None]
            arab_idx = 0
            rom_level_dict["word_subclass"][arab_idx] = dict()
            arab_level_dict = rom_level_dict["word_subclass"][arab_idx]
            arab_level_dict['def_blocks'] = [None]
            arab_level_dict['def_blocks'][def_idx] = dict()
            def_block_dict = arab_level_dict['def_blocks'][def_idx]

            corpus_list_of_dicts = process_data_corpus(data_corpus)
            for element in corpus_list_of_dicts:
                key_class = element["class_name"]
                source_content = element["class_content"]
                (def_block_dict,
                    previous_class,
                    gra_was_in_block,
                    def_idx) = process_def_block_separation(
                    arab_level_dict,
                    previous_class,
                    key_class,
                    def_idx,
                    gra_was_in_block)
                def_block_dict = update_dict_w_appending(
                    def_block_dict, key_class, source_content)
        else:
            raise KeyError(
                '"roms" or (in the worst case) "source" key is expected"')

    return dict_dict


def process_def_block_separation(arab_level_dict, previous_class, key_class,
                                 def_idx, gra_was_in_block):
    '''sometimes multiple def_blocks in json are put in the same sub-entrie.
    this function decide whether to increment the def_idx and therefor
    separate them or not.'''

    if ((previous_class in ['grammatical_construction', 'idiom_proverb'])
            and not (key_class in ['grammatical_construction', 'idiom_proverb'])):
        gra_was_in_block = True

    if ((previous_class == 'example' and key_class != 'example')
            or (gra_was_in_block
                and (key_class in ['grammatical_construction', 'idiom_proverb']))
            or (previous_class == 'definition' and key_class != 'example')):
        # add a def block
        def_idx += 1
        arab_level_dict['def_blocks'].append(dict())
        def_block_dict = arab_level_dict['def_blocks'][def_idx]
        def_block_dict["header_num"] = ''
    else:
        # stay in the same block
        def_block_dict = arab_level_dict['def_blocks'][def_idx]

    previous_class = key_class

    return def_block_dict, previous_class, gra_was_in_block, def_idx


def update_dict_w_appending(def_block_dict, key_class, source_content):
    # if entry already exist, make it a list and append
    if key_class in def_block_dict:
        # raise Exception(f'{key_class} element cannot be overwritten')
        if not isinstance(def_block_dict[key_class], list):
            def_block_dict[key_class] = [def_block_dict[key_class]]
        def_block_dict[key_class].append(source_content)
    else:
        def_block_dict[key_class] = source_content

    return def_block_dict


def update_dict_w_ignoring(rom_level_dict, key, value):
    # only replace entry if content is ''
    if key in rom_level_dict:
        logger.debug(f'Key: {key}\n'
                     f'Old value: {rom_level_dict[key]}\n'
                     f'New value: {value}')
        if rom_level_dict[key] == '':
            rom_level_dict[key] = value
    else:
        rom_level_dict[key] = value

    return rom_level_dict


def populate_rom_and_arab_level_dict(full_headword,
                                     rom_level_dict, arab_level_dict):
    if full_headword != '':
        corpus_list_of_dicts = process_data_corpus(full_headword)
        for element in corpus_list_of_dicts:
            key_class = element["class_name"]
            source_content = element["class_content"]

            if key_class == 'NO_CLASS':
                if source_content:
                    logger.info('Naked Text found!\n'
                                f'Text: {source_content}')
                continue

            if key_class == 'separator':
                # ignoring classes should be done here
                # (can also be done in treat_class(), but less optimal)
                continue

            if key_class in ['headword', 'wordclass', 'flexion', 'genus']:
                rom_level_dict = update_dict_w_ignoring(
                    rom_level_dict, key_class, source_content)
            elif key_class in arab_level_dict:
                continue
            else:
                if len(arab_level_dict) > 1:
                    logger.warning('subclass entry already have a key: '
                                   f'{arab_level_dict.keys()}')
                    # bug (low priority ) style: 'inf' isn't supposed
                    # to be appended here sondern, it have to go to
                    # it's children
                    # also idiom_proverb (hereinlegen for exp)
                    # but wont treat it because there's no nice way to.
                    # It's is from the side of Pons
                arab_level_dict[key_class] = source_content

    return rom_level_dict, arab_level_dict

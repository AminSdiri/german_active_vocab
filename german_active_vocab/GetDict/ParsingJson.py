from typing import Any

from GetDict.ParsingSoup import extract_classes_names_and_content
from .HiddenWordsList import generate_hidden_words_list
from utils import (remove_from_str,
                   set_up_logger)

logger = set_up_logger(__name__)

# TODO (2) simplify code. too many local variables, too many nested blocks (pylint) 

'''
    pons dict structure:
    {
        'content':  # ROM LEVEL list[dict]
                    [    
                        {
                            'headword': '',
                            'wordclass': '',  # verb/adjektiv/name/adverb
                            'flexion': '',  # [present, präteritum, perfekt]
                            'genus': '',  # der/die/das
                            'hidden_words_list': []
                            'secondary_words_to_hide': {}
                            'word_subclass':  # ARAB LEVEL list[dict]
                                            [
                                                {
                                                    'verbclass': '',  # with_obj/without_obj
                                                    ... sometimes style amd rethoric are also here (should it stay here?)
                                                    'def_blocks':  # BLOCKS list[dict]
                                                                    [
                                                                        {
                                                                            'header_num': '',   # 1. /2. ...
                                                                            'grammatical_construction': '',  # jd macht etw
                                                                            'definition': '',
                                                                            'example': '',  # []
                                                                            'rhetoric': ''  # pejorativ...
                                                                            'style': '',  # gebrauch
                                                                            ...
                                                                        },
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

def construct_dict_content_from_json(json_data, search_word: str, translate: bool = False) -> list[dict[str,Any]]:

    if not json_data:
        # not found in pons
        return []

    dict_content = [None] * len(json_data)

    for rom_idx, rom_level_json in enumerate(json_data):
        if "roms" in rom_level_json:
            dict_content[rom_idx] = {}
            rom_level_dict = dict_content[rom_idx]
            rom_level_dict["word_subclass"] = [None] * len(rom_level_json["roms"])
            for arab_idx, arab_level_json in enumerate(rom_level_json["roms"]):
                rom_level_dict["word_subclass"][arab_idx] = {}
                arab_level_dict = rom_level_dict["word_subclass"][arab_idx]

                # headword
                headword = remove_from_str(text=arab_level_json["headword"],
                                           substrings=[b'\xcc\xa3', b'\xcc\xb1', b'\xc2\xb7'])
                rom_level_dict = _update_dict_w_ignoring(rom_level_dict, 'headword', headword)

                # wordclass
                wordclass = arab_level_json.get('wordclass', '')
                rom_level_dict = _update_dict_w_ignoring(rom_level_dict, 'wordclass', wordclass)

                # extract everything from full_headword into rom and arab dict levels
                (rom_level_dict,
                 arab_level_dict) = _populate_rom_and_arab_levels(arab_level_json["headword_full"],
                                                                  rom_level_dict, arab_level_dict)

                arab_level_dict['def_blocks'] = populate_def_blocks(translate, arab_level_json["arabs"])

        elif "source" in rom_level_json:
            gra_was_in_block = False
            previous_class = ''
            def_idx = 0
            data_corpus = rom_level_json["source"]

            dict_content[rom_idx] = {}
            rom_level_dict = dict_content[rom_idx]
            rom_level_dict["headword"] = search_word
            rom_level_dict["word_subclass"] = [None]
            arab_idx = 0
            rom_level_dict["word_subclass"][arab_idx] = {}
            arab_level_dict = rom_level_dict["word_subclass"][arab_idx]
            arab_level_dict['def_blocks'] = [None]
            arab_level_dict['def_blocks'][def_idx] = {}
            def_block_dict = arab_level_dict['def_blocks'][def_idx]

            extracted_classes = extract_classes_names_and_content(data_corpus)
            for element in extracted_classes:
                class_name = element["class_name"]
                class_content = element["class_content"]

                # add to the current block or a new one
                (previous_class,
                    gra_was_in_block,
                    go_next) = _process_def_block_separation(previous_class,
                                                            class_name,
                                                            gra_was_in_block)
                if go_next:
                    def_idx += 1
                    arab_level_dict['def_blocks'].append({})
                    def_block_dict = arab_level_dict['def_blocks'][def_idx]
                    def_block_dict["header_num"] = ''
                else:
                    def_block_dict = arab_level_dict['def_blocks'][def_idx]
                    
                def_block_dict = _update_dict_w_appending(def_block_dict, class_name, class_content)
        else:
            raise KeyError('"roms" or (in the worst case) "source" key is expected"')

    dict_content = generate_hidden_words_list(dict_content)

    return dict_content

def populate_def_blocks(translate: bool, json_definition_blocks: list[dict]) -> list[dict[str, Any]]:
    def_blocks = []
    def_idx = 0
    for json_definition_block in json_definition_blocks:
        def_blocks.append({})
        def_block_dict = def_blocks[def_idx]

        def_block_dict, skip = clean_up_header_number(def_block_dict, block_number=json_definition_block["header"])
        if skip:
            continue

        gra_was_in_block = False
        previous_class = ''
        source_and_target_dicts = json_definition_block["translations"]
        if translate:
            for definition_part in source_and_target_dicts:
                def_block_dict = _update_dict_w_appending(def_block_dict, 'source', definition_part["source"])
                def_block_dict = _update_dict_w_appending(def_block_dict, 'target', definition_part["target"])
        else:
            for definition_part in source_and_target_dicts:
                extracted_classes = extract_classes_names_and_content(definition_part["source"])
                for element in extracted_classes:
                    class_name = element["class_name"]
                    class_content = element["class_content"]

                    if class_name == 'NO_CLASS':
                        if class_content:
                            logger.warning(f'Naked Text found!\n: {class_content}')
                        continue
                    
                    # add to the current block or to a new one
                    (previous_class,
                    gra_was_in_block,
                    go_next) = _process_def_block_separation(previous_class,
                                                            class_name,
                                                            gra_was_in_block)
                    if go_next:
                        def_idx += 1
                        def_blocks.append({})
                        def_block_dict = def_blocks[def_idx]
                        def_block_dict["header_num"] = ''
                    else:
                        def_block_dict = def_blocks[def_idx]

                    def_block_dict = _update_dict_w_appending(def_block_dict, class_name, class_content)
        def_idx += 1
    return def_blocks

def clean_up_header_number(def_block_dict: dict[str, Any], block_number: str) -> tuple[dict[str, Any], bool]:
    '''header_number sometime contains other elements (style..)
        putting those in sibling entries'''
    
    # ignore blocks that contain those headers
    skip = False
    if ('Zusammen- oder Getrenntschreibung' in block_number
                        or 'Zusammenschreibung' in block_number
                            or 'Getrennt' in block_number
                            or 'Großschreibung' in block_number):
        # ignoring can be also done here
        skip = True
        return def_block_dict, skip

    block_number_list_of_dicts = extract_classes_names_and_content(block_number)
    for element in block_number_list_of_dicts:
        if element["class_name"] == 'NO_CLASS':
            def_block_dict["header_num"] = element["class_content"]
        else:
            def_block_dict = _update_dict_w_appending(def_block_dict,
                                                      class_name=element["class_name"],
                                                      class_content=element["class_content"])
    return def_block_dict, skip

def _process_def_block_separation(previous_class: str,
                                  current_class: str,
                                  gra_was_in_block: bool) -> tuple[str, bool, bool]:
    '''sometimes multiple def_blocks in json are put in the same sub-entrie.
    this function decide whether to increment the def_idx and therefore
    separate them or not.'''

    if ((previous_class in ['grammatical_construction', 'idiom_proverb'])
            and not (current_class in ['grammatical_construction', 'idiom_proverb'])):
        gra_was_in_block = True

    # add a def block or stay in the same block
    go_next = ((previous_class == 'example' and current_class != 'example')
            or (gra_was_in_block and (current_class in ['grammatical_construction', 'idiom_proverb']))
            or (previous_class == 'definition' and current_class != 'example'))

    previous_class = current_class

    return previous_class, gra_was_in_block, go_next

def _update_dict_w_appending(def_block_dict: dict[str, str|list[str]],
                             class_name: str,
                             class_content: str) -> dict[str, str | list[str]]:
    # if entry already exist, make it a list and append
    if class_name in def_block_dict:
        # raise Exception(f'{key_class} element cannot be overwritten')
        if not isinstance(def_block_dict[class_name], list):
            def_block_dict[class_name] = [def_block_dict[class_name]]
        def_block_dict[class_name].append(class_content)
    else:
        def_block_dict[class_name] = class_content

    return def_block_dict

def _update_dict_w_ignoring(rom_level_dict: dict[str, Any], key: str, value: str) -> dict[str, Any]:
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

def _populate_rom_and_arab_levels(full_headword: str,
                                  rom_level_dict: dict[str, Any],
                                  arab_level_dict: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ''' Put ['headword', 'wordclass', 'flexion', 'genus'] in the rom_level (header) 
    and move everything else to the arab_level'''

    if full_headword != '':
        extracted_classes = extract_classes_names_and_content(full_headword)
        for element in extracted_classes:
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
                if key_class == 'flexion':
                    source_content = source_content.replace('<', '[').replace('>', ']')
                rom_level_dict = _update_dict_w_ignoring(rom_level_dict, key_class, source_content)
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

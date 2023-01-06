import json
import subprocess
from settings import dict_src_path, dict_data_path, anki_cfg
from utils import read_str_from_file, write_str_to_file
import ast
from PushToAnki import Anki
from SavingToQuiz import wrap_words_to_learn_in_clozes, generate_hidden_words_list
from itertools import zip_longest

# TODO mark words added to anki as added to anki in dict_dict and/or wordlist.csv
# DONE add manually hidden words to dict_dict hidden_words_list
def get_definitions_from_dict_dict(dict_dict, info='definition'):
    definitions_list = []
    for big_section in dict_dict['content']:
        if "word_subclass" not in big_section:
            # it's a dict from duden
            continue
        for small_section in big_section["word_subclass"]:
            # lenna fama style(umg..), grammatical use, 

            for def_block in small_section["def_blocks"]:
                # lenna fama definitions w examples

                for h3_key,h3_value in def_block.items():
                    if h3_key == info:
                        if isinstance(h3_value, list):
                            definitions_list += h3_value
                        else:
                            definitions_list.append(h3_value)
                    else:
                        print(f'Hint: you can also get {h3_key} from the dict')

    return definitions_list
             
def extract_synonymes_in_html(dict_dict):
    if 'synonymes' in dict_dict:
        synonymes = dict_dict['synonymes']
        syns_list_of_strings = []
        for syns in synonymes:
            syns_list_of_strings.append(', '.join(syns))
        synonymes = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in syns_list_of_strings]) + '</ul>'
    else:
        synonymes = ''
    return synonymes
    
files = (dict_data_path / 'dict_dicts').glob("*.json")
files_path = list(files)
files = [file.stem for file in files_path]
print('Rest: ', len(files))
k=0

for file_path, word in zip(files_path, files):
    word = word.replace('_standerised', '').replace('_du', '')
    print('opening ', word)
    dict_str = read_str_from_file(file_path)
    dict_dict = ast.literal_eval(dict_str)

    # TODO STRUCT (1) BUG dicts saved from duden are not the same as those saved from Pons!! (different outer structure)
    try:
        german_phrases = dict_dict['custom_examples']['german']
    except TypeError:
        continue
    english_translations = dict_dict['custom_examples']['english']


    definitions_list = get_definitions_from_dict_dict(dict_dict, info='definition')
    definitions = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in definitions_list]) + '</ul>'

    examples_list = get_definitions_from_dict_dict(dict_dict, info='example')
    examples = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in examples_list]) + '</ul>'
    
    synonymes = extract_synonymes_in_html(dict_dict)

    if german_phrases:
        # this is temporary to add hidden_words_list to all enteries, otherwise always read from dict
        if 'hidden_words_list' not in dict_dict:
            hidden_words_list = generate_hidden_words_list(dict_dict)
            dict_dict['hidden_words_list'] = hidden_words_list
            write_str_to_file(file_path, json.dumps(dict_dict))
        else:
            hidden_words_list = dict_dict['hidden_words_list']

        for german_phrase, english_translation in zip_longest(german_phrases, english_translations):
            if english_translation is None:
                english_translation = ''
            front_with_cloze_wrapping = wrap_words_to_learn_in_clozes(german_phrase, hidden_words_list)

            with Anki(base=anki_cfg['base'],
                        profile=anki_cfg['profile']) as a:
                note_dupeOrEmpty = a.add_notes_single(cloze=front_with_cloze_wrapping,
                                   hint1=synonymes,
                                   hint2=english_translation,
                                   hint3=definitions,
                                   answer_extra=word,
                                   tags='',
                                   model=anki_cfg['model'],
                                   deck=anki_cfg['deck'],
                                   overwrite_notes=anki_cfg['overwrite'])
                # fixing issues                   
                if note_dupeOrEmpty == 3:
                    k += 1
                    if k > 10:  raise RuntimeError('yezzi')
                    # hidden_words_list = generate_hidden_words_list(dict_dict)
                    # dict_dict['hidden_words_list'] = hidden_words_list
                    # write_str_to_file(file_path, json.dumps(dict_dict))
                    command = ['python3', str(dict_src_path / 'main.py'), word]
                    print(command)
                    subprocess.Popen(command)

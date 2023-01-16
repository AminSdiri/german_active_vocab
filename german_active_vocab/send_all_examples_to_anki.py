import subprocess
from GetDict.GenerateDict import extract_synonymes_in_html_format, get_definitions_from_dict_dict
from settings import DICT_SRC_PATH, DICT_DATA_PATH, ANKI_CONFIG
from utils import read_str_from_file
import ast
from PushToAnki import Anki
from SavingToQuiz import wrap_words_to_learn_in_clozes
from itertools import zip_longest

# TODO mark words added to anki as added to anki in dict_dict and/or wordlist.csv
# DONE add manually hidden words to dict_dict hidden_words_list


if __name__ == '__main__':
    files = (DICT_DATA_PATH / 'dict_dicts').glob("*.json")
    files_path = list(files)
    files = [file.stem for file in files_path]
    print('Rest: ', len(files))
    k=0
    amount = len(files)

    for file_path, word in zip(files_path, files):
        k+=1
        word = word.replace('_standerised', '')
        print('opening ', word)
        dict_str = read_str_from_file(file_path)
        dict_dict = ast.literal_eval(dict_str)

        try:
            german_phrases = dict_dict['custom_examples']['german']
        except TypeError:
            continue
        english_translations = dict_dict['custom_examples']['english']

        definitions_list = get_definitions_from_dict_dict(dict_dict, info='definition')
        definitions = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in definitions_list]) + '</ul>'

        examples_list = get_definitions_from_dict_dict(dict_dict, info='example')
        examples = '<ul>' + ''.join([f'<li>{elem}</li>' for elem in examples_list]) + '</ul>'
        
        synonymes = extract_synonymes_in_html_format(dict_dict)

        if german_phrases:
            for german_phrase, english_translation in zip_longest(german_phrases, english_translations):
                if english_translation is None:
                    english_translation = ''
                front_with_cloze_wrapping = wrap_words_to_learn_in_clozes(german_phrase, dict_dict, file_path)

                with Anki(base=ANKI_CONFIG['base'],
                            profile=ANKI_CONFIG['profile']) as a:
                    note_dupeOrEmpty = a.add_notes_single(cloze=front_with_cloze_wrapping,
                                    hint1=synonymes,
                                    hint2=english_translation,
                                    hint3=definitions,
                                    answer_extra=word,
                                    tags='',
                                    model=ANKI_CONFIG['model'],
                                    deck=ANKI_CONFIG['deck'],
                                    overwrite_notes=ANKI_CONFIG['overwrite'])
                # fixing issues                   
                if note_dupeOrEmpty == 3:
                    command = ['python3', str(DICT_SRC_PATH / 'main.py'), word]
                    print(f'reached {k} from {amount}')
                    if '{{c1::' not in front_with_cloze_wrapping:
                        print(dict_dict['hidden_words_list'])
                    subprocess.Popen(command)

import subprocess
from GetDict.GenerateDict import extract_synonymes_in_html, get_definitions_from_dict_dict
from settings import dict_src_path, dict_data_path, anki_cfg
from utils import read_str_from_file
import ast
from PushToAnki import Anki
from SavingToQuiz import wrap_words_to_learn_in_clozes
from itertools import zip_longest

# TODO mark words added to anki as added to anki in dict_dict and/or wordlist.csv
# DONE add manually hidden words to dict_dict hidden_words_list


if __name__ == '__main__':
    files = (dict_data_path / 'dict_dicts').glob("*.json")
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
            for german_phrase, english_translation in zip_longest(german_phrases, english_translations):
                if english_translation is None:
                    english_translation = ''
                front_with_cloze_wrapping = wrap_words_to_learn_in_clozes(german_phrase, dict_dict, file_path)

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
                    # hidden_words_list = generate_hidden_words_list(dict_dict)
                    # dict_dict['hidden_words_list'] = hidden_words_list
                    # write_str_to_file(file_path, json.dumps(dict_dict))
                    command = ['python3', str(dict_src_path / 'main.py'), word]
                    print(f'reached {k} from {amount}')
                    if '{{c1::' not in front_with_cloze_wrapping:
                        print(dict_dict['hidden_words_list'])
                    subprocess.Popen(command)

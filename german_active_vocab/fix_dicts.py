import json
import subprocess
from GetDict.HiddenWordsList import generate_hidden_words_list
from settings import DICT_SRC_PATH, DICT_DATA_PATH
from utils import read_str_from_file, write_str_to_file
import ast
import os

# ken el fichier deja mawjouda erreur
# filename feha _du w dict fih headword -> source duden w fasakh _du mel fichier w sajjel ama na7i overwriting
# fama 7keya mehom barka -> erreur
# ezouz mafamech -> source pons w sajjel 

if __name__ == '__main__':
    files = (DICT_DATA_PATH / 'word_dicts').glob("*.json")
    files_path = list(files)
    files = [file.stem for file in files_path]
    print('Rest: ', len(files))
    k=0

    for file_path, word in zip(files_path, files):
        k+=1
        if '_en' in word or '_fr' in word:   continue

        dict_str = read_str_from_file(file_path)
        word_dict = ast.literal_eval(dict_str)
        
        # dict_from_duden = False
        # if 'headword' in word_dict:
        #     dict_from_duden = True

        # filename_du = False
        # if '_du' in word:
        #     filename_du = True

        # if dict_from_duden and filename_du:
        #     word_dict['source'] = 'duden'
        #     renamed_path = dict_data_path / 'word_dicts' / f"{word.replace('_du', '')}.json"
        #     if os.path.exists(renamed_path):
        #         print('conflicting path exists, copy other file first to tst for overwrites')
        #         print(f'Duden Word: {word} examples:')
        #         print(word_dict['custom_examples']['german'])
        #         print(word_dict['custom_examples']['english'])
        #         pons_dict_str = read_str_from_file(renamed_path)
        #         pons_word_dict = ast.literal_eval(pons_dict_str)
        #         print(f'Pons Word examples:')
        #         print(pons_word_dict['custom_examples']['german'])
        #         print(pons_word_dict['custom_examples']['english'])
        #     else:
        #         write_str_to_file(renamed_path, json.dumps(word_dict))
        #         os.remove(file_path)

        # if 'source' not in word_dict and dict_from_duden:
        #     word_dict['source'] = 'duden'
        #     write_str_to_file(file_path, json.dumps(word_dict))

        # if 'source' not in word_dict and not dict_from_duden:
        #     word_dict['source'] = 'pons'
        #     write_str_to_file(file_path, json.dumps(word_dict))

        # if word_dict['source'] == 'pons' and dict_from_duden:
        #     raise RuntimeError

        # print(1)
        # print('next')
        ############################################

        # if 'hidden_words_list' not in word_dict:
        #     print(f'{k}/{len(files)}')
        #     word_dict['hidden_words_list'] = generate_hidden_words_list(word_dict)
        #     write_str_to_file(file_path, json.dumps(word_dict))

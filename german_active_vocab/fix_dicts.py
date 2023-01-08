import json
import subprocess
from GetDict.HiddenWordsList import generate_hidden_words_list
from settings import dict_src_path, dict_data_path
from utils import read_str_from_file, write_str_to_file
import ast
import os

# ken el fichier deja mawjouda erreur
# filename feha _du w dict fih headword -> source duden w fasakh _du mel fichier w sajjel ama na7i overwriting
# fama 7keya mehom barka -> erreur
# ezouz mafamech -> source pons w sajjel 

if __name__ == '__main__':
    files = (dict_data_path / 'dict_dicts').glob("*.json")
    files_path = list(files)
    files = [file.stem for file in files_path]
    print('Rest: ', len(files))
    k=0

    for file_path, word in zip(files_path, files):
        k+=1
        if '_en' in word or '_fr' in word:   continue

        dict_str = read_str_from_file(file_path)
        dict_dict = ast.literal_eval(dict_str)
        
        # dict_from_duden = False
        # if 'headword' in dict_dict:
        #     dict_from_duden = True

        # filename_du = False
        # if '_du' in word:
        #     filename_du = True

        # if dict_from_duden and filename_du:
        #     dict_dict['source'] = 'duden'
        #     renamed_path = dict_data_path / 'dict_dicts' / f"{word.replace('_du', '')}.json"
        #     if os.path.exists(renamed_path):
        #         print('conflicting path exists, copy other file first to tst for overwrites')
        #         print(f'Duden Word: {word} examples:')
        #         print(dict_dict['custom_examples']['german'])
        #         print(dict_dict['custom_examples']['english'])
        #         pons_dict_str = read_str_from_file(renamed_path)
        #         pons_dict_dict = ast.literal_eval(pons_dict_str)
        #         print(f'Pons Word examples:')
        #         print(pons_dict_dict['custom_examples']['german'])
        #         print(pons_dict_dict['custom_examples']['english'])
        #     else:
        #         write_str_to_file(renamed_path, json.dumps(dict_dict))
        #         os.remove(file_path)

        # if 'source' not in dict_dict and dict_from_duden:
        #     dict_dict['source'] = 'duden'
        #     write_str_to_file(file_path, json.dumps(dict_dict))

        # if 'source' not in dict_dict and not dict_from_duden:
        #     dict_dict['source'] = 'pons'
        #     write_str_to_file(file_path, json.dumps(dict_dict))

        # if dict_dict['source'] == 'pons' and dict_from_duden:
        #     raise RuntimeError

        # print(1)
        # print('next')
        ############################################

        # if 'hidden_words_list' not in dict_dict:
        #     print(f'{k}/{len(files)}')
        #     dict_dict['hidden_words_list'] = generate_hidden_words_list(dict_dict)
        #     write_str_to_file(file_path, json.dumps(dict_dict))

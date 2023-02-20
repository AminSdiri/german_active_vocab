import json
import subprocess
import time
from GetDict.HiddenWordsList import generate_hidden_words_list
from settings import DICT_SRC_PATH, DICT_DATA_PATH
from utils import read_str_from_file, write_str_to_file
import ast
import os

# ken el fichier deja mawjouda erreur
# filename feha _du w dict fih headword -> source duden w fasakh _du mel fichier w sajjel ama na7i overwriting
# fama 7keya mehom barka -> erreur
# ezouz mafamech -> source pons w sajjel
# BUG (0) umgang manajamtch nbookmakri die Art und Weise, wie man <acronym title="jemanden">jdn</acronym> oder etwas behandelt

if __name__ == '__main__':
    files = (DICT_DATA_PATH / 'html').glob("*.html")
    files_path = list(files)
    files = [file.stem for file in files_path]
    print('Rest: ', len(files))
    k=0

    for file_path, word in zip(files_path, files):
        print('Executing Command')
        os.popen(f'firefox {file_path}') # open html in firefox
        command_str = f'python3 {DICT_SRC_PATH} -w "{word}"'
        os.popen(command_str)
        time.sleep(10)
        k+=1
        if k % 10 == 0:
            time.sleep(600)
            #break
        
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

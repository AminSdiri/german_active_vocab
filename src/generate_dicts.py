import subprocess
from pathlib import Path
from time import sleep
import os
import pandas as pd

from utils import replace_umlauts

# TODO 3 put untreated htmls (from old directory) in html2 and launch this script to update them
# make sure custom_examples get captured

dict_data_path = Path.home() / 'Dictionnary'
# files = (dict_data_path / 'html').glob("*.html")
# files = list(files)
# files.sort(key=os.path.getmtime, reverse=True)
# files = [x.stem for x in files]

# if type(index) is str:
#         history_entry = index
#     else:
#         history_entry = index.text()

# history_entry_path = dict_data_path / 'html' /(history_entry+'.html')
# text = read_str_from_file(history_entry_path)
# self.history_window.txt_cont.insertHtml(text)

files = (dict_data_path / 'html2' ).glob("*.html")
files = list(files)
files = [file.stem for file in files]
word_list_htmls = [file for file in files if 'quiz' not in file]
k = 0
print('Rest: ', len(word_list_htmls))
for word in word_list_htmls:
    if k<10:
        # files = (dict_data_path / 'dict_dicts').glob(f"{replace_umlauts(word)}*")
        # files = list(files)
        # print(word)
        # if not files:
        print('opening ', word)
        # subprocess.Popen(['python3', '/home/mani/Dokumente/active_vocabulary/src/Dict.py', word, 'html'])
        subprocess.Popen(['python3', '/home/mani/Dokumente/active_vocabulary/src/Dict.py', f"{word} new_dict"])
        file_to_del = (dict_data_path / 'html2' / f'{word}.html')
        os.remove(file_to_del)
        file_to_del = (dict_data_path / 'html2' / f'{word}.quiz.html')
        os.remove(file_to_del)
        k += 1
sleep(1000)
from german_active_vocab.settings import dict_data_path, anki_cfg
from german_active_vocab.utils import read_str_from_file
import ast
from german_active_vocab.PushToAnki import Anki
from german_active_vocab.WordProcessing import wrap_words_to_learn_in_clozes
from german_active_vocab.SavingToQuiz import update_words_to_hide

files = (dict_data_path / 'dict_dicts').glob("*.json")
files_path = list(files)
files = [file.stem for file in files_path]
print('Rest: ', len(files))
for file_path, word in zip(files_path, files):
    print('opening ', word)
    dict_str = read_str_from_file(file_path)
    dict_dict = ast.literal_eval(dict_str)

    word = self.def_obj.word
    german_phrase, english_phrase = self.get_example_fileds_content()
    words_2_hide = update_words_to_hide(dict_dict)
    front_with_cloze_wrapping = wrap_words_to_learn_in_clozes(german_phrase, words_2_hide)

    fields = [front_with_cloze_wrapping, english_phrase, word]

    with Anki(base=anki_cfg['base'],
                profile=anki_cfg['profile']) as a:
        a.add_notes_single(fields=fields, tags='', model=anki_cfg['model'], deck=anki_cfg['deck'])

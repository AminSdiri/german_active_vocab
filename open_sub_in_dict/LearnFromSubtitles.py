#!/usr/bin/env python3
#coding=utf-8

'''Pre-requisits
- enable HTTP web interface in VLC:
Settings > Show all settings > Main interfaces > Check web checkbox > On the left select "Lua" from the tree > use "vlc" as HTTP password (without quotes) > Save settings > Restart VLC
- install xmllint: 
(for ubuntu) sudo apt install libxml2-utils
- set a Shortcutkey to launch GetCurrentVLCTime.sh

* when you have a Movie/Show you like in your wished language:
1. Download subs in both source and translation languages, 2 Options: 
    - The hard way: get subs manually and rename the files to video.lang.srt format where lang is "ger" or "eng".
    - The easy way: You can do this automaticly with the VLC extension VLsub (usually preinstalled with VLC, otherwise download and set up from here https://addons.videolan.org/p/1154045) under Tools, check the option add lang suffixe in filename in VLsub configuration to get the right format.
2. Sync sub programmatically with ffsubsync (https://github.com/smacke/ffsubsync) from terminal. you can run it twice for better synchronisation:
    2.1 ffs video.mp4 -i video.ger.srt -o video.ger.srt (sync ger subtitle to ger video
    2.2 ffs video.ger.srt -i video.eng.srt -o video.eng.srt (sync eng subs to ger subs)
3. Enjoy watching your movie and call the learn subs shortcut when you hear/see a new word (don't try to catch them all, I was there..)
'''

import sys
import os
import glob
from pathlib import Path
import traceback
import pysrt
from plyer import notification
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow,
                             QPushButton,
                             QWidget,
                             QLineEdit,
                             QTextEdit,
                             QProgressBar)
import qdarktheme

from TreatSubtitles import clean_subtitle, fetch_subs_from_timestamp, format_example, get_phrase_text

# DONE (1) add button to automaticly execute second step
# DONE (0) Clean up code
# TODO (1) deal with paths properly
# DONE (0) refract repeating code into function
# TODO (0) separate Model from View
# TODO (2) move to the right directory or a separate project
# TODO (3) scrollable subtitles look with greyed out previous and next lines (for context)

# videos_path = Path('/media/mani/50 jdida') / 'Videos' / 'Shows'
videos_path = Path.home() / 'Videos'
script_path = Path(__file__).parent.parent.resolve() / 'german_active_vocab'
        
class BigWindow(QWidget):
    def __init__(self, parent=None):
        super(BigWindow, self).__init__(parent)

        self.example_field_ger = QTextEdit(self)
        self.example_field_ger.move(5, 5)
        self.example_field_ger.resize(490, 140)

        self.example_field_eng = QTextEdit(self)
        self.example_field_eng.move(5, 150)
        self.example_field_eng.resize(490, 145)

        self.line = QLineEdit(self)
        self.line.move(5, 355)
        self.line.resize(200, 45)
        self.line.setPlaceholderText("type the new word...")

        self.append_previous_button = QPushButton('Add Prev', self)
        self.append_previous_button.move(5, 305)
        self.append_previous_button.resize(90, 25)

        self.jump_previous_button = QPushButton('Previous', self)
        self.jump_previous_button.move(105, 305)
        self.jump_previous_button.resize(90, 25)

        self.jump_next_button = QPushButton('Next', self)
        self.jump_next_button.move(300, 305)
        self.jump_next_button.resize(90, 25)

        self.append_next_button = QPushButton('Add Next', self)
        self.append_next_button.move(400, 305)
        self.append_next_button.resize(90, 25)

        self.save_button = QPushButton('Save\nto Dict', self)
        self.save_button.move(210, 355)
        self.save_button.resize(70, 45)

        self.sync_button = QPushButton('Sync \nSubs', self)
        self.sync_button.move(420, 355)
        self.sync_button.resize(70, 45)

        self.progress = QProgressBar(self)
        self.progress.move(5, 335)
        self.progress.resize(485, 15)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.big_window = BigWindow(self)
        self.current_slice_deu = ''
        self.slice_indexes_deu = []
        self.current_slice_eng = ''
        self.slice_indexes_eng = []

        if len(sys.argv) == 1+2:
            self.file_name = sys.argv[1].replace('.mp4', '')\
                                        .replace('.avi', '')\
                                        .replace('.mkv', '')
            self.curr_time = sys.argv[2]
            self.get_srts()
            self.start_big_window()
            self.go_to_sub()
        else:
            self.start_big_window()

    def start_big_window(self):
        self.resize(500, 410)
        self.move(100, 150)
        self.setWindowTitle("Sub-Learner")
        self.setCentralWidget(self.big_window)

        self.big_window.line.returnPressed.connect(self.save_method)
        self.big_window.jump_previous_button.clicked.connect(self.go_previous)
        self.big_window.jump_next_button.clicked.connect(self.go_next)
        self.big_window.append_previous_button.clicked.connect(self.add_previous)
        self.big_window.append_next_button.clicked.connect(self.add_next)
        self.big_window.save_button.clicked.connect(self.save_method)
        self.big_window.sync_button.clicked.connect(self.sync_subtitles)

        self.show()

    def go_to_sub(self):
        print('go2subs')

        hour, minute, second = self.curr_time.split(':')
        minute = int(minute) + 60*int(hour)
        second = int(second)
        
        current_slice_deu, self.slice_indexes_deu = fetch_subs_from_timestamp(srt_object=self.subs_de,
                                                                              minute=minute,
                                                                              second=second)
        current_slice_eng, self.slice_indexes_eng = fetch_subs_from_timestamp(srt_object=self.subs_en,
                                                                              minute=minute,
                                                                              second=second)

        self.update_view(current_slice_deu, current_slice_eng)

    def get_srts(self):

        self.subs_de, self.path_de = self.get_srt_object(lang='ger')
        self.subs_en, self.path_en = self.get_srt_object(lang='eng') 

    def get_srt_object(self, lang):
        if lang not in ('ger', 'eng'):
            raise RuntimeError('language must be german or english')
    
        # find srt files
        if "S0" in self.file_name:
            name_show, number_episode = self.file_name.split()
            # name_show = name_show.decode("utf8")
            search_pattern = f'{name_show}*{number_episode}*{lang}*.srt'
            search_path = videos_path / name_show / search_pattern
        else:
            name_show = self.file_name
            # TODO add support for ' char in title (exp: before the devil knows you're dead)
            # name_show = name_show.decode("utf8")
            search_path = videos_path / f'{name_show}*{lang}*.srt'
        
        for file in glob.glob(str(search_path)):
            srt_file_path = file
        
        # read srt objects
        try:
            srt_object = pysrt.open(srt_file_path)
        except UnicodeDecodeError: # UnicodeEncodeError:
            srt_object = pysrt.open(srt_file_path, encoding='iso-8859-1') # error_handling=pysrt.ERROR_PASS

        return srt_object, srt_file_path

    def go_previous(self):
        # go to next sub_de
        jump_to = 'previous'
        mode = 'replace'
        current_slice_deu, self.slice_indexes_deu = get_phrase_text(srt_object=self.subs_de,
                                                                             slice_indexes=self.slice_indexes_deu,
                                                                             jump_to=jump_to,
                                                                             mode=mode)
        current_slice_eng, self.slice_indexes_eng = get_phrase_text(srt_object=self.subs_en,
                                                                             slice_indexes=self.slice_indexes_eng,
                                                                             jump_to=jump_to,
                                                                             mode=mode)

        self.update_view(current_slice_deu, current_slice_eng)

    def update_progress(self):
        progress = (max(self.slice_indexes_deu)/len(self.subs_de))*100
        self.big_window.progress.setValue(int(progress))

    def go_next(self):
        # go to next sub_de
        jump_to = 'next'
        mode = 'replace'
        current_slice_deu, self.slice_indexes_deu = get_phrase_text(srt_object=self.subs_de,
                                                                    slice_indexes=self.slice_indexes_deu,
                                                                    jump_to=jump_to,
                                                                    mode=mode)
        current_slice_eng, self.slice_indexes_eng = get_phrase_text(srt_object=self.subs_en,
                                                                    slice_indexes=self.slice_indexes_eng,
                                                                    jump_to=jump_to,
                                                                    mode=mode)

        self.update_view(current_slice_deu, current_slice_eng)

    def add_previous(self):
        jump_to = 'previous'
        mode = 'append'
        current_slice_deu, self.slice_indexes_deu = get_phrase_text(srt_object=self.subs_de,
                                                                    slice_indexes=self.slice_indexes_deu,
                                                                    jump_to=jump_to,
                                                                    mode=mode)
        current_slice_eng, self.slice_indexes_eng = get_phrase_text(srt_object=self.subs_en,
                                                                    slice_indexes=self.slice_indexes_eng,
                                                                    jump_to=jump_to,
                                                                    mode=mode)

        self.update_view(current_slice_deu, current_slice_eng)

    def add_next(self):
        jump_to = 'next'
        mode = 'append'
        current_slice_deu, self.slice_indexes_deu = get_phrase_text(srt_object=self.subs_de,
                                                                    slice_indexes=self.slice_indexes_deu,
                                                                    jump_to=jump_to,
                                                                    mode=mode)
        current_slice_eng, self.slice_indexes_eng = get_phrase_text(srt_object=self.subs_en,
                                                                    slice_indexes=self.slice_indexes_eng,
                                                                    jump_to=jump_to,
                                                                    mode=mode)

        self.update_view(current_slice_deu, current_slice_eng)

    def update_view(self, current_sub_de, current_sub_en):
        self.big_window.example_field_ger.clear()
        self.big_window.example_field_eng.clear()
        self.big_window.example_field_ger.insertPlainText(clean_subtitle(current_sub_de))
        self.big_window.example_field_eng.insertPlainText(clean_subtitle(current_sub_en))
        self.update_progress()
        self.show()

    def save_method(self):
        ''' open with active Vocabulary trainer'''
        # updated
        print('save_method')

        german_example = self.big_window.example_field_ger.toPlainText()
        german_example = format_example(video_title=self.file_name,
                                        example=german_example)
        english_example = self.big_window.example_field_eng.toPlainText()
        english_example = format_example(video_title=self.file_name,
                                         example=english_example)

        print('Executing Command')
        command_str = (f'python3 {script_path} -w "{self.big_window.line.text()}" -g "{german_example}" -e "{english_example}"')
        print(command_str)
        os.popen(command_str)

    def sync_subtitles(self):
        video_absolute_path = str(self.path_de).replace('.ger.srt', '.mp4')

        sync_to_video_command_str = (f'ffs "{video_absolute_path}" -i "{self.path_de}" -o "{self.path_de}"')
        sync_to_str_command_str = (f'ffs "{self.path_de}" -i "{self.path_en}" -o "{self.path_en}"')
        print('Synching Subtitles: ')
        print(sync_to_video_command_str)
        print(sync_to_str_command_str)
        # TODO (3) use QPrecess? https://stackoverflow.com/questions/19409940/how-to-get-output-system-command-in-qt
        os.popen(sync_to_video_command_str)
        os.popen(sync_to_str_command_str)
        os.popen(sync_to_video_command_str)
        os.popen(sync_to_str_command_str)
        import subprocess # TODO (3) better? if I want to launch the command in a separate terminal
        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', sync_to_str_command_str], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

def excepthook(exc_type, exc_value, exc_tb):
    formatted_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", formatted_traceback)
    notification.notify(title='An Error Occured',
                        message=exc_value.args[0],
                        timeout=10)
    
    # show error in Qt MessageBox
    # msg = QMessageBox()
    # msg.setIcon(QMessageBox.Critical)
    # msg.setText("An Error Occured")
    # msg.setInformativeText(exc_value.args[0])
    # msg.setWindowTitle("Error")

    QApplication.quit() # or sys.exit(0)? 

if __name__ == '__main__':
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    w = MainWindow()
    sys.exit(app.exec_())

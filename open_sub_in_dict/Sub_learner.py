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
import pysrt
from pathlib import Path
import traceback
from plyer import notification
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow,
                             QPushButton,
                             QWidget,
                             QLineEdit,
                             QTextEdit,
                             QProgressBar)
import qdarktheme

# DONE (1) add button to automaticly execute second step
# DONE (0) Clean up code
# TODO (1) deal with paths properly
# TODO (0) refract repeating code into function
# TODO (0) separate Model from View
# TODO (2) move to the right directory or a separate project
# TODO (3) scrollable subtitles look with greyed out previous and next lines (for context)

# videos_path = Path('/media/mani/50 jdida') / 'Videos' / 'Shows'
videos_path = Path.home() / 'Videos'
script_path = Path.home() / 'Dokumente' / 'Algorithms' / 'german_active_vocab' / 'german_active_vocab'


def clean_subtitle(subs):
    subs = subs.replace('</i>', '')\
        .replace('<i>', '')\
        .replace('– –', '–')\
        .replace('-', '–')\
        .replace('– –', '–')\
        .replace("\n", " ")
    return subs


class BigWindow(QWidget):
    def __init__(self, parent=None):
        super(BigWindow, self).__init__(parent)

        self.Deu_cont = QTextEdit(self)
        self.Deu_cont.move(5, 5)
        self.Deu_cont.resize(490, 295)

        self.Eng_cont = QTextEdit(self)
        self.Eng_cont.move(500, 5)
        self.Eng_cont.resize(490, 295)

        self.line = QLineEdit(self)
        self.line.move(400, 310)
        self.line.resize(200, 40)

        self.prv_button = QPushButton('Previous', self)
        self.prv_button.move(5, 350)

        self.nxt_button = QPushButton('Next', self)
        self.nxt_button.move(105, 350)

        self.apr_button = QPushButton('Add Prev', self)
        self.apr_button.move(205, 350)

        self.anx_button = QPushButton('Add Next', self)
        self.anx_button.move(305, 350)

        self.sv_button = QPushButton('Save', self)
        self.sv_button.move(405, 350)

        self.sync_button = QPushButton('Sync', self)
        self.sync_button.move(605, 350)

        self.progress = QProgressBar(self)
        self.progress.setGeometry(5, 300, 400, 40)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setGeometry(535, 150, 210, 50)
        if len(sys.argv) == 1+2:
            self.file_name = sys.argv[1].replace('.mp4', '').replace('.avi', '').replace('.mkv', '')
            self.curr_time = sys.argv[2]
            self.get_srts()
            self.start_BigWindow()
            self.go_to_sub()
        else:
            self.start_BigWindow()

    def start_BigWindow(self):
        self.resize(1000, 400)
        self.move(100, 150)
        self.ToolTab = BigWindow(self)
        self.setWindowTitle("Sub-Learner")
        self.setCentralWidget(self.ToolTab)
        self.ToolTab.line.returnPressed.connect(self.save_method)
        self.ToolTab.prv_button.clicked.connect(self.go_previous)
        self.ToolTab.nxt_button.clicked.connect(self.go_next)
        self.ToolTab.apr_button.clicked.connect(self.add_previous)
        self.ToolTab.anx_button.clicked.connect(self.add_next)
        self.ToolTab.sv_button.clicked.connect(self.save_method)
        self.ToolTab.sync_button.clicked.connect(self.sync_subtitles)
        self.show()

    def go_to_sub(self):
        print('go2subs')

        hour, minute, second = self.curr_time.split(':')
        minute = int(minute) + 60*int(hour)
        
        # progressivly expand time window until a subtitle is found
        for time_window in range(1, 60):
            parts_de = self.subs_de.slice(starts_before={'minutes': int(minute),
                                                        'seconds': int(second)+2*time_window},
                                        ends_after={'minutes': int(minute),
                                                    'seconds': int(second)-2*time_window})
            if parts_de:
                break
            if time_window == 60:
                raise Exception(f'No German Subtitles found between {hour}:{minute-2}:{second} and {hour}:{minute+2}:{second}')

        self.index_list_de = [part.index for part in parts_de]

        current_sub_de = ''.join([f' – {part.text}' for part in parts_de])

        print('Deu: '+current_sub_de)

        for time_window in range(1, 60):
            parts_en = self.subs_en.slice(starts_before={'minutes': int(minute),
                                                        'seconds': int(second)+2*time_window},
                                        ends_after={'minutes': int(minute),
                                                    'seconds': int(second)-2*time_window})
            if parts_en:
                break
            if time_window == 60:
                raise Exception(f'No English Subtitles found between {hour}:{minute-2}:{second} and {hour}:{minute+2}:{second}')

        self.index_list_en = [part.index for part in parts_en]

        current_sub_en = ''.join([f' – {part.text}' for part in parts_en])
        print('Eng: '+current_sub_en)

        self.update_view(current_sub_de, current_sub_en)

    def get_srts(self):
        # updated
        # TODO use same methode for both lang
        print(self.curr_time)
        if "S0" in self.file_name:
            name_show, number_episode = self.file_name.split()
            print(name_show)
            print(number_episode)
            search_pattern_ger = f'{name_show}*{number_episode}*Ger*.srt'
            search_path_de = videos_path / name_show / search_pattern_ger
            search_pattern_eng = f'{name_show}*{number_episode}*Eng*.srt'
            search_path_en = videos_path / name_show / search_pattern_eng
            for file in glob.glob(str(search_path_de)):
                print(file)
                self.path_de = file
            for file in glob.glob(str(search_path_en)):
                print(file)
                self.path_en = file
        else:
            search_path_de = videos_path / f'{self.file_name}*ger*.srt'
            search_path_en = videos_path / f'{self.file_name}*eng*.srt'
            for file in glob.glob(str(search_path_de)):
                self.path_de = file
            for file in glob.glob(str(search_path_en)):
                self.path_en = file

        try:
            self.subs_de = pysrt.open(self.path_de)
        except UnicodeDecodeError: # UnicodeEncodeError:
            self.subs_de = pysrt.open(self.path_de, encoding='iso-8859-1')  

        try:
            self.subs_en = pysrt.open(self.path_en)
        except UnicodeDecodeError:
            self.subs_en = pysrt.open(self.path_en, encoding='iso-8859-1') # error_handling=pysrt.ERROR_PASS

    def go_previous(self):
        # go to next sub_de
        previous_de_sub_index = min(self.index_list_de)-1
        self.index_list_de = [previous_de_sub_index]
        current_sub_de = self.subs_de[previous_de_sub_index]
        current_sub_de = current_sub_de.text

        previous_en_sub_index = min(self.index_list_en)-1
        self.index_list_en = [previous_en_sub_index]
        current_sub_en = self.subs_de[previous_en_sub_index]
        current_sub_en = current_sub_en.text


        # TODO (2) Why?
        # # get start_timestamp + end_timestamp
        # sub_start_minutes = current_sub_de.start.minutes
        # sub_start_seconds = current_sub_de.start.seconds - 2
        # sub_end_minutes = current_sub_de.end.minutes
        # sub_end_seconds = current_sub_de.end.seconds + 2
        # sub_end_hours = current_sub_de.end.hours
        # sub_start_hours = current_sub_de.start.hours
        # sub_end_minutes += 60*sub_end_hours
        # sub_start_minutes += 60*sub_start_hours

        # # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        # parts_en = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
        #                                           'seconds': sub_end_seconds},
        #                            ends_after={'minutes': sub_start_minutes,
        #                                        'seconds': sub_start_seconds})
                                               
        # current_sub_en = ''.join([f' – {part.text}' for part in parts_en])

        self.update_view(current_sub_de, current_sub_en)

    def update_progress(self):
        progress = (max(self.index_list_de)/len(self.subs_de))*100
        self.ToolTab.progress.setValue(int(progress))

    def go_next(self):
        # go to next sub_de
        next_de_sub_index = max(self.index_list_de)+1
        self.index_list_de = [next_de_sub_index]
        current_sub_de = self.subs_de[next_de_sub_index]
        current_sub_de = current_sub_de.text

        next_en_sub_index = max(self.index_list_en)+1
        self.index_list_en = [next_en_sub_index]
        current_sub_en = self.subs_en[next_en_sub_index]
        current_sub_en = current_sub_en.text
        
        # same, why?
        # # get start_timestamp and end_timestamp
        # sub_start_minutes = current_sub_de.start.minutes
        # sub_start_seconds = current_sub_de.start.seconds - 2
        # sub_end_minutes = current_sub_de.end.minutes
        # sub_end_seconds = current_sub_de.end.seconds + 2
        # sub_end_hours = current_sub_de.end.hours
        # sub_start_hours = current_sub_de.start.hours
        # sub_end_minutes += 60*sub_end_hours
        # sub_start_minutes += 60*sub_start_hours

        # self.ToolTab.Deu_cont.clear()
        # self.ToolTab.Eng_cont.clear()
        # # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        # parts = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
        #                                           'seconds': sub_end_seconds},
        #                            ends_after={'minutes': sub_start_minutes,
        #                                        'seconds': sub_start_seconds})
        # current_sub_en = ''
        # for part in parts:
        #     current_sub_en += ' – ' + part.text

        self.update_view(current_sub_de, current_sub_en)

    def add_previous(self):
        self.index_list_de.insert(0, min(self.index_list_de)-1)
        current_sub_de = ''.join([f' – {self.subs_de[x].text}' for x in self.index_list_de])

        self.index_list_en.insert(0, min(self.index_list_en)-1)
        current_sub_en = ''.join([f' – {self.subs_en[x].text}' for x in self.index_list_en])

        # Why
        # first_sub = self.subs_de[min(self.index_list_de)-1]
        # last_sub = self.subs_de[max(self.index_list_de)]
        # sub_start_minutes = first_sub.start.minutes
        # sub_start_seconds = first_sub.start.seconds - 2
        # sub_end_minutes = last_sub.end.minutes
        # sub_end_seconds = last_sub.end.seconds + 2
        # sub_end_hours = last_sub.end.hours
        # sub_start_hours = first_sub.start.hours
        # sub_end_minutes += 60*sub_end_hours
        # sub_start_minutes += 60*sub_start_hours

        # self.ToolTab.Deu_cont.clear()
        # self.ToolTab.Eng_cont.clear()
        # # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        # parts = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
        #                                           'seconds': sub_end_seconds},
        #                            ends_after={'minutes': sub_start_minutes,
        #                            'seconds': sub_start_seconds})
        # current_sub_en = ''
        # for part in parts:
        #     current_sub_en += ' – ' + part.text
        
        self.update_view(current_sub_de, current_sub_en)

    def add_next(self):
        self.index_list_de.append(max(self.index_list_de) + 1)
        current_sub_de = ''.join([f' – {self.subs_de[x].text}' for x in self.index_list_de])

        self.index_list_en.append(max(self.index_list_en) + 1)
        current_sub_en = ''.join([f' – {self.subs_en[x].text}' for x in self.index_list_en])

        # why again
        # first_sub = self.subs_de[min(self.index_list)]
        # last_sub = self.subs_de[new_index]
        # sub_start_minutes = first_sub.start.minutes
        # sub_start_seconds = first_sub.start.seconds - 2
        # sub_end_minutes = last_sub.end.minutes
        # sub_end_seconds = last_sub.end.seconds + 2
        # sub_end_hours = last_sub.end.hours
        # sub_start_hours = first_sub.start.hours
        # sub_end_minutes += 60*sub_end_hours
        # sub_start_minutes += 60*sub_start_hours

        # # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        # parts = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
        #                                           'seconds': sub_end_seconds},
        #                            ends_after={'minutes': sub_start_minutes,
        #                            'seconds': sub_start_seconds})
        # current_sub_en = ''
        # for part in parts:
        #     current_sub_en += ' – ' + part.text

        self.update_view(current_sub_de, current_sub_en)

    def update_view(self, current_sub_de, current_sub_en):
        self.ToolTab.Deu_cont.clear()
        self.ToolTab.Eng_cont.clear()
        self.ToolTab.Deu_cont.insertPlainText(clean_subtitle(current_sub_de))
        self.ToolTab.Eng_cont.insertPlainText(clean_subtitle(current_sub_en))
        self.update_progress()
        self.show()

    def save_method(self):
        ''' open with active Vocabulary trainer'''
        # updated
        print('save_method')

        Beispiel_de = self.ToolTab.Deu_cont.toPlainText()
        Beispiel_de = self.format_example(Beispiel_de)

        Beispiel_en = self.ToolTab.Eng_cont.toPlainText()
        Beispiel_en = self.format_example(Beispiel_en)

        print('Executing Command')
        command_str = (f'python3 {script_path} -w "{self.ToolTab.line.text()}" -g "{Beispiel_de}" -e "{Beispiel_en}"')
        print(command_str)
        os.popen(command_str)

    def format_example(self, example: str) -> str:
        # updated
        example = example.replace("'", "//QUOTE").replace('"', "//DOUBLEQUOTE")
        example += f' ({self.file_name})'
        example = example.strip()
        return example

    def sync_subtitles(self):
        video_absolute_path = str(self.path_de).replace('.ger.srt', '.mp4')

        sync_to_video_command_str = (f'ffs "{video_absolute_path}" -i "{self.path_de}" -o "{self.path_de}"')
        sync_to_str_command_str = (f'ffs "{self.path_de}" -i "{self.path_en}" -o "{self.path_en}"')
        print('Synching Subtitles: ')
        print(sync_to_video_command_str)
        print(sync_to_str_command_str)
        # TODO use QPrecess? https://stackoverflow.com/questions/19409940/how-to-get-output-system-command-in-qt
        os.popen(sync_to_video_command_str)
        os.popen(sync_to_str_command_str)
        os.popen(sync_to_video_command_str)
        os.popen(sync_to_str_command_str)
        import subprocess # better? if I want to launch the command in a separate terminal
        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', sync_to_str_command_str], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
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

#!/usr/bin/env python3
#coding=utf-8

import pysrt
import sys
import os
import glob
from pathlib import Path
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow,
                             QPushButton,
                             QWidget,
                             QLineEdit,
                             QTextEdit,
                             QProgressBar)

videos_path = Path.home() / 'Videos' / 'Shows'


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
        # self.line.setFocus()
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
        self.progress = QProgressBar(self)
        self.progress.setGeometry(5, 300, 400, 40)
        # self.startBtn = QPushButton('Start')
        # self.startBtn.move(605, 350)
        # self.pauseBtn = QPushButton('Pause')
        # self.pauseBtn.move(705, 350)
        # self.endBtn = QPushButton('Stop')
        # self.endBtn.move(805, 350)
        # self.timer = QTimer()
        # self.curr_time = QtCore.QTime(00, 00, 00)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setGeometry(535, 150, 210, 50)
        self.word = ''
        # self.subs_de = pysrt.open(self.path_de)
        # self.subs_en = pysrt.open(self.path_en)
        self.index_de = -1
        nbargin = len(sys.argv) - 1
        print(nbargin)
        if nbargin == 2:
            self.file_name = sys.argv[1].replace(
                '.mp4', '').replace('.avi', '').replace('.mkv', '')
            self.curr_time = sys.argv[2]
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
        self.ToolTab.line.setText(self.word)
        self.ToolTab.line.returnPressed.connect(self.save_method)
        self.ToolTab.prv_button.clicked.connect(self.go_previous)
        self.ToolTab.nxt_button.clicked.connect(self.go_next)
        self.ToolTab.apr_button.clicked.connect(self.add_previous)
        self.ToolTab.anx_button.clicked.connect(self.add_next)
        self.ToolTab.sv_button.clicked.connect(self.save_method)
        # self.timer.timeout.connect(self.show_subs_by_time)
        # self.startBtn.clicked.connect(self.startTimer)
        # self.endBtn.clicked.connect(self.endTimer)
        # self.pauseBtn.clicked.connect(self.pauseTimer)
        self.show()

    def go_to_sub(self):
        print('go2subs')
        print(self.curr_time)
        if "S0" in self.file_name:
            name_show, number_episode = self.file_name.split()
            print(name_show)
            print(number_episode)
            search_pattern_ger = f'{name_show}*{number_episode}*Ger*.srt'
            search_path_de = videos_path / name_show / search_pattern_ger
            search_pattern_eng = f'{name_show}*{number_episode}*Eng*.srt'
            search_path_en = videos_path / name_show / search_pattern_eng
            for file in glob.glob(search_path_de):
                print(file)
                self.path_de = file
            for file in glob.glob(search_path_en):
                print(file)
                self.path_en = file
        else:
            name_show = self.file_name
            search_path_de = videos_path / 'Movies' / f'{name_show}*Ger*.srt'
            search_path_en = videos_path / 'Movies' / f'{name_show}*Eng*.srt'
            print(search_path_de)
            for file in glob.glob(search_path_de):
                self.path_de = file
            for file in glob.glob(search_path_en):
                self.path_en = file
        try:
            self.subs_de = pysrt.open(self.path_de)
        except UnicodeEncodeError:
            self.subs_de = pysrt.open(self.path_de, encoding='iso-8859-1')
        self.subs_en = pysrt.open(self.path_en)
        hour, minute, second = self.curr_time.split(':')
        minute = int(minute) + 60*int(hour)
        parts_de = self.subs_de.slice(starts_before={'minutes': int(minute),
                                                     'seconds': int(second)+2},
                                      ends_after={'minutes': int(minute),
                                                  'seconds': int(second)-2})
        current_sub_de = ''
        self.index_de = parts_de[0].index
        self.index_list = [self.index_de]
        for part in parts_de:
            current_sub_de += ' – ' + part.text
        print('Deu: '+current_sub_de)
        parts_en = self.subs_en.slice(starts_before={'minutes': int(minute),
                                                     'seconds': int(
            second)+2}, ends_after={'minutes': int(minute),
                                    'seconds': int(second)-2})
        current_sub_en = ''
        self.index_en = parts_en[0].index
        for part in parts_en:
            current_sub_en += ' – ' + part.text
        print('Eng: '+current_sub_en)
        self.ToolTab.Deu_cont.insertPlainText(clean_subtitle(current_sub_de))
        self.ToolTab.Eng_cont.insertPlainText(clean_subtitle(current_sub_en))
        self.show()

    def go_previous(self):
        # go to next sub_de
        self.index_de -= 1
        self.index_list = [self.index_de]
        current_sub_de = self.subs_de[self.index_de]
        # get start_timestamp + end_timestamp
        sub_start_minutes = current_sub_de.start.minutes
        sub_start_seconds = current_sub_de.start.seconds - 2
        sub_end_minutes = current_sub_de.end.minutes
        sub_end_seconds = current_sub_de.end.seconds + 2
        sub_end_hours = current_sub_de.end.hours
        sub_start_hours = current_sub_de.start.hours
        sub_end_minutes += 60*sub_end_hours
        sub_start_minutes += 60*sub_start_hours

        self.ToolTab.Deu_cont.clear()
        self.ToolTab.Eng_cont.clear()

        # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        parts = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
                                                  'seconds': sub_end_seconds},
                                   ends_after={'minutes': sub_start_minutes,
                                               'seconds': sub_start_seconds})
        current_sub_en = ''
        for part in parts:
            current_sub_en += ' – ' + part.text
        # show
        self.ToolTab.Deu_cont.insertPlainText(
            clean_subtitle(current_sub_de.text))
        self.ToolTab.Eng_cont.insertPlainText(clean_subtitle(current_sub_en))
        progress = (self.index_de/len(self.subs_de))*100
        self.ToolTab.progress.setValue(progress)
        self.show()

    def go_next(self):
        # go to next sub_de
        self.index_de += 1
        self.index_list = [self.index_de]
        current_sub_de = self.subs_de[self.index_de]

        # get start_timestamp and end_timestamp
        sub_start_minutes = current_sub_de.start.minutes
        sub_start_seconds = current_sub_de.start.seconds - 2
        sub_end_minutes = current_sub_de.end.minutes
        sub_end_seconds = current_sub_de.end.seconds + 2
        sub_end_hours = current_sub_de.end.hours
        sub_start_hours = current_sub_de.start.hours
        sub_end_minutes += 60*sub_end_hours
        sub_start_minutes += 60*sub_start_hours

        self.ToolTab.Deu_cont.clear()
        self.ToolTab.Eng_cont.clear()
        # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        parts = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
                                                  'seconds': sub_end_seconds},
                                   ends_after={'minutes': sub_start_minutes,
                                               'seconds': sub_start_seconds})
        current_sub_en = ''
        for part in parts:
            current_sub_en += ' – ' + part.text
        # show
        self.ToolTab.Deu_cont.insertPlainText(
            clean_subtitle(current_sub_de.text))
        self.ToolTab.Eng_cont.insertPlainText(clean_subtitle(current_sub_en))
        progress = (self.index_de/len(self.subs_de))*100
        self.ToolTab.progress.setValue(progress)
        self.show()

    def add_previous(self):
        new_index = min(self.index_list)-1
        self.index_list.insert(0, new_index)
        current_sub_de = ''
        for x in self.index_list:
            current_sub_de += ' – '+self.subs_de[x].text
        first_sub = self.subs_de[new_index]
        last_sub = self.subs_de[max(self.index_list)]
        sub_start_minutes = first_sub.start.minutes
        sub_start_seconds = first_sub.start.seconds - 2
        sub_end_minutes = last_sub.end.minutes
        sub_end_seconds = last_sub.end.seconds + 2
        sub_end_hours = last_sub.end.hours
        sub_start_hours = first_sub.start.hours
        sub_end_minutes += 60*sub_end_hours
        sub_start_minutes += 60*sub_start_hours

        self.ToolTab.Deu_cont.clear()
        self.ToolTab.Eng_cont.clear()
        # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        parts = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
                                                  'seconds': sub_end_seconds},
                                   ends_after={'minutes': sub_start_minutes,
                                   'seconds': sub_start_seconds})
        current_sub_en = ''
        for part in parts:
            current_sub_en += ' – ' + part.text
        # show
        self.ToolTab.Deu_cont.insertPlainText(clean_subtitle(current_sub_de))
        self.ToolTab.Eng_cont.insertPlainText(clean_subtitle(current_sub_en))
        self.show()

    def add_next(self):
        new_index = max(self.index_list) + 1
        self.index_list.append(new_index)
        current_sub_de = ''
        for x in self.index_list:
            current_sub_de += ' – '+self.subs_de[x].text
        first_sub = self.subs_de[min(self.index_list)]
        last_sub = self.subs_de[new_index]
        sub_start_minutes = first_sub.start.minutes
        sub_start_seconds = first_sub.start.seconds - 2
        sub_end_minutes = last_sub.end.minutes
        sub_end_seconds = last_sub.end.seconds + 2
        sub_end_hours = last_sub.end.hours
        sub_start_hours = first_sub.start.hours
        sub_end_minutes += 60*sub_end_hours
        sub_start_minutes += 60*sub_start_hours

        self.ToolTab.Deu_cont.clear()
        self.ToolTab.Eng_cont.clear()
        # go to sub_en by start_timestamp-500 ms and end_timestamp+500_ms
        parts = self.subs_en.slice(starts_before={'minutes': sub_end_minutes,
                                                  'seconds': sub_end_seconds},
                                   ends_after={'minutes': sub_start_minutes,
                                   'seconds': sub_start_seconds})
        current_sub_en = ''
        for part in parts:
            current_sub_en += ' – ' + part.text
        # show
        self.ToolTab.Deu_cont.insertPlainText(clean_subtitle(current_sub_de))
        self.ToolTab.Eng_cont.insertPlainText(clean_subtitle(current_sub_en))
        self.show()

    def save_method(self):
        # open with active Vocabulary trainer
        word = self.ToolTab.line.text()
        Beispiel_de = self.ToolTab.Deu_cont.toPlainText()
        Beispiel_en = self.ToolTab.Eng_cont.toPlainText()
        Beispiel_de = Beispiel_de.replace(
            "'", "//QUOTE")+" ("+self.file_name+")"
        Beispiel_en = Beispiel_en.replace(
            "'", "//QUOTE")+" ("+self.file_name+")"
        command_str = f'dic.py {word} "{Beispiel_de}" "{Beispiel_en}"'
        print(command_str)
        stream = os.popen()
        # output = stream.read()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())

# from PyQt5.QtCore import *
from dataclasses import dataclass, field
import logging
import math
from bs4.builder import HTML
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs
from pathlib import Path
from pandas.core.frame import DataFrame

dict_path = Path.home() / 'Dictionnary'

# set up logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)  # Levels: debug, info, warning, error, critical
formatter = logging.Formatter(
    '%(levelname)8s -- %(name)-15s line %(lineno)-4s: %(message)s')
logger.handlers[0].setFormatter(formatter)


@dataclass
class QuizEntry():
    quiz_priority_order: str
    words_dataframe: DataFrame
    maxrevpersession: int = 10
    quiz_params: dict = field(default_factory=dict)
    quiz_window_titel: str = ''
    full_text: HTML = ''
    quiz_text: HTML = ''
    quiz_file_path: Path = ''
    full_file_path: Path = ''
    _nb_revisited: int = 0

    def __post_init__(self):
        self.queue_quiz_word()

        self.get_file_paths()

    def get_file_paths(self):
        self.quiz_file_path = (dict_path /
                               (self.quiz_params['queued_word'] +
                                ".quiz.html"))
        with open(self.quiz_file_path, 'r') as f:
            self.quiz_text = f.read()
        self.full_file_path = (dict_path /
                               (self.quiz_params['queued_word'] +
                                ".html"))
        with open(self.full_file_path, 'r') as f:
            self.full_text = f.read()

    def queue_quiz_word(self):
        logger.info("queue_quiz_word")
        now = datetime.now() - timedelta(hours=3)
        self.todayscharge = 0
        yesterday = now + timedelta(days=-1)
        planned_str = 'error'
        logger.debug('quiz_priority_order: '+self.quiz_priority_order)
        if self.quiz_priority_order == 'due_words':
            logger.debug('Quiz Order set to planned Words')

            # Start by words due Today then yesteday
            # then queue the oldest due word
            # than oldest seen words
            df_dates = self.words_dataframe['Next_date'].apply(
                lambda x: x.date())
            due_today_df = self.words_dataframe[(df_dates == now.date())]
            due_yesterday_df = self.words_dataframe[(
                df_dates == yesterday.date())]
            due_past_df = self.words_dataframe[df_dates < yesterday.date()]

            self.todayscharge = (len(due_today_df)
                                 + len(due_yesterday_df)
                                 + len(due_past_df))

            if len(due_today_df) > 0:
                self._countdown = 0
                queued_word = due_today_df.index[0]
                planned_str = ' for Today'
            elif len(due_yesterday_df) > 0:
                self._countdown = 0
                queued_word = due_yesterday_df.index[0]
                planned_str = ' for Yesteday'
            elif len(due_past_df) > 0:
                self._countdown = 1
                oldest_next_dtm = self.words_dataframe['Next_date'].min()
                queued_word = self.words_dataframe[
                    self.words_dataframe['Next_date'] == oldest_next_dtm].index[0]
                planned_str = f' versäumt {oldest_next_dtm.strftime("%d.%m.%y")}'

        elif self.quiz_priority_order == 'old_words':
            logger.debug('Quiz Order set to oldest seen Words')

            self._countdown = 1
            self.todayscharge = 999
            oldest_seen_dtm = self.words_dataframe['Previous_date'].min()
            queued_word = self.words_dataframe[
                self.words_dataframe['Previous_date'] ==
                oldest_seen_dtm].index[0]
            planned_dtm = self.words_dataframe.loc[queued_word, "Next_date"]
            planned_str = (' Von '
                           f'{oldest_seen_dtm.strftime("%d.%m.%y")}'
                           ', '
                           f'geplannt {planned_dtm.strftime("%d.%m.%y")}')

        logger.debug('todayscharge: '+str(self.todayscharge))
        if self.todayscharge > 0:
            logger.debug('queued_word: '+str(queued_word))

            last_seen = self.words_dataframe.loc[queued_word, "Previous_date"]\
                .strftime('%d.%m.%y')
            self.quiz_window_titel = f'Wörterbuch: Quiz '
            f'({str(self.todayscharge)}) {planned_str} , Last seen  {last_seen}'

            repetitions = float(
                self.words_dataframe.loc[queued_word, "Repetitions"])
            EF_score = float(self.words_dataframe.loc[queued_word, "EF_score"])
            # interval = float(df.loc[queued_word, "Interval"])
            real_interval = (
                now - self.words_dataframe.loc[queued_word, "Previous_date"]).days
        else:
            queued_word = ''
            self.quiz_window_titel = 'No Words Left'
            EF_score = 0
            real_interval = 0
            repetitions = 0
            self._countdown = 0

        self.quiz_params = {'queued_word': queued_word,
                            'EF_score': EF_score,
                            'real_interval': real_interval,
                            'repetitions': repetitions}

    def quiz_counter(self):
        no_words_left4today = False
        reached_daily_limit = False
        if self.todayscharge > 0:
            if self._countdown:
                self._nb_revisited += 1
            if self._nb_revisited > self.maxrevpersession:
                reached_daily_limit = True
        else:
            no_words_left4today = True

        return no_words_left4today, reached_daily_limit


@dataclass
class FocusEntry():
    focus_df: DataFrame
    focus_part: str = ''
    focus_part_revealed: str = ''
    focus_params_dict: dict = field(default_factory=dict)

    def __post_init__(self):
        self.queue_focus_word()

    def queue_focus_word(self):
        now = datetime.now() - timedelta(hours=3)
        logger.info("queue_focus_word")
        selected_ignored = 1
        before_today = self.focus_df["Next_date"] <= now.strftime("%Y-%m-%d")
        due_words = self.focus_df[before_today]
        due_words['weights'] = 1/due_words['EF_score']
        while selected_ignored:
            logger.debug(due_words)
            # TODO more sophisticated weighting
            random_focus_df = due_words.sample(n=1, weights='weights')
            selected_ignored = int(random_focus_df['Ignore'].values[0])
            word = random_focus_df['Word'].values[0]
            part_idx = random_focus_df['Part'].values[0]
            part_idx = int(part_idx.item())
            wordpart = random_focus_df.index[0]

            quiz_file = dict_path / (word+".quiz.html")
            full_file = dict_path / (word+".html")
            with open(quiz_file, 'r') as quiz_file:
                quiz_txt = quiz_file.read()
            with open(full_file, 'r') as full_file:
                full_txt = full_file.read()

            quiz_parts = bs(quiz_txt, "lxml").find_all('p')
            full_parts = bs(full_txt, "lxml").find_all('p')

            assert len(quiz_parts) == len(full_parts)

            self.focus_part = str(quiz_parts[part_idx])
            self.focus_part_revealed = str(full_parts[part_idx])

            repetitions = float(self.focus_df.loc[wordpart, "Repetitions"])
            EF_score = float(self.focus_df.loc[wordpart, "EF_score"])
            real_interval = (
                now - self.focus_df.loc[wordpart, "Previous_date"]).days

            self.focus_params_dict = {'queued_word': wordpart,
                                      'EF_score': EF_score,
                                      'real_interval': real_interval,
                                      'repetitions': repetitions}


def update_train_data(queued_word, df, now, easiness, interval):
    logger.info("update_train_data")

    new_train_row = {"Word": queued_word,
                     "Planned_date": [df.loc[queued_word, "Next_date"]],
                     "Repetitions": [df.loc[queued_word, "Repetitions"]],
                     "EF_score": [df.loc[queued_word, "EF_score"]],
                     "Last_Interval": [df.loc[queued_word, "Interval"]],
                     "Last_easiness": [df.loc[queued_word, "Easiness"]],
                     "Previous_date": [df.loc[queued_word, "Previous_date"]],
                     "Revist_date": [now.strftime("%d.%m.%y")],
                     "Current_easiness": [easiness],
                     "Current_Interval": [interval]}
    new_train_row = pd.DataFrame(new_train_row)

    train_data = pd.read_csv(
        dict_path / 'train_data.csv', index_col=0)
    train_data = train_data.append(new_train_row, ignore_index=True)
    cols = ['Word', 'Revist_date', 'Planned_date',
            'Previous_date', 'Current_Interval',
            'Last_Interval', 'Current_easiness', 'Last_easiness',
            'Repetitions', 'EF_score', 'Tag']
    train_data = train_data[cols]

    train_data.to_csv(dict_path / 'train_data.csv')


def ignore_headers(quiz_text):
    logger.info("create_ignore_list")
    quiz_list = bs(quiz_text, "lxml").find_all('p')
    nb_parts = len(quiz_list)
    ignore_list = [1]*len(quiz_list)
    for index in range(0, len(quiz_list)):
        quiz_list_lvl2 = quiz_list[index].find_all('span')
        for item in quiz_list_lvl2:
            contain_example = 'italic' in item['style']
            if contain_example:
                ignore_list[index] = 0
                continue
    # logger.debug('Indexes to Ignore', ignore_list)
    return ignore_list, nb_parts


def spaced_repetition(easiness, now,  df, saving_file, EF_score=1,
                      queued_word='', real_interval='', repetitions=0):
    logger.info("spaced_repetition")

    EF_score = max(1.3, EF_score + 0.1 - (5.0 - easiness)
                   * (0.08 + (5.0 - easiness) * 0.02))

    if easiness < 3:
        repetitions = 0
    else:
        repetitions += 1

    if repetitions == 0:
        interval = 1
    elif repetitions == 1:
        interval = 1
    elif repetitions == 2:
        interval = 6
    else:
        interval = real_interval * EF_score
    next_date = now + timedelta(days=math.ceil(interval))

    # TODO standarize datetime writing format
    # next_date = next_date.strftime("%d.%m.%y")
    update_train_data(queued_word, df, now, easiness, interval)
    df.loc[queued_word, "Next_date"] = next_date
    df.loc[queued_word, "Repetitions"] = repetitions
    df.loc[queued_word, "EF_score"] = EF_score
    df.loc[queued_word, "Interval"] = interval
    df.loc[queued_word, "Easiness"] = easiness
    df.loc[queued_word, "Previous_date"] = now  # .strftime("%d.%m.%y")
    df.to_csv(dict_path / saving_file)

# import pytest
from unittest.mock import patch
import sys
from PyQt5.QtWidgets import QApplication

from german_active_vocab.main import MainWindow, set_theme, excepthook



def test_simple_search_from_pons():
    with patch('sys.argv', ['main', '--word', 'machen']):
        app = QApplication(sys.argv)
        set_theme(app)
        sys.excepthook = excepthook
        w = MainWindow()
        exit_code = app.exec()
        assert not exit_code

def test_simple_search_from_duden():
    with patch('sys.argv', ['main', '--word', 'schnappen du']):
        app = QApplication(sys.argv)
        set_theme(app)
        sys.excepthook = excepthook
        w = MainWindow()
        exit_code = app.exec()
        assert not exit_code
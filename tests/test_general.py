from unittest.mock import patch
import pytest
import qdarktheme
from pytestqt.plugin import qapp
# from pytestqt import qtbot # mokrza ki zebi. Documentation moch wath7a, sa3at ghalta.

from german_active_vocab.MainWindow import MainWindow



# SOLVED multiple tests are not possible, PyQt doesn't immediatly close event loop after w.close
# CANCELED (0) add pre-commit hooks in vscode # not possible now
# TODO (1) test new_cache keyword
# TODO (1) test new_dict keyword
# DONE configure testing in vscode
# https://code.visualstudio.com/docs/python/testing

def run_app(qapp):
    qdarktheme.setup_theme("dark")
    main_window = MainWindow()
    qapp.exec_()
    assert main_window._end_test

@pytest.mark.dependency()
@patch('sys.argv', ['main'])
def test_simple_search_from_search_box(qapp): #qtbot
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen'])
def test_pons(qapp):
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen', '--ger', 'german example phrase', '--eng', 'english translation phrase'])
def test_pons_with_examples(qapp):
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen du'])
def test_duden(qapp):
    run_app(qapp)
    
@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen en'])
def test_translate_en(qapp):
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen new_cache'])
def test_no_cache_pons(qapp):
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen du new_cache'])
def test_no_cache_duden(qapp):
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen new_dict'])
def test_no_dict_pons(qapp):
    run_app(qapp)


# https://pytest-qt.readthedocs.io/en/latest/wait_until.html
# qtbot.addWidget(w)
# qtbot.wait(100000) #100 secondes
# qtbot.waitUntil(w.close)
# qtbot.waitUntil(w.def_window.return_button.clicked)
# qtbot.waitUntil(w.isVisible)
# qtbot.waitUntil(w.return_clicked)

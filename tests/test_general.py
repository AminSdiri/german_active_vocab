from unittest.mock import patch
import pytest
from german_active_vocab.MainWindow import MainWindow

# from pytestqt import qtbot # mokrza ki zebi. Documentation moch wath7a, sa3at ghalta.
from pytestqt.plugin import qapp


# BUG* multiple tests are not possible, PyQt doesn't immediatly close event loop after w.close
# TODO test new_cache keyword
# TODO test new_dict keyword

def run_app(qapp):
    import qdarktheme
    qdarktheme.setup_theme("dark")
    w = MainWindow()
    qapp.exec_()
    assert w._end_test

@pytest.mark.dependency()
@patch('sys.argv', ['main'])
def test_simple_search_from_search_box(qapp): #qtbot
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen'])
def test_simple_search_from_pons(qapp):
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen', '--ger', 'german example phrase', '--eng', 'english translation phrase'])
def test_simple_search_from_pons_with_examples(qapp):
    run_app(qapp)

@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen du'])
def test_simple_search_from_duden(qapp):
    run_app(qapp)
    
@pytest.mark.dependency(depends=["test_simple_search_from_search_box"])
@patch('sys.argv', ['main', '--word', 'machen en'])
def test_simple_search_translate_en(qapp):
    run_app(qapp)


# https://pytest-qt.readthedocs.io/en/latest/wait_until.html
# qtbot.addWidget(w)
# qtbot.wait(100000) #100 secondes
# qtbot.waitUntil(w.close)
# qtbot.waitUntil(w.def_window.return_button.clicked)
# qtbot.waitUntil(w.isVisible)
# qtbot.waitUntil(w.return_clicked)
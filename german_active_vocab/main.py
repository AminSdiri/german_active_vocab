# !/usr/bin/env python3
# coding = utf-8

import sys
import traceback
from plyer import notification
from PyQt5.QtWidgets import QApplication

from MainWindow import MainWindow, set_theme
from utils import set_up_logger
# from autologging import traced

# TODO (0) STRUCT Baddel structure mta3 Model, Viewer, controller walla Presenter

# git update-index --skip-worktree <file> to skip tracking files
# https://www.youtube.com/watch?v=0kpm10AxiNE&list=PLQVvvaa0QuDdVpDFNq4FwY9APZPGSUyR4&index=11 choose theme


# user needs to generate API and put in in API path...
# TODO (1) using boxLayout with percentages instead of hardcoded dimensions
# TODO (0) Write Readme file with examples (screenshots) and how to install
# TODO (0) List the different fonctionalities for the readme.md
# TODO (0) write integral tests for the different search syntaxes,
# TODO (2) BIG write test functions for the different functionalities,
# DONE (2) find os-agnostic alternative to notify-send for windows and macos
# example: from plyer import notification

# .strftime("%d.%m.%y") is a bad idea! losing the time information
# TODO (1) STRUCT organize now and now_(-3h) 
# DONE (2) move theme
# DONE (0) restruct main
# TODO (0) riguel pytest lel vscode

logger = set_up_logger(__name__)

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    notification.notify(title='An Error Occured',
                        message=exc_value.args[0],
                        timeout=10)
    QApplication.quit()
    sys.exit(1)

def main() -> None:
    app = QApplication([])
    set_theme(app)
    sys.excepthook = excepthook
    w = MainWindow()
    exit_code = app.exec()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

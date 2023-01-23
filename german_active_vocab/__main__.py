# !/usr/bin/env python3
# coding = utf-8

import sys
import traceback
from plyer import notification
from PyQt5.QtWidgets import QApplication, QMessageBox

from MainWindow import MainWindow, set_theme
from utils import set_up_logger


# TODO (1) user needs to generate API and put in in API path... -> add API to environement path
# TODO (1) using boxLayout with percentages instead of hardcoded dimensions
# TODO (0) Write Readme file with examples (screenshots) and how to install
# TODO (0) List the different fonctionalities for the readme.md
# DONE (0) write integration tests for the different search syntaxes,
# TODO (2) write unit tests for the different functionalities,
# DONE (2) find os-agnostic alternative to notify-send for windows and macos
# TODO (3) .strftime("%d.%m.%y") is a bad idea! losing the time information
# TODO (1) STRUCT organize now and now_(-3h) 
# DONE (2) move theme
# DONE (0) restruct main
# TODO (0) STRUCT all to Model, Viewer/controller architecture
# TODO (4) choose theme https://www.youtube.com/watch?v=0kpm10AxiNE&list=PLQVvvaa0QuDdVpDFNq4FwY9APZPGSUyR4&index=11
# DONE (0) ignore data files :: git update-index --skip-worktree <file> to skip tracking files

logger = set_up_logger(__name__)

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    notification.notify(title='An Error Occured',
                        message=exc_value.args[0],
                        timeout=10)
    
    # show error in Qt MessageBox
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("An Error Occured")
    msg.setInformativeText(exc_value.args[0])
    msg.setWindowTitle("Error")

    QApplication.quit() # or sys.exit(0)? 

def main() -> int:
    app = QApplication(sys.argv)
    set_theme(app)
    w = MainWindow()
    exit_code = app.exec_()
    return exit_code

if __name__ == '__main__':
    sys.excepthook = excepthook  # show errors as system notifications
    exit_code = main()
    sys.exit(exit_code)

import sys
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot



class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished: pyqtSignal = pyqtSignal()
    error: pyqtSignal = pyqtSignal(object, object, object)
    result: pyqtSignal = pyqtSignal(object)
    progress: pyqtSignal = pyqtSignal(int)
    message_box_content_carrier: pyqtSignal = pyqtSignal(dict)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, callable_fn, *args, **kwargs) -> None:
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.callable_fn = callable_fn
        self.args = args
        self.kwargs = kwargs
        self.signals: WorkerSignals = WorkerSignals()

        # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress
        self.kwargs['message_box_content_carrier'] = self.signals.message_box_content_carrier

    @pyqtSlot()
    def run(self) -> None:
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        if 'debugpy' in sys.modules: # debugpy throws error 111 if it's run outside debug mode
            # make debugging the Worker Thread possible
            import debugpy
            debugpy.debug_this_thread()

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.callable_fn(*self.args, **self.kwargs)
        except Exception: # FIXED No exception type specified
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.signals.error.emit(exc_type, exc_value, exc_traceback)
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

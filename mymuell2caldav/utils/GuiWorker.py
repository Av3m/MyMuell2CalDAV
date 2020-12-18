from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressBar, QPushButton, QStatusBar


class GuiWorker(QThread):
    finished = pyqtSignal(bool, str)
    rangeChanged = pyqtSignal(int, int)
    progressChanged = pyqtSignal(int)
    stateChanged = pyqtSignal(str)

    _button = None

    def __init__(self, runnable, parent=None):
        QThread.__init__(self, parent)
        self._callable = runnable

    def connectProgressBar(self, progress_bar: QProgressBar):
        self.progressChanged.connect(progress_bar.setValue)
        self.rangeChanged.connect(progress_bar.setRange)
        progress_bar.setTextVisible(True)


    def connectButton(self, button: QPushButton):
        self._button = button
        self._button.clicked.connect(self.start)

    def connectStatusBar(self, statusbar: QStatusBar):
        self.stateChanged.connect(lambda val: statusbar.showMessage(val))

    def run(self):
        if self._button:
            self._button.setEnabled(False)
        ret = self._callable(self)
        self._button.setEnabled(True)
        self.finished.emit(ret[0], ret[1])

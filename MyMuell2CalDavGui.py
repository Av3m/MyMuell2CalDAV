from PyQt5.QtWidgets import \
    QApplication, \
    QWidget, \
    QListWidget, \
    QListWidgetItem, \
    QVBoxLayout, \
    QHBoxLayout, \
    QGridLayout, \
    QLineEdit, \
    QGroupBox, \
    QLabel, \
    QPushButton, \
    QMessageBox, \
    QComboBox, \
    QProgressBar, \
    QStatusBar, \
    QSizePolicy, \
    QMainWindow


from PyQt5.QtCore import QModelIndex, Qt
import MyMuellDataModel
import sys
import CalendarSync

from GuiWorker import GuiWorker


class MyMuell2CalDavGui(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._dataModel = MyMuellDataModel.MyMuellDataModel()
        self._davClient = CalendarSync.CalendarSync()

        self._selectedCity = None

        self._cities = []

        self._citiesWidget = QListWidget()
        self._filterText = QLineEdit()

        self._url = QLineEdit()
        self._user = QLineEdit()
        self._password = QLineEdit()
        self._calendarNames = QComboBox()
        self._connectButton = QPushButton("connect")
        self._syncButton = QPushButton("sync events")
        self._deleteButton = QPushButton("delete existing events")
        self._errorMessage = QMessageBox()
        self._progressBar = QProgressBar()
        self._statusBar = QStatusBar()

        self._settings = self._dataModel.storage.settings

        self._url.setText(self._settings["url"])
        self._password.setText(self._settings["password"])
        self._user.setText(self._settings["user"])

        self._workerConnect = GuiWorker(self.runnable_connect_caldav)
        self._workerSync = GuiWorker(self.runnable_sync_events)
        self._workerDelete = GuiWorker(self.runnable_delete_events)


        self.initUI()

        self.__fillCities()

    def entrySelected(self, i: QListWidgetItem):
        city = self._dataModel.get_city_by_id(i.data(QListWidgetItem.UserType))

        self._selectedCity = (city["id"], city["area_id"])

    def saveSettings(self, val):
        self._settings["url"] = self._url.text()
        self._settings["user"] = self._user.text()
        self._settings["password"] = self._password.text()

        if self._calendarNames.currentText() != '':
            self._settings["calendar"] = self._calendarNames.currentText()

        if len(self._citiesWidget.selectedItems()) > 0:
            self._settings["mymuellcity"] = self._citiesWidget.selectedItems()[0].text()

        self._dataModel.storage.settings = self._settings

    def runnable_sync_events(self, worker: GuiWorker) -> tuple[bool, str]:
        if self._selectedCity is None:
            return False, "please select a city"

        if self._calendarNames.currentText() == '':
            return False, "please select a calendar"

        worker.stateChanged.emit("create calendar {} if not existent".format(self._calendarNames.currentText()))

        self._davClient.createCalendar(self._calendarNames.currentText())

        worker.stateChanged.emit("get events from MyMüll.de (city id {}, aread id {}".format(*self._selectedCity))
        events = self._dataModel.get_events(*self._selectedCity)
        worker.rangeChanged.emit(0, len(events))
        worker.progressChanged.emit(0)

        for i in range(0, len(events)):
            worker.stateChanged.emit("creating event {} {}".format(events[i]["title"], events[i]["day"]))
            self._davClient.syncEvents(events[i])
            worker.progressChanged.emit(i+1)

        worker.stateChanged.emit("syncing events finished")
        return True, "syncing events finished"

    def runnable_delete_events(self, worker: GuiWorker) -> tuple[bool, str]:
        if self._calendarNames.currentText() == '':
            return False, "please select a calendar"

        worker.stateChanged.emit("deleting existing events from calendar")

        self._davClient.createCalendar(self._calendarNames.currentText())
        events = self._davClient.getExistingMuellEvents()
        if len(events) > 0:
            worker.rangeChanged.emit(0, len(events))
            worker.progressChanged.emit(0)
        else:
            worker.rangeChanged.emit(0, 1)
            worker.progressChanged.emit(1)

        for i in range(0, len(events)):
            worker.stateChanged.emit("deleting event {}".format(events[i].vobject_instance.vevent.uid.value))
            events[i].delete()
            worker.progressChanged.emit(i+1)

        worker.stateChanged.emit("deletion finished.")
        return True, "deleting events finished"

    def runnable_connect_caldav(self, worker: GuiWorker) -> tuple[bool, str]:


        try:
            worker.stateChanged.emit("connecting to {}".format(self._url.text()))
            self._davClient.connect(self._url.text(), self._user.text(), self._password.text())
            self._calendarNames.blockSignals(True)
            for i in self._davClient.getCalendars():
                self._calendarNames.addItem(i)

            self._calendarNames.blockSignals(False)
            self._calendarNames.setEnabled(True)

            if self._settings["calendar"] != '':
                self._calendarNames.setCurrentText(self._settings["calendar"])



            worker.stateChanged.emit("connected.")




        except Exception as e:
            worker.stateChanged.emit("connection failed.")
            return False, str(e)

        return True, "connect successful"

    def initUI(self):

        tlWidget = QWidget()
        layout = QGridLayout()
        tlWidget.setLayout(layout)

        self.setCentralWidget(tlWidget)



        groupBoxMyMuell = QGroupBox("MyMüll.de Cities")
        layoutGroupBoxMyMuell = QGridLayout()
        groupBoxMyMuell.setLayout(layoutGroupBoxMyMuell)

        groupBoxCalDav = QGroupBox("CalDAV Settings")
        layoutGroupBoxCalDav = QGridLayout()
        groupBoxCalDav.setLayout(layoutGroupBoxCalDav)

        groupBoxProgress = QGroupBox("Progress")
        layoutGroupBoxProgress = QVBoxLayout()
        groupBoxProgress.setLayout(layoutGroupBoxProgress)

        layoutGroupBoxMyMuell.addWidget(self._citiesWidget, 0, 0, 4, 6)
        layoutGroupBoxMyMuell.addWidget(QLabel("Filter Cities"), 4, 0, 1, 1)
        layoutGroupBoxMyMuell.addWidget(self._filterText, 4, 1, 1, 5)

        layout.addWidget(groupBoxMyMuell)
        layout.addWidget(groupBoxCalDav)
        layout.addWidget(groupBoxProgress)

        self.setStatusBar(self._statusBar)

        layoutGroupBoxCalDav.addWidget(QLabel("url"), 0, 0, 1, 1)
        layoutGroupBoxCalDav.addWidget(self._url, 0, 1, 1, 5)
        layoutGroupBoxCalDav.addWidget(QLabel("username"), 1, 0, 1, 1)
        layoutGroupBoxCalDav.addWidget(self._user, 1, 1, 1, 5)
        layoutGroupBoxCalDav.addWidget(QLabel("password"), 2, 0, 1, 1)
        layoutGroupBoxCalDav.addWidget(self._password, 2, 1, 1, 5)
        layoutGroupBoxCalDav.addWidget(QLabel("calendar"), 3, 0, 1, 1)
        layoutGroupBoxCalDav.addWidget(self._calendarNames, 3, 1, 1, 5)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self._connectButton)
        buttonLayout.addWidget(self._syncButton)
        buttonLayout.addWidget(self._deleteButton)

        layoutGroupBoxCalDav.addLayout(buttonLayout, 4, 0, 6, 6)

        layoutGroupBoxProgress.addWidget(self._progressBar)
        layoutGroupBoxCalDav.setSpacing(0)
        layoutGroupBoxCalDav.setContentsMargins(0, 0, 0, 0)

        self._password.setEchoMode(QLineEdit.Password)

        self._calendarNames.setEditable(True)

        self._filterText.show()
        self._citiesWidget.show()

        self._syncButton.setEnabled(False)
        self._calendarNames.setEnabled(False)

        self._citiesWidget.currentItemChanged.connect(lambda cur, prev: self.entrySelected(cur))
        self._filterText.textChanged.connect(self.__fillCities)

        self._url.textChanged.connect(self.saveSettings)
        self._user.textChanged.connect(self.saveSettings)
        self._password.textChanged.connect(self.saveSettings)

        self._citiesWidget.itemSelectionChanged.connect(lambda: self.saveSettings(0))

        self._workerSync.connectProgressBar(self._progressBar)
        self._workerSync.connectButton(self._syncButton)

        self._workerConnect.connectButton(self._connectButton)
        self._workerDelete.connectButton(self._deleteButton)

        self._workerSync.connectStatusBar(self._statusBar)
        self._workerConnect.connectStatusBar(self._statusBar)
        self._workerDelete.connectStatusBar(self._statusBar)
        self._workerDelete.connectProgressBar(self._progressBar)

        self._workerConnect.finished.connect(self.slot_process_finished)
        self._workerSync.finished.connect(self.slot_process_finished)
        self._workerDelete.finished.connect(self.slot_process_finished)

        self._calendarNames.currentTextChanged.connect(self.slot_calendar_selected)

        self._progressBar.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))
        groupBoxProgress.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))
        groupBoxCalDav.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))

        self._url.setContentsMargins(0, 10, 0, 10)
        self._password.setContentsMargins(0, 10, 0, 10)
        self._user.setContentsMargins(0, 10, 0, 10)
        self._calendarNames.setContentsMargins(0, 10, 0, 10)


        #self.setGeometry(300, 300, 1000, 800)
        self.setMinimumWidth(800)
        self.setWindowTitle("MyMuell DAV GUI")



    def slot_process_finished(self, result: bool, msg: str):
        if result:
            self._errorMessage.information(self, "info", msg)
            self._syncButton.setEnabled(True)
        else:
            self._errorMessage.critical(self, "error", msg)
            self._syncButton.setEnabled(False)

    def slot_calendar_selected(self):

        if self._calendarNames.currentText() != '' and self._davClient.is_connected:
            self.saveSettings(0)
            self._syncButton.setEnabled(True)
        else:
            self._syncButton.setEnabled(False)

    def __fillCities(self, pattern=".+"):
        self._citiesWidget.blockSignals(True)
        self._citiesWidget.clear()

        self._cities = self._dataModel.match_city(pattern)

        for i in self._cities:
            c = self._dataModel.get_city_by_index(i)
            item = QListWidgetItem()

            item.setData(QListWidgetItem.UserType, c["id"])
            item.setText(c["name"])

            self._citiesWidget.addItem(item)

        self._citiesWidget.blockSignals(False)

        if self._settings["mymuellcity"] != '':
            items = self._citiesWidget.findItems(self._settings["mymuellcity"], Qt.MatchExactly)
            if len(items) > 0:
                self._citiesWidget.setCurrentItem(items[0])




def main():
    app = QApplication(sys.argv)
    w = MyMuell2CalDavGui()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

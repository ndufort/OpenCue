#  Copyright Contributors to the OpenCue Project
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


"""The main window of the application. Multiple windows may exist.

All CueGUI windows are an instance of this MainWindow."""


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division


from builtins import str
from builtins import range
import sys
import time

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import opencue

import cuegui.Constants
import cuegui.Logger
import cuegui.Plugins
import cuegui.Utils


logger = cuegui.Logger.getLogger(__file__)


class MainWindow(QtWidgets.QMainWindow):
    """The main window of the application. Multiple windows may exist."""

    windows = []
    windows_names = []
    windows_titles = {}
    windows_actions = {}

    def __init__(self, app_name, app_version, window_name, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)

        self.__actions_facility = {}
        self.facility_default = None
        self.facility_dict = None
        self.windowMenu = None

        self.qApp = QtGui.qApp
        # pylint: disable=no-member
        self.settings = QtGui.qApp.settings
        # pylint: enable=no-member
        self.windows_names = [app_name] + ["%s_%s" % (app_name, num) for num in range(2, 5)]
        self.app_name = app_name
        self.app_version = app_version
        if window_name:
            self.name = window_name
        else:
            self.name = self.windows_names[0]

        # Provides a location for widgets to the right of the menu
        menuLayout = QtWidgets.QHBoxLayout()
        menuLayout.addStretch()
        self.menuBar().setLayout(menuLayout)

        # Configure window
        self.setMinimumSize(600, 400)
        self.setAnimated(False)
        self.setDockNestingEnabled(True)

        # Register this window
        self.__windowOpened()

        # Create menus
        self.__createMenus()

        # Setup plugins
        # pylint: disable=no-member
        self.__plugins = cuegui.Plugins.Plugins(self, self.name)
        # pylint: enable=no-member
        self.__plugins.setupPluginMenu(self.PluginMenu)

        # Restore saved settings
        self.__restoreSettings()

        # pylint: disable=no-member
        QtGui.qApp.status.connect(self.showStatusBarMessage)
        # pylint: enable=no-member

        self.showStatusBarMessage("Ready")

    def displayStartupNotice(self):
        """Displays the application startup notice."""
        now = int(time.time())
        lastView = int(self.settings.value("LastNotice", 0))
        if lastView < cuegui.Constants.STARTUP_NOTICE_DATE:
            QtWidgets.QMessageBox.information(self, "Notice", cuegui.Constants.STARTUP_NOTICE_MSG,
                                              QtWidgets.QMessageBox.Ok)
        self.settings.setValue("LastNotice", now)

    def showStatusBarMessage(self, message, delay=5000):
        """Shows a message on the status bar."""
        self.statusBar().showMessage(str(message), delay)

    def displayAbout(self):
        """Displays about text."""
        msg = self.app_name + "\n\nA opencue tool\n\n"
        msg += "Qt:\n%s\n\n" % QtCore.qVersion()
        msg += "Python:\n%s\n\n" % sys.version
        QtWidgets.QMessageBox.about(self, "About", msg)

    @staticmethod
    def openSuggestionPage():
        """Opens the suggestion page URL."""
        cuegui.Utils.openURL(cuegui.Constants.URL_SUGGESTION)

    @staticmethod
    def openBugPage():
        """Opens the bug report page."""
        cuegui.Utils.openURL(cuegui.Constants.URL_BUG)

    @staticmethod
    def openUserGuide():
        """Opens the user guide page."""
        cuegui.Utils.openURL(cuegui.Constants.URL_USERGUIDE)

    ################################################################################
    # Handles facility menu
    ################################################################################

    def __facilityMenuSetup(self, menu):
        """Creates the facility menu actions
        @param menu: The QMenu that the actions should be added to
        @type  menu: QMenu
        @return: The QMenu that the actions were added to
        @rtype:  QMenu"""
        self.__actions_facility = {}
        menu.setFont(cuegui.Constants.STANDARD_FONT)
        menu.triggered.connect(self.__facilityMenuHandle)

        cue_config = opencue.Cuebot.getConfig()
        self.facility_default = cue_config.get("cuebot.facility_default")
        self.facility_dict = cue_config.get("cuebot.facility")

        for facility in self.facility_dict:
            self.__actions_facility[facility] = QtWidgets.QAction(facility, menu)
            self.__actions_facility[facility].setCheckable(True)
            menu.addAction(self.__actions_facility[facility])

        self.__actions_facility[self.facility_default].setChecked(True)
        return menu

    def __facilityMenuHandle(self, action):
        """Called when a facility menu item is clicked on.
        @param action: Menu QAction
        @type  action: QAction"""
        # If all cues are unchecked, check default one
        if not action.isChecked():
            checked = False
            for facility in list(self.__actions_facility.values()):
                if facility.isChecked():
                    checked = True
            if not checked:
                self.__actions_facility[self.facility_default].setChecked(True)
        # Uncheck all other facilities if one is checked
        else:
            for facility in self.__actions_facility:
                if facility != action.text():
                    self.__actions_facility[facility].setChecked(False)

        for facility in list(self.__actions_facility.values()):
            if facility.isChecked():
                opencue.Cuebot.setFacility(str(facility.text()))
                # pylint: disable=no-member
                QtGui.qApp.facility_changed.emit()
                # pylint: enable=no-member
                return

    ################################################################################

    def __createMenus(self):
        """Creates the menus at the top of the window"""
        self.menuBar().setFont(cuegui.Constants.STANDARD_FONT)

        # Menu bar
        self.fileMenu = self.menuBar().addMenu("&File")
        self.facilityMenu = self.__facilityMenuSetup(self.menuBar().addMenu("&Cuebot"))
        self.PluginMenu = self.menuBar().addMenu("&Views/Plugins")
        self.windowMenu = self.menuBar().addMenu("&Window")
        self.helpMenu = self.menuBar().addMenu("&Help")

        # Menu Bar: File -> Close Window
        close = QtWidgets.QAction(QtGui.QIcon('icons/exit.png'), '&Close Window', self)
        close.setStatusTip('Close Window')
        close.triggered.connect(self.__windowCloseWindow)  # pylint: disable=no-member
        self.fileMenu.addAction(close)

        # Menu Bar: File -> Exit Application
        exitAction = QtWidgets.QAction(QtGui.QIcon('icons/exit.png'), 'E&xit Application', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.__windowCloseApplication)  # pylint: disable=no-member
        self.fileMenu.addAction(exitAction)

        self.__windowMenuSetup(self.windowMenu)

        self.windowMenu.addSeparator()

        self.__toggleFullscreenSetup(self.windowMenu)

        # Menu Bar: Help -> Online User Guide.
        action = QtWidgets.QAction('Online User Guide', self)
        action.triggered.connect(self.openUserGuide)  # pylint: disable=no-member
        self.helpMenu.addAction(action)

        # Menu Bar: Help -> Make a Suggestion
        action = QtWidgets.QAction('Make a Suggestion', self)
        action.triggered.connect(self.openSuggestionPage)  # pylint: disable=no-member
        self.helpMenu.addAction(action)

        # Menu Bar: Help -> Report a Bug
        action = QtWidgets.QAction('Report a Bug', self)
        action.triggered.connect(self.openBugPage)  # pylint: disable=no-member
        self.helpMenu.addAction(action)

        self.helpMenu.addSeparator()

        # Menu Bar: Help -> About
        about = QtWidgets.QAction(QtGui.QIcon('icons/about.png'), 'About', self)
        about.setShortcut('F1')
        about.setStatusTip('About')
        about.triggered.connect(self.displayAbout)  # pylint: disable=no-member
        self.helpMenu.addAction(about)

    ################################################################################
    # Handles adding windows
    ################################################################################

    def __windowMenuSetup(self, menu):
        """Creates the menu items for dealing with multiple main windows"""
        self.windowMenu = menu

        # Menu Bar: Window -> Change Window Title
        changeTitle = QtWidgets.QAction("Change Window Title", self)
        changeTitle.triggered.connect(self.__windowMenuHandleChangeTitle)  # pylint: disable=no-member
        menu.addAction(changeTitle)

        # Menu Bar: Window -> Save Window Settings
        saveWindowSettings = QtWidgets.QAction("Save Window Settings", self)
        saveWindowSettings.triggered.connect(self.__saveSettings)  # pylint: disable=no-member
        menu.addAction(saveWindowSettings)

        # Menu Bar: Window -> Revert To Default Window Layout
        revertWindowSettings = QtWidgets.QAction("Revert To Default Window Layout", self)
        revertWindowSettings.triggered.connect(self.__revertLayout)  # pylint: disable=no-member
        menu.addAction(revertWindowSettings)

        menu.addSeparator()

        # Load list of window titles
        if not self.windows_titles:
            for name in self.windows_names:
                self.windows_titles[name] = str(self.settings.value("%s/Title" % name, name))

        # Create menu items for Window -> Open/Raise/Add Window "?"
        for name in self.windows_names:
            if name not in self.windows_actions:
                self.windows_actions[name] = QtWidgets.QAction("", self)

            menu.addAction(self.windows_actions[name])

        self.windowMenu.triggered.connect(self.__windowMenuHandle)

        self.__windowMenuUpdate()

    def __windowMenuUpdate(self):
        """Updates the QAction for each main window"""
        number = 1
        for name in self.windows_names:
            title = self.settings.value("%s/Title" % name, "")
            if title:
                title = "Open Window: %s" % self.windows_titles[name]
            else:
                title = "(%s) Add new window" % number
            self.windows_actions[name].setText(title)
            number += 1

        # Rename all the window menu actions to the window title
        for window in self.windows:
            self.windows_actions[window.name].setText("Raise Window: %s" % window.windowTitle())

    def __windowMenuHandle(self, action):
        """Handles the proper action for when a main window's QAction is clicked"""
        action_title = str(action.text())
        if action_title.startswith("Open Window: "):
            window_title = action_title.replace("Open Window: ","")
            for name in self.windows_titles:
                if self.windows_titles[name] == window_title:
                    self.windowMenuOpenWindow(name)

        elif action_title.endswith("Add new window") and len(action_title) == 18:
            number = int(action_title[1:].split(")")[0]) - 1
            self.windowMenuOpenWindow(self.windows_names[number])

        elif action_title.startswith("Raise Window: "):
            for window in self.windows:
                if str(window.windowTitle()) == action_title.replace("Raise Window: ",""):
                    window.raise_()
                    return

    def __windowMenuHandleChangeTitle(self):
        """Changes the title of the current window"""
        # Change the title of the current window
        (value, choice) = QtWidgets.QInputDialog.getText(
            self, "Rename window","Please provide a title for the window",
            QtWidgets.QLineEdit.Normal, str(self.windowTitle()))
        if choice:
            # Don't allow the same name twice
            for window in self.windows:
                if window.name == str(value) or str(window.windowTitle()) == str(value):
                    return
            self.setWindowTitle(str(value))
            self.windows_titles[self.name] = str(value)

        # Save the new title to settings
        self.settings.setValue("%s/Title" % self.name, self.windowTitle())

        self.__windowMenuUpdate()

    def windowMenuOpenWindow(self, name):
        """Launches the desired window"""
        # Don't open the same window twice
        for window in self.windows:
            if window.name == name or str(window.windowTitle()) == name:
                window.raise_()
                return

        # Create the new window
        mainWindow = MainWindow(self.app_name, self.app_version, name)
        if str(mainWindow.windowTitle()) == self.app_name:
            mainWindow.setWindowTitle(name)
        mainWindow.show()
        mainWindow.raise_()

        self.__windowMenuUpdate()

    def __windowOpened(self):
        """Called from __init__ on window creation"""
        # pylint: disable=no-member
        self.qApp.quit.connect(self.close)
        self.windows.append(self)
        self.qApp.closingApp = False
        # pylint: enable=no-member

    def __windowClosed(self):
        """Called from closeEvent on window close"""

        # Disconnect to avoid multiple attempts to close a window
        # pylint: disable=no-member
        self.qApp.quit.connect(self.close)
        # pylint: enable=no-member

        # Save the fact that this window is open or not when the app closed
        # pylint: disable=no-member
        self.settings.setValue("%s/Open" % self.name, self.qApp.closingApp)
        # pylint: enable=no-member

        # pylint: disable=bare-except
        try:
            self.windows.remove(self)
        except:
            pass
        self.__windowMenuUpdate()

    def __windowCloseWindow(self):
        """Closes the current window"""
        self.close()

    def __windowCloseApplication(self):
        """Called when the entire application should exit. Signals other windows
        to exit."""
        # pylint: disable=no-member
        self.qApp.closingApp = True
        self.qApp.quit.emit()
        # pylint: enable=no-member

    ################################################################################

    def __toggleFullscreenSetup(self, menu):
        # Menu Bar: Window -> Toggle Full-Screen
        fullscreen = QtWidgets.QAction(
            QtGui.QIcon('icons/fullscreen.png'), 'Toggle Full-Screen', self)
        fullscreen.setShortcut('Ctrl+F')
        fullscreen.setStatusTip('Toggle Full-Screen')
        fullscreen.triggered.connect(self.__toggleFullscreen)  # pylint: disable=no-member
        menu.addAction(fullscreen)

    def __toggleFullscreen(self):
        """Toggles the window state between fullscreen and maximized"""
        if self.isFullScreen():
            self.showNormal()
            self.showMaximized()
        else:
            self.showFullScreen()

    ################################################################################

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            # pylint: disable=no-member
            QtGui.qApp.request_update.emit()
            # pylint: enable=no-member
            event.accept()

    def closeEvent(self, event):
        """Called when the window is closed
        @type  event: QEvent
        @param event: The close event"""
        del event
        self.__saveSettings()
        self.__windowClosed()

    def __restoreSettings(self):
        """Restores the windows settings"""
        self.__plugins.restoreState()

        self.setWindowTitle(self.settings.value("%s/Title" % self.name,
                                                self.app_name))
        self.restoreState(self.settings.value("%s/State" % self.name,
                                              QtCore.QByteArray()))
        self.resize(self.settings.value("%s/Size" % self.name,
                                        QtCore.QSize(1280, 1024)))
        self.move(self.settings.value("%s/Position" % self.name,
                                      QtCore.QPoint(0, 0)))

    def __saveSettings(self):
        """Saves the windows settings"""
        logger.info('Saving: %s', self.settings.fileName())

        self.__plugins.saveState()

        # For populating the default state: print self.saveState().toBase64()

        self.settings.setValue("Version", self.app_version)

        self.settings.setValue("%s/Title" % self.name,
                               self.windowTitle())
        self.settings.setValue("%s/State" % self.name,
                               self.saveState())
        self.settings.setValue("%s/Size" % self.name,
                               self.size())
        self.settings.setValue("%s/Position" % self.name,
                               self.pos())

    def __revertLayout(self):
        """Revert back to default window layout"""
        result = QtWidgets.QMessageBox.question(
                    self,
                    "Restart required ",
                    "You must restart for this action to take effect, close window?: ",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        if result == QtWidgets.QMessageBox.Yes:
            self.settings.setValue("RevertLayout", True)
            self.__windowCloseApplication()

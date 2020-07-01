import logging
import sys
import os, traceback
import shutil
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
                QHBoxLayout, QLabel, QPushButton, QLineEdit, QProgressBar, QDoubleSpinBox, 
                QSpinBox, QAction, qApp, QStackedWidget, QMenuBar, QInputDialog, QFileDialog,
                QPlainTextEdit)

import time

from PyQt5.QtWidgets import QMessageBox

from GUI.Widgets.ProjectWidget import ProjectWidget
from GUI.Threading.BatchThread import BatchThread
from GUI.Dialogs.ProgressBarDialog import ProgressBarDialog
from GUI.Dialogs.NewProjectDialog import NewProjectDialog

class MainGUI(QMainWindow):

    def __init__(self, logman, comment_mgr, val):
        logging.debug("MainGUI(): Instantiated")
        super(MainGUI, self).__init__()
        self.setWindowTitle('Traffic Annotation Workflow')
        self.setFixedSize(670,565)

        self.logman = logman
        self.comment_mgr = comment_mgr
        self.val = val

        #shared data between widgets
        self.configname = ''
        self.path = ''
        self.existingconfignames = []
        self.annotatedPCAP = ''
        self.sessionName = ''
        self.existingSessionNames = []
        self.logEnabled = ''
        self.closeConfirmed = ''

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        mainlayout = QVBoxLayout()
        self.baseWidget = QWidget() #BaseWidget()
        self.projectTree = QtWidgets.QTreeWidget()
        self.baseWidgets = {}
        self.blankTreeContextMenu = {}
        
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

        #Add tab widget - RES
        tabWidget = QtWidgets.QTabWidget()
        tabWidget.setGeometry(QtCore.QRect(0, 15, 668, 565))
        tabWidget.setObjectName("tabWidget")

        #BaseWidget
        self.baseWidget.setWindowTitle("BaseWidget")
        self.baseWidget.setObjectName("BaseWidget")
        baseLayoutWidget = QtWidgets.QWidget()
        baseLayoutWidget.setObjectName("layoutWidget")
        self.baseOuterVertBox = QtWidgets.QVBoxLayout()
        self.baseOuterVertBox.setObjectName("outerVertBox")
        baseLayoutWidget.setLayout(self.baseOuterVertBox)

        self.baseWidget.setLayout(self.baseOuterVertBox)

        #Configuration window - RES
        ## windowBoxHLayout contains:
        ###projectTree (Left)
        ###basedataStackedWidget (Right)
        windowWidget = QtWidgets.QWidget()
        windowWidget.setObjectName("windowWidget")
        windowBoxHLayout = QtWidgets.QHBoxLayout()
        windowBoxHLayout.setObjectName("windowBoxHLayout")
        windowWidget.setLayout(windowBoxHLayout)

        self.projectTree.itemSelectionChanged.connect(self.onItemSelected)
        self.projectTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.projectTree.customContextMenuRequested.connect(self.showContextMenu)
        self.projectTree.setEnabled(True)
        self.projectTree.setMaximumSize(200,521)
        self.projectTree.setObjectName("projectTree")
        self.projectTree.headerItem().setText(0, "Projects")
        self.projectTree.setSortingEnabled(False)
        windowBoxHLayout.addWidget(self.projectTree)

        self.basedataStackedWidget = QStackedWidget()
        self.basedataStackedWidget.setObjectName("basedataStackedWidget")
        windowBoxHLayout.addWidget(self.basedataStackedWidget)
        tabWidget.addTab(windowWidget, "Configuration")

        #Set up context menu
        self.setupContextMenus()

        #ADD TAB WIDGET - RES
        self.initMenu()
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.mainMenu)
        mainlayout.addWidget(tabWidget)
        self.mainWidget.setLayout(mainlayout)

        logging.debug("MainWindow(): Complete")

    #RES Method
    def onItemSelected(self):
        logging.debug("MainApp:onItemSelected instantiated")
    	# Get the selected item
        self.selectedItem = self.projectTree.currentItem()
        if self.selectedItem == None:
            logging.debug("MainApp:onItemSelected no configurations left")
            self.statusBar.showMessage("No configuration items selected or available.")
            return
        # Now enable the save button
        self.saveProjectMenuButton.setEnabled(True)

        #Check if it's the case that an project name was selected
        parentSelectedItem = self.selectedItem.parent()
        if(parentSelectedItem == None):
            #A base widget was selected
            #print("PROJECT_WIDGET: " + str((self.baseWidgets[self.selectedItem.text(0)]["ProjectWidget"])))
            self.basedataStackedWidget.setCurrentWidget(self.baseWidgets[self.selectedItem.text(0)]["ProjectWidget"])
        else:
            #Check if it's the case that a VM Name was selected
            if(self.selectedItem.text(0)[0] == "V"):
                logging.debug("Setting right widget: " + str(self.baseWidgets[parentSelectedItem.text(0)]["VMWidgets"][self.selectedItem.text(0)]))
                self.basedataStackedWidget.setCurrentWidget(self.baseWidgets[parentSelectedItem.text(0)]["VMWidgets"][self.selectedItem.text(0)])
            #Check if it's the case that a Material Name was selected
            elif(self.selectedItem.text(0)[0] == "M"):
                logging.debug("Setting right widget: " + str(self.baseWidgets[parentSelectedItem.text(0)]["MaterialWidgets"][self.selectedItem.text(0)]))
                self.basedataStackedWidget.setCurrentWidget(self.baseWidgets[parentSelectedItem.text(0)]["MaterialWidgets"][self.selectedItem.text(0)])

    #RES METHOD
    def setupContextMenus(self):
        logging.debug("MainApp:setupContextMenus() instantiated")
        #Context menu for blank space
        self.blankTreeContextMenu = QtWidgets.QMenu()
       	self.addproject = self.blankTreeContextMenu.addAction("New project")
       	self.addproject.triggered.connect(self.newProject)
        self.importproject = self.blankTreeContextMenu.addAction("Import project folder")
        self.importproject.triggered.connect(self.importActionEvent)

        #Context menu project 
        self.projectContextMenu = QtWidgets.QMenu()
        self.addCuration = self.projectContextMenu.addAction("Add Curation")
        self.addCuration.triggered.connect(self.on_add_curation_clicked)

    def on_add_curation_clicked(self):
        logging.debug("on_add_curation_clicked(): Instantiated")

        ok = QInputDialog.getText(self, 'New Session', 
            'Enter new session name \r\n(non alphanumeric characters will be removed)')
        if ok:
            self.sessionName = ''.join(e for e in self.sessionName if e.isalnum())
            if self.sessionName in self.existingSessionNames:
                QMessageBox.warning(self,
                                        "Session Name Exists",
                                        "The session name specified already exists",
                                        QMessageBox.Ok)    
            else:
                #if all good, add session name to list
                self.existingSessionNames += [self.sessionName]    

        logging.debug("on_add_curation_clicked(): Completed")

    #RES METHOD
    def showContextMenu(self, position):
    	logging.debug("MainApp:showContextMenu() instantiated: " + str(position))
    	if(self.projectTree.itemAt(position) == None):
    		self.blankTreeContextMenu.popup(self.projectTree.mapToGlobal(position))
    	elif(self.projectTree.itemAt(position).parent() == None):
    		self.projectContextMenu.popup(self.projectTree.mapToGlobal(position))
    	else:
    		self.itemContextMenu.popup(self.projectTree.mapToGlobal(position))

    #RES METHOD
    def initMenu(self):               
        
        self.mainMenu = QMenuBar()
        self.fileMenu = self.mainMenu.addMenu("File")

        self.newProjectMenuButton = QAction(QIcon(), "New Project", self)
        self.newProjectMenuButton.setShortcut("Ctrl+N")
        self.newProjectMenuButton.setStatusTip("Create New Project")
        self.newProjectMenuButton.triggered.connect(self.newProject)
        self.fileMenu.addAction(self.newProjectMenuButton)

        self.importProjectMenuButton = QAction(QIcon(), "Import Project", self)
        self.importProjectMenuButton.setShortcut("Ctrl+I")
        self.importProjectMenuButton.setStatusTip("Import folder")
        self.importProjectMenuButton.triggered.connect(self.importActionEvent)
        self.fileMenu.addAction(self.importProjectMenuButton)

        self.saveProjectMenuButton = QAction(QIcon(), "Save Project", self)
        self.saveProjectMenuButton.setShortcut("Ctrl+S")
        self.saveProjectMenuButton.setStatusTip("Save currently selected project")
        #self.saveProjectMenuButton.triggered.connect(self.saveProjectButton)
        self.saveProjectMenuButton.setEnabled(False)
        self.fileMenu.addAction(self.saveProjectMenuButton)

        self.quitAppMenuButton = QAction(QIcon(), "Quit", self)
        self.quitAppMenuButton.setShortcut("Ctrl+Q")
        self.quitAppMenuButton.setStatusTip("Quit App")
        self.quitAppMenuButton.triggered.connect(self.closeEvent)
        self.fileMenu.addAction(self.quitAppMenuButton)
    
    #Used to create a new project, this is where the prompt to write a name for the project is taken.
    def newProject(self):
        #Creating a custom widget to display what is needed for creating a new project:
        self.newPro = NewProjectDialog(self.logman, self.existingconfignames)
        self.newPro.logEnabled.connect(self.log_enabled)
        self.newPro.created.connect(self.project_created)
        self.newPro.show()

    #Slot for when the user created the new project, path and configname
    @QtCore.pyqtSlot(str, list, str, str)
    def project_created(self, configname, existingconfignames, pcap, path):
        self.configname = configname
        self.path = path
        self.existingconfignames = existingconfignames
        self.annotatedPCAP = pcap

        self.addProject()

    #Slot to let us know if the logging has started
    @QtCore.pyqtSlot(str)
    def log_enabled(self, status):
        self.logEnabled = status

    #Slot to let us know if the close has been confirmed or canceled
    @QtCore.pyqtSlot(str)
    def close_confirmed(self, status):
        self.closeConfirmed = status

    #Used to create a new project, and this is where the project will actually be populated
    def addProject(self):
        self.projectWidget  = ProjectWidget(self.configname, self.annotatedPCAP, self.path)
        #create the folders and files for new project:
        self.filename = self.configname
        self.successfilenames = []
        self.successfoldernames = []
        #self.destinationPath = self.path
        self.foldersToCreate = []
        self.filesToCreate = []
        """ basePath = os.path.join(self.path,self.filename)
        self.foldersToCreate.append(basePath)
        self.foldersToCreate.append(os.path.join(basePath, "Materials"))
        self.foldersToCreate.append(os.path.join(basePath, "Logs")) """

        if self.filename != None:
            logging.debug("addProject(): OK pressed and valid configname entered: " + str(self.filename))
        
        configTreeWidgetItem = QtWidgets.QTreeWidgetItem(self.projectTree)
        configTreeWidgetItem.setText(0,self.filename)
        self.projectWidget.addProjectItem(self.filename)

        #Add base info
        self.baseWidgets[self.configname] = {"BaseWidget": {}, "ProjectWidget": {} }
        self.baseWidgets[self.configname]["BaseWidget"] = self.baseWidget
        self.basedataStackedWidget.addWidget(self.baseWidget)
        
        self.baseWidgets[self.configname]["ProjectWidget"] = self.projectWidget

        self.basedataStackedWidget.addWidget(self.projectWidget)
        self.basedataStackedWidget.addWidget(self.baseWidget)

    #A combination of RES Methods
    def importActionEvent(self):
        logging.debug("MainApp:importActionEvent() instantiated") 

        folder_chosen = str(QFileDialog.getExistingDirectory(self, "Select Directory to Store Data"))
        if folder_chosen == "":
            logging.debug("File choose cancelled")
            return

    def update_progress_bar(self):
        logging.debug('update_progress_bar(): Instantiated')
        self.progress_dialog_overall.update_progress()
        logging.debug('update_progress_bar(): Complete')

    def closeEvent(self, event):
        logging.debug("closeEvent(): instantiated")

        self.quit_event = event

        if self.logEnabled == "TRUE":
            #This means that the new project widget is still running so call the close event
            #for that widget first to stop logger
            self.newPro.closeEvent(event)

            #Check if the close was confirmed or not
            if self.close_confirmed == True:
                #after that's done, make sure to quit the app
                self.quit_app()
            else: 
                pass
        else:
            close = QMessageBox.question(self, 
                                "QUIT",
                                "Are you sure you want to quit? \n Any unsaved data will be lost",
                                QMessageBox.Yes | QMessageBox.No)
            if close == QMessageBox.Yes:
                qApp.quit()
                return
            elif close == QMessageBox.No and not type(self.quit_event) == bool:
                    self.quit_event.ignore()
            pass
        return
        
    def quit_app(self):
        self.quit_event.accept()
        qApp.quit()
        return
            
        
                
import logging
import subprocess
import shlex
import sys
from ConfigurationManager.ConfigurationManager import ConfigurationManager
from PyQt5.QtCore import QThread

class FileExplorerRunner(QThread):

    def __init__(self, folder_location=None):
        logging.debug('FileExplorerRunner(): Instantiated')
        QThread.__init__(self)
        self.cmd = ConfigurationManager.get_instance().read_config_abspath("SYSTEM","FILE_EXPLORER_FILENAME")
        if folder_location != None:
            self.cmd+= " " + folder_location
        logging.debug('FileExplorerRunner(): Complete')

    def run(self):
        logging.debug('FileExplorerRunner.run(): Instantiated')
        if sys.platform == "linux" or sys.platform == "linux2":
            logging.debug('FileExplorerRunner.run(): Running command: ' + str(self.cmd))
            output = subprocess.check_output(shlex.split(self.cmd))
        else: 
            output = subprocess.check_output(self.cmd)

        logging.debug('FileExplorerRunner.run(): Complete')


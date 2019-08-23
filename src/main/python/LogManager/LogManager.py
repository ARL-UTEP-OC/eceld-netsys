import time
import logging
import os
import shutil
import sys, traceback
from subprocess import Popen
import Pyro4
from ConfigurationManager.ConfigurationManager import ConfigurationManager
from LogManager.DissectorGenerator import DissectorGenerator

class LogManager():
    def __init__(self):
        logging.debug("LogManager(): Instantiating ecel_manager()")
        #start the nameserver
        logging.debug("ecel_manager(): getting a handle to the ecel.service")
        self.ecel_manager = Pyro4.Proxy("PYRONAME:ecel.service")    # use name server object lookup uri shortcut
        self.generated_dissector_filenames = []
        logging.debug("LogManager(): Completed Instantiating ecel_manager()")

    def removeDataAll(self):
        logging.debug("removeDataAll(): requesting to remove all data")
        self.ecel_manager.remove_data()
        logging.debug("removeDataAll(): Completed requesting to remove all data")

    def startCollectors(self):
        logging.debug("startCollectors(): requesting to start collectors")
        self.ecel_manager.start_collectors()
        logging.debug("startCollectors(): Completed requesting to start collectors")

    def stopCollectors(self):
        logging.debug("stopCollectors(): requesting to stop collectors")
        self.ecel_manager.stop_collectors()
        logging.debug("stopCollectors(): Completed requesting to stop collectors")

    def parseDataAll(self):
        logging.debug("parseDataAll(): requesting to parse all data")
        self.ecel_manager.parse_data_all()
        logging.debug("parseDataAll(): Completed requesting to parse all data")

    def exportData(self, export_data_path=None):
        logging.debug("exportData(): requesting to export data to " + str(export_data_path))
        
        self.export_data_path = export_data_path
        if export_data_path == None:
            #read from config file
            self.export_data_path = ConfigurationManager.get_instance().read_config_value("LOG_MANAGER", "EXPORT_DATA_PATH_TEMP")

        anyParsersRunning = self.ecel_manager.is_parser_running()
        logging.debug ("Checking if parsers running: " + str(anyParsersRunning))
        while anyParsersRunning == True:
            logging.debug ("Waiting a few seconds...")
            time.sleep(5)
            anyParsersRunning = self.ecel_manager.is_parser_running()
        logging.debug ("No more parsers running. Continuing...")

        try:
            if os.path.exists(self.export_data_path) == False:
                os.makedirs(self.export_data_path)
        except:
            logging.error("exportData(): An error occured when trying to use path for export: " + str(self.export_data_path))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        self.ecel_manager.export_data(self.export_data_path)
        logging.debug("exportData(): Completed requesting to export data")

    def copyLatestData(self, export_data_path_temp=None, export_data_path_latest=None, user_pcap_filename=None):
        logging.debug('copyData(): Instantiated')
        #get the directory with all of the exported data:
        self.export_data_path_temp = export_data_path_temp
        if self.export_data_path_temp == None:
            #read from config file
            self.export_data_path_temp = ConfigurationManager.get_instance().read_config_value("LOG_MANAGER", "EXPORT_DATA_PATH_TEMP")
        
        #this is where the latest exported data will be placed
        self.export_data_path_latest = export_data_path_latest
        if self.export_data_path_latest == None:
            #read from config file
            self.export_data_path_latest = ConfigurationManager.get_instance().read_config_value("LOG_MANAGER", "EXPORT_DATA_PATH_LATEST")

        self.user_pcap_filename = user_pcap_filename
        if self.user_pcap_filename == None:
            #read from config file
            self.user_pcap_filename = ConfigurationManager.get_instance().read_config_value("LOG_MANAGER", "USER_PCAP_FILENAME")

        latestlogdirs = self.getSortedInDirs(self.export_data_path_temp, dircontains="export")
        latestlogdir = ""
        if len(latestlogdirs) > 0:
            #get the latest directory based on its timestamp
            latestlogdir = latestlogdirs[-1]
        else:
            logging.error("No export log file directory found in path: " + self.export_data_path_temp)
            return
        try:
            if os.path.exists(self.export_data_path_latest) == False:
                os.makedirs(self.export_data_path_latest)
            pcapbase = os.path.dirname(self.user_pcap_filename)
            if os.path.exists(pcapbase) == False:
                os.makedirs(pcapbase)
        except:
            logging.error("on_log_stop_button_clicked(): An error occured when trying create directory")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)

        try:
            #cp all JSON files to out dir
            snoopyFile = os.path.join(latestlogdir,"parsed","snoopy","snoopyData.JSON")
            keystrokesFile = os.path.join(latestlogdir,"parsed","pykeylogger","keypressData.JSON")
            if os.path.exists(snoopyFile):
                shutil.copy(snoopyFile,os.path.join(self.export_data_path_latest,"SystemCalls.JSON"))
            if os.path.exists(keystrokesFile):
                shutil.copy(keystrokesFile,os.path.join(self.export_data_path_latest,"Keypresses.JSON"))
            #cp merged pcap to dir
            pcapFile = os.path.join(latestlogdir,"raw","tshark","merged.pcapng")
            if os.path.exists(pcapFile):
                shutil.copy(pcapFile,self.user_pcap_filename)
        except:
            logging.error("on_log_stop_button_clicked(): An error occured when trying to copy log files")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    def getSortedInDirs(self, path, dircontains=""):
        logging.debug('getSortedInDirs(): Instantiated')
        name_list = os.listdir(path)
        dirs = []
        for name in name_list:
            fullpath = os.path.join(path,name)
            if os.path.isdir(fullpath) and (dircontains in name):
                dirs.append(fullpath)
        logging.debug('getSortedInDirs(): Completed')
        if dirs != None:
            return sorted(dirs)
        return []

    def generateDissectors(self, export_data_path_latest=None, dissector_path=None, dissector_code_template_filename=None):
        logging.debug('generateDissectors(): Instantiated')
        dg = DissectorGenerator()
        #clear out the previous list of generated dissectors
        self.generated_dissector_filenames = []

        #this is where the latest exported data will be read
        self.export_data_path_latest = export_data_path_latest
        if self.export_data_path_latest == None:
            #read from config file
            self.export_data_path_latest = ConfigurationManager.get_instance().read_config_value("LOG_MANAGER", "EXPORT_DATA_PATH_LATEST")

        #this is where the dissectors will be placed
        self.dissector_path = dissector_path
        if self.dissector_path == None:
            #read from config file
            self.dissector_path = ConfigurationManager.get_instance().read_config_value("LOG_MANAGER", "DISSECTOR_PATH")

        #this is where the dissectors will be placed
        self.dissector_code_template_filename = dissector_code_template_filename
        if self.dissector_code_template_filename == None:
            #read from config file
            self.dissector_code_template_filename = ConfigurationManager.get_instance().read_config_value("LOG_MANAGER", "DISSECTOR_CODE_TEMPLATE_FILENAME")

        #get files in directory
        self.filelist = dg.getJSONFiles(self.export_data_path_latest)

        file_events = {}
        
        try:
            #remove directory if it exists and then create it
            if os.path.exists(self.dissector_path) == True:
                shutil.rmtree(self.dissector_path, ignore_errors=True)
            os.makedirs(self.dissector_path)
        except:
            logging.error("generateDissectors(): An error occured when trying to copy log files")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)

        for filename in self.filelist:
            #save the filename as a key, all the events (event, time) as the value
            file_events = dg.readJSONData(filename)
            base = os.path.basename(filename)
            basenoext = os.path.splitext(base)[0]
            dissector_filename = dg.eventsToDissector(file_events, dissector_name=basenoext, ofilename=os.path.join(self.dissector_path,basenoext), template_filename=self.dissector_code_template_filename, start_threshold=0.0, end_threshold=0.2)
            self.generated_dissector_filenames.append(dissector_filename)
        logging.debug('generateDissectors(): Completed')

    def get_generated_dissector_filenames(self):
        logging.debug('get_generated_dissector_filenames(): Instantiated')
        logging.debug('get_generated_dissector_filenames(): Completed')
        return self.generated_dissector_filenames       

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Instantiating ECELDClient()")
    lm = LogManager()
    lm.startCollectors()
    time.sleep(5)
    lm.stopCollectors()
    lm.parseDataAll()
    lm.exportData(export_data_path="/root/Desktop/")
    logging.debug("Completed ECELDClient()") 

"""
This module consolidates all local configuration for the script, including modulename collection for logfile name
setup and initializing the config file.
Also other utilities find their home here.
"""

import configparser
import datetime
import logging
import logging.handlers
import os
import platform
import re
import sys


def get_modulename(scriptname):
    """
    Modulename is required for logfile and for properties file.
    :param scriptname: Name of the script for which modulename is required. Use __file__.
    :return: Module Filename from the calling script.
    """
    # Extract calling application name
    (filepath, filename) = os.path.split(scriptname)
    (module, fileext) = os.path.splitext(filename)
    return module


def init_loghandler(config, modulename):
    """
    This function initializes the loghandler. Logfilename consists of calling module name + computername.
    Logfile directory is read from the project .ini file.
    Format of the logmessage is specified in basicConfig function.
    This is for Log Handler configuration. If basic log file configuration is required, then use init_logfile.
    :param config: Reference to the configuration ini file. Directory for logfile should be
    in section Main entry logdir.
    :param modulename: The name of the module. Each module will create it's own logfile.
    :return: Log Handler
    """
    logdir = config['Main']['logdir']
    # Extract Computername
    computername = platform.node()
    # Define logfileName
    logfile = logdir + "/" + modulename + "_" + computername + ".log"
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # Create Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # Create Rotating File Handler
    # Get logfiles of 1M
    maxbytes = 1024 * 1024
    rfh = logging.handlers.RotatingFileHandler(logfile, maxBytes=maxbytes, backupCount=5)
    # Create Formatter for file
    formatter_file = logging.Formatter(fmt='%(asctime)s|%(module)s|%(funcName)s|%(lineno)d|%(levelname)s|%(message)s',
                                       datefmt='%d/%m/%Y|%H:%M:%S')
    formatter_console = logging.Formatter(fmt='%(asctime)s - %(module)s - %(funcName)s - %(lineno)d - %(levelname)s -'
                                              ' %(message)s',
                                          datefmt='%H:%M:%S')
    # Add Formatter to Console Handler
    ch.setFormatter(formatter_console)
    # Add Formatter to Rotating File Handler
    rfh.setFormatter(formatter_file)
    # Add Handler to the logger
    logger.addHandler(ch)
    logger.addHandler(rfh)
    return logger


def get_inifile(projectname, scriptname):
    """
    Read Project configuration ini file in subdirectory properties.
    :param projectname: Name of the project.
    :param scriptname: Name of the calling application. This is used to calculate the config file path.
    :return: Object reference to the inifile.
    """
    # Use Project Name as ini file.
    # os.path.realpath will ensure full path name
    # os.path.split will split in directory and basename
    (filepath, filename) = os.path.split(os.path.realpath(scriptname))
    # Set filename according to your system specs (Windows, Linux, ...)
    configfile = os.path.join(filepath, "properties", projectname + ".ini")
    ini_config = configparser.ConfigParser()
    try:
        ini_config.read_file(open(configfile))
    except:
        e = sys.exc_info()[1]
        ec = sys.exc_info()[0]
        log_msg = "Read Inifile not successful: {0} ({1}) - filepath: {2}"
        print(log_msg.format(e, ec, filepath))
        sys.exit(1)
    return ini_config

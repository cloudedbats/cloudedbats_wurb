#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import sys
import pathlib
import logging
from logging import handlers

class WurbLogging(object):
    """ Log module for the CloudedBats recording unit.
        Two target log files are used. Both are implemented as rotation logs.
        1. Internal log stored on the Raspberry Pi micro SD card.
        2. External log stored on the USB memory for easy access when moving the 
           USB memory to another computer. 
           
        Usage:
            self._logger = logging.getLogger('CloudedBatsWURB')
            self._logger.info('Info message.')
            self._logger.warning('Warning message.')
            self._logger.error('Error message.')
            self._logger.debug('Debug message.')
            try: ...
            except Exception as e:
                self._logger.error('Exception: ' + str(e))
    """
    
    def __init__(self):
        """ """

    def setup(self,
              usb_required=True,  
              internal_path = 'wurb_log_files',
              external_path = '/media/usb0/cloudedbats_wurb/log_files'):
        """ """
        self._usb_required = usb_required
        log = logging.getLogger('CloudedBatsWURB')
#        log.setLevel(logging.INFO)
        log.setLevel(logging.DEBUG)
        #
        # Internal.
        dir_path = pathlib.Path(sys.modules['__main__'].__file__).parents[0] # Same level as wurb_main.py.
        self._internal_dir_path = pathlib.Path(dir_path, internal_path)
        self._internal_log_path = pathlib.Path(self._internal_dir_path, 'wurb_log.txt')
        # External.
        self._external_dir_path = pathlib.Path(external_path)
        self._external_log_path = pathlib.Path(self._external_dir_path, 'wurb_log.txt')
        
        # Log directories.
        if not self._internal_dir_path.exists():
            self._internal_dir_path.mkdir(parents=True)
        if self._usb_required:
            if pathlib.Path('/media/usb0').exists():
                if not self._external_dir_path.exists():
                    self._external_dir_path.mkdir(parents=True)
        
        # Define rotation log files for internal log files.
        try:
            log_handler = handlers.RotatingFileHandler(str(self._internal_log_path),
                                                       maxBytes = 128*1024,
                                                       backupCount = 10)
            log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-10s : %(message)s '))
            log_handler.setLevel(logging.DEBUG)
            log.addHandler(log_handler)
        except Exception as e:
            print('WURB logging: Failed to set up logging: ' + str(e))
        
        # Define rotation log files for external log files.
        try:
            if self._usb_required:
                if pathlib.Path('/media/usb0').exists():
                    log_handler_ext = handlers.RotatingFileHandler(str(self._external_log_path),
                                                                   maxBytes = 128*1024,
                                                                   backupCount = 10)
                    log_handler_ext.setFormatter(logging.Formatter('%(asctime)s %(levelname)-10s : %(message)s '))
                    log_handler_ext.setLevel(logging.INFO)
                    log.addHandler(log_handler_ext)
                else:
                    log.warning('')
                    log.warning('')
                    log.warning('Logging: Path /media/usb0 does not exist.')
        except Exception as e:
            print('WURB logging: Failed to set up logging on /media/usb0: ' + str(e))
            

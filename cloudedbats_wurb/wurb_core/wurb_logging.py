#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import pathlib
import logging
import logging.handlers

class WurbLogging(object):
    """ """
    def __init__(self):
        """ """

    def setup(self,
              internal_path = '../wurb_logging',
              external_path = '/media/usb/clouded_bats/wurb_logging'):
        """ """
        log = logging.getLogger('CloudedBatsWURB')
#        log.setLevel(logging.INFO)
        log.setLevel(logging.DEBUG)
        #
        # Internal.
        dir_path = os.path.dirname(os.path.abspath(__file__))
        self._internal_dir_path = pathlib.Path(dir_path, internal_path)
        self._internal_log_path = pathlib.Path(self._internal_dir_path, 'wurb_log.txt')
        # External.
        self._external_dir_path = pathlib.Path(external_path)
        self._external_log_path = pathlib.Path(self._external_dir_path, 'wurb_log.txt')
        
        # Log directories.
        if not self._internal_dir_path.exists():
            self._internal_dir_path.mkdir(parents=True)
        if pathlib.Path('media/usb').exists():
            if not self._external_dir_path.exists():
                self._external_dir_path.mkdir(parents=True)
        
        # Define rotation log files for internal log files.
        log_handler = logging.handlers.RotatingFileHandler(str(self._internal_log_path),
                                                           maxBytes = 128*1024,
                                                           backupCount = 10)
        log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-10s : %(message)s '))
        log_handler.setLevel(logging.DEBUG)
        log.addHandler(log_handler)
        
        # Define rotation log files for external log files.
        if pathlib.Path('media/usb').exists():
            log_handler = logging.handlers.RotatingFileHandler(str(self._external_log_path),
                                                               maxBytes = 128*1024,
                                                               backupCount = 10)
            log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-10s : %(message)s '))
            log_handler.setLevel(logging.INFO)
            log.addHandler(log_handler)

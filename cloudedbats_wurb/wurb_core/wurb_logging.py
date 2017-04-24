#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import logging
import logging.handlers

class WurbLogging(object):
    """ """
    def __init__(self):
        """ """

    def setup(self):
        """ """
        log = logging.getLogger('CloudedBatsWURB')
        log.setLevel(logging.INFO)
        # Define rotation log files.
        log_file_name = 'cloudedbats_log.txt'
        dir_path = os.path.dirname(os.path.abspath(__file__))
        log_handler = logging.handlers.RotatingFileHandler(os.path.join(dir_path, log_file_name),
                                                           maxBytes = 128*1024,
                                                           backupCount = 10)
        log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-10s : %(message)s '))
        log_handler.setLevel(logging.DEBUG)
        log.addHandler(log_handler)

#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import wurb_core

if __name__ == "__main__":
    """ Main module for CloudedBats WURB, 
        Wireless Ultrasonic Recorder for Bats. """
    
    wurb_app = wurb_core.WurbApplication()

# # TODO: For development.
#     import time
#     time.sleep(1.0)
#     wurb_app.perform_event('test_rec_on')
#     time.sleep(20.0) 
#     wurb_app.perform_event('test_rec_off')
#     time.sleep(0.1)
#     wurb_app.stop()

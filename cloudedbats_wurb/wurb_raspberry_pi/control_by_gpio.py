#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import time
import logging
import threading
# Check if GPIO is available.
gpio_available = True
try: import RPi.GPIO as GPIO
except: gpio_available = False

class ControlByGpio(object):
    """ Use GPIO for control when running without a graphical user interface. """

    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        # Recording control.
        self.rec_on_state = False
        self.rec_off_state = False
        self.rec_on_count = 0
        self.rec_off_count = 0
        # GPIO
        if not gpio_available:
            self._logger.error('GPIO control: RaspberryPi-GPIO not available.')
            return
        #
        self._gpio_pin_rec_on = 37 # GPIO 26
        self._gpio_pin_rec_off = 38 # GPIO 20
        self._setup_gpio()
        #
        self._active = True
        self._start_gpio_check()
        
    def stop(self):
        """ """
        self._active = False
    
    def is_gpio_rec_on(self):
        """ """
        return self.rec_on_state
    
    def is_gpio_rec_off(self):
        """ """
        return self.rec_off_state
    
    def is_gpio_rec_auto(self):
        """ """
        return (self.rec_on_state == False) and (self.rec_off_state == False)
    
    def _fire_event(self, event):
        """ Event for the state machine. """
        if self._callback_function:
            self._callback_function(event)            
    
    def _setup_gpio(self):
        """ """
        GPIO.setmode(GPIO.BOARD) # Use pin numbers (1-40). 
        # Use the built in pull-up resistors. 
        GPIO.setup(self._gpio_pin_rec_on, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self._gpio_pin_rec_off, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def _start_gpio_check(self):
        """ """
        # Check GPIO activity in a separate thread.
        self._check_gpio_thread = threading.Thread(target = self._check_gpio, args = [])
        self._check_gpio_thread.start()
         
    def _check_gpio(self):
        """ """
        old_rec_on_state = self.rec_on_state
        old_rec_off_state = self.rec_off_state
        
        while self._active:
            time.sleep(0.1)
            try:
                # Check if recording on is active.
                if GPIO.input(self._gpio_pin_rec_on):
                    # High = inactive.
                    self.rec_on_count = 0
                    self.rec_on_state = False
                else:
                    # Low = active.
                    if self.rec_on_count >= 5: # After 0.5 sec.
                        self.rec_on_state = True
                    else:
                        self.rec_on_count += 1
                
                # Check if recording off is active.
                if GPIO.input(self._gpio_pin_rec_off):
                    # High = inactive.
                    self.rec_off_count = 0
                    self.rec_off_state = False
                else:
                    # Low = active.
                    if self.rec_off_count >= 5: # After 0.5 sec.
                        self.rec_off_state = True
                    else:
                        self.rec_off_count += 1
                        
                # Fire event.
                if (old_rec_on_state != self.rec_on_state) or \
                   (old_rec_off_state != self.rec_off_state):

                    if self.rec_on_state:
                        # Rec on active.
                        self._fire_event('gpio_rec_on')
                    elif self.rec_off_state:
                        # Rec off active.
                        self._fire_event('gpio_rec_off')
                    else:
                        # Both inactive = Auto.
                        self._fire_event('gpio_rec_auto')
                #                
                old_rec_on_state = self.rec_on_state
                old_rec_off_state = self.rec_off_state

            except:
                pass


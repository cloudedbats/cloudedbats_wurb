#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os 
import time 
import logging
import threading

class ControlByMouse(object):
    """ For Raspberry Pi. Makes a mouse acting as a remote controller when 
        running the RPi without a graphical user interface. 
        Alternatives:
        - Left and right button pressed: RPi shutdown.
        - Left button pressed: Start rec, auto mode deactivated.
        - Middle button (or scroll wheel) pressed: Activate auto mode. 
        - Right button pressed: Stop rec, auto mode deactivated.
    """

    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        #
        # Set time before action.
        self.left_and_right_time = 3.0 # Left and right buttons. 3 sec.
        self.left_time = 1.0 # Left button. 1 sec.
        self.middle_time = 1.0 # Left button. 1 sec.
        self.right_time = 1.0 # Right button. 1 sec.
        # Local.
        self._left_and_right_start = False
        self._left_start = False
        self._middle_start = False
        self._right_start = False
        self._last_command = ''
        self._mouse_thread = None
        # Start.
        self._active = False
        self._start_remote_control()

    def stop(self):
        """ """
        # TODO: Note, the read command is blocking the thread.
        self._active = False
        
    def left_and_right_action(self):
        """ """
#         self._logger.info('Mouse control: Raspberry Pi shutdown.')
#         os.system('sudo shutdown -h now')
        self._callback_function('mouse_rpi_shutdown')

    def left_action(self):
        """ """
        self._callback_function('mouse_rec_on')

    def middle_action(self):
        """ """
        self._callback_function('mouse_rec_auto')
        # self._cloudedbats_mini.auto_on()

    def right_action(self):
        """ """
        self._callback_function('mouse_rec_off')
        # self._cloudedbats_mini.rec_off()
        
    # Local methods.
    def _start_remote_control(self):
        """ """
        self._active = True
        # Check mouse button clicks in a separate thread.
        self._mouse_thread = threading.Thread(target = self._read_mouse_device, args = [])
        self._mouse_thread.start()
        #
        # Check for actions in a separate thread.
        self._actions_thread = threading.Thread(target = self._check_for_actions, args = [])
        self._actions_thread.start()
        #

    def _check_for_actions(self):
        """ Note: Running in thread. """
        # Check for actions.
        try:
            while self._active:
                # 
                try: time.sleep(0.1) # Check 10 times/sec.
                except: pass
                # Terminate loop if no object instance.
                if self is None: 
                    break
                #
                if self._left_and_right_start and ((time.time() - self._left_and_right_start) >= self.left_and_right_time):
                    if self._last_command != 'left_and_right':
                        try:
                            self._logger.info('Mouse control: Left and right buttons pressed.')
                            self.left_and_right_action()
                        except: pass
                        self._last_command = 'left_and_right'
                    #
                    continue
                #   
                if self._left_start and ((time.time() - self._left_start) >= self.left_time):
                    if self._last_command != 'left':
                        try:
                            self._logger.info('Mouse control: Left button pressed.')
                            self.left_action()
                        except: pass
                        self._last_command = 'left'
                    #
                    continue
                #   
                if self._middle_start and ((time.time() - self._middle_start) >= self.middle_time):
                    if self._last_command != 'middle':
                        try:
                            self._logger.info('Mouse control: Middle button pressed.')
                            self.middle_action()
                        except: pass
                        self._last_command = 'middle'
                    #
                    continue
                #
                if self._right_start and ((time.time() - self._right_start) >= self.right_time):
                    if self._last_command != 'right':
                        try:
                            self._logger.info('Mouse control: Right button pressed.')
                            self.right_action()
                        except: pass
                        self._last_command = 'right'
                    #
                    continue
        #
        except Exception as e :
            self._logger.error('Mouse control: Failed to check mouse actions: ' + str(e))
        

    def _read_mouse_device(self):
        """ Note: Running in thread. """
        # Open 'file' for reading mouse actions.
        try:
            with open( "/dev/input/mice", "rb" ) as mice_file:
                # Loop and check mouse buttons.
                while self._active:
                    #
                    try: time.sleep(0.01) # Should be short.
                    except: pass
                    # Terminate loop if no object instance.
                    if self is None: 
                        break
                    # The read command waits until next mouse action.
                    mouse_buffer = mice_file.read(3) # TODO: This is blocking the thread. 
                    buttons = ord(mouse_buffer[0])
                    button_left = (buttons & 0x1) > 0
                    button_right = (buttons & 0x2) > 0
                    button_middle = (buttons & 0x4) > 0
                    
                    # Left and right buttons.
                    if button_left and button_right:
                        if not self._left_and_right_start:
                            self._left_and_right_start = time.time()
                            self._left_start = False
                            self._middle_start = False
                            self._right_start = False
                        #
                        continue
                    # Left button.
                    if button_left:
                        if not self._left_start:
                            self._left_and_right_start = False
                            self._left_start = time.time()
                            self._middle_start = False
                            self._right_start = False
                        #
                        continue
                    # Middle button.
                    if button_middle:
                        if not self._middle_start:
                            self._left_and_right_start = False
                            self._left_start = False
                            self._middle_start = time.time()
                            self._right_start = False
                        #
                        continue
                    # Right button.
                    if button_right:
                        if not self._right_start:
                            self._left_and_right_start = False
                            self._left_start = False
                            self._middle_start = False
                            self._right_start = time.time()
                        #
                        continue
                    # No valid button pressed. Reset last command.
                    self._left_and_right_start = False
                    self._left_start = False
                    self._middle_start = False
                    self._right_start = False
                    self._last_command = None
        #
        except Exception as e :
            self._logger.error('Mouse control: Failed to read mouse device: ' + str(e))
            


#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import time
import logging
import wurb_core
import wurb_raspberry_pi

class WurbMain():
    """ """
    def __init__(self):
        """ """
        # Logging.
        wurb_core.WurbLogging().setup()
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._logger.info('')
        self._logger.info('Welcome to CloudedBats-WURB')
        self._logger.info('=========== ^ö^ ===========')
        self._logger.info('')
        self._logger.info('Connected sound cards for input streams:' )
        input_sound_cards = wurb_core.SoundSource().get_device_list()
        if input_sound_cards:
            for input_sound_card in input_sound_cards:
                self._logger.info('- ' + input_sound_card) 
        else:
            self._logger.info('- No connected sound cards found.') 
        #
        time.sleep(0.1)
        #
        self._settings = None
        self._state_machine = None
        self._scheduler = None
        self._gpio_ctrl = None
        self._mouse_ctrl = None
        #
        self.start()
        #
        
        
        self._logger.info('Logger test-info')
        self._logger.error('Logger test-error')
        self._logger.warning('Log test-warning')
        self._logger.debug('Logger test-debug')
        
        
    
    def start(self):
        """ """
        # Config and settings. Singleton util.
        self._settings = wurb_core.WurbSettings()
        self._settings.start()
        # State machine.
        self._state_machine = wurb_core.WurbStateMachine()
        self._state_machine.set_states(self.define_state_machine())
        self._state_machine.set_perform_action_function(self.perform_action)
        self._state_machine.start()
        # Sunset-sunrise. Singleton util.
        wurb_core.WurbSunsetSunrise().set_timezone(self._settings.get_value('timezone', 'UTC'))
        # GPS. Singleton util.
        wurb_core.WurbGpsReader()
        # Control-GPIO. Connected by callback.
        self._gpio_ctrl = wurb_raspberry_pi.ControlByGpio(callback_function=self.perform_event)
        # Control-mouse. Connected by callback.
        self._mouse_ctrl = wurb_raspberry_pi.ControlByMouse(callback_function=self.perform_event)
        # Control-scheduler. Connected by callback.
        self._scheduler = wurb_core.WurbScheduler(callback_function=self.perform_event)
        # Sound stream parts.
        self._sound_source = wurb_core.SoundSource(callback_function=self.perform_event)
        self._sound_process = wurb_core.SoundProcess(callback_function=self.perform_event)
        self._sound_target = wurb_core.SoundTarget(callback_function=self.perform_event)
        self._sound_manager = wurb_core.WurbSoundStreamManager(
                                    self._sound_source, 
                                    self._sound_process, 
                                    self._sound_target,
                                    source_queue_max=100)
    
    def stop(self):
        """ """
        # Stop modules.
        wurb_core.WurbGpsReader().stop_gps()
        if self._gpio_ctrl: self._gpio_ctrl.stop()
        if self._mouse_ctrl: self._mouse_ctrl.stop()
        if self._scheduler: self._scheduler.stop()
        if self._state_machine: self._state_machine.stop()
        if self._settings: self._settings.stop()
        
    def perform_event(self, event):
        """ Used for event callbacks from connected modules. """
        if self._state_machine:
            self._state_machine.event(event)

    def perform_action(self, action):
        """ Actions from state machine. """
        if action:
            if action == '':
                pass
            elif action == 'load_config':
                print('DEBUG: WurbMain action: ' + action)
            elif action == 'load_wifi_config':
                print('DEBUG: WurbMain action: ' + action)
            elif action == 'load_settings':
                print('DEBUG: WurbMain action: ' + action)
            elif action == 'rec_start':
                print('DEBUG: WurbMain action: ' + action)
                self._sound_manager.start_streaming()
            elif action == 'rec_stop':
                print('DEBUG: WurbMain action: ' + action)
                self._sound_manager.stop_streaming() #(stop_immediate=True)
            elif action == 'rpi_shutdown':
                print('DEBUG: WurbMain action: ' + action)
            #    
            else:
                self._logger.debug('DEBUG: WURB Main. Failed to find action: ' + action)

    def define_state_machine(self):
        """ """
        state_machine_data = [
            # Startup.
            {'states': ['init'], 'events': ['setup'], 'new_state': 'idle', 
             'actions': ['load_config', 'load_wifi_config', 'load_settings'] }, 
            # 
            {'states': ['idle'], 'events': ['gpio_rec_on', 'mouse_rec_on', 'test_rec_on'], 'new_state': 'rec_on', 
             'actions': ['rec_start', ''] }, 
            # 
            {'states': ['rec_on'], 'events': ['gpio_rec_off', 'mouse_rec_off', 'test_rec_off'], 'new_state': 'idle', 
             'actions': ['rec_stop', ''] }, 
            # 
            {'states': ['*'], 'events': ['shutdown', 'mouse_shutdown', 'gpio_shutdown'], 'new_state': 'rpi_off', 
             'actions': ['rpi_shutdown', ''] }, 
            # 
            {'states': ['auto_rec_on'], 'events': ['scheduler_rec_off'], 'new_state': 'auto_rec_on', 
             'actions': ['', ''] }, 
            # 
            {'states': ['auto_rec_off'], 'events': ['scheduler_rec_on'], 'new_state': 'auto_rec_on', 
             'actions': ['', ''] }, 
            # 
            {'states': [''], 'events': [''], 'new_state': '', 
             'actions': ['', ''] }, 
            ]
        #
        return state_machine_data


### Main. ###
if __name__ == "__main__":
    """ """
    wurb_main = WurbMain()
    wurb_main.perform_event('setup')

    test = True
    if test:
        time.sleep(1.0)
        wurb_main.perform_event('test_rec_on')
        time.sleep(35.0)
        wurb_main.perform_event('test_rec_off')
        time.sleep(0.1)
        wurb_main.stop()


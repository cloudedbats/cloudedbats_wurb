#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import time
import logging
import wurb_core
import wurb_raspberry_pi

class WurbMain():
    """ Main class for CloudedBats WURB, Wireless Ultrasonic Recorder for Bats.
        Version: "Bat-season 2017, development and test."
    """
    def __init__(self):
        """ """
        # Logging.
        wurb_core.WurbLogging().setup()
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._logger.info('')
        self._logger.info('Welcome to CloudedBats-WURB')
        self._logger.info('Project page: http://cloudedbats.org')
        self._logger.info('=============== ^ö^ ================')
        self._logger.info('')
        
        try:
            # Check input cards and write to log.
            self._logger.info('Connected sound cards for input streams:' )
            input_sound_cards = wurb_core.SoundSource().get_device_list()
            if input_sound_cards:
                for input_sound_card in input_sound_cards:
                    self._logger.info('- ' + input_sound_card) 
            else:
                self._logger.error('- No connected sound cards found at startup.') 
            self._logger.info('')
            # Suspend manin thread for logging.
            time.sleep(0.1)
            # Modules.
            self._settings = None
            self._state_machine = None
            self._scheduler = None
            self._gpio_ctrl = None
            self._mouse_ctrl = None
            # Start all modules.
            self.start()
        except Exception as e:
            self._logger.error('')
            self._logger.error('WURB Main: Exception during startup.')
            self._logger.error('WURB Main: ' + str(e))
            self._logger.error('')
            raise
    
    def start(self):
        """ """
        # Config and settings. Singleton util.
        self._settings = wurb_core.WurbSettings()
        self._settings.start()
        # State machine.
        self._state_machine = wurb_core.WurbStateMachine()
        self._state_machine.load_states(self.define_state_machine())
        self._state_machine.set_perform_action_function(self.perform_action)
        self._state_machine.set_current_state('rec_auto')
        self._state_machine.start()
        # Sunset-sunrise. Singleton util.
        wurb_core.WurbSunsetSunrise().set_timezone(self._settings.get_value('wurb_timezone', 'UTC'))
        # GPS. Singleton util.
        wurb_core.WurbGpsReader().start_gps()
        # Control-GPIO. Connected by callback.
        self._gpio_ctrl = wurb_raspberry_pi.ControlByGpio(callback_function=self.perform_event)
        # Control-mouse. Connected by callback.
        self._mouse_ctrl = wurb_raspberry_pi.ControlByMouse(callback_function=self.perform_event)
        # Control-scheduler. Connected by callback.
        self._scheduler = wurb_core.WurbScheduler(callback_function=self.perform_event)
        # Sound stream parts:
        # - Source
        if not self._settings.get_value('recorder_pettersson_m500', 'False'):
            # Generic USB microphones, including Pettersson M500-384.
            self._sound_source = wurb_core.SoundSource(callback_function=self.perform_event)
        else:
            # Microphone for Windows. Special code to handle Pettersson M500.
            self._sound_source = wurb_core.SoundSourceM500(callback_function=self.perform_event)
        # - Process.
        self._sound_process = wurb_core.SoundProcess(callback_function=self.perform_event)
        # - Target.
        self._sound_target = wurb_core.SoundTarget(callback_function=self.perform_event)
        # - Manager.
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
        self._logger.info('WURB Main: State machine action: ' + action)
        if action:
            if action == '':
                pass
            #
            elif action == 'rec_start':
                self._sound_manager.start_streaming()
            #
            elif action == 'rec_stop':
                self._sound_manager.stop_streaming() #(stop_immediate=True)
            #
            elif action == 'rec_flush_file':
                pass # TODO: Not implemented.
            #
            elif action == 'auto_check_state':
                self._scheduler.check_state()
            #
            elif action == 'led_warning_flash_on':
                print('TEST led_warning_flash_on') # TODO: Not implemented.
            #
            elif action == 'led_warning_flash_off':
                print('TEST led_warning_flash_off') # TODO: Not implemented.
            #
            elif action == 'led_error_flash_on':
                print('TEST led_error_flash_on') # TODO: Not implemented.
            #
            elif action == 'led_error_flash_off':
                print('TEST led_error_flash_off') # TODO: Not implemented.
            #
            elif action == 'sleep_1s':
                time.sleep(1)
            #
            elif action == 'rpi_shutdown':
                os.system('sudo shutdown -h now')
            #    
            else:
                self._logger.debug('WURB Main: Failed to find action: ' + action)

    def define_state_machine(self):
        """ """
        state_machine_data = [
            # 
            {'states': ['rec_auto', 'rec_off'], 'events': ['gpio_rec_on', 'mouse_rec_on', 'test_rec_on'], 
             'new_state': 'rec_on', 
             'actions': ['rec_flush_file', 'rec_start'] }, # , 'led_error_flash_off', 'led_warning_flash_off'] },
            # 
            {'states': ['rec_auto', 'rec_on'], 'events': ['gpio_rec_off', 'mouse_rec_off', 'test_rec_off'], 
             'new_state': 'rec_off',  
             'actions': ['rec_stop'] }, 
            # 
            {'states': ['rec_on', 'rec_off'], 'events': ['gpio_rec_auto', 'mouse_rec_auto', 'test_rec_auto'], 
             'new_state': 'rec_auto',  
             'actions': ['rec_stop', 'sleep_1s', 'auto_check_state'] }, 
            # 
            {'states': ['rec_auto'], 'events': ['scheduler_rec_on'], 
             'new_state': 'rec_auto', 
             'actions': ['rec_start'] }, # , 'led_error_flash_off', 'led_warning_flash_off'] }, 
            # 
            {'states': ['rec_auto'], 'events': ['scheduler_rec_off'], 
             'new_state': 'rec_auto', 
             'actions': ['rec_stop'] }, 
            # Test.
            {'states': ['*'], 'events': ['rec_source_warning', 'rec_target_warning'], 
             'new_state': '*', 
             'actions': [] }, # 'led_warning_flash_on'] }, 
            # Test.
            {'states': ['*'], 'events': ['rec_source_error', 'rec_target_error'], 
             'new_state': '*', 
             'actions': ['rec_stop'] }, # , 'led_error_flash_on'] }, 
            # 
            {'states': ['*'], 'events': ['mouse_rpi_shutdown'], 
             'new_state': 'rpi_off', 
             'actions': ['rec_stop', 'rpi_shutdown', ''] }, 
            ]
        #
        return state_machine_data


### Main. ###
if __name__ == "__main__":
    """ """
    wurb_main = WurbMain()

# # TODO: For development.
#     time.sleep(1.0)
#     wurb_main.perform_event('test_rec_on')
#     time.sleep(20.0) 
#     wurb_main.perform_event('test_rec_off')
#     time.sleep(0.1)
#     wurb_main.stop()


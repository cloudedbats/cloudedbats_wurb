#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import time
import pathlib
import shutil
import logging
import wurb_core
import wurb_raspberry_pi

class WurbApplication():
    """ Main class for CloudedBats WURB, Wireless Ultrasonic Recorder for Bats.
    """
    def __init__(self, usb_memory_used=True):
        """ """
        self._usb_memory_used = usb_memory_used
        # Logging.
        wurb_core.WurbLogging().setup(usb_memory_used = self._usb_memory_used)
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._logger.info('')
        self._logger.info('')
        self._logger.info('Welcome to CloudedBats WURB')
        self._logger.info('Project page: http://cloudedbats.org')
        self._logger.info('=============== ^ö^ ================')
        
        try:
            # Check input cards and write to log.
            self._logger.info('')
            self._logger.info('=== Check sound cards. ===')
            self._logger.info('Connected sound cards for input streams:' )
            input_sound_cards = wurb_core.get_device_list()
            if input_sound_cards:
                for input_sound_card in input_sound_cards:
                    self._logger.info('- ' + input_sound_card) 
            else:
                self._logger.error('- No connected sound cards found at startup.') 
            
            # Suspend main thread for logging.
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
        # State machine.
        self._logger.info('')
        self._logger.info('=== State machine startup. ===')
        self._state_machine = wurb_core.WurbStateMachine()
        self._state_machine.load_states(self.define_state_machine())
        self._state_machine.set_perform_action_function(self.perform_action)
        self._state_machine.set_current_state('wurb_init')
        self._state_machine.start()
        
        # Settings. Singleton util.
        self._logger.info('')
        self._logger.info('=== Setting startup. ===')
        self._settings = wurb_core.WurbSettings()
        desc = [
            '# ',
            '# Default settings for CloudedBats WURB.',
        	'# Check the file "cloudedbats_wurb/README.txt" for more info.',
            '# ',
        ]
        self._settings.set_default_values(desc, [], [])
        # Load default settings for wurb_recorder.
        (desc, default, dev) = wurb_core.wurb_recorder.default_settings()
        self._settings.set_default_values(desc, default, dev)
        # Load default settings for wurb_scheduler.
        desc, default, dev = wurb_core.wurb_scheduler.default_settings()
        self._settings.set_default_values(desc, default, dev)
        # Load default settings for wurb_gps_reader.
        desc, default, dev = wurb_core.wurb_gps_reader.default_settings()
        self._settings.set_default_values(desc, default, dev)
        # Load default settings for wurb_sound_detector.
        desc, default, dev = wurb_core.wurb_sound_detector.default_settings()
        self._settings.set_default_values(desc, default, dev)
        # Internal and external paths to setting files.
        current_dir = pathlib.Path(__file__).parents[1]
        internal_path = pathlib.Path(current_dir, 'wurb_settings')
        external_path = pathlib.Path('/media/usb0/cloudedbats_wurb/settings')
        internal_setting_path = pathlib.Path(internal_path, 'user_settings.txt')
        # Create directories.
        if not internal_path.exists():
            internal_path.mkdir(parents=True)
        if self._usb_memory_used:
            if not external_path.exists():
                external_path.mkdir(parents=True)
        # Copy settings from USB.
        if self._usb_memory_used:
            external_setting_path = pathlib.Path(external_path, 'user_settings.txt')
            if external_setting_path.exists():
                self._logger.info('Settings: Copying user_settings.txt from USB')
                shutil.copy(str(external_setting_path), 
                            str(internal_setting_path))
        # Load setting from file.
        self._logger.info('WURB Main: Loading user settings file.')
        self._settings.load_settings(internal_setting_path)
        # Save default setting and last used settings.
        self._settings.save_default_settings(pathlib.Path(internal_path, 'user_settings_DEFAULT.txt'))
        self._settings.save_last_used_settings(pathlib.Path(internal_path, 'user_settings_LAST_USED.txt'))
        if self._usb_memory_used:
            self._logger.info('Settings: Copying settings files and readme.txt to USB')
            shutil.copy(str(pathlib.Path(current_dir, 'wurb_core/README.txt')), 
                        str(pathlib.Path(external_path.parent, 'README.txt')))
            self._settings.save_default_settings(pathlib.Path(external_path, 'user_settings_DEFAULT.txt'))
            self._settings.save_last_used_settings(pathlib.Path(external_path, 'user_settings_LAST_USED.txt'))
        
        # Sunset-sunrise. Singleton util.
        self._logger.info('')
        self._logger.info('=== Setting and config startup. ===')
        wurb_core.WurbSunsetSunrise().set_timezone(self._settings.text('timezone'))
        
        # GPS. Singleton util.
        self._logger.info('')
        self._logger.info('=== GPS startup. ===')
        wurb_core.WurbGpsReader().start()
        
        # Initiate sound recorder.
        self._logger.info('')
        self._logger.info('=== Sound recorder startup. ===')
        self._recorder = wurb_core.WurbRecorder(callback_function=self.perform_event)
        self._recorder.setup_sound_manager()
        
        # Control-GPIO. Connected by callback.
        self._logger.info('')
        self._logger.info('=== GPIO control startup. ===')
        self._gpio_ctrl = wurb_raspberry_pi.ControlByGpio(callback_function=self.perform_event)
        # Control-mouse. Connected by callback.
        self._logger.info('')
        self._logger.info('=== Computer mouse startup. ===')
        self._mouse_ctrl = wurb_raspberry_pi.ControlByMouse(callback_function=self.perform_event)
        
        # Control-scheduler. Connected by callback.
        self._logger.info('')
        self._logger.info('=== Scheduler startup. ===')
        self._scheduler = wurb_core.WurbScheduler(callback_function=self.perform_event)

        self._logger.info('')
        self._logger.info('=== Startup done. ===')
        self._logger.info('')
    
    def stop(self):
        """ """
        # Stop modules.
        wurb_core.WurbGpsReader().stop()
        if self._recorder: self._recorder.stop_recording(stop_immediate=True)
        if self._gpio_ctrl: self._gpio_ctrl.stop()
        if self._mouse_ctrl: self._mouse_ctrl.stop()
        if self._scheduler: self._scheduler.stop()
        if self._state_machine: self._state_machine.stop()
        
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
                self._recorder.start_recording()
            #
            elif action == 'rec_stop':
                self._recorder.stop_recording() #(stop_immediate=True)
            #
            elif action == 'auto_check_state':
                self._scheduler.check_state()
            #
            elif action == 'restart_scheduler':
                time.sleep(1.0)
                self._scheduler.start()
            #
            elif action == 'sleep_1s':
                time.sleep(1.0)
            elif action == 'sleep_10s':
                time.sleep(10.0)
            #
            elif action == 'rpi_shutdown':
                self.stop()
                os.system('sudo shutdown -h now')
            #
            elif action == 'rpi_reboot':
                self.stop()
                os.system('sudo reboot')
            #    
            else:
                self._logger.debug('WURB Main: Failed to find action: ' + action)

    def define_state_machine(self):
        """ """
        state_machine_data = [
            # 
            {'states': ['wurb_init', 'rec_auto', 'rec_off', 'rec_on'], 
             'events': ['gpio_rec_on', 'mouse_rec_on', 'test_rec_on'], 
             'new_state': 'rec_on', 
             'actions': ['rec_stop', 'rec_start'] }, 
            # 
            {'states': ['wurb_init', 'rec_auto', 'rec_on', 'rec_off'], 
             'events': ['gpio_rec_off', 'mouse_rec_off', 'test_rec_off'], 
             'new_state': 'rec_off',  
             'actions': ['rec_stop'] }, 
            # 
            {'states': ['wurb_init', 'rec_on', 'rec_off', 'rec_auto'], 
             'events': ['gpio_rec_auto', 'mouse_rec_auto', 'test_rec_auto'], 
             'new_state': 'rec_auto',  
             'actions': ['rec_stop', 'sleep_1s', 'auto_check_state'] }, 
            # 
            {'states': ['wurb_init', 'rec_auto'], 
             'events': ['scheduler_rec_on'], 
             'new_state': 'rec_auto', 
             'actions': ['rec_start'] }, 
            # 
            {'states': ['wurb_init', 'rec_auto'], 
             'events': ['scheduler_rec_off'], 
             'new_state': 'rec_auto', 
             'actions': ['rec_stop'] }, 
            # 
            {'states': ['*'], 
             'events': ['scheduler_restart'], 
             'new_state': '*', 
             'actions': ['restart_scheduler'] }, 
            # Test.
            {'states': ['*'], 
             'events': ['rec_source_warning', 'rec_target_warning'], 
             'new_state': '*', 
             'actions': [] }, 
            # Test.
            {'states': ['*'], 
             'events': ['rec_source_error', 'rec_target_error'], 
             'new_state': 'rpi_off', 
             'actions': ['rec_stop', 'rpi_shutdown'] },  #['rec_stop', 'sleep_10s', 'rpi_reboot'] }, 
            # 
            {'states': ['*'], 
             'events': ['mouse_rpi_shutdown'], # ['mouse_rpi_shutdown', 'no_usb_detected_error'], 
             'new_state': 'rpi_off', 
             'actions': ['rec_stop', 'rpi_shutdown'] }, 
            ]
        #
        return state_machine_data


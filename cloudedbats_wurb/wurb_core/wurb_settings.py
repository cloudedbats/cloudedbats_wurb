#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import sys
import pathlib
import shutil
import logging
import wurb_core

@wurb_core.singleton
class WurbSettings(object):
    """ Used for configurations and settings. 
        There are three alternatives for settings:
        1. Use default values. Default values are defined in the modules where they are used. 
        2. Use the internally used file 'wurb_settings/user_settings.txt'.
        3. Add a file to the connected USB memory. Path on USB memory; 
                'cloudedbats_wurb/settings/user_settings.txt' 
        At startup files for config/settings are copied from the USB memory to the internally
        stored 'wurb_settings' folder.
        To get an updated list of possible settings alternatives, search for the string 
        'self._settings.get_value(' in the whole project.
        A 'user_settings_TEMPLATE.txt' file will also be prepared. """
        
    def __init__(self):
        """ """
        pass # Parameters not allowed in singleton.
    
    def start(self, callback_function=None, 
                    usb_required=True,  
                    internal_path='wurb_settings',
                    external_path='/media/usb0/cloudedbats_wurb/settings'):
        """ """
        self._callback_function = callback_function
        self._usb_required = usb_required
        self._logger = logging.getLogger('CloudedBatsWURB')
        # Internal.
        dir_path = pathlib.Path(sys.modules['__main__'].__file__).parents[0] # Same level as wurb_main.py.
        self._internal_dir_path = pathlib.Path(dir_path, internal_path)
#         self._hw_config_path = pathlib.Path(self._internal_dir_path, 'hw_config.txt')
        self._user_settings_path = pathlib.Path(self._internal_dir_path, 'user_settings.txt')
        self._user_settings_template_path = pathlib.Path(self._internal_dir_path, 'user_settings_TEMPLATE.txt')
        # External.
        if self._usb_required:
            self._external_dir_path = pathlib.Path(external_path)
#             self._external_hw_config_path = pathlib.Path(external_path, 'hw_config.txt')
#             self._external_wifi_config_path = pathlib.Path(external_path, 'wifi_config.txt')
            self._external_user_settings_path = pathlib.Path(external_path, 'user_settings.txt')
            self._external_user_settings_template_path = pathlib.Path(external_path, 'user_settings_TEMPLATE.txt')
        #
        self._wurb_config = {}
        self._wurb_scheduler_events = [] # Multiple rows are allowed for scheduler events.
        
        # Copy template settings file to USB memory. Shutdown if USB not available. 
        if self._usb_required:
            try: 
                self._copy_template_settings_to_external()
            except:
                # Not possible to write to USB memory.
                if self._callback_function:
                    self._callback_function('no_usb_shutdown')
            # Copy user defined settings from USB to internal location.
            self._copy_settings_from_external()
            
        # Load settings.
#         self._load_hw_config()
#         self._load_wifi_config()
        self._load_user_settings()
        
    def stop(self):
        """ """
        pass # Dummy.
        
    def get_value(self, key, default = ''):
        """ """
        value = self._wurb_config.get(key, default)
        # Check if int.
        try:
            return int(value)
        except:
            pass
        # Check if float.
        try:
            return float(value)
        except:
            pass
        # Check for boolean.
        if value.lower() in ['true']:
            return True
        elif value.lower() in ['false']:
            return False
        # Must be string.
        return value
    
    def get_scheduler_events(self):
        """ """
        return self._wurb_scheduler_events
    
#     def _load_hw_config(self):
#         """ """
#         self._logger.info('Settings: Loading configuration file: ' + str(self._hw_config_path))
#         self._load_settings(self._hw_config_path)
        
#     def _load_wifi_config(self):
#         """ """
#         self._logger.info('Settings: Loading configuration file: ' + str(self._wifi_config_path))
#         self._load_settings(self._wifi_config_path)
        
    def _load_user_settings(self):
        """ """
        self._logger.info('Settings: Loading configuration file: ' + str(self._user_settings_path))
        self._load_settings(self._user_settings_path)
        
    def _copy_template_settings_to_external(self):
        """ """
        # Create directory for settings.
        if not self._external_dir_path.exists():
            self._external_dir_path.mkdir(parents=True)
        # Copy template to USB memory.
        if self._user_settings_template_path.exists():
            shutil.copy(str(self._user_settings_template_path), str(self._external_user_settings_template_path))
            self._logger.info('Template for user settings moved to USB memory.')
        
    def _copy_settings_from_external(self):
        """ """
        # Create directory for settings.
        if not self._internal_dir_path.exists():
            self._internal_dir_path.mkdir(parents=True)
        # Copy new versions of config and settings from usb memory.
        if pathlib.Path(self._external_dir_path).exists():
            # wurb_hw_config.txt
#             if self._external_hw_config_path.exists():
#                 shutil.copy(str(self._external_hw_config_path), str(self._hw_config_path))
#                 self._logger.info('Settings: "hw_config.txt" moved from USB memory.')
#             # wurb_wifi_config.txt
#             if self._external_wifi_config_path.exists():
#                 shutil.copy(str(self._external_wifi_config_path), str(self._wifi_config_path))
#                 self._logger.info('Settings: "wifi_config.txt" moved from USB memory.')
            # wurb_settings.txt
            if self._external_user_settings_path.exists():
                shutil.copy(str(self._external_user_settings_path), str(self._user_settings_path))
                self._logger.info('Settings: "user_settings.txt" moved from USB memory.')
        
    def _load_settings(self, file_path):
        """ """
        if not file_path.exists():
            self._logger.warning('Settings: Config/settings file does not exists. Default values are used.')
            return
        #
        with file_path.open('r') as infile:
            for row in infile:
                key_value = row.strip()
                key = ''
                value = ''
                # Remove comments.
                if '#' in key_value:
                    key_value = key_value.split('#')[0].strip() # Use left part.
                # Split key/value.
                if key_value:
                    if ':' in key_value:
                        key_value_list = key_value.split(':', 1) # Split on first occurrence.
                        key = key_value_list[0].strip()
                        value = key_value_list[1].strip()
                        if key and value:
                            if key == 'scheduler_event':
                                # Many rows with the same key are allowed.
                                self._wurb_scheduler_events.append(value)
                            else:
                                # Add to dict. Only one is allowed.
                                self._wurb_config[key] = value


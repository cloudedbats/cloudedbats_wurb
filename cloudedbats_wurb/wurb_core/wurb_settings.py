#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import pathlib
import shutil
import logging
import wurb_core

@wurb_core.singleton
class WurbSettings(object):
    """ Used for config and settings. 
        There are three alternatives for settings:
        1. Use default values. Default values are defined in the modules where they are used. 
        2. Use the internally used file 'wurb_settings/user_settings.txt'.
        3. Add a file to the connected USB memory. Path on USB memory; 
                'cloudedbats_wurb/settings/user_settings.txt' 
        At startup files for config/settings are copied from the USB memory to the internally
        stored 'wurb_settings' folder at starup, if available. Otherwise, defaults are used.
        A 'user_settings_DEFAULTS.txt' file will also automatically be prepared at startup. 
    """
        
    def __init__(self):
        """ Note: Singleton, parameters not allowed. """
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._wurb_settings = {}
        self._default_settings_text = []
        self._default_settings = {}
        self._valid_settings = {}    
        self._wurb_scheduler_events = []

    def text(self, key):
        """ """
        value = ''
        if key in self._wurb_settings:
            value = self._wurb_settings.get(key)
        elif key in self._default_settings:
            value = self._default_settings.get(key)
        # Return string.
        return value

    def boolean(self, key):
        """ """
        value = 'F'
        if key in self._wurb_settings:
            value = self._wurb_settings.get(key)
        elif key in self._default_settings:
            value = self._default_settings.get(key)
        #
        if value.lower() in ['yes', 'no', 'y', 'n', 'true', 'false', 't', 'f']:
            return True
        # Return Boolean.
        return False

    def integer(self, key):
        """ """
        value = '0'
        if key in self._wurb_settings:
            value = self._wurb_settings.get(key)
        elif key in self._default_settings:
            value = self._default_settings.get(key)
        # Return integer.
        try:
            return int(value)
        except:
            return 0

    def float(self, key):
        """ """
        value = '0.0'
        if key in self._wurb_settings:
            value = self._wurb_settings.get(key)
        elif key in self._default_settings:
            value = self._default_settings.get(key)
        # Return float.
        try:
            return float(value)
        except:
            return 0

    def scheduler_events(self):
        """ """
        return self._wurb_scheduler_events
    
    def set_default_values(self, description=None, default_settings=None, developer_settings=None):
        """ """
        # Description.
        if description:
            self._default_settings_text.append('')
            for row in description:
                self._default_settings_text.append(row)

        # Public settings.
        if default_settings:
            self._default_settings_text.append('')
            for row in default_settings:
                self._wurb_settings[row['key']] = row['value']
                self._default_settings_text.append(row['key'] + ': ' + str(row['value']))
                self._default_settings[row['key']] = row['value']
                if 'valid' in row:
                    self._valid_settings[row['key']] = row['valid']

        # Hidden settings.
        if developer_settings:
            for row in developer_settings:
                self._wurb_settings[row['key']] = row['value']
                self._default_settings[row['key']] = row['value']
                if 'valid' in row:
                    self._valid_settings[row['key']] = row['valid']
                
        print('DEBUG')
        
#     def _load_user_settings(self):
#         """ """
#         self._logger.info('Settings: Loading user settings file: ' + str(self._user_settings_path))
#         self._load_settings(self._user_settings_path)
#         
#     def _copy_template_settings_to_external(self):
#         """ """
#         # Create directory for settings.
#         if not self._external_dir_path.exists():
#             self._external_dir_path.mkdir(parents=True)
#         # Copy template to USB memory.
#         if self._user_settings_template_path.exists():
#             shutil.copy(str(self._user_settings_template_path), str(self._external_user_settings_template_path))
#             self._logger.info('Template for user settings moved to USB memory.')
#         
#     def _copy_settings_from_external(self):
#         """ """
#         # Create directory for settings.
#         if not self._internal_dir_path.exists():
#             self._internal_dir_path.mkdir(parents=True)
#         # Copy new versions of config and settings from usb memory.
#         if pathlib.Path(self._external_dir_path).exists():
#             # wurb_hw_config.txt
# #             if self._external_hw_config_path.exists():
# #                 shutil.copy(str(self._external_hw_config_path), str(self._hw_config_path))
# #                 self._logger.info('Settings: "hw_config.txt" moved from USB memory.')
# #             # wurb_wifi_config.txt
# #             if self._external_wifi_config_path.exists():
# #                 shutil.copy(str(self._external_wifi_config_path), str(self._wifi_config_path))
# #                 self._logger.info('Settings: "wifi_config.txt" moved from USB memory.')
#             # wurb_settings.txt
#             if self._external_user_settings_path.exists():
#                 shutil.copy(str(self._external_user_settings_path), str(self._user_settings_path))
#                 self._logger.info('Settings: "user_settings.txt" moved from USB memory.')
        
    def load_settings(self, file_path):
        """ """
        if not file_path.exists():
            self._logger.warning('Settings: Config/settings file does not exists. Default values are used.')
            return
        #
        self._logger.info('Settings: Used settings from file: ')
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
                                self._logger.info('- Scheduler event: ' + str(value))
                            else:
                                # Add to dict. Only one is allowed.
                                self._wurb_settings[key] = value
                                self._logger.info('- Setting key: ' + str(key) + ' value: ' + str(value))


    def save_default_settings(self, file_path):
        """ """
        with file_path.open('w') as file:
            file.write('\r\n'.join(self._default_settings_text))

    def save_last_used_settings(self, file_path):
        """ """
        used_settings = []
        for key, value in self._wurb_settings.items():
            used_settings.append(key + ': ' + str(value))   
        #
        with file_path.open('w') as file:
            file.write('\r\n'.join(used_settings))



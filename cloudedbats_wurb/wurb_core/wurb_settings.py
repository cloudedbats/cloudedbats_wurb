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
        self._developer_settings = {}
        self._valid_settings = {}    
        self._wurb_scheduler_events = []

    def text(self, key):
        """ """
        value = ''
        if key in self._wurb_settings:
            value = self._wurb_settings.get(key)
        # Return string.
        return value

    def boolean(self, key):
        """ """
        value = 'F'
        if key in self._wurb_settings:
            value = self._wurb_settings.get(key)
        # Return Boolean.        
        if value.lower() in ['yes', 'y', 'true', 't']:
            return True
        else:
            return False

    def integer(self, key):
        """ """
        value = '0'
        if key in self._wurb_settings:
            value = self._wurb_settings.get(key)
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
                if row['key'] == 'scheduler_event':
                    self._default_settings_text.append(row['key'] + ': ' + str(row['value']))
                    self._wurb_scheduler_events.append(row['value'])
                else:
                    self._default_settings_text.append(row['key'] + ': ' + str(row['value']))
                    self._wurb_settings[row['key']] = row['value']
                    self._default_settings[row['key']] = row['value']
                    if 'valid' in row:
                        self._valid_settings[row['key']] = row['valid']

        # Hidden settings.
        if developer_settings:
            for row in developer_settings:
                self._wurb_settings[row['key']] = row['value']
                self._developer_settings[row['key']] = row['value']
                if 'valid' in row:
                    self._valid_settings[row['key']] = row['valid']
    
    def load_settings(self, file_path):
        """ """
        if not file_path.exists():
            self._logger.warning('Settings: Config/settings file does not exists. Default values are used.')
            return
        #
        self._logger.info('Settings: Used settings from file: ')
        clear_default_scheduler_events = True
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
                                # Clear defaults if scheduler events are defined. First time only.
                                if clear_default_scheduler_events:
                                    self._wurb_scheduler_events = []
                                    clear_default_scheduler_events = False
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
        used_settings = [
            '',
            '# Settings used during the last ',
            '# execution of CloudedBats WURB.',
            '',
            '# Standard settings:',
            ' ',
            ]
        #
        for key in sorted(self._wurb_settings.keys()):
            if key in self._default_settings:
                used_settings.append(key + ': ' + str(self._wurb_settings[key]))
        #
        used_settings.append(' ')
        used_settings.append('# Scheduler events:')
        used_settings.append(' ')
        #
        for row in self._wurb_scheduler_events:
            used_settings.append('scheduler_event: ' + row)
        #
        used_settings.append(' ')
        used_settings.append('# Development settings:')
        used_settings.append(' ')
        #
        for key in sorted(self._wurb_settings.keys()):
            if key in self._developer_settings:
                used_settings.append(key + ': ' + str(self._wurb_settings[key]))
        #
        used_settings.append(' ')
        used_settings.append('# Unrecognised settings:')
        used_settings.append(' ')
        #
        for key in sorted(self._wurb_settings.keys()):
            if (key not in self._default_settings) and \
               (key not in self._developer_settings) :
                used_settings.append(key + ': ' + str(self._wurb_settings[key]))
        #
        with file_path.open('w') as file:
            file.write('\r\n'.join(used_settings))



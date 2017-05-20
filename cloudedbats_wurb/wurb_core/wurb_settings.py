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
    """ """
    def __init__(self,
                 internal_path = 'wurb_settings',
                 external_path = '/media/usb/cloudedbats_wurb/settings'):
        """ """
        self._logger = logging.getLogger('CloudedBatsWURB')
        # Internal.
        dir_path = pathlib.Path(sys.modules['__main__'].__file__).parents[0] # Same level as wurb_main.py.
        self._internal_dir_path = pathlib.Path(dir_path, internal_path)
        self._hw_config_path = pathlib.Path(self._internal_dir_path, 'wurb_hw_config.txt')
        self._wifi_config_path = pathlib.Path(self._internal_dir_path, 'wurb_wifi_config.txt')
        self._user_settings_path = pathlib.Path(self._internal_dir_path, 'wurb_user_settings.txt')
        # External.
        self._external_dir_path = pathlib.Path(external_path)
        self._external_hw_config_path = pathlib.Path(external_path, 'wurb_hw_config.txt')
        self._external_wifi_config_path = pathlib.Path(external_path, 'wurb_wifi_config.txt')
        self._external_user_settings_path = pathlib.Path(external_path, 'wurb_user_settings.txt')
        #
        self._wurb_config = {}
        
    def start(self):
        """ """
        self._move_settings()
        self._load_hw_config()
        self._load_wifi_config()
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
    
    def _load_hw_config(self):
        """ """
        self._logger.info('Settings: Loading configuration file: ' + str(self._hw_config_path))
        self._load_settings(self._hw_config_path)
        
    def _load_wifi_config(self):
        """ """
        self._logger.info('Settings: Loading configuration file: ' + str(self._wifi_config_path))
        self._load_settings(self._wifi_config_path)
        
    def _load_user_settings(self):
        """ """
        self._logger.info('Settings: Loading configuration file: ' + str(self._user_settings_path))
        self._load_settings(self._user_settings_path)
        
    def _move_settings(self):
        """ """
        # Create directory for settings.
        if not self._internal_dir_path.exists():
            self._internal_dir_path.mkdir(parents=True)
        # Copy new versions of config and settings from usb memory.
        if pathlib.Path(self._external_dir_path).exists():
            # wurb_hw_config.txt
            if self._external_hw_config_file_path.exists():
                shutil.copy(str(self._external_hw_config_path), str(self._hw_config_path))
            # wurb_wifi_config.txt
            if self._external_wifi_config_file_path.exists():
                shutil.copy(str(self._external_wifi_config_path), str(self._wifi_config_path))
            # wurb_settings.txt
            if self._external_settings_file_path.exists():
                shutil.copy(str(self._external_settings_path), str(self._settings_path))
        
    def _load_settings(self, file_path):
        """ """
        if not file_path.exists():
            self._logger.warning('Settings: File does not exists (default values are used): ' + str(file_path))
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
                            self._wurb_config[key] = value


#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import time
import datetime
import logging
import threading
import wurb_core

class WurbScheduler(object):
    """ 
    
    """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        self._local_time = datetime.datetime.now()
        self._latitude = None
        self._longitude = None
        self._use_gps = False
        self._wait_for_gps_at_startup = False
        #
        self._scheduler_event_list = []
        self._read_settings()
        #
        self._rec_on = False
        self._thread_active = False
        self.start()
        
    def is_rec_on(self):
        """ """
        return self._rec_on

    def check_state(self):
        """ Used from the state machine to trigger callback. """
        if self._callback_function:
            if self._rec_on:
                self._callback_function('scheduler_rec_on')
            else:
                self._callback_function('scheduler_rec_off')

    def start(self):
        """ """
        # Check if already started.
        if self._thread_active:
            return
        # Don't start if events are missing.
        if len(self._scheduler_event_list) == 0:
            return
        #
        self._read_gps_time_and_pos()
        self._calculate_event_times()
        #
        try:
            self._thread_active = True
            self._scheduler_thread = threading.Thread(target = self._scheduler_exec, args = [])
            self._scheduler_thread.start()
        except Exception as e:
            self._logger.error('Scheduler: Failed to start the scheduler. ' + str(e))
        
    def stop(self):
        """ """
        self._thread_active = False
    
    def _read_settings(self):
        """ """
        # GPS usage.
        self._use_gps = self._settings.get_value('scheduler_use_gps', 'False')
        self._wait_for_gps_at_startup = self._settings.get_value('scheduler_wait_for_gps_at_startup', 'False')
        # Default for latitude/longitude in the decimal degree format.
        self._latitude = float(self._settings.get_value('default_latitude', '0.0'))
        self._longitude = float(self._settings.get_value('default_longitude', '0.0'))
        
        # Read scheduling events from the settings file.
        self._scheduler_event_list = []
        for event in self._settings.get_scheduler_events():
            event_parts = event.split('/')
            if len(event_parts) >= 2:
                event_dict = {}
                event_dict['event_action'] = event_parts[0].strip()
                event_dict['event_time_str'] = event_parts[1].strip()
                if len(event_parts) >= 3:
                    event_dict['event_adjust_str'] = event_parts[2].strip()
                #
                self._scheduler_event_list.append(event_dict)


    def _read_gps_time_and_pos(self):
        """ """
        if self._use_gps:
            # Get time and position from GPS. 
            gps_local_time = wurb_core.WurbGpsReader().get_time_local()
            gps_latitude = wurb_core.WurbGpsReader().get_latitude()
            gps_longitude = wurb_core.WurbGpsReader().get_longitude()
            #
            if self._wait_for_gps_at_startup:
                self._logger.info('Scheduler: Waiting for GPS time and position.')
                while not (gps_local_time and gps_latitude and gps_longitude):
                    #
                    if not self._thread_active:
                        self._logger.info('Scheduler: Waiting for GPS was terminated.')
                        break
                    #
                    time.sleep(5.0)
                    gps_local_time = wurb_core.WurbGpsReader().get_time_local()
                    gps_latitude = wurb_core.WurbGpsReader().get_latitude()
                    gps_longitude = wurb_core.WurbGpsReader().get_longitude()
                #
                self._logger.info('Scheduler: Received GPS time and position.')            
            #
            if gps_local_time:
                self._local_time = gps_local_time
            if gps_latitude:
                self._latitude = gps_latitude
            if gps_longitude:
                self._longitude = gps_longitude

    def _calculate_event_times(self):
        """ """
        # Get Sunset, sunrise, etc.
        sunrise_dict = wurb_core.WurbSunsetSunrise().get_solartime_dict(
                                                        self._latitude, 
                                                        self._longitude, 
                                                        self._local_time.date())
        # 
        self._logger.info('Scheduler: Date: ' + str(self._local_time.date()) + 
                          ' latitude: ' + str(self._latitude) +
                          ' longitude: ' + str(self._longitude))
        self._logger.info('Scheduler: Sunset: ' + sunrise_dict.get('sunset', '-') + 
                          ' dusk: ' + sunrise_dict.get('dusk', '-') + 
                          ' dawn: ' + sunrise_dict.get('dawn', '-') + 
                          ' sunrise: ' + sunrise_dict.get('sunrise', '-'))

        # Calculate time for each event.
        for event_dict in self._scheduler_event_list:            
            try:
                time_event_str = event_dict.get('event_time_str', None)
                time_adjust_int = int(event_dict.get('event_adjust_str', '0'))
                # Convert event strings.
                if time_event_str == 'sunset':
                    time_event_str = sunrise_dict.get('sunset', '18:00')
                elif time_event_str == 'dusk':
                    time_event_str = sunrise_dict.get('dusk', '18:20')
                elif time_event_str == 'dawn':
                    time_event_str = sunrise_dict.get('dawn', '05:40')
                elif time_event_str == 'sunrise':
                    time_event_str = sunrise_dict.get('sunrise', '06:00')
                # Calculate start and stop time.
                event_time = datetime.datetime.strptime(time_event_str, '%H:%M')
                event_time += datetime.timedelta(minutes = time_adjust_int)
                event_time = event_time.time()
                #
                event_dict['event_time'] = event_time
            #
            except Exception as e:
                self._logger.error('Scheduler: Failed to calculate event times. Exception: ' + str(e))
        
        # Sort list.
        self._scheduler_event_list = sorted(self._scheduler_event_list, key=lambda k: k['event_time']) 
        
        for event_dict in self._scheduler_event_list:                 
            self._logger.info(  '- Event: ' + event_dict.get('event_time_str', '') + 
                                ' Adjust: ' + str(event_dict.get('event_adjust_str', '')) + 
                                ' Calc.time: ' + str(event_dict.get('event_time', '')) + 
                                ' Action: ' + event_dict.get('event_action', '-'))
    
    
    def _scheduler_exec(self):
        """ """
        # Loop over all rows to check last rec state and last time in list.
        rec_on_old = None
        max_event_time = None
        for event_dict in self._scheduler_event_list:
            max_event_time = event_dict.get('event_time', '-')
            action = event_dict.get('event_action', '-')
            if action == 'scheduler_rec_on':
                self._rec_on = True
            elif  action == 'scheduler_rec_off':
                self._rec_on = False
                 
        # Loop over all rows once again to find current index.
        last_used_index = None
        time_now = datetime.datetime.now().time()
        for index, event_dict in enumerate(self._scheduler_event_list):
            event_time = event_dict.get('event_time', '')
            # Save last used index.
            if (event_time < time_now):
                last_used_index = index
                # Update rec state.
                action = event_dict.get('event_action', '-')
                if action == 'scheduler_rec_on':
                    self._rec_on = True
                elif  action == 'scheduler_rec_off':
                    self._rec_on = False
        
        # Start main loop.        
        while self._thread_active:
            time_now = datetime.datetime.now().time()
            #
            if (last_used_index == 0) and (time_now >= max_event_time):
                # Wait until new day. 
                pass
            else:
                # Loop from last index.
                if last_used_index is None:
                    remaining_list = self._scheduler_event_list
                else:
                    remaining_list = self._scheduler_event_list[(last_used_index):]
                for index, event_dict in enumerate(remaining_list):
                    event_time = event_dict.get('event_time', '')
                    if (time_now > event_time) and (last_used_index != index):
                        # Check if end of list.
                        if index >= (len(self._scheduler_event_list) - 1):
                            last_used_index = None
                        else:
                            last_used_index = index
                        # Update rec state.
                        action = event_dict.get('event_action', '-')
                        if action == 'scheduler_rec_on':
                            self._rec_on = True
                        elif  action == 'scheduler_rec_off':
                            self._rec_on = False
                        else:
                            # For valid actions defined in the state machine. Check wurb_application.py.
                            self._callback_function(action)
    
                # Send event when state changed.
                if rec_on_old != self._rec_on:
                    if self._callback_function:
                        if self._rec_on:
                            self._callback_function('scheduler_rec_on')
                        else:
                            self._callback_function('scheduler_rec_off')
                    #
                    rec_on_old = self._rec_on

            # Recalculate event times.
            ### TODO: At midnight...
                
            # Sleep, but exit earlier if externally termined.
            for i in range(10):
                if not self._thread_active:
                    return # Terminate thread.
                time.sleep(1.0)

    def _check_if_rec_is_on(self):
        """ """
        
        pass
    
#         try:
#             # Prefere GPS time.
#             gps_time = wurb_core.WurbGpsReader().get_time_local()
#             if gps_time:
#                 time_now = gps_time.time()
#             else:
#                 time_now = datetime.datetime.now().time()
#             # Start and stop the same day.
#             if self._start_time < self._stop_time:
#                 if (time_now >= self._start_time) and (time_now <= self._stop_time):
#                     self._rec_on = True
#                 else: 
#                     self._rec_on = False
#             else: # Stop the day after.
#                 if (time_now >= self._stop_time) and (time_now <= self._start_time):
#                     self._rec_on = False
#                 else: 
#                     self._rec_on = True   
#         #
#         except Exception as e:
#             self._logger.error('Scheduler: Exception: ' + str(e))

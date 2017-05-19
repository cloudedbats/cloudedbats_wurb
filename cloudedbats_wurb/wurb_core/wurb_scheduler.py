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
    """ """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        self._local_time = None
        self._latitude = None
        self._longitude = None
        #
        self._rec_on = False
        self._thread_active = False
        self.start()
        
    def is_rec_on(self):
        """ """
        return self._rec_on

    def check_state(self):
        """ """
        if self._callback_function:
            if self._rec_on:
                self._callback_function('scheduler_rec_on')
            else:
                self._callback_function('scheduler_rec_off')

    def start(self):
        """ """
        if self._thread_active:
            return
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
        
    def _scheduler_exec(self):
        """ """
        # Defaults.
        self._local_time = datetime.datetime.now()
        self._latitude = float(self._settings.get_value('scheduler_default_latitude', '0.0'))
        self._longitude = float(self._settings.get_value('scheduler_default_longitude', '0.0'))
        # GPS.
        gps_only = self._settings.get_value('scheduler_use_gps_only', 'False')
        self._gps_time_and_pos(gps_only)
        #
        start, stop = self._calculate_start_and_stop_time()
        self._start_time = start
        self._stop_time = stop
        #
        rec_on_old = self._rec_on
        while self._thread_active:
            self._check_if_rec_is_on()
            # Send event when changed state
            if rec_on_old != self._rec_on:
                if self._callback_function:
                    if self._rec_on:
                        self._callback_function('scheduler_rec_on')
                    else:
                        self._callback_function('scheduler_rec_off')
                #
                rec_on_old = self._rec_on
            #
            time.sleep(1.0)

    def _gps_time_and_pos(self, gps_only=False):
        """ """
        # Get time and position from GPS. 
        gps_local_time = wurb_core.WurbGpsReader().get_time_local()
        gps_latitude = wurb_core.WurbGpsReader().get_latitude()
        gps_longitude = wurb_core.WurbGpsReader().get_longitude()
        #
        if gps_only:
            while not (gps_local_time and gps_latitude and gps_longitude):
                self._logger.info('Scheduler: Waiting for GPS time and position.')
                #
                if not self._thread_active:
                    break
                #
                time.sleep(5.0)
                gps_local_time = wurb_core.WurbGpsReader().get_time_local()
                gps_latitude = wurb_core.WurbGpsReader().get_latitude()
                gps_longitude = wurb_core.WurbGpsReader().get_longitude()
        #
        if gps_local_time:
            self._local_time = gps_local_time
        if gps_latitude:
            self._latitude = gps_latitude
        if gps_longitude:
            self._longitude = gps_longitude
        #
    
    def _calculate_start_and_stop_time(self):
        """ """
        try:
            # Read from config file.
            start_event_str = self._settings.get_value('scheduler_start_event', 'sunset')
            start_adjust_int = self._settings.get_value('scheduler_start_adjust', 0)
            stop_event_str = self._settings.get_value('scheduler_stop_event', 'sunrise')
            stop_adjust_int = self._settings.get_value('scheduler_stop_adjust', 0)
            # Get Sunset, sunrise, etc.
            sunrise_dict = wurb_core.WurbSunsetSunrise().get_solartime_dict(
                                                                    self._latitude, 
                                                                    self._longitude, 
                                                                    self._local_time.date())
            # 
            self._logger.info('Scheduler: Sunset: ' + sunrise_dict.get('sunset', '-') + 
                              ' dusk: ' + sunrise_dict.get('dusk', '-') + 
                              ' dawn: ' + sunrise_dict.get('dawn', '-') + 
                              ' sunrise: ' + sunrise_dict.get('sunrise', '-'))
            # Convert event strings.
            start_time_str = start_event_str # If event is time.
            stop_time_str = stop_event_str # If event is time.
            #
            if start_event_str == 'sunset':
                start_time_str = sunrise_dict.get('sunset', '18:00')
            elif start_event_str == 'dusk':
                start_time_str = sunrise_dict.get('dusk', '18:20')
            elif start_event_str == 'dawn':
                start_time_str = sunrise_dict.get('dawn', '05:40')
            elif start_event_str == 'sunrise':
                start_time_str = sunrise_dict.get('sunrise', '06:00')
            # Convert event strings.
            if stop_event_str == 'sunset':
                stop_time_str = sunrise_dict.get('sunset', '18:00')
            elif stop_event_str == 'dusk':
                stop_time_str = sunrise_dict.get('dusk', '18:20')
            elif stop_event_str == 'dawn':
                stop_time_str = sunrise_dict.get('dawn', '05:40')
            elif stop_event_str == 'sunrise':
                stop_time_str = sunrise_dict.get('sunrise', '06:00')
            # Calculate start and stop time.
            start = datetime.datetime.strptime(start_time_str, '%H:%M')
            start += datetime.timedelta(minutes = start_adjust_int)
            start = start.time()
            stop = datetime.datetime.strptime(stop_time_str, '%H:%M')
            stop += datetime.timedelta(minutes = stop_adjust_int)
            stop = stop.time()
            #
            self._logger.info('Scheduler: Date: ' + str(self._local_time.date()) + 
                              ' latitude: ' + str(self._latitude) +
                              ' longitude: ' + str(self._longitude))
            self._logger.info('Scheduler: Start event: ' + start_event_str + 
                              ' adjust: ' + str(start_adjust_int))
            self._logger.info('Scheduler: Stop event: ' + stop_event_str + 
                              ' adjust: ' + str(stop_adjust_int))
            self._logger.info('Scheduler: Calculated start time: ' + str(start) + 
                              ' stop time: ' + str(stop))
            #
            return start, stop
        #
        except Exception as e:
            self._logger.error('Scheduler: Failed to calculate start and stop time. ' + str(e))
            return None, None

    def _check_if_rec_is_on(self):
        """ """
        try:
            # Prefere GPS time.
            gps_time = wurb_core.WurbGpsReader().get_time_local()
            if gps_time:
                time_now = gps_time.time()
            else:
                time_now = datetime.datetime.now().time()
            # Start and stop the same day.
            if self._start_time < self._stop_time:
                if (time_now >= self._start_time) and (time_now <= self._stop_time):
                    self._rec_on = True
                else: 
                    self._rec_on = False
            else: # Stop the day after.
                if (time_now >= self._stop_time) and (time_now <= self._start_time):
                    self._rec_on = False
                else: 
                    self._rec_on = True   
        #
        except Exception as e:
            self._logger.error('Scheduler: Exception: ' + str(e))
            

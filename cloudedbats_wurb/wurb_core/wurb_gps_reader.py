#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

from gps3 import gps3
import os
import pytz
import time
import dateutil.parser
import threading
import logging
import wurb_core

@wurb_core.singleton
class WurbGpsReader(object):
    """ Singleton class for GPS time and position. 
        Usage:
            WurbGpsReader().start_gps() # Activates GPS.
            time = WurbGpsReader().get_time_utc() 
            latitude = WurbGpsReader().get_latitude() 
            longitude = WurbGpsReader().get_longitude() 
            latlong = WurbGpsReader().get_latlong_string() 
            WurbGpsReader().gps_stop() # DEactivates GPS.
    """
    def __init__(self):
        """ """
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        # Use clear to initiate class members.
        self._clear()
        # Default port for GPSD.
        self._gpsd_port = self._settings.get_value('gps_reader_gpsd_port', '2947')
        # Default timezone.
        self._timezone = pytz.timezone(self._settings.get_value('wurb_timezone', 'UTC'))
        # Use GPS time for Raspberry Pi.
        self._set_rpi_time_from_gps = self._settings.get_value('gps_reader_set_rpi_time_from_gps', 'False')
        # 
        self._debug = False
    
    def start_gps(self):
        """ Start reading GPS stream. """
        self._gps_start()
    
    def stop_gps(self):
        """ Stop GPS stream. """
        self._active = False
    
    def get_time_utc(self):
        """ """
        if self.gps_time:
            return dateutil.parser.parse(self.gps_time)
        else:
            return None
    
    def get_time_utc_string(self):
        """ """
        if self.gps_time:
            return self.gps_time
        else:
            return None
    
    def set_timezone(self, timezone = 'UTC'):
        """ """
        self._timezone = pytz.timezone(timezone)
    
    def get_time_local(self, timezone = None):
        """ """
        if not timezone:
            timezone = self._timezone
        #
        if self.gps_time:
            return dateutil.parser.parse(self.gps_time).astimezone(timezone)
        else:
            return None
    
    def get_time_local_string(self, timezone = None):
        """ """
        if not timezone:
            timezone = self._timezone
        #
        if self.gps_time:
            datetime_utc = dateutil.parser.parse(self.gps_time)
            datetimestring = str(datetime_utc.astimezone(timezone).strftime("%Y%m%dT%H%M%S%z"))
            return datetimestring
        else:
            return None
    
    def get_latitude(self):
        """ """
        return self.gps_latitude
    
    def get_longitude(self):
        """ """
        return self.gps_longitude
    
    def get_latlong_string(self):
        """ """
        if (not self.gps_latitude) or (not self.gps_longitude):
            return None
        #
        if (self.gps_latitude != 'n/a') and (self.gps_longitude != 'n/a'):
            if self.gps_latitude >= 0: lat_prefix = 'N'
            else: lat_prefix = 'S'
            if self.gps_longitude >= 0: long_prefix = 'E'
            else: long_prefix = 'W'
            #    
            latlong_string = lat_prefix + format(abs(self.gps_latitude), '.4f') + \
                             long_prefix + format(abs(self.gps_longitude), '.4f')
            #
            return latlong_string
        else:
            return None
    
    def _clear(self):
        """ """
        self._active = False
        #
        self.gps_time = None
        self.gps_latitude = None
        self.gps_longitude = None
    
    def _gps_start(self):
        """ """
        try:
            # Start loop in thread.
            self._active = True
            self._gps_thread = threading.Thread(target = self._gps_thread, args = [])
            self._gps_thread.start()
            self._logger.info('GPS reader: Activated.')
        except Exception as e:
            self._logger.error('GPS reader: Failed to connect to GPSD. ' + str(e))
    
    def _gps_thread(self):
        """ """
        first_gps_time_received = False
        first_gps_pos_received = False
        #
        try:
            gps_socket = gps3.GPSDSocket()
            data_stream = gps3.DataStream()
            gps_socket.connect()
            gps_socket.watch(True)
            #
            while self._active:
                
                new_data = gps_socket.next(timeout=5) # Timeout for thread termination. 
                if new_data:
                    data_stream.unpack(new_data)
                    #
                    gps_time = data_stream.TPV['time']
                    gps_latitude = data_stream.TPV['lat']
                    gps_longitude = data_stream.TPV['lon']
                    #
                    if gps_time and (gps_time != 'n/a'):
                        self.gps_time = data_stream.TPV['time']
                        #
                        if not first_gps_time_received:
                            first_gps_time_received = True
                            self._logger.info('GPS reader: First GPS time received: ' + self.get_time_local_string())
                            # Set Raspberry Pi time.
                            if self._set_rpi_time_from_gps:
                                self._logger.info('GPS reader: Raspberry Pi date/time is set.')
                                os.system('sudo date --set "' + self.gps_time + '"')
                    else:
                        # Don't use the old fetched time.
                        self.gps_time = None
                        
                    if gps_latitude and (gps_latitude != 'n/a'):
                        if gps_longitude and (gps_longitude != 'n/a'):
                            # Always use last known position.
                            self.gps_latitude = gps_latitude
                            self.gps_longitude = gps_longitude
                            #
                            if not first_gps_pos_received:
                                first_gps_pos_received = True
                                self._logger.info('GPS reader: First GPS position received: ' + self.get_latlong_string())
                    #
                    if self._debug:
                        if self.gps_time: print(str(self.gps_time))
                        if self.gps_latitude: print(str(self.gps_latitude)) 
                        if self.gps_longitude: print(str(self.gps_longitude))
                else:
                    # Don't use the old fetched time.
                    self.gps_time = None
        #
        finally:
            gps_socket.watch(False)



### Test. ###
if __name__ == "__main__":
    """ """
    gps_reader = WurbGpsReader()
    gps_reader.start_gps()
    gps_reader._debug = True # False
    #
    time.sleep(10)
    print('')
    print('TIME: ' + str(gps_reader.get_time_utc()))
    print('LATLONG-STRING: ' + str(gps_reader.get_latlong_string()))
    print('')
    time.sleep(10)
    #
    gps_reader.stop_gps()

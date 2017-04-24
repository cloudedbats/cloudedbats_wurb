#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

from datetime import date
import pytz
import logging
import wurb_core

@wurb_core.singleton
class WurbSunsetSunrise(object):
    """ Singleton class. Usage, see test example below. """
    def __init__(self):
        """ """        
        self._logger = logging.getLogger('CloudedBatsWURB')
        # Default timezone.
        self._timezone = pytz.timezone('UTC')
        #
        self._solartime_cache = {} # Key: (lat,long, date), value: solartime_dict

    def set_timezone(self, timezone = 'UTC'):
        """ """
        self._timezone = pytz.timezone(timezone)

    def get_solartime_dict(self, latitude = 0.0, 
                                 longitude = 0.0, 
                                 selected_date = None):
        """ """
        try:
            if not selected_date:
                selected_date = date.today()
            if (latitude, longitude, selected_date) not in self._solartime_cache:
                self._add_to_solartime_cache(latitude, longitude, selected_date)
            #
            return self._solartime_cache.get((latitude, longitude, selected_date), {})
        #
        except Exception as e:
            self._logger('Sunset: Failed to calculate sunset/sunrise: ' + str(e))
        #
        return {}

    def _add_to_solartime_cache(self, latitude, longitude, selected_date):
        """ """
        sun = wurb_core.SolarTime()
        schedule = sun.sun_utc(selected_date, float(latitude), float(longitude))
        #
        solartime_dict = {}
        solartime_dict['date'] = str(selected_date)
        solartime_dict['latitude'] = str(latitude)
        solartime_dict['longitude'] = str(longitude)
        solartime_dict['dawn'] = str(schedule['dawn'].astimezone(self._timezone).time().strftime("%H:%M"))
        solartime_dict['sunrise'] = str(schedule['sunrise'].astimezone(self._timezone).time().strftime("%H:%M"))
        solartime_dict['sunset'] = str(schedule['sunset'].astimezone(self._timezone).time().strftime("%H:%M"))
        solartime_dict['dusk'] = str(schedule['dusk'].astimezone(self._timezone).time().strftime("%H:%M"))
        #
        self._solartime_cache[(latitude, longitude, selected_date)] = solartime_dict


### Test. ###
if __name__ == "__main__":
    """ """
    solartime_dict = WurbSunsetSunrise().get_solartime_dict(57.6620, 12.6383, date.today())
#     solartime_dict = WurbSunsetSunrise().get_solartime_dict(56.78, 12.34, date.today())

    print('WurbSunsetSunrise dictionary: ' + str(solartime_dict))
    print('WurbSunsetSunrise date:       ' + str(solartime_dict['date']))
    print('WurbSunsetSunrise latitude:   ' + str(solartime_dict['latitude']))
    print('WurbSunsetSunrise longitude:  ' + str(solartime_dict['longitude']))
    print('WurbSunsetSunrise dawn:       ' + str(solartime_dict['dawn']))
    print('WurbSunsetSunrise sunrise:    ' + str(solartime_dict['sunrise']))
    print('WurbSunsetSunrise sunset:     ' + str(solartime_dict['sunset']))
    print('WurbSunsetSunrise dusk:       ' + str(solartime_dict['dusk']))


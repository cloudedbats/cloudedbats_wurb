#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

from .wurb_utils import singleton

# WURB Modules.
from .lib.solartime import SolarTime
from .lib.dsp4bats.time_domain_utils import SignalUtil 
from .lib.dsp4bats.frequency_domain_utils import DbfsSpectrumUtil

from .wurb_sunset_sunrise import WurbSunsetSunrise # Singleton.
from .wurb_gps_reader import WurbGpsReader # Singleton.
from .wurb_settings import WurbSettings
from .wurb_state_machine import WurbStateMachine
from .wurb_scheduler import WurbScheduler
from .wurb_logging import WurbLogging

# Base classes for sound streaming.
from .wurb_stream_base import WurbSoundStreamManager
from .wurb_stream_base import SoundSourceBase
from .wurb_stream_base import SoundProcessBase
from .wurb_stream_base import SoundTargetBase
# Special code for Petterson M500. Designed for Windows USB.
from .pettersson_m500_batmic import PetterssonM500BatMic

# Sound data flow from microphone to file.
from .wurb_recorder import get_device_list
from .wurb_recorder import get_device_index
from .wurb_recorder import SoundSource
from .wurb_recorder import SoundSourceM500
from .wurb_recorder import SoundProcess
from .wurb_recorder import SoundTarget
from .wurb_recorder import WurbRecorder

from .wurb_sound_detector import SoundDetector
from .wurb_sound_detector import SoundDetectorBase
from .wurb_sound_detector import SoundDetectorSimple
from .wurb_sound_detector import SoundDetectorTest1

# Main app.
from .wurb_application import WurbApplication

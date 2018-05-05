#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

from .wurb_utils import singleton

# Lib modules.
from .lib.solartime import SolarTime
from .lib.dsp4bats.frequency_domain_utils import DbfsSpectrumUtil
# # Check if librosa is available.
# try:
#     import librosa
#     from .lib.dsp4bats.time_domain_utils import SignalUtil 
# except: pass

# Base classes for sound streaming.
from .lib.dsp4bats.sound_stream_manager import SoundStreamManager
from .lib.dsp4bats.sound_stream_manager import SoundSourceBase
from .lib.dsp4bats.sound_stream_manager import SoundProcessBase
from .lib.dsp4bats.sound_stream_manager import SoundTargetBase
# Special code for Petterson M500. Designed for Windows USB.
from wurb_core.lib.pettersson_m500_batmic import PetterssonM500BatMic

# WURB Modules.
from .wurb_sunset_sunrise import WurbSunsetSunrise # Singleton.
from .wurb_gps_reader import WurbGpsReader # Singleton.
from .wurb_settings import WurbSettings
from .wurb_state_machine import WurbStateMachine
from .wurb_scheduler import WurbScheduler
from .wurb_logging import WurbLogging

# Sound data flow from microphone to file.
from .wurb_recorder import get_device_list
from .wurb_recorder import get_device_index
from .wurb_recorder import SoundSource
from .wurb_recorder import SoundSourceM500
from .wurb_recorder import SoundProcess
from .wurb_recorder import SoundTarget
from .wurb_recorder import WurbRecorder

# Sound detection.
from .wurb_sound_detector import SoundDetector

# Main app.
from .wurb_application import WurbApplication

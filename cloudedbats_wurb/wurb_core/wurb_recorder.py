#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2017 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import numpy as np
import math
import time
import wave
import scipy.signal
import pyaudio
import logging
import wurb_core

class SoundSource(wurb_core.SoundSourceBase):
    """ Subclass of SoundSourceBase. """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundSource, self).__init__()
        
    def source_exec(self):
        """ Called from base class. """
 
        # From settings. Defaults for Pettersson M500-384.
        self._in_sampling_rate_hz = self._settings.get_value('recorder_in_sampling_rate_hz', '384000') # in_sampling_rate_hz
        self._in_adc_resolution_bits = self._settings.get_value('recorder_in_adc_resolution_bits', '16') # in_adc_resolution_bits
        self._in_width = int(self._in_adc_resolution_bits / 8) 
        self._in_channels = self._settings.get_value('recorder_in_channels', '1') # in_channels
        # Sound card.
        in_device_name = self._settings.get_value('recorder_part_of_device_name', 'Pettersson')
        in_device_index = self._settings.get_value('recorder_device_index', 0) # Default=First recognized sound card.
        if in_device_name:
            self._in_device_index = self.get_device_index(in_device_name)
        else:
            self._in_device_index = in_device_index
        #
        self._active = True
        #
        buffer_size = self._settings.get_value('recorder_in_buffer_size', 1024 * 64) # 2**16
        self._logger.info('Recorder: Buffer size: ' + str(buffer_size))
 
        try:
            self._pyaudio = pyaudio.PyAudio()
            self._stream_active = True
            self._stream = None
            #
            self._stream = self._pyaudio.open(
                format = self._pyaudio.get_format_from_width(self._in_width),
                channels = self._in_channels,
                rate = self._in_sampling_rate_hz,
                frames_per_buffer = buffer_size,
                input = True,
                output = False,
                input_device_index = self._in_device_index,
                start = True,
            )
        except Exception as e:
            self._stream = None
            self._logger.error('Recorder: Failed to create stream: ' + str(e))
            # Report to state machine.
            self._callback_function('rec_source_error')
            return
        # Main source loop.
        data = self._stream.read(buffer_size) #, exception_on_overflow=False)
        while self._active and data:
#                 raw_data  = np.fromstring(data, dtype=np.int16) # To ndarray.
#                 self.push_item(raw_data)
            self.push_item((time.time(), data)) # Push time and data buffer.
            data = self._stream.read(buffer_size) #, exception_on_overflow=False)
        #
        self._logger.debug('Source: Source terminated.')
        self.push_item(None)
        #
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except: 
                self._logger.error('Recorder: Pyaudio stream stop/close failed.')
            self._stream = None
        #
        if self._pyaudio is not None:
            try: self._pyaudio.terminate()
            except: 
                self._logger.error('Recorder: Pyaudio terminate failed.')
            self._pyaudio = None

    # Sound source utils.   
    def get_device_list(self):
        """ """
        py_audio = pyaudio.PyAudio()
        device_list = []
        device_count = py_audio.get_device_count()
        for index in range(device_count):
            info_dict = py_audio.get_device_info_by_index(index)
            # Sound card for input only.
            if info_dict['maxInputChannels'] != 0:
                device_list.append(info_dict['name'])
        #
        return device_list

    def get_device_index(self, part_of_device_name):
        """ """
        py_audio = pyaudio.PyAudio()
        device_count = py_audio.get_device_count()
        for index in range(device_count):
            info_dict = py_audio.get_device_info_by_index(index)
            if part_of_device_name in info_dict['name']:
                return index
        #
        return None
    
class SoundSourceM500(SoundSource):
    """ Subclass of SoundSource for the Pettersson M500 microphone. """
    def __init__(self, callback_function=None):
        """ """
        super(SoundSourceM500, self).__init__(callback_function)
        #
        self._in_sampling_rate_hz = self._settings.get_value('recorder_in_sampling_rate_hz', '500000') # in_sampling_rate_hz
        self._in_adc_resolution_bits = self._settings.get_value('recorder_in_adc_resolution_bits', '16') # in_adc_resolution_bits
        self._in_width = int(self._in_adc_resolution_bits / 8) 
        self._in_channels = self._settings.get_value('recorder_in_channels', '1') # in_channels
        #
        self._m500batmic = None
        
    def source_exec(self):
        """ For the Pettersson M500 microphone. """
        self._active = True
        #
        try:
            if not self._m500batmic:
                self._m500batmic = wurb_core.PetterssonM500BatMic()
            #
            self._stream_active = True
            #
            self._m500batmic.start_stream()
            self._m500batmic.led_on()            

        except Exception as e:
            self._logger.error('Recorder: Failed to create stream: ' + str(e))
            # Report to state machine.
            self._callback_function('rec_source_error')
            return
        # Main source loop.
        data = self._m500batmic.read_stream().tostring()
        while self._active and data:
            self.push_item((time.time(), data)) # Push time and data buffer.
            data = self._m500batmic.read_stream().tostring()
        #
        self._logger.debug('Source M500: Source terminated.')
        self.push_item(None)
        #
        self._m500batmic.stop_stream()


class SoundProcess(wurb_core.SoundProcessBase):
    """ Subclass of SoundProcessBase. """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundProcess, self).__init__()
        #
        self._work_buffer = np.array([], dtype=np.int16) # Create empty ndarray.
#         self._work_buffer = []
        #
#         self._threshold_db = -60.0
#         self._threshold = math.pow(10.0, self._threshold_db/20.0)
        self._threshold_db = -32.0
        self._threshold_db = -30.0
#         self._threshold_db = -80.0
        self._threshold = math.pow(10.0, self._threshold_db/10.0)
#         test_db = 20*math.log10(0.01)
#         self._logger.debug('DEBUG: ' + str(test_db))
        self._logger.debug('Threshold db: ' + str(self._threshold_db) + ' magnitude: ' + str(self._threshold))
        #
#         self._peak_freq_file = open('peak_file.txt', 'w')
#         peak_header = ['time', 'frequency', 'amplitude']
#         self._peak_freq_file.write('\t'.join(peak_header) + '\n')

    def process_exec(self):
        """ Called from base class. """
        self._active = True
        #
        self._counter_ms = 0
        #
        self._frame_size = 2048
        self._jump_size = 384 # Jump 1 ms.
        #
#         self._window = np.hanning(self._frame_size)
        self._window = np.blackman(self._frame_size)
        #
        self._freq_bins_hz = np.fft.rfftfreq(self._frame_size, d=1/384000)
        self._empty_frame = np.zeros(self._jump_size)
        #
#         self._silent_counter_max = 250
        self._silent_counter_max = 1000 # Unit ms.
        self._silent_counter = self._silent_counter_max
        self._pre_silent_items = []
        #
        test_count = 0
        
        silent_buffer = []
        silent_counter = 9999 # Don't send before sound detected.
        
        while self._active:
            time_and_data = self.pull_item()

            if time_and_data is None:
                self._logger.debug('Process terminated.')
                self._active = False
                # Terminated by previous step.
                self.push_item(None)
                #
#                 self._peak_freq_file.close()
                #
            else:
#                 self.process_buffer(raw_data)
                sound_detected = self._sound_analysis(time_and_data)
                if sound_detected:
                    if len(silent_buffer) > 0:
                        for silent_time_and_data in silent_buffer:
                            self.push_item(silent_time_and_data)
                        #
                        silent_buffer = []
                    #    
                    self.push_item(time_and_data)
                    silent_counter = 0
                else:
                    if silent_counter < 25: # >4 sec.
                        self.push_item(time_and_data)
                        silent_counter += 1
                    elif silent_counter < 60: # 10 sec.
                        silent_buffer.append(time_and_data)
                        silent_counter += 1
                    else:
                        self.push_item(False)
                        silent_buffer.append(time_and_data)
                        while len(silent_buffer) > 25: # >4 sec.
                            silent_buffer.pop(0)
                    
    def _sound_analysis(self, time_and_data):
        """ """
        rec_time, raw_data = time_and_data
        # TODO: Move this:
        self_window_size = 2048
        self._jump_size = 2048
        self_blackmanharris_window = scipy.signal.blackmanharris(self_window_size)        
        # Max db value in window. dbFS = db full scale. Half spectrum used.
        self_blackmanharris_dbfs_max = np.sum(self_blackmanharris_window) / 2 
        self_freq_bins_hz = np.arange((self_window_size / 2) + 1) / (self_window_size / 384000) # self_sampling_frequency)
        #
        data_int16 = np.fromstring(raw_data, dtype=np.int16) # To ndarray.
#         self._work_buffer = np.concatenate([self._work_buffer, data_int16])
        self._work_buffer = data_int16
        #
        while len(self._work_buffer) >= self._frame_size:
            # Get frame of window size.
            data_frame = self._work_buffer[:self._frame_size] # Copy frame.
            self._work_buffer = self._work_buffer[self._jump_size:] # Cut the first jumped size.            
            # Transform to intervall -1 to 1 and apply window function.
            signal = data_frame / 32768.0 * self_blackmanharris_window
            # From time domain to frequeny domain.
            spectrum = np.fft.rfft(signal)
            # High pass filter. Unit Hz. Cut below 15 kHz.
            spectrum[ self_freq_bins_hz < 15000.0 ] = 0.000000001 # log10 does not like zero.
            # Convert spectrum to dBFS (bin values related to maximal possible value).
            dbfs_spectrum = 20 * np.log10(np.abs(spectrum) / self_blackmanharris_dbfs_max)
            # Find peak and dBFS value for the peak.
            bin_peak_index = dbfs_spectrum.argmax()
            peak_db = dbfs_spectrum[bin_peak_index]
            # Treshold.
            if peak_db > -50:
                peak_frequency_hz = bin_peak_index * 384000 / self_window_size
                self._logger.debug('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
                print('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
                return True
        #
        print('DEBUG: Silent.')
        return False


class SoundTarget(wurb_core.SoundTargetBase):
    """ Subclass of SoundTargetBase. """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundTarget, self).__init__()
        #
        # From settings. 
        self._dir_path = self._settings.get_value('recorder_dir_path', '/media/usb0/wurb1_rec')
        self._filename_lat_long = self._settings.get_value('recorder_filename_lat_long', 'N00.00E00.00')
        self._filename_prefix = self._settings.get_value('recorder_filename_prefix', 'WURB1')
        if not self._settings.get_value('recorder_pettersson_m500', 'False'):
            self._filename_rec_type = self._settings.get_value('recorder_filename_rec_type', 'TE384')
            self._out_sampling_rate_hz = self._settings.get_value('recorder_out_sampling_rate_hz', '38400')
        else:
            self._filename_rec_type = self._settings.get_value('recorder_filename_rec_type', 'TE500')
            self._out_sampling_rate_hz = self._settings.get_value('recorder_out_sampling_rate_hz', '50000')
        self._adc_resolution = self._settings.get_value('recorder_adc_resolution', '16')
        self._width = int(self._adc_resolution / 8) 
        self._channels = self._settings.get_value('recorder_out_channels', '1') # 1 = mono, 2 = stereo.
        self._max_record_length_s = self._settings.get_value('recorder_max_record_length_s', '300')
        #
        self._wave_file = None
        self._file_open = False
        self._total_start_time = None
        self._internal_buffer_list = []
        #
        self._write_thread_active = False
        self._active = False
    
    def target_exec(self):
        """ Called from base class. """
        self._active = True
        rec_start_time = None
        # Use buffer to increase write speed.
        item_list = []
        item_list_max = 10
        #
        try:
            while self._active:
                item = self.pull_item()
                # None indicates terminate by previous part in chain.
                if item is None:
                    self._active = False # Terminated by previous step.                 
                # False indicates silent part. Close file until not silent. 
                elif item is False:
                    if self._wave_file:
                        # Flush buffer.
                        joined_items = b''.join(item_list)
                        self._wave_file.writeframes(joined_items)
                        item_list = []
                        # Close.
                        self._close_file()
                # Normal case, write frames.
                else:
                    rec_time, data = item
                    
                    item_list.append(data)
                    # Open file if first after silent part.
                    if not self._file_open:
                        self._open_file()
                        if rec_start_time is None:
                            rec_start_time = rec_time
                        else:
                            rec_start_time += self._max_record_length_s
                    #
                    if len(item_list) >= item_list_max:
                        # Flush buffer.
                        if self._wave_file:
                            joined_items = b''.join(item_list)
                            self._wave_file.writeframes(joined_items)
                            item_list = []
                # Check if max rec length was reached.
                if rec_start_time:
                    if (rec_start_time + self._max_record_length_s) < rec_time:
                        # Flush buffer.
                        if self._wave_file:
                            # Flush buffer.
                            joined_items = b''.join(item_list)
                            self._wave_file.writeframes(joined_items)
                            item_list = []
                            # Close.
                            self._close_file()
            
            # Thread terminated.
            if self._wave_file:
                if len(item_list) > 0:
                    # Flush buffer.
                    joined_items = b''.join(item_list)
                    self._wave_file.writeframes(joined_items)
                    item_list = []
                #
                self._close_file()
        #
        except Exception as e:
            self._logger.error('Recorder: Sound target exception: ' + str(e))
            self._active = False # Terminate
            self._callback_function('rec_target_error')

    def _open_file(self):
        """ """
        self._file_open = True
        # Create file name.
        # Default time and position.
        datetimestring = time.strftime("%Y%m%dT%H%M%S%z")
        latlongstring = self._filename_lat_long
        # Use GPS time if available.
        datetime_local_gps = wurb_core.WurbGpsReader().get_time_local_string()
        if datetime_local_gps:
            datetimestring = datetime_local_gps
        # Use GPS time if available.
        latlong = wurb_core.WurbGpsReader().get_latlong_string()
        if latlong:
            latlongstring = latlong
        #
        filename =  self._filename_prefix + \
                    '_' + \
                    datetimestring + \
                    '_' + \
                    latlongstring + \
                    '_' + \
                    self._filename_rec_type + \
                    '.wav'
        filenamepath = os.path.join(self._dir_path, filename)
        #
        if not os.path.exists(self._dir_path):
            os.makedirs(self._dir_path) # For data, full access.
        # Open wave file for writing.
        self._wave_file = wave.open(filenamepath, 'wb')
        self._wave_file.setnchannels(self._channels)
        self._wave_file.setsampwidth(self._width)
        self._wave_file.setframerate(self._out_sampling_rate_hz)
        #
        self._logger.info('Recorder: New wave file: ' + filename)

    def _close_file(self):
        """ """
        self._logger.info('Recorder: Audio target wave file closed.')
        if self._wave_file is not None:
            self._wave_file.close()
            self._wave_file = None 
        #    
        self._file_open = False



# === TEST ===    
if __name__ == "__main__":
    """ """
    # Default configured for Pettersson M500-384.
    # Command to test M500-384: PYTHONPATH="." python3 wurb_core/wurb_recorder.py
    source = SoundSource() 
    #
    # M500 as source. Must have sudo privileges for direct USB access.
    # Command to test M500: sudo PYTHONPATH="." python3 wurb_core/wurb_recorder.py
    # source = SoundSourceM500() 
    #
    process = SoundProcess()
    #
    target = SoundTarget()
    #
    manager = wurb_core.WurbSoundStreamManager(source, process, target,
                                               source_queue_max=100)
    #
    manager.start_streaming()
    time.sleep(30)
    manager.stop_streaming()


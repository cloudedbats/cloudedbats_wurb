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
import struct
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
        
        # From settings. Defaults for Pettersson M500-384.
        self._in_sampling_rate_hz = int(self._settings.get_value('aaa', '384000')) # in_sampling_rate_hz
        self._in_adc_resolution_bits = int(self._settings.get_value('aaa', '16')) # in_adc_resolution_bits
        self._in_width = int(self._in_adc_resolution_bits / 8) 
        self._in_channels = int(self._settings.get_value('aaa', '1')) # in_channels
        # Sound card.
        in_device_name = self._settings.get_value('aaa', 'Pettersson') # 
        in_device_index = self._settings.get_value('aaa', 0) # Default: First recognized sound card.
        if in_device_name:
            self._in_device_index = self.get_device_index(in_device_name)
        else:
            self._in_device_index = in_device_index
        
    def source_exec(self):
        """ Called from base class. """
        self._active = True
        #
        buffer_size = 1024 * 64 # 2**16
#         buffer_size = 1024 * 16 # TEST.
        self._logger.info('Sound recorder: Buffer size: ' + str(buffer_size))
                
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
            self._logger.error('Sound recorder: Failed to create stream: ' + str(e))
            # Report to state machine.
            self._callback_function('rec_source_error')
            return
        # Main source loop.
        data = self._stream.read(buffer_size) #, exception_on_overflow=False)
        while self._active and data:
#             raw_data  = np.fromstring(data, dtype=np.int16) # To ndarray.
#             self.push_item(raw_data)
            self.push_item((time.time(), data)) # Push time and data buffer.
            data = self._stream.read(buffer_size) #, exception_on_overflow=False)
        #
        print('Source terminated.')
        self.push_item(None)
        #
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except: 
                self._logger.error('Sound recorder: Pyaudio stream stop/close failed.')
            self._stream = None
        #
        if self._pyaudio is not None:
            try: self._pyaudio.terminate()
            except: 
                self._logger.error('Sound recorder: Pyaudio terminate failed.')
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
#         print('DEBUG: ' + str(test_db))
        print('Threshold db: ' + str(self._threshold_db) + ' magnitude: ' + str(self._threshold))
        #
        self._peak_freq_file = open('peak_file.txt', 'w')
        peak_header = ['time', 'frequency', 'amplitude']
        self._peak_freq_file.write('\t'.join(peak_header) + '\n')

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
                print('Process terminated.')
                self._active = False
                # Terminated by previous step.
                self.push_item(None)
                #
                self._peak_freq_file.close()
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
                    if silent_counter < 6: # 1 sec.
                        self.push_item(time_and_data)
                        silent_counter += 1
                    elif silent_counter < 60: # 10 sec.
                        silent_buffer.append(time_and_data)
                        silent_counter += 1
                    else:
                        self.push_item(False)
                        silent_buffer.append(time_and_data)
                        while len(silent_buffer) > 6: # 1 sec.
                            silent_buffer.pop(0)
                    
    def _sound_analysis(self, time_and_data):
        """ """
        rec_time, raw_data = time_and_data
        
        self_window_size = 2048
        self._jump_size = 2048
        self_blackmanharris_window = scipy.signal.blackmanharris(self_window_size)        
        # Max db value in window. dbFS = db full scale. Half spectrum used.
        self_blackmanharris_dbfs_max = np.sum(self_blackmanharris_window) / 2 
        self_freq_bins_hz = np.arange((self_window_size / 2) + 1) / (self_window_size / 384000) # self_sampling_frequency)

        
        data_int16 = np.fromstring(raw_data, dtype=np.int16) # To ndarray.
#         self._work_buffer = np.concatenate([self._work_buffer, data_int16])
        self._work_buffer = data_int16
        #
        while len(self._work_buffer) >= self._frame_size:
            data_frame = self._work_buffer[:self._frame_size] # Copy frame.
            self._work_buffer = self._work_buffer[self._jump_size:] # Cut the first jumped size.            
            #
            signal = data_frame / 32768.0 # Transform to intervall 0-1.
            
            signal = signal * self_blackmanharris_window
            spectrum = np.fft.rfft(signal)

            spectrum[ self_freq_bins_hz < 15000.0 ] = 0.0000001 # High pass filter. Unit Hz.


            dbfs_spectrum = 20 * np.log10(np.abs(spectrum) / self_blackmanharris_dbfs_max)
            
            bin_peak_index = dbfs_spectrum.argmax()
            peak_db = dbfs_spectrum[bin_peak_index]
            
            if peak_db > -50:
                peak_frequency_hz = bin_peak_index * 384000 / self_window_size
                print('DEBUG: Peak freq hz: '+ str(peak_frequency_hz) + '   dbFS: ' + str(peak_db))
                return True

        #
        print('DEBUG: Silent.')
        return False
            
#     def _sound_analysis(self, raw_data):
#         """ """
#         data_int16 = np.fromstring(raw_data, dtype=np.int16) # To ndarray.
# #         self._work_buffer.concatenate(data_int16)
#         self._work_buffer = np.concatenate([self._work_buffer, data_int16])
#         #
#         while len(self._work_buffer) >= self._frame_size:
#             data_frame = self._work_buffer[:self._frame_size] # Copy frame.
#             self._work_buffer = self._work_buffer[self._jump_size:] # Cut the first jumped size.            
# #             #
# #             if self._is_silent(data):
#             signal = data_frame / 32768.0 # Transform to intervall 0-1.
#             # Alterenative 1:
#     #         if np.max(signal) < self._threshold:
#     #             return True
#             # Alternative 2:
#     #         if np.sqrt(np.mean(signal**2)) < self._threshold:
#     #             return True
#             # Alternative 3:
#             signal = signal * self._window
#             spectrum_cpx = np.fft.rfft(signal)
#     #         spectrum_cpx = spectrum_cpx**2
#             spectrum_cpx[ self._freq_bins_hz < 15000.0 ] = 0 # High pass filter. Unit Hz.
#             signal_cpx = np.fft.irfft(spectrum_cpx) 
#             signal = np.abs(signal_cpx)
#      
#             if np.mean(signal) < self._threshold:
#     #         if np.sqrt(np.mean(signal**2)) < self._threshold:
#     #         if np.max(signal) < self._threshold:
#                 return True
#             #
#             # Check peak frequency if not silent.
#             self._find_peak(spectrum_cpx)
#      
#             # Test:
#             if np.max(signal) > 0.2:
#                 print('Max-2: ' + str(np.max(signal)))
#             return False
#         #
#         return False
            

                    
    
#     def process_buffer(self, raw_data):
#         """ """
#         self._work_buffer += raw_data
#         #
#         while len(self._work_buffer) >= self._frame_size:
#             data_raw = self._work_buffer[:self._frame_size] # Copy frame.
#             data = np.fromstring(data_raw, dtype=np.int16) # To ndarray.
# 
#             out_buffer = self._work_buffer[:self._jump_size] # Copy. Don't destroy out buffer.
#             self._work_buffer = self._work_buffer[self._jump_size:] # Cut the first jumped size.            
#             #
#             if self._is_silent(data):
#                 if self._silent_counter < self._silent_counter_max:
#                     self.push_item(out_buffer)
#                 else:
#                     self._pre_silent_items.append(out_buffer) 
#                     if len(self._pre_silent_items) >  self._silent_counter_max:
#                         self._pre_silent_items.pop(0)  
#                     pass
#                 #
#                 if self._silent_counter > self._silent_counter_max:
#                     if (self._silent_counter *4) % self._silent_counter_max == 0: # %=modulo.
#                         # Add some empty frames to indicate silence length.
#                         self.push_item(self._empty_frame.astype(np.int16))
#                 #
#                 self._silent_counter += 1
#             else:
#                 #
#                 if len(self._pre_silent_items) >  0:
#                     for pre_silent_item in self._pre_silent_items:
#                         self.push_item(pre_silent_item)
#                     self._pre_silent_items = []
#                 #
#                 if self._silent_counter > self._silent_counter_max:
#                     print('Silent counter: ' + str(self._silent_counter))
#                 self._silent_counter = 0
#                 #
#                 self.push_item(out_buffer)
#             #
#             self._counter_ms += 1
#     
#     def _is_silent(self, data):
#         """ """
#         signal = data / 32768.0 # Transform to intervall 0-1.
#         # Alterenative 1:
# #         if np.max(signal) < self._threshold:
# #             return True
#         # Alternative 2:
# #         if np.sqrt(np.mean(signal**2)) < self._threshold:
# #             return True
#         # Alternative 3:
#         signal = signal * self._window
#         spectrum_cpx = np.fft.rfft(signal)
# #         spectrum_cpx = spectrum_cpx**2
#         spectrum_cpx[ self._freq_bins_hz < 15000.0 ] = 0 # High pass filter. Unit Hz.
#         signal_cpx = np.fft.irfft(spectrum_cpx) 
#         signal = np.abs(signal_cpx)
# 
#         if np.mean(signal) < self._threshold:
# #         if np.sqrt(np.mean(signal**2)) < self._threshold:
# #         if np.max(signal) < self._threshold:
#             return True
#         #
#         # Check peak frequency if not silent.
#         self._find_peak(spectrum_cpx)
# 
#         # Test:
#         if np.max(signal) > 0.2:
#             print('Max-2: ' + str(np.max(signal)))
#         return False
# 
#     def _find_peak(self, spectrum_cpx):
#         """ """
#         bin_peak_index = spectrum_cpx.argmax()
#         #
#         if (bin_peak_index > 1) and (bin_peak_index < len(spectrum_cpx) - 3):
#             # Use quadratic interpolation around the max.
#             spectrum = np.abs(spectrum_cpx)    
#             y0,y1,y2 = np.log(spectrum[bin_peak_index-1:bin_peak_index+2:] + [0.000001, 0.000001, 0.000001]) # Delta.
#             x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
#             # Adjust bin frequency value.
#             ###thefreq = (which+x1)*384000/2048
#             peak_frequency_hz = (bin_peak_index + x1) * 384000 / self._frame_size
#         else:
#             peak_frequency_hz = bin_peak_index * 384000 / self._frame_size
#         #
#         # Test:
#         peak_frequency_hz_simple = bin_peak_index * 384000 / self._frame_size
#         value_at_max = np.abs(spectrum_cpx[bin_peak_index])
# #         print('Peak: ' + str(peak_frequency_hz) + 
# #               '   Peak-simple: ' + str(peak_frequency_hz_simple) + 
# #               '   value: ' + str(value_at_max))
#         #
#         print('Time ms: ' + str(self._counter_ms) + 
#               '   Peak: ' + str(round(peak_frequency_hz/1000, 2)) +
#               '   Value: ' + str(round(value_at_max, 2)))
#         
#         # TODO: Add to file (peak over time) and plot result.
#         peak_row = [str(self._counter_ms), 
#                     str(round(peak_frequency_hz/1000, 2)), 
#                     str(round(value_at_max, 2))]
#         self._peak_freq_file.write('\t'.join(peak_row) + '\n')
        

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
        self._dir_path = self._settings.get_value('aaa', 'test_rec') # dir_path
        self._filename_lat_long = self._settings.get_value('aaa', 'N00.00E00.00') # filename_lat_long
        self._filename_prefix = self._settings.get_value('aaa', 'WURB') # filename_prefix
        self._filename_rec_type = self._settings.get_value('aaa', 'TE384') # filename_rec_type
        self._sampling_rate = int(self._settings.get_value('aaa', '38400')) # sampling_rate_hz
        self._adc_resolution = int(self._settings.get_value('aaa', '16')) # adc_resolution_bits
        self._width = int(self._adc_resolution / 8) 
        self._channels = int(self._settings.get_value('aaa', '1')) # channels # 1 = mono, 2 = stereo.
        self._max_record_length_s = int(self._settings.get_value('aaa', '300')) # max_record_length_s TODO: each_record_length_s
        self._timezone = self._settings.get_value('aaa', '') # timezone
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
        item_list_max = 1
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
            self._logger.error('Sound recorder: Sound target exception: ' + str(e))
            self._active = False # Terminate
            self._callback_function('rec_target_error')

    def _open_file(self):
        """ """
        self._file_open = True
        self._logger.info('Sound recorder: Audio target _open_file')
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
        self._wave_file.setframerate(self._sampling_rate)

    def _close_file(self):
        """ """
        self._logger.info('Sound recorder: Audio target _close_file')
        if self._wave_file is not None:
            self._wave_file.close()
            self._wave_file = None 
        #    
        self._file_open = False
    


# === MAIN ===    
if __name__ == "__main__":
    """ """
    source = SoundSource()
    process = SoundProcess()
    target = SoundTarget()
    manager = wurb_core.WurbSoundStreamManager(source, process, target,
                                               source_queue_max=100)
    #
    manager.start_streaming()


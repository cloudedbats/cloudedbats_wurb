#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org
# Copyright (c) 2016-2018 Arnold Andreasson 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import logging
import pathlib
import math
import time
import numpy as np
#import scipy.signal
import wave
import scipy.signal
import pyaudio
import librosa
import wurb_core

def default_settings():
    """ Available settings for the this module.
        This info is used to define default values and to 
        generate the wurb_settings_DEFAULT.txt file."""
    
    description = [
        '# ',
        ]
    default_settings = [
        {'key': 'rec_directory_path', 'value': '/media/usb0/wurb1_rec'}, 
        {'key': 'rec_filename_prefix', 'value': 'WURB1'},
        {'key': 'rec_max_length_s', 'value': '10'},
        {'key': 'rec_sampling_freq_khz', 'value': '384'}, 
        {'key': 'rec_format', 'value': 'TE', 
                'valid': ['TE', 'FS']}, # TE=Time Expansion, FS=Full Scan.        
        # Hardware.
        {'key': 'rec_microphone_type', 'value': 'STD-USB', 
                'valid': ['STD-USB', 'M500']}, # STD-USB, M500
        {'key': 'rec_part_of_device_name', 'value': 'Pettersson'}, # Example: 'Pettersson'.
        {'key': 'rec_device_index', 'value': 0},
        ]
    developer_settings = [
        {'key': 'aaa', 'value': 'bbb'}, 
        ]
    #
    return description, default_settings, developer_settings

def get_device_list():
    """ Sound source util. Check connected sound cards. """
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

def get_device_index(part_of_device_name):
    """ Sound source util. Lookup for device by name. """
    py_audio = pyaudio.PyAudio()
    device_count = py_audio.get_device_count()
    for index in range(device_count):
        info_dict = py_audio.get_device_info_by_index(index)
        if part_of_device_name in info_dict['name']:
            return index
    #
    return None


class WurbRecorder(object):
    """ """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        
    def setup_sound_manager(self):
        # Sound stream parts:
        # - Source
        self._sound_source = None
        if self._settings.text('rec_microphone_type') == 'M500':
            # The Pettersson M500 microphone is developed for Windows. Special code to handle M500.
            self._sound_source = wurb_core.SoundSourceM500(callback_function=self._callback_function)
        else:
            # Generic USB microphones, including Pettersson M500-384.
            self._sound_source = wurb_core.SoundSource(callback_function=self._callback_function)
        # - Process.
        self._sound_process = wurb_core.SoundProcess(callback_function=self._callback_function)
        # - Target.
        self._sound_target = wurb_core.SoundTarget(callback_function=self._callback_function)
        # - Manager.
        self._sound_manager = wurb_core.WurbSoundStreamManager(
                                    self._sound_source, 
                                    self._sound_process, 
                                    self._sound_target)
        
        return self._sound_manager


class SoundSource(wurb_core.SoundSourceBase):
    """ Subclass of SoundSourceBase. """
    
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundSource, self).__init__()
        #
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        #
        self.read_settings()
        
    def read_settings(self):
        """ Called from base class. """
        # From settings. Defaults for Pettersson M500-384.
        self._sampling_freq_hz = self._settings.integer('rec_sampling_freq_khz') * 1000
        # Sound card.
        in_device_name = self._settings.text('rec_part_of_device_name')
        in_device_index = self._settings.integer('rec_device_index') # Default=0. First recognized sound card.
        if in_device_name:
            self._in_device_index = wurb_core.get_device_index(in_device_name)
        else:
            self._in_device_index = in_device_index

        self._logger.info('Recorder: Sampling frequency (hz): ' + str(self._sampling_freq_hz))
         
    def _setup_pyaudio(self):
        """ """
        # Initiate PyAudio.
        try:
            self._stream = self._pyaudio.open(
                format = self._pyaudio.get_format_from_width(2), # 2=16 bits.
                channels = 1, # 1=Mono.
                rate = self._sampling_freq_hz,
                frames_per_buffer = self._sampling_freq_hz, # Buffer 1 sec.
                input = True,
                output = False,
                input_device_index = self._in_device_index,
                start = False,
            )
        except Exception as e:
            self._stream = None
            self._logger.error('Recorder: Failed to create stream: ' + str(e))
            # Report to state machine.
            if self._callback_function:
                self._callback_function('rec_source_error')
            return

    def source_exec(self):
        """ Called from base class. """
        
        if self._stream is None:
            self._setup_pyaudio()
        #
        self._active = True
        self._stream_active = True
        self._stream.start_stream()
        #
        buffer_size = int(self._sampling_freq_hz / 2)
        
        # Main source loop.
        try:
            data = self._stream.read(buffer_size) #, exception_on_overflow=False)
            while self._active and data:
                
                print('Sound buffer read at: ', str(time.time()), '   Length: ', len(data))
                print('Sound buffer read at: ', self._stream.get_time(), ' (pyaudio time)')
                print('')
                
                self.push_item((time.time(), data)) # Push time and data buffer.
                data = self._stream.read(buffer_size) #, exception_on_overflow=False)
        except Exception as e:
            self._logger.error('Recorder: Failed to read stream: ' + str(e))

        # Main loop terminated.
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

class SoundSourceM500(SoundSource):
    """ Subclass of SoundSource for the Pettersson M500 microphone. """
    def __init__(self, callback_function=None):
        """ """
        super(SoundSourceM500, self).__init__(callback_function)
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
            if self._callback_function:
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
        # Get sound detector based on user settings.
        sound_detector = wurb_core.SoundDetector().get_detector()
        #
        silent_buffer = []
        silent_counter = 9999 # Don't send before sound detected.
        
        while self._active:
            time_and_data = self.pull_item()

            if time_and_data is None:
                self._logger.debug('Process terminated.')
                self._active = False
                # Terminated by previous step.
                self.push_item(None)
            else:
#                 self.process_buffer(raw_data)
                sound_detected = sound_detector.check_for_sound(time_and_data)
                ###sound_detected = self._sound_analysis(time_and_data)
                if sound_detected:
                    # Send pre buffer if this is the first one.
                    if len(silent_buffer) > 0:
                        for silent_time_and_data in silent_buffer:
                            self.push_item(silent_time_and_data)
                        #
                        silent_buffer = []
                    # Send buffer.    
                    self.push_item(time_and_data)
                    silent_counter = 0
                else:
                    if silent_counter < 1: # Unit 0.5 sec.
                        # Send after sound detected.
                        self.push_item(time_and_data)
                        silent_counter += 1
                    elif silent_counter < 4: # Unit 0.5 sec.
                        # Accept 
                        silent_buffer.append(time_and_data)
                        silent_counter += 1
                    else:
                        # Silent, but store in pre buffer.
                        self.push_item(False)
                        silent_buffer.append(time_and_data)
                        while len(silent_buffer) > 1: # Unit 0.5sec.
                            silent_buffer.pop(0)
                    
#     def _sound_analysis(self, time_and_data):
#         """ """
#         
#         test_time = time.time()
#         
#         _rec_time, raw_data = time_and_data
#         
#         freq_window_size = 1024
#         sampling_freq = 384000
#         time_filter_low_limit_hz = 15000
#         time_filter_high_limit_hz = None
#         scanning_results_dir = '/home/arnold/Desktop/WURB_REC_TEST'
#         scanning_results_file_name = 'detected_peks'
# 
#         # localmax_noise_threshold_factor = 1.2
#         localmax_noise_threshold_factor = 3.0
#         
#         localmax_jump_factor = 1000
#         localmax_frame_length = 1024
#         freq_jump_factor = 1000
#         freq_filter_low_hz = 15000
#         freq_threshold_dbfs = -50.0
#         freq_threshold_below_peak_db = 20.0
#         freq_max_frames_to_check = 200
#         freq_max_silent_slots = 8
#         samp_width = 2
#         self.debug=True
# 
#         # Create dsp4bats utils.
#         signal_util = wurb_core.SignalUtil(sampling_freq)
#         spectrum_util = wurb_core.DbfsSpectrumUtil(window_size=freq_window_size,
#                                                    window_function='kaiser',
#                                                    kaiser_beta=14,
#                                                    sampling_freq=sampling_freq)
#         
#         # Prepare output file for metrics. Create on demand.
#         metrics_file_name = pathlib.Path(scanning_results_file_name).stem + '_Metrics.txt'
#         out_header = spectrum_util.chirp_metrics_header()
#         out_file = None
#         # Read file.
#         checked_peaks_counter = 0
#         found_peak_counter = 0
#         acc_checked_peaks_counter = 0
#         acc_found_peak_counter = 0
#         
#         # Iterate over buffers.
#         if len(raw_data) > 0:
#             
#             signal = librosa.util.buf_to_float(raw_data, n_bytes=samp_width)
#             
#             # Get noise level for 1 sec buffer.
#             signal_noise_level = signal_util.noise_level(signal)
#             signal_noise_level_db = signal_util.noise_level_in_db(signal)
#             #
#             signal_filtered = signal_util.butterworth_filter(signal, 
#                                                          low_freq_hz=time_filter_low_limit_hz,
#                                                          high_freq_hz=time_filter_high_limit_hz)
#             # Get noise level for 1 sec buffer after filtering.
#             noise_level = signal_util.noise_level(signal_filtered)
#             noise_level_db = signal_util.noise_level_in_db(signal_filtered)
#             if self.debug:
#                 print('Noise level (before filter):', np.round(noise_level, 5), 
#                       '(', np.round(signal_noise_level, 5), ')', 
#                       ' Noise (db):', np.round(noise_level_db, 2), 
#                       '(', np.round(signal_noise_level_db, 5), ')'
#                       )
#             # Find peaks in time domain.
#             peaks = signal_util.find_localmax(signal=signal_filtered,
#                                               noise_threshold=noise_level * localmax_noise_threshold_factor, 
#                                               jump=int(sampling_freq/localmax_jump_factor), 
#                                               frame_length=localmax_frame_length) # Window size.
# 
#             checked_peaks_counter = len(peaks)
#             acc_checked_peaks_counter += len(peaks)
#             found_peak_counter = 0
#             
#             for peak_position in peaks:
#     
#                 # Extract metrics.
#                 result = spectrum_util.chirp_metrics(
#                                             signal=signal_filtered, 
#                                             peak_position=peak_position, 
#                                             jump_factor=freq_jump_factor, 
#                                             high_pass_filter_freq_hz=freq_filter_low_hz, 
#                                             threshold_dbfs = freq_threshold_dbfs, 
#                                             threshold_dbfs_below_peak = freq_threshold_below_peak_db, 
#                                             max_frames_to_check=freq_max_frames_to_check, 
#                                             max_silent_slots=freq_max_silent_slots, 
#                                             debug=False)
# 
#                 if result is False:
#                     continue # 
#                 else:
#                     result_dict = dict(zip(out_header, result))
#                     ## out_row = [result_dict.get(x, '') for x in out_header]
#                     # Add buffer steps to peak_signal_index, start_signal_index and end_signal_index.
#                     out_row = []
#                     for key in out_header:
#                         if '_signal_index' in key:
#                             # Adjust index if more than one buffer was read.
#                             index = int(result_dict.get(key, 0))
# ###                            index += buffer_number * signal_util.sampling_freq
#                             out_row.append(index)
#                         else:
#                             out_row.append(result_dict.get(key, ''))
#                     # Write to file.
#                     if out_file is None:
#                         ###out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('w')
#                         out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('a')
#                         out_file.write('\t'.join(map(str, out_header)) + '\n')# Read until end of file.
#                     #
#                     out_file.write('\t'.join(map(str, out_row)) + '\n')
#                     #
#                     found_peak_counter += 1
#                     acc_found_peak_counter += 1
# 
#             if self.debug:
#                 print('Buffer: Detected peak counter: ', str(found_peak_counter),
#                       '  of ', checked_peaks_counter, ' checked peaks.') 
#             
#         # Done.
#         if self.debug:
#             print('Summary: Detected peak counter: ', str(acc_found_peak_counter),
#                   '  of ', acc_checked_peaks_counter, ' checked peaks.') 
# 
#         if out_file is None:
#             print('\n', 'Warning: No detected peaks found. No metrics produced.', '\n') 
#         else: 
#             out_file.close()
# 
# 
#         print('DEBUG: Sound analysis time: ', time.time() - test_time)
# 
# 
#         if acc_found_peak_counter > 0:
#             sound_detected = True
#         else:
#             sound_detected = False
#         #
#         if sound_detected:
# #             peak_frequency_hz = bin_peak_index * 384000 / self_window_size
# #             self._logger.debug('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
# #             print('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
#             return True
#         #
#         print('DEBUG: Silent.')
#         return False


class SoundTarget(wurb_core.SoundTargetBase):
    """ Subclass of SoundTargetBase. """
    def __init__(self, callback_function=None):
        """ """
        self._callback_function = callback_function
        self._logger = logging.getLogger('CloudedBatsWURB')
        self._settings = wurb_core.WurbSettings()
        #
        super(SoundTarget, self).__init__()
        # From settings. 
        self._dir_path = self._settings.text('rec_directory_path')
        self._filename_prefix = self._settings.text('rec_filename_prefix')
        rec_max_length_s = self._settings.integer('rec_max_length_s')
        self.rec_max_length = rec_max_length_s * 2
        # Different microphone types.
        if self._settings.boolean('rec_microphone_type') == 'M500':
            # For M500 only.
            if self._settings.boolean('rec_format') == 'TE':
                self._filename_rec_type = 'TE500'
                self._out_sampling_rate_hz = 50000
            else:
                self._filename_rec_type = 'FS500'
                self._out_sampling_rate_hz = 500000
        else:
            # For standard USB, inclusive M500-384.
            if self._settings.text('rec_format') == 'TE':
                self._filename_rec_type = 'TE' + self._settings.text('rec_sampling_freq_khz')
                self._out_sampling_rate_hz = self._settings.integer('rec_sampling_freq_khz') * 100
            else:
                self._filename_rec_type = 'FS' + self._settings.text('rec_sampling_freq_khz')
                self._out_sampling_rate_hz = self._settings.integer('rec_sampling_freq_khz') * 1000
        #
        self._total_start_time = None
        self._internal_buffer_list = []
        self._write_thread_active = False
        self._active = False
    
    def target_exec(self):
        """ Called from base class. """
        self._active = True
        wave_file_writer = None
        # Use buffer to increase write speed.
        item_list = []
        item_list_max = 5 # Unit 0.5 sec. Before flush to file.
        item_counter = 0
        #
        try:
            while self._active:
                item = self.pull_item()
                
                # "None" indicates terminate by previous part in chain.
                if item is None:
                    self._active = False # Terminated by previous step.
                    continue              

                # "False" indicates silent part. Close file until not silent. 
                elif item is False:
                    if wave_file_writer:
                        # Flush buffer.
                        joined_items = b''.join(item_list)
                        item_list = []
                        wave_file_writer.write(joined_items)
                        # Close.
                        wave_file_writer.close()
                        wave_file_writer = None
                    #
                    continue
                
                # Normal case, write frames.
                else:
                    _rec_time, data = item # "rec_time" not used.

                    # Open file if first after silent part.
                    if not wave_file_writer:
                        wave_file_writer = WaveFileWriter(self)
                        
                    # Check if max rec length was reached.
                    if item_counter >= self.rec_max_length: 
                        if wave_file_writer:
                            # Flush buffer.
                            joined_items = b''.join(item_list)
                            item_list = []
                            wave_file_writer.write(joined_items)
                            # Close the old one.
                            wave_file_writer.close()
                            wave_file_writer = None
                            item_counter = 0
                            # Open a new file.
                            wave_file_writer = WaveFileWriter(self)
                                
                    # Append data to buffer
                    item_list.append(data)
                    item_counter += 1
                    
                    # Flush buffer when needed.
                    if len(item_list) >= item_list_max:
                        if wave_file_writer:
                            joined_items = b''.join(item_list)
                            item_list = []
                            wave_file_writer.write(joined_items)
            
            # Thread terminated.
            if wave_file_writer:
                if len(item_list) > 0:
                    # Flush buffer.
                    joined_items = b''.join(item_list)
                    item_list = []
                    wave_file_writer.write(joined_items)
                #
                wave_file_writer.close()
                wave_file_writer = None
        #
        except Exception as e:
            self._logger.error('Recorder: Sound target exception: ' + str(e))
            self._active = False # Terminate
            if self._callback_function:
                self._callback_function('rec_target_error')


class WaveFileWriter():
    """ Each file is connected to a separate object to avoid concurrency problems. """
    def __init__(self, sound_target_obj):
        """ """
        self._wave_file = None
        self._sound_target_obj = sound_target_obj
        self._size_counter = 0 
        
        # Create file name.
        # Default time and position.
        datetimestring = time.strftime("%Y%m%dT%H%M%S%z")
        latlongstring = 'N00.00E00.00' # Default.
        # Use GPS time if available.
        datetime_local_gps = wurb_core.WurbGpsReader().get_time_local_string()
        if datetime_local_gps:
            datetimestring = datetime_local_gps
        # Use GPS position if available.
        latlong = wurb_core.WurbGpsReader().get_latlong_string()
        if latlong:
            latlongstring = latlong
            
        # Filename example: "WURB1_20180420T205942+0200_N00.00E00.00_TE384.wav"
        filename =  sound_target_obj._filename_prefix + \
                    '_' + \
                    datetimestring + \
                    '_' + \
                    latlongstring + \
                    '_' + \
                    sound_target_obj._filename_rec_type + \
                    '.wav'
        filenamepath = os.path.join(sound_target_obj._dir_path, filename)
        #
        if not os.path.exists(sound_target_obj._dir_path):
            os.makedirs(sound_target_obj._dir_path) # For data, full access.
        # Open wave file for writing.
        self._wave_file = wave.open(filenamepath, 'wb')
        self._wave_file.setnchannels(1) # 1=Mono.
        self._wave_file.setsampwidth(2) # 2=16 bits.
        self._wave_file.setframerate(sound_target_obj._out_sampling_rate_hz)
        #
        sound_target_obj._logger.info('Recorder: New sound file: ' + filename)
        
    def write(self, buffer):
        """ """
        self._wave_file.writeframes(buffer)
        self._size_counter += len(buffer) / 2 # Count frames.

    def close(self):
        """ """
        if self._wave_file is not None:
            self._wave_file.close()
            self._wave_file = None 

            length_in_sec = self._size_counter / self._sound_target_obj._out_sampling_rate_hz
            self._sound_target_obj._logger.info('Recorder: Sound file closed. Length:' + str(length_in_sec) + ' sec.')


# class SoundDetectorBase():
#     """ """
#     def __init__(self, sampling_freq, window_size, debug):
#         """ """
#         self.sampling_freq = sampling_freq
#         self.window_size = window_size
#         self.debug = debug
#         # Create dsp4bats utils.
#         self.window_size = 1024
#         self.signal_util = wurb_core.SignalUtil(sampling_freq)
#         self.spectrum_util = wurb_core.DbfsSpectrumUtil(window_size=self.window_size,
#                                                    window_function='kaiser',
#                                                    kaiser_beta=14,
#                                                    sampling_freq=self.sampling_freq)
#     
#     def check_for_sound(self, time_and_data):
#         """ Abstract. """
#         
# class SoundDetectorSimple(SoundDetectorBase):
#     """ """
#     def __init__(self, sampling_freq=384000, window_size=1024, debug=False):
#         """ """
#         super(SoundDetectorSimple, self).__init__(sampling_freq, window_size, debug)
#         #
#         self.window_size = 2048
#         self.jump_size = 2048
#         self.blackmanharris_window = scipy.signal.blackmanharris(self.window_size)        
#         # Max db value in window. dbFS = db full scale. Half spectrum used.
#         self.blackmanharris_dbfs_max = np.sum(self.blackmanharris_window) / 2 
#         self.freq_bins_hz = np.arange((self.window_size / 2) + 1) / (self.window_size / 384000) # self_sampling_frequency)
#     
#     def check_for_sound(self, time_and_data):
#         """ This is the old algorithm used during 2017. """
#         _rec_time, raw_data = time_and_data
#         #
#         data_int16 = np.fromstring(raw_data, dtype=np.int16) # To ndarray.
#         # self._work_buffer = np.concatenate([self._work_buffer, data_int16])
#         self._work_buffer = data_int16
#         #
#         while len(self._work_buffer) >= self.window_size:
#             # Get frame of window size.
#             data_frame = self._work_buffer[:self.window_size] # Copy frame.
#             self._work_buffer = self._work_buffer[self.jump_size:] # Cut the first jumped size.            
#             # Transform to intervall -1 to 1 and apply window function.
#             signal = data_frame / 32768.0 * self.blackmanharris_window
#             # From time domain to frequeny domain.
#             spectrum = np.fft.rfft(signal)
#             # High pass filter. Unit Hz. Cut below 15 kHz.
#             spectrum[ self.freq_bins_hz < 15000.0 ] = 0.000000001 # log10 does not like zero.
#             # Convert spectrum to dBFS (bin values related to maximal possible value).
#             dbfs_spectrum = 20 * np.log10(np.abs(spectrum) / self.blackmanharris_dbfs_max)
#             # Find peak and dBFS value for the peak.
#             bin_peak_index = dbfs_spectrum.argmax()
#             peak_db = dbfs_spectrum[bin_peak_index]
#             # Treshold.
#             if peak_db > -50:
#                 peak_frequency_hz = bin_peak_index * 384000 / self.window_size
#                 ###self._logger.debug('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
#                 if self.debug:
#                     print('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
#                 #
#                 return True
#         #
#         if self.debug:
#             print('DEBUG: Silent.')
#         #
#         return False
#         
# class SoundDetector(SoundDetectorBase):
#     """ """
#     def __init__(self, sampling_freq=384000):
#         """ """
#         super(SoundDetector, self).__init__(sampling_freq)
# 
#     def check_for_sound(self, time_and_data):
#         """ """
#         
#         test_time = time.time()
#         
#         _rec_time, raw_data = time_and_data
#         
#         time_filter_low_limit_hz = 15000
#         time_filter_high_limit_hz = None
#         scanning_results_dir = '/home/arnold/Desktop/WURB_REC_TEST'
#         scanning_results_file_name = 'detected_peks'
# 
#         # localmax_noise_threshold_factor = 1.2
#         localmax_noise_threshold_factor = 3.0
#         
#         localmax_jump_factor = 1000
#         localmax_frame_length = 1024
#         freq_jump_factor = 1000
#         freq_filter_low_hz = 15000
#         freq_threshold_dbfs = -50.0
#         freq_threshold_below_peak_db = 20.0
#         freq_max_frames_to_check = 200
#         freq_max_silent_slots = 8
#         samp_width = 2
#         self.debug=True
# 
#         
#         # Prepare output file for metrics. Create on demand.
#         metrics_file_name = pathlib.Path(scanning_results_file_name).stem + '_Metrics.txt'
#         out_header = self.spectrum_util.chirp_metrics_header()
#         out_file = None
#         # Read file.
#         checked_peaks_counter = 0
#         found_peak_counter = 0
#         acc_checked_peaks_counter = 0
#         acc_found_peak_counter = 0
#         
#         # Iterate over buffers.
#         if len(raw_data) > 0:
#             
#             signal = librosa.util.buf_to_float(raw_data, n_bytes=samp_width)
#             
#             # Get noise level for 1 sec buffer.
#             signal_noise_level = self.signal_util.noise_level(signal)
#             signal_noise_level_db = self.signal_util.noise_level_in_db(signal)
#             #
#             signal_filtered = self.signal_util.butterworth_filter(signal, 
#                                                          low_freq_hz=time_filter_low_limit_hz,
#                                                          high_freq_hz=time_filter_high_limit_hz)
#             # Get noise level for 1 sec buffer after filtering.
#             noise_level = self.signal_util.noise_level(signal_filtered)
#             noise_level_db = self.signal_util.noise_level_in_db(signal_filtered)
#             if self.debug:
#                 print('Noise level (before filter):', np.round(noise_level, 5), 
#                       '(', np.round(signal_noise_level, 5), ')', 
#                       ' Noise (db):', np.round(noise_level_db, 2), 
#                       '(', np.round(signal_noise_level_db, 5), ')'
#                       )
#             # Find peaks in time domain.
#             peaks = self.signal_util.find_localmax(signal=signal_filtered,
#                                               noise_threshold=noise_level * localmax_noise_threshold_factor, 
#                                               jump=int(self.sampling_freq/localmax_jump_factor), 
#                                               frame_length=localmax_frame_length) # Window size.
# 
#             checked_peaks_counter = len(peaks)
#             acc_checked_peaks_counter += len(peaks)
#             found_peak_counter = 0
#             
#             for peak_position in peaks:
#     
#                 # Extract metrics.
#                 result = self.spectrum_util.chirp_metrics(
#                                             signal=signal_filtered, 
#                                             peak_position=peak_position, 
#                                             jump_factor=freq_jump_factor, 
#                                             high_pass_filter_freq_hz=freq_filter_low_hz, 
#                                             threshold_dbfs = freq_threshold_dbfs, 
#                                             threshold_dbfs_below_peak = freq_threshold_below_peak_db, 
#                                             max_frames_to_check=freq_max_frames_to_check, 
#                                             max_silent_slots=freq_max_silent_slots, 
#                                             debug=False)
# 
#                 if result is False:
#                     continue # 
#                 else:
#                     result_dict = dict(zip(out_header, result))
#                     ## out_row = [result_dict.get(x, '') for x in out_header]
#                     # Add buffer steps to peak_signal_index, start_signal_index and end_signal_index.
#                     out_row = []
#                     for key in out_header:
#                         if '_signal_index' in key:
#                             # Adjust index if more than one buffer was read.
#                             index = int(result_dict.get(key, 0))
# ###                            index += buffer_number * signal_util.sampling_freq
#                             out_row.append(index)
#                         else:
#                             out_row.append(result_dict.get(key, ''))
#                     # Write to file.
#                     if out_file is None:
#                         ###out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('w')
#                         out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('a')
#                         out_file.write('\t'.join(map(str, out_header)) + '\n')# Read until end of file.
#                     #
#                     out_file.write('\t'.join(map(str, out_row)) + '\n')
#                     #
#                     found_peak_counter += 1
#                     acc_found_peak_counter += 1
# 
#             if self.debug:
#                 print('Buffer: Detected peak counter: ', str(found_peak_counter),
#                       '  of ', checked_peaks_counter, ' checked peaks.') 
#             
#         # Done.
#         if self.debug:
#             print('Summary: Detected peak counter: ', str(acc_found_peak_counter),
#                   '  of ', acc_checked_peaks_counter, ' checked peaks.') 
# 
#         if out_file is None:
#             print('\n', 'Warning: No detected peaks found. No metrics produced.', '\n') 
#         else: 
#             out_file.close()
# 
# 
#         print('DEBUG: Sound analysis time: ', time.time() - test_time)
# 
# 
#         if acc_found_peak_counter > 0:
#             sound_detected = True
#         else:
#             sound_detected = False
#         #
#         if sound_detected:
# #             peak_frequency_hz = bin_peak_index * 384000 / self_window_size
# #             self._logger.debug('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
# #             print('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
#             return True
#         #
#         print('DEBUG: Silent.')
#         return False
#     
#     
# # class SoundDetector(SoundDetectorBase):
# #     """ """
# #     def __init__(self):
# #         """ """
# #         
# # 
# #     def check_for_sound(self, time_and_data):
# #         """ """
# #         
# #         test_time = time.time()
# #         
# #         _rec_time, raw_data = time_and_data
# #         
# #         freq_window_size = 1024
# #         sampling_freq = 384000
# #         time_filter_low_limit_hz = 15000
# #         time_filter_high_limit_hz = None
# #         scanning_results_dir = '/home/arnold/Desktop/WURB_REC_TEST'
# #         scanning_results_file_name = 'detected_peks'
# # 
# #         # localmax_noise_threshold_factor = 1.2
# #         localmax_noise_threshold_factor = 3.0
# #         
# #         localmax_jump_factor = 1000
# #         localmax_frame_length = 1024
# #         freq_jump_factor = 1000
# #         freq_filter_low_hz = 15000
# #         freq_threshold_dbfs = -50.0
# #         freq_threshold_below_peak_db = 20.0
# #         freq_max_frames_to_check = 200
# #         freq_max_silent_slots = 8
# #         samp_width = 2
# #         self.debug=True
# # 
# #         # Create dsp4bats utils.
# #         signal_util = wurb_core.SignalUtil(sampling_freq)
# #         spectrum_util = wurb_core.DbfsSpectrumUtil(window_size=freq_window_size,
# #                                                    window_function='kaiser',
# #                                                    kaiser_beta=14,
# #                                                    sampling_freq=sampling_freq)
# #         
# #         # Prepare output file for metrics. Create on demand.
# #         metrics_file_name = pathlib.Path(scanning_results_file_name).stem + '_Metrics.txt'
# #         out_header = spectrum_util.chirp_metrics_header()
# #         out_file = None
# #         # Read file.
# #         checked_peaks_counter = 0
# #         found_peak_counter = 0
# #         acc_checked_peaks_counter = 0
# #         acc_found_peak_counter = 0
# #         
# #         # Iterate over buffers.
# #         if len(raw_data) > 0:
# #             
# #             signal = librosa.util.buf_to_float(raw_data, n_bytes=samp_width)
# #             
# #             # Get noise level for 1 sec buffer.
# #             signal_noise_level = signal_util.noise_level(signal)
# #             signal_noise_level_db = signal_util.noise_level_in_db(signal)
# #             #
# #             signal_filtered = signal_util.butterworth_filter(signal, 
# #                                                          low_freq_hz=time_filter_low_limit_hz,
# #                                                          high_freq_hz=time_filter_high_limit_hz)
# #             # Get noise level for 1 sec buffer after filtering.
# #             noise_level = signal_util.noise_level(signal_filtered)
# #             noise_level_db = signal_util.noise_level_in_db(signal_filtered)
# #             if self.debug:
# #                 print('Noise level (before filter):', np.round(noise_level, 5), 
# #                       '(', np.round(signal_noise_level, 5), ')', 
# #                       ' Noise (db):', np.round(noise_level_db, 2), 
# #                       '(', np.round(signal_noise_level_db, 5), ')'
# #                       )
# #             # Find peaks in time domain.
# #             peaks = signal_util.find_localmax(signal=signal_filtered,
# #                                               noise_threshold=noise_level * localmax_noise_threshold_factor, 
# #                                               jump=int(sampling_freq/localmax_jump_factor), 
# #                                               frame_length=localmax_frame_length) # Window size.
# # 
# #             checked_peaks_counter = len(peaks)
# #             acc_checked_peaks_counter += len(peaks)
# #             found_peak_counter = 0
# #             
# #             for peak_position in peaks:
# #     
# #                 # Extract metrics.
# #                 result = spectrum_util.chirp_metrics(
# #                                             signal=signal_filtered, 
# #                                             peak_position=peak_position, 
# #                                             jump_factor=freq_jump_factor, 
# #                                             high_pass_filter_freq_hz=freq_filter_low_hz, 
# #                                             threshold_dbfs = freq_threshold_dbfs, 
# #                                             threshold_dbfs_below_peak = freq_threshold_below_peak_db, 
# #                                             max_frames_to_check=freq_max_frames_to_check, 
# #                                             max_silent_slots=freq_max_silent_slots, 
# #                                             debug=False)
# # 
# #                 if result is False:
# #                     continue # 
# #                 else:
# #                     result_dict = dict(zip(out_header, result))
# #                     ## out_row = [result_dict.get(x, '') for x in out_header]
# #                     # Add buffer steps to peak_signal_index, start_signal_index and end_signal_index.
# #                     out_row = []
# #                     for key in out_header:
# #                         if '_signal_index' in key:
# #                             # Adjust index if more than one buffer was read.
# #                             index = int(result_dict.get(key, 0))
# # ###                            index += buffer_number * signal_util.sampling_freq
# #                             out_row.append(index)
# #                         else:
# #                             out_row.append(result_dict.get(key, ''))
# #                     # Write to file.
# #                     if out_file is None:
# #                         ###out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('w')
# #                         out_file = pathlib.Path(scanning_results_dir, metrics_file_name).open('a')
# #                         out_file.write('\t'.join(map(str, out_header)) + '\n')# Read until end of file.
# #                     #
# #                     out_file.write('\t'.join(map(str, out_row)) + '\n')
# #                     #
# #                     found_peak_counter += 1
# #                     acc_found_peak_counter += 1
# # 
# #             if self.debug:
# #                 print('Buffer: Detected peak counter: ', str(found_peak_counter),
# #                       '  of ', checked_peaks_counter, ' checked peaks.') 
# #             
# #         # Done.
# #         if self.debug:
# #             print('Summary: Detected peak counter: ', str(acc_found_peak_counter),
# #                   '  of ', acc_checked_peaks_counter, ' checked peaks.') 
# # 
# #         if out_file is None:
# #             print('\n', 'Warning: No detected peaks found. No metrics produced.', '\n') 
# #         else: 
# #             out_file.close()
# # 
# # 
# #         print('DEBUG: Sound analysis time: ', time.time() - test_time)
# # 
# # 
# #         if acc_found_peak_counter > 0:
# #             sound_detected = True
# #         else:
# #             sound_detected = False
# #         #
# #         if sound_detected:
# # #             peak_frequency_hz = bin_peak_index * 384000 / self_window_size
# # #             self._logger.debug('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
# # #             print('Peak freq hz: '+ str(peak_frequency_hz) + '   dBFS: ' + str(peak_db))
# #             return True
# #         #
# #         print('DEBUG: Silent.')
# #         return False
    

# === TEST ===    
if __name__ == "__main__":
    """ """
    import sys
    path = ".."
    sys.path.append(path)
    #
    settings = wurb_core.WurbSettings()
    (desc, default, dev) = wurb_core.wurb_recorder.default_settings()
    settings.set_default_values(desc, default, dev)
    (desc, default, dev) = wurb_core.wurb_gps_reader.default_settings()
    settings.set_default_values(desc, default, dev)
    #
    manager = wurb_core.WurbRecorder().setup_sound_manager()
    #
    print('TEST - started.')
    manager.start_streaming()
    time.sleep(15.5)
    manager.stop_streaming()
    print('TEST - ended.')



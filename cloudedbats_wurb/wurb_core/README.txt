
CloudedBats - WURB, Wireless Ultrasonic Recorder for Bats.

Project page: https://github.com/cloudedbats/cloudedbats_wurb
Main project page: http://cloudedbats.org


Introduction
------------

The CloudedBats WURB is a recording unit for bats, based on open and free software 
and standard hardware components. See the project page for more info. 

When using the WURB in the default settings mode, then the recorded sound files, 
log files and settings files are stored on the USB memory connected to the WURB.


Sound files
-----------

Sound files are stored as wave (".wav") files in a directory called "wurb1_rec"
when using the default settings. Files are named like this example:
"WURB1_20180516T224540+0200_N57.6626E12.6393_FS384.wav"


Log files
---------

Log files can be found in the directory "cloudedbats_wurb/log_files". 
The last file is called "wurb_log.txt". Up to 10 older log files are stored, and 
they are named "wurb_log.txt.1", "wurb_log.txt.2", etc.


Settings/config
---------------

Settings files for configurations made by the user can be found in the directory
"cloudedbats_wurb/settings". 
The files "user_settings_DEFAULT.txt" and "user_settings_LAST_USED.txt" are 
automatically generated at each startup. 
Default settings are overridden by creating a file named "user_settings.txt" in 
the same directory containing the rows that should be modified. 
The new settings file will be stored in the WURB and used at next startup, even 
if the user are using another USB memory without the "user_settings.txt" file.
Some usage example can be found in the user manual (see the project page). 


Settings for the sound recorder
-------------------------------

- "rec_directory_path" (default: "/media/usb0/wurb1_rec")
  
  The first part, "/media/usb0" tells the WURB that the first connected USB 
  memory should be used. The part "wurb1_rec" can be modified to identify
  different detectors or survey location.
  
- "rec_filename_prefix" (default: "WURB1")
  
  The first part of each filename. Change tis to make it easier to sort files.

- "rec_format" (default: "TE")
  
  Use "TE" for Time Expansion or "FS" for Full Scan. The same amount of data
  is stored when using FS, but the time scale will be increased by 10 and the 
  frequency decreased by 10.

- "rec_max_length_s" (default: "20")
  
  The length of a recording depends on when sound is detected. This parameter
  defines when a new file should be created. No sound frames are lost when 
  switching to a new file.

- "rec_buffers_s" (default: "2.0")
  
  Defines the buffer size to be used before and after a detected sound. 
  The recording will continue if sound is detected again within this 
  buffer size multiplied by two.
  
- "rec_sampling_freq_khz" (default: "384")
  
  Set the sampling frequency for the microphone. For example 192, 256, 
  384 or 500, but it depends on the used microphone.

- "rec_microphone_type" (default: "USB")
  
  The value "USB" should always be used with one exception. This is
  for the Pettersson M500 microphone running at 500 kHz. Then "M500" 
  should be used. 

- "rec_part_of_device_name" (default: "Pettersson")
  
  Detected input devices are logged at startup in the "wurb_log.txt" file.
  Select a part of the devise name that makes it unique. "UltraMic" will
  work for Dodotronic microphones (at least for the 192 kHz version.)  

- "rec_device_index" (default: "0")
  
  Can be used as an alternative for the "rec_part_of_device_name" parameter.


Settings for the scheduler
--------------------------

- "scheduler_use_gps" (default: "Y")
  
  Use GPS for time and position.

- "scheduler_wait_for_gps" (default: "Y")
  
  If "Y", then the scheduler will wait until the GPS is ready. 

- "default_latitude" (default: "0.0")
  
  Latitude to be used if GPS is not used. Needed to calculate sunset, sunrise, etc.
  Use negative numbers for the southern hemisphere. 

- "default_longitude" (default: "0.0")
  
  Longitude to be used if GPS is not used. Needed to calculate sunset, sunrise, etc.
  Use negative numbers for longitude west.
  
- "scheduler_event"
    Default-1: "scheduler_rec_on/sunset/-10"
    Default-2: "scheduler_rec_off/sunrise/+10"
    Default-3: "scheduler_rpi_shutdown/sunrise/+15"
  
  Scheduler events consists of three parts:
    1. "command to be executed". Should be defined as a valid event in the stat 
       machine in the python module "wurb_applicatio.py".
    2. "time event". "sunset", "sunrise", "dusk" and "dawn" are valid, as well as 
       timestamps on the format "hh:mm", for example "02:30".
    3. "adjustment in minutes". 
    Add as many scheduler events as you want.


Settings for the GPS reader
---------------------------

- "timezone" (default: "UTC")

  Time zones should be declared by using the "tx database" format, for example 
  "Europe/Stockholm". More information here:
  https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

- "set_time_from_gps" (default: "Y")

  Use the GPS time to set the Raspberry Pi time. This is not needed if the 
  Raspberry Pi always is connected to the internet.


Settings for sound detection algorithms
---------------------------------------

- "sound_detector" (default: "Simple")

  Available detector algorithms at the moment are:
  - "None: Records everything, silence included.
  - "Simple: Starts when sound above a specified frequency is detected.
  Check the file "user_settings_Last_used.txt" for some more alternatives for 
  fine-tuning.



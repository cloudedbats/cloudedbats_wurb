# CloudedBats WURB - User manual - version 2018.05.*

The CloudedBats WURB, Wireless Ultrasonic Recorder for Bats, is a recording unit for bats, based on open and free software and standard hardware components. This user manual is valid for the software released in May 2018. 

## Basic usage with default configuration

This instruction can be used if you have an already prepared WURB with default settings, and want to run it as a stand-alone recorder or during transects.

1. Check hardware components. A standard WURB consists of:

    - A Raspberry Pi computer. 
    - Micro-SD card with the Raspbian Light operating system (Linux) and the CloudedBats WURB software.
    - Pettersson M500-384 Ultrasonic microphone. USB connected and running at 384 kHz.
    - GPS with USB connection.
    - USB memory for recorded sound files. Also used for user settings and log files.
    - Buttons or switches for control like rec-on, rec-off, rec-auto-mode, and computer shutdown.
    - Alternatively, a USB connected computer mouse, preferably a wireless one, can be used instead for rec-on, rec-off, and computer shutdown.
    - Power supply connected via the Micro-USB connection. PowerBanks works well for single night sessions. Mobile chargers with Micro-USB can also be used. Power consumption depends mainly on the Raspberry Pi model used. About 1A at 5V (=5W) is continuously used with peaks at about 2A.

2. Turn power on. This is done by connecting the Micro-USB cable or press the power on/off button on the PowerBank.

3. Wait for the GPS to start tracking satellites. Time and position is then set and the WURB calculates times for sunset, sunrise, dawn and dusk automatically.

4. Based on the default settings, the WURB will automatically start to record 10 minutes before sunset and stop 10 minutes after sunrise. To save batteries the default settings is set to shutdown the WURB 15 minutes after sunrise.

5. Recordings will start 2 seconds before a sound is detected and continue 2 sec after. If the recording will last for more than 20 seconds, a new file will be started. Each filename will contain start time and position in latitude/longitude. Default settings for sound detection are any sound above 15 kHz and above -50 dBFS. 

6. When finished, then shut down the WURB. This can be done either by turn the switch to "RPi-off" or press the left and right button simultaneous for 5 seconds if a computer mouse is used. Wait until the Raspberry Pi has finished, and then disconnect power by removing the Micro-USB cable, or by pressing the PowerBank on/off button. 

7. Move the USB memory to a computer and check the files.

8. Log files can be found in the USB memory in the directory "cloudedbats_wurb/log_files". The last file is called "wurb_log.txt". Up to 10 older log files are stored and they are named "wurb_log.txt.1", "wurb_log.txt.2", etc.

9. Settings files can be found in the directory "cloudedbats_wurb/settings". The files "user_settings_DEFAULT.txt" and "user_settings_LAST_USED.txt" are automatically generated at each startup. If you want to replace some settings, then create a file called "user_settings.txt" in the same directory containing the rows that should be modified. That file will be stored in the WURB and used at next startup, even if you are using another USB memory without the "user_settings.txt" file.

10. File names for sound files contains the following parts (no hidden metadata in the sound file):

    - Prefix. From the "user_settings.txt" file.
    - Date and time. In ISO 8601 format, including UTC offset.
    - Current position as latitude/longitude. In the decimal-degree format.
    - Recording type. FS, Full Scan, or TE, Time Expanded, combined with sampling frequency in kHz. 

    Example: "WURB1_20180516T224540+0200_N57.6626E12.6393_FS384.wav"

11. Check the recordings with any analysis software that can read wave files ("*.wav"). 
Sonic Visualiser (https://sonicvisualiser.org) is a free software that runs on Windows, MacOS and Linux.

12. Since the Raspberry Pi is equipped with WiFi it is possible to fetch sound files and check log files, etc. during an ongoing recording session. By default the WURB will connect to a password-protected WiFi network called "cloudedbats" (pw: "plecotusauritus") or an open WiFi network call "cloudedbats-wifi", if available. Read the software installation instruction if the WURB should accept other networks. Connection to Internet via a hub and Ethernet is also an option. FileZilla is a great tool for accessing files on a remote computer.  Log in as "pi@wurb1.local" with password "cloudedbats" if SSH is used from a terminal window.

## User settings

User settings can be modified by editing a text file located on the USB memory, as described in step 9 above. Some more detailed information about available options can be found here, as well as in the "cloudedbats_wurb" directory on the USB memory:
https://github.com/cloudedbats/cloudedbats_wurb/blob/master/cloudedbats_wurb/wurb_core/README.txt 

Here are some examples to be used in the "user_settings.txt" file in the "cloudedbats_wurb/settings" directory:

Basic setup:

    rec_filename_prefix: WURB1
    rec_directory_path: /media/usb0/wurb1_rec
    rec_format: FS  
    rec_max_length_s: 20
    rec_buffers_s: 2.0
    default_latitude: 56.78
    default_longitude: 12.34
    timezone: Europe/Stockholm

When using Pettersson M500-384 (default):

    rec_microphone_type: USB
    rec_sampling_freq_khz: 384
    rec_part_of_device_name: Pettersson

When using Pettersson M500:

    rec_microphone_type: M500
    rec_sampling_freq_khz: 500

When using Dodotronic 192 kHz:

    rec_microphone_type: USB
    rec_sampling_freq_khz: 192
    rec_part_of_device_name: UltraMic

If no GPS is used:

    scheduler_use_gps: N
    scheduler_wait_for_gps: N
    set_time_from_gps: N

Example settings for the scheduler:

    scheduler_event: scheduler_rec_on/sunset/-10
    scheduler_event: scheduler_rec_off/23:00/+0
    scheduler_event: scheduler_rec_on/01:00/+0
    scheduler_event: scheduler_rec_off/sunrise/+10
    scheduler_event: scheduler_rpi_shutdown/sunrise/+15

## WURB control via switches or buttons 

The WURB can be controlled via some buttons or switches connected to the GPIO-pins on the Raspberry Pi. 

They are implemented as pull-down resistors, and uses the Raspberry Pi built in 10 kOhm resistors. That means that it is ok to connect a GPIO-pin directly to ground without any additional resistors, but it works with shorter cables only. Some modifications in the WURB software are needed if longer cables should be used. Be sure that you don't connect the 5 V or 3.3 V GPIO pins to ground, that will destroy the unit. Search for a 40 pins GPIO layout schema before you start. 

Used connection are: 

- Raspberry Pi shutdown: Connect GPIO pin #40 (aka. GPIO 21) to ground. 
- Raspberry Pi WiFi off: Connect GPIO pin #36 (aka. GPIO 16) to ground.
- Recording on: Connect GPIO pin #37 (aka. GPIO 26) to ground.
- Recording off: Connect GPIO pin #38 (aka. GPIO 20) to ground.
- Auto mode, controlled by scheduler: Nothing connected.
- Suitable ground GPIO pins are #39, #34 and #30.

A recommended setup is to use two three-way switches of the type on-off-on. Connect the middle connection on the switch to ground and the other as described above. Recommended labels for the two switches: "RPi: off - on - wifi-off" and "Rec: off - auto - on".

If nothing is connected, then the WURB will start up and run in "Auto mode". This will be enough in many situations, but you still need to implement the "Raspberry Pi shutdown" functionality. Simple solutions are a press button, or similar, that connects pin #40 with #39 for some seconds. 

## WURB control via a computer mouse

If you don't like soldering, an alternative is to use an USB connected computer mouse.
Available commands are:

- Press left button for 2 sec: Recording on.  
- Press right button for 2 sec: Recording off.  
- Press middle button (the scroll wheel) for 2 sec: Auto mode, controlled by scheduler.  
- Press left and right button simultaneously for 5 sec: Raspberry Pi shutdown.

## CloudedBats - links

- CloudedBats main project page: http://cloudedbats.org 

- WURB page and code repository: https://github.com/cloudedbats/cloudedbats_wurb 

- WURB releases: https://github.com/cloudedbats/cloudedbats_wurb/releases 

- Issues: https://github.com/cloudedbats/cloudedbats/issues 

- Feedback: info@cloudedbats.org 

# CloudedBats WURB - User manual - version 2018.05.*

The CloudedBats WURB, Wireless Ultrasonic Recorder for Bats, is a recording unit based on open and free software and standard hardware components. This user manual is valid for the software released in May 2018. 

## Basic usage with default configuration

This instruction can be used if you have an already prepared WURB with default settings, and want to run it as a stand-alone recorder or during transects.

1. Check hardware components. A standard WURB consists of:

    - A Raspberry Pi computer. 
    - Micro-SD card with the Raspbian Light operating system (Linux) and the CloudedBats WURB software.
    - Pettersson M500-384 Ultrasonic microphone. USB connected and running at 384 kHz.
    - GPS with USB connection.
    - USB memory for recorded sound files. Also used for settings and log files.
    - Buttons or switches for control like rec-on, rec-off, rec-auto-mode, and computer shutdown.
    - Alternatively a USB connected computer mouse, preferably a wireless one, can be used instead for rec-on, rec-off, and computer shutdown.
    - Power supply connected via the Micro-USB connection. PowerBanks works well for single night sessions. Mobile chargers with Micro-USB can also be used. 

2. Turn power on. This is done by connecting the Micro-USB cable or press the power on/off button on the PowerBank.

3. Wait for the GPS to start tracking satellites. Time and position is then set and the WURB calculates times for sunset, sunrise, dawn and dusk automatically.

4. Based on the default settings the WURB will automatically start to record 10 minutes before sunset and stop 10 minutes after sunrise. To save batteries the default settings is set to shutdown the WURB 15 minutes after sunrise.

5. Recordings will start 2 seconds before a sound is detected and continue 2 sec after. If the recording will last for more than 20 seconds, a new file will be started. Each filename will contain start time and position in latitude/longitude. Default settings for sound detection are any sound above 15 kHz and above -50 dBFS. 

6. When finished, then shut down the WURB. This can be done either by turn the switch to "RPi-off" or press the left and right button simultaneous for 5 seconds if a computer mouse is used. Wait until the Raspberry Pi has finished, and then disconnect power by removing the Micro-USB cable, or by pressing the PowerBank on/off button. 

7. Move the USB memory to a computer and check the files.

8. Log files can be found in the USB memory in the directory "cloudedbats_wurb/log_files". The last file is called "wurb_log.txt". Up to 10 older log files are stored and they are named "wurb_log.txt.1", "wurb_log.txt.2", etc.

9. Settings files can be found in the directory "cloudedbats_wurb/settings". The files "user_settings_DEFAULT.txt" and "user_settings_LAST_USED.txt" are automatically generated at each startup. If you want to replace some settings, then create a file called "user_settings.txt" in the same directory containing the rows that should be modified. That file will be stored in the WURB and used at next startup, even if you are using another USB memory without the "user_settings.txt" file.

10. File names for sound files contains the following parts:

    - Prefix. From the "user_settings.txt" file.
    - Date and time. In ISO 8601 format, including UTC offset.
    - Position as latitude/longitude. In the decimal-degree format.
    - Recording type. FS, Full Scan, or TE, Time Expanded, combined with sampling frequency in kHz. 

    Example: "WURB1_20180516T224540+0200_N57.6626E12.6393_FS384.wav"

11. Check the recordings with any analysis software that can read wave files ("*.wav"). 
Sonic Visualiser (https://sonicvisualiser.org) is a free software that runs on Windows, Macos and Linux.

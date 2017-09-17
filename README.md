# WURB - Wireless Ultrasonic Recorder for Bats

This is a part of CloudedBats: http://cloudedbats.org
and contains the source code repository for the CloudedBats recording unit.

CloudedBats WURB is a bat detector for passive monitoring. It can be use either as a stand alone unit or can be used with internet connection.

#### Parts needed to build your own recording unit

![WURB parts needed](doc/cloudedbats_wurb_parts.jpg?raw=true "WURB - Parts needed to build your own recording unit.")
Image: CloudedBats.org / [CC-BY](https://creativecommons.org/licenses/by/3.0/)

### Functional features

- Support for full spectrum and time expanded recordings.
- Support for continuous recordings at high speed.
- Sound detection algorithm to avoid empty files. Configurable buffer sizes before and after detected sound.
- GPS support.
- Scheduler for start and stop related to timestamps, sunset, dawn, etc. calculated from GPS time and position.
- Manually controlled via switches or wireless computer mouse (for remote control).
- Highly configurable via text files for standalone use.
- Configurable via CloudedBats web server (under development).
- Can receive commands and report results to a CloudedBats web server when connected to internet (under development).
- Post processing of recorded sound files to extract metrics for visualisation on the web (under development).
- Log files for performed actions and errors. 

### Other characteristics

- The CloudedBats software is developed as open source software. Free to use.
- The software is developed on top of modern open source code libraries and frameworks.
- Inexpensive hardware can be used. You need an ultrasonic microphone, a Raspberry Pi computer (35 € + VAT) and some common USB devices for storage, GPS, etc. 
- Different options for storing wave files are available. Both USB memory and portable USB hard disks can be used.
- If the network is setup properly file transfer can be done via the Internet. For example, by using SFTP with FileZilla.
- The Raspberry Pi computer offers many options for enhancements and software developers can easily build other types of systems by using parts of the CloudedBats software. An example is to use the infrared camera module NoIR that can be used for rooster monitoring and visual species identification.

### Drawbacks

- Higher power consumption compared to other passive monitoring systems.
- You must put together the system yourself and find a suitable plastic food box if used outdoors.
- I can only provide limited support. However, most software developers using Linux / Python should easily understand the code and system setup.



### The ultrasonic microphone

The quality of the recordings is entirely determined by the quality of the microphone. When it comes to automatic analysis where recordings are to be compared to reference recordings, it is important that the microphones have comparable characteristics.

to be continued...


### How to build your own WURB

Hardware parts:

- ...

The CloudedBats software:

- Installation instruction: https://github.com/cloudedbats/cloudedbats_wurb/blob/master/doc/software_installation_cloudedbats-wurb.md

### Issues

All issues are handle at the main page for CloudedBats: https://github.com/cloudedbats/cloudedbats/issues

## Contact

Arnold Andreasson, Sweden.

info@cloudedbats.org

# WURB - Wireless Ultrasonic Recorder for Bats

**Note: This version of the WURB detector has been replaced by a completely rewritten new version.
The new version can be found here: https://github.com/cloudedbats/cloudedbats_wurb_2020**

**This version will not be removed since it is a stable version and maybe still have users.** 

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
- Manually controlled via switches or a computer mouse.
- Configurable via text files.
- Log files for performed actions and errors. 

### Other characteristics

- The CloudedBats software is developed as open source software. Free to use under the terms of the MIT license.
- The software is developed on top of modern open source code libraries and frameworks.
- Inexpensive hardware can be used. You need an ultrasonic microphone, a Raspberry Pi computer (35 € + VAT) and some common USB devices for storage, GPS, etc. 
- Different options for storing wave files are available. Both USB memory and portable USB hard disks can be used.
- If the network is setup properly file transfer can be done via the Internet. For example, by using FileZilla.
- The Raspberry Pi computer offers many options for enhancements and software developers can easily build other types of systems by using parts of the CloudedBats software. An example is to use the infrared camera module NoIR that can be used for rooster monitoring and visual species identification.

### Drawbacks

- Higher power consumption compared to other passive monitoring systems.
- You must put together the system yourself and find a suitable plastic food box if used outdoors.
- I can only provide limited support. However, most software developers using Linux / Python should easily understand the code and system setup.

### User documentation

- User manual: https://github.com/cloudedbats/cloudedbats_wurb/blob/master/doc/cloudedbats_wurb_user_manual.md

- Software installation guide: https://github.com/cloudedbats/cloudedbats_wurb/blob/master/doc/cloudedbats_wurb_software_installation.md

### Latest stable release

Release: https://github.com/cloudedbats/cloudedbats_wurb/releases/latest

Issues (for the whole CloudedBats project): https://github.com/cloudedbats/cloudedbats/issues 

## Contact

Arnold Andreasson, Sweden.

info@cloudedbats.org

# Software installation - WURB 
 
This guide describes how to install the CloudedBats-WURB, Wireless Ultrasonic Recorder for Bats, on a Raspberry Pi. The user of this guide should be familiar with the Linux operating system and the Raspberry Pi computer. If not, please contact me to get a link to an already prepared disk image file for download. 

The installation process is the same for Raspberry Pi 4 B (not tested), Raspberry Pi 3 B and Raspberry Pi Zero W. It is possible to move the Micro-SD card between the models after the installation.

Some comments on the new Raspbian Buster release: Raspbian Buster is base on a pre-release of the new Debian Buster release. There was a problem with the automatic detection of USB memory sticks. I did manage to set it up in "the old style" and will try the "new style" when more info is available for how to do it. I used the "2019-06-20-raspbian-buster-lite" version for this guide. 

### Download Raspbian Buster Light.

Raspbian Buster Light is based on Debian version 10. Raspbian Buster is required if you want to use the new Raspberry Pi 4. The commands used when running Raspbian in terminal mode are very similar to Ubuntu commands since both are based on Debian operating system.
 
Download page:
 
    https://www.raspberrypi.org/downloads/raspbian/
 
Follow the instructions and install the Raspbian Buster Light image file (.img) on a Micro-SD card. The graphical SD card writing tool Etcher (https://www.balena.io/etcher/) is recommended. If you want to format the SD card back later for normal use, then the SD Memory Card Formatter (https://www.sdcard.org/downloads/formatter/index.html) is recommended because other formatters may result in lower read/write performance.
 
### SSH - activate
 
It is possible to connect a monitor/TV via HDMI and keyboard/mouse via USB to the Raspberry Pi and perform the installation. Personally I prefer to use ssh from a terminal window on another computer in the same local network, and this guide describes that alternative.
 
For security reasons ssh is disabled by default. The easiest way to enable it is to connect the Micro-SD card to a computer and create an empty file named 'ssh'. The Micro-SD card will show up as a volume called "boot". A more detailed description can be found here: https://www.raspberrypi.org/documentation/remote-access/ssh/

### WiFi setup

In the same way as for the SSH activation it is possible to add a "wpa_supplicant.conf" file to the SD card before you move it to the Raspberry Pi. It will then automatically be moved to the right position at the first Raspberry Pi startup.

Create a file with the name "wpa_supplicant.conf" containing a similar content that I use, but for your network. Then move that file to the SD card "boot" volume. The content for my setup:

    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    country=SE
    
    network={
        ssid="cloudedbats"
        psk="plecotusauritus"
    }

**Note**: Must be 'tab', not spaces, for indentation before "ssid" and "psk". This may be a problem if you copy and paste it from a web page.

Alternative 1: If you want to change, or add, it later then just type this command when connected to the Raspberry Pi:

    sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
    
Alternative 2: Another alternative to add WiFi networks is to run "sudo raspi-config" and let that tool do it. More info below.

### Startup the Raspberry Pi

Move the Micro-SD card to the Raspberry Pi and start it. You can either connect an Ethernet cable or use WiFi to connect the Raspberry Pi to your local network. (Alternatively connect a monitor/TV via HDMI and keyboard/mouse directly to the Raspberry Pi. Since this is a "headless" version of Raspbian there will be no graphical user interface on the monitor/TV, only a command line interface.)

Start a terminal window on a computer in the local network. ('raspberrypi.local' works on Mac, I don't know if it is working on Windows. If you are using Windows this page may help: https://desertbot.io/blog/headless-raspberry-pi-3-bplus-ssh-wifi-setup)   
 
    ssh pi@raspberrypi.local
    # Then enter password: raspberry

### Change password.
 
    passwd     
 
For example, change password to 'cloudedbats'.
 
### Basic Raspberry Pi configuration
 
    sudo raspi-config 
 
Change these parts:
 
- Network options - Hostname: wurb1 (for example)
- Network options - Wi-Fi (to add more WiFi networks)
- Localisation Options - Change Timezone: Europe - Stockholm  (for example)
- Advanced Options - Expand Filesystem

### Reboot and login again with the new host name
 
    sudo reboot
 
    (wait until rebooted)
 
    ssh pi@wurb1.local
    pw: cloudedbats
 
### Upgrade Raspbian Buster Light
 
    sudo apt update
    sudo apt upgrade
 
### Install software packages. 
 
    sudo apt install git portaudio19-dev gpsd gpsd-clients usbmount
 
    sudo apt install python3 python3-pip python3-numpy python3-scipy python3-all-dev python3-rpi.gpio
 
    sudo pip3 install pyaudio gps3 python-dateutil pyusb pytz
 
### Config GPS
 
    sudo nano /etc/default/gpsd 
 
Set these values:
 
    START_DAEMON="true"
    USBAUTO="true"
    DEVICES="/dev/ttyUSB0"
    #DEVICES="/dev/ttyACM0"
    GPSD_OPTIONS="-n"
    GPSD_SOCKET="/var/run/gpsd.sock"

**Note**: Some USB connected GPS units uses another communication protocol. When using "GPS/Glonass Ublox-7 (Diymall Vk-172 vk 172)" I had to change DEVICES to "/dev/ttyACM0".

### Config usbmount for automatic handling of USB memory/disk.
 
    sudo nano /etc/usbmount/usbmount.conf
 
Modify to these values:
 
    MOUNTOPTIONS="noexec,nodev,noatime,nodiratime"
    FS_MOUNTOPTIONS="-fstype=vfat,uid=pi,gid=pi,dmask=0000,fmask=0111"

Debian Buster differ from earlier versions and this modification is needed

    sudo nano /lib/systemd/system/systemd-udevd.service

Disable all rows after "TasksMax=infinity" by writing the comment marker # 
at the beginning of each row.

Note: Versions before Raspbian Stretch worked directly. When using Raspbian Stretch you
had to change "MountFlags=slave" to "MountFlags=shared" in the file above.
That does not work in Buster, but it works when disabling the rows described above. 
Maybe not the best solution, but it works. 
More info here: https://github.com/systemd/systemd/issues/11982 

### Time sync from the Internet 

Before Raspbian Stretch this was installed by default. You must set up it yourself if you need it.  

    sudo apt install ntp
    sudo systemctl enable ntp
    sudo timedatectl set-ntp 1

### Special rules for Pettersson M500 (windows version).
 
Pettersson M500-384 is developed for Linux etc., but M500 is for Windows only.
Therefore, when using the M500 microphone under Linux some security rules
must be added to make it possible to use low level USB calls.

Add a new file called "pettersson_m500_batmic.rules".
 
    sudo nano /etc/udev/rules.d/pettersson_m500_batmic.rules
 
Add this line to the file:
 
    SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="pi"
 
### Install the CloudedBats WURB software
 
    cd /home/pi
    mkdir cloudedbats
    cd cloudedbats/
    
    git clone https://github.com/cloudedbats/cloudedbats_wurb.git .

Or to get the latest changes or a specific release (check alternatives in branches and releases):

    git clone -b stable https://github.com/cloudedbats/cloudedbats_wurb.git .
    git clone -b 2017-sept https://github.com/cloudedbats/cloudedbats_wurb.git .
    
To update the CloudedBats-WURB software only, just run a "git pull" command.

### Automatic start for the WURB software at startup
 
    sudo nano /etc/rc.local
 
Add this before "exit 0":
 
    # CloudedBats.
    sudo -u pi python3 /home/pi/cloudedbats/cloudedbats_wurb/wurb_raspberry_pi/control_raspberrypi_by_gpio.py &
    sudo -u pi python3 /home/pi/cloudedbats/cloudedbats_wurb/wurb_main.py &
    # sudo -u pi python3 /home/pi/cloudedbats/cloudedbats_wurb/wurb_main_no_usb.py &
 
### Finished
 
    sudo shutdown -h now
 
### Connect pheripherals.
 
- Disconnect power.
 
- Connect USB memory or disk.
- Connect GPS (optional, but recommended).
- Connect ultrasonic microphone.
- Connect computer mouse (optional).
- Connect switches for Raspberry Pi and Rec. control.
 
- Connect power.
 
### Login and test
 
    ssh pi@wurb1.local
    pw: cloudedbats
 
### Test GPS.
 
    cgps -s
 
### Check log files.
 
    cat /home/pi/cloudedbats/cloudedbats_wurb/wurb_log_files/wurb_log.txt
    cat /home/pi/cloudedbats/cloudedbats_wurb/wurb_log_files/raspberry_pi_gpio_control_log.txt

### USB memory

I you want to check the USB memory stick content during a recording session it is possible to do that over SSH. Another useful alternative is to use FileZilla, or some other similar software, to download wave files during an ongoing recording session. They are located in the "/media/usb0/wurb1_rec" directory when running the detector with the default settings.

    # Show log file.
    cat /media/usb0/cloudedbats_wurb/log_files/wurb_log.txt
    
    # Show currently used settings.
    cat /media/usb0/cloudedbats_wurb/settings/user_settings_LAST_USED.txt 
    
    # List recordings. 
    ls /media/usb0/wurb1_rec

### Running multiple detectors

When this installation is done on one SD card it is possible to clone it. The process is as follows:

* Create a new image file based on the content of the SD card (link to instruction below).
* Compress the image file if you want to share it over internet. If the SD card is 16 GB in size, then the image file will be 16 GB in size. When zipped it will be about 1 GB.
* Decompress (unzip) the file if it was compressed.
* Use Etcher to write the image to a new SD card. I use "TOSHIBA EXCERIA PRO 16 GB, UHS Speed Class 3". Slower cards does also work, but takes much longer due to the lower writing speed.
* Move the SD card to a Raspberry Pi and start it. Connect to it ("ssh pi@wurb1.local") and start the config tool ("sudo raspi-config") and give it a new name, for example "wurb2". Restart and connect with the new name ("ssh pi@wurb2.local").

Now you can set up a cluster of detectors and use WiFi to check their status over ssh and collect recorded files by using FileZilla.

Link to "How to Clone Raspberry Pi SD Card on Windows, Linux and macOS": https://beebom.com/how-clone-raspberry-pi-sd-card-windows-linux-macos/ 





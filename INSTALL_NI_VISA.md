# NI-VISA on CentOS 7
## 0 Operating system
- [CentOS 7](https://www.centos.org/)
- `libusbx` covers the requirement for `libusb-1.0` from `pyserial` 
```linux
sudo yum -y update
sudo yum -y install libusbx-devel
```
## 1 Software installation
- python3
- python3-pip
    - pyusb
    - pyserial
    - PyVISA
- NI-VISA

### 1.1 Install NI-VISA
Download the [NI Linux Device Drivers](http://www.ni.com/download/ni-linux-device-drivers-2018/7664/en/)
- [NI Linux Device Drivers.zip](http://download.ni.com/support/softlib/MasterRepository/NI%20Linux%20Device%20Drivers.zip)

Unpack the zip-file and as sudo-user install
```linux
sudo rpm -i rpm_RHEL7CentOS7.rpm
```
Now one should be able to install NI-VISA and other drivers via the package manager
```linux
yum search ni-visa 
```
Example output (cropped)
```
|
...
|
=====================N/S matched: ni-visa ======================
ni-visa.noarch : NI-VISA (metapackage)
ni-visa-config.x86_64 : Provides utility for configuring NI-VISA settings
|
...
|
ni-visa-passport-enet.x86_64 : Provides support for NI-VISA applications using LXI and other networked devices (TCP/IP, VXI-11, and HiSLIP)
ni-visa-passport-enet-serial.x86_64 : Provides support for NI-VISA applications using NI ENET-Serial devices
ni-visa-passport-gpib.x86_64 : Provides support for NI-VISA GPIB applications
ni-visa-passport-pxi.x86_64 : Provides support for NI-VISA PXI(e)/PCI(e) applications
ni-visa-passport-pxi-dkms.x86_64 : Installs the kernel support for NI-VISA PXI(e)/PCI(e)
ni-visa-passport-remote.x86_64 : Provides support for NI-VISA applications communicating to networked systems running NI-VISA Server
ni-visa-passport-usb.x86_64 : Provides support for NI-VISA USB applications
ni-visa-lxi-discovery.x86_64 : Provides the LXI Discovery Service for discovering LXI-based resources
ni-visa-passport-serial.x86_64 : Enables support for RS-232 and RS-485 serial devices
|
...
|
```
Now you can choose to install the drivers you'll need. 
```linux
sudo yum install -y ni-visa ni-visa-config
```
### 1.2 Install python3.6 on CentOS
[Python3.6 on CentOS 7](https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-centos-7)
```linux
sudo yum -y update
sudo yum -y install yum-utils
sudo yum -y groupinstall development

sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y install python36u python36u-devel

python3.6 -V

sudo yum -y install python36u-pip
```

### 1.3 Install python dependencies

First create a virtual environment
```linux
mkdir ~/virtualenvs
python3.6 -m venv ~/virtualenvs/pyvisa
```
Then activate it. Now you do not have to type `python3.6` any longer; `python`/`python3` is sufficient.
```linux
source ~/virtualenvs/pyvisa/bin/activate
```
Upgrade pip and setuptools, then install the needed packages to be able to communicate with the instruments
```linux
pip install --upgrade pip setuptools
pip install pyserial pyusb PyVISA
```
List all the installed packages in the virtual environment
```linux
pip list
```
Example output:
```linux
Package     Version
----------- -------
pip         19.0.3 
pyserial    3.4    
pyusb       1.0.2  
PyVISA      1.9.1  
setuptools  40.8.0 

```
## 2 Test
### 2.1 NI-VISA
Run visaconf. A GUI should appear where one can add and edit resources.
```linux
visaconf
```
### 2.2 Python environment
If not already activate the virtual environment as shown previously. Then test the pyvisa installation:
```python3
python -m visa info
```
The output should look something like below. What you should notice is the listed Backends; ni should be listed and with a path to `libvisa.so.X.Y.Z`. Below there also is a Backend called py. This is a fairly complete implementation of the VISA standard completely implemented in python. It is available through `pip install PyVISA-py`
```
Machine Details:
   Platform ID:    Linux-3.10.0-957.5.1.el7.x86_64-x86_64-with-centos-7.6.1810-Core
   Processor:      x86_64

Python:
   Implementation: CPython
   Executable:     /home/maintainer/virtual_environments/visa_tools/bin/python
   Version:        3.6.7
   Compiler:       GCC 4.8.5 20150623 (Red Hat 4.8.5-36)
   Bits:           64bit
   Build:          Dec  5 2018 15:02:05 (#default)
   Unicode:        UCS4

PyVISA Version: 1.9.1

Backends:
   ni:
      Version: 1.9.1 (bundled with PyVISA)
      #1: /usr/lib/x86_64-linux-gnu/libvisa.so.18.2.0:
         found by: auto
         bitness: 64
         Vendor: National Instruments
         Impl. Version: 18874880
         Spec. Version: 5244928
   py:
      Version: 0.3.1
      ASRL INSTR: Available via PySerial (3.4)
      USB INSTR: Available via PyUSB (1.0.2). Backend: libusb1
      USB RAW: Available via PyUSB (1.0.2). Backend: libusb1
      TCPIP INSTR: Available 
      TCPIP SOCKET: Available 
      GPIB INSTR:
         Please install linux-gpib to use this resource type.
         No module named 'gpib'

```
## Links
[NI Linux Device Drivers (July 2018)](http://www.ni.com/download/ni-linux-device-drivers-2018/7664/en/)

[Downloading and Installing NI Driver Software on Linux Desktop](http://www.ni.com/product-documentation/54754/en/)

[NI-VISA and Operating System Compatibility](http://www.ni.com/product-documentation/54146/en/)

[Python3.6 on CentOS 7](https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-centos-7)
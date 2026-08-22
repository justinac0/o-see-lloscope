# o-see-lloscope

This is the code network winter hackerthon project for team [dont have a name yet]

## Problems

There are permission issues that can be quite tricky to solve on linux - keep that in mind.
This is mainly due to usbtmc issues and trying to communicate to the device. To solve this
for now you have to run you python environment as sudo (not cool). Playing with udev rules
currently and hopefully will have a non-sudo solution soon.

- Turns out the /dev/bus/usb/[bus]/[device] for the Rigol had bad privs. just chown these for your user and the python should work. Use lsusb to find the device.
    - for example 'sudo chown justin:justin /dev/bus/usb/001/008'

## Setup

1. Have python installed
2. Create python virtual environment 'python -m venv venv'
3. Source virtual environment
4. Install deps 'pip install -r requirements'
5. Run 'python main.py' with Rigol DS1054z connected to your pc.
6. If you can't connect to the device it is likely that the usbtmc perms are causing issues.

## Research / Inspiration

- [SCPI Through Python](https://testflowinc.com/blog/automate-rigol-oscilloscope-python-scpi-pyvisa-guide)

# Features

Must-have: 
1. Capturing data such as vpp, frequency, voltage, average voltage, amplitude
2. Manual adjustment and scaling of measurements such as frequency, etc
3. Provide full access to someone who's screen readers or provide alternative options 

Should-have:
1. Machine learning model that describe noise and provide descriptions 
2. Tone generation 

Could-have: 
1. Plots with customizable colors and line thicknesses 
2. Navigate through the data 




import numpy as np
import matplotlib.pyplot as plt
import os
import llm
from pathlib import Path


# NOTE(everyone): actions interacting with channel data assume we
# use channel 1 always.


# Globals
previous_voltage_capture: list = []

# Action Functions

def testFunc(scope, args):
    print("test: ", args[0])


def errorFunc(args):
    print ("cmd not found")


def autoFunc(scope, argse):
    scope.write(":AUToscale")


def measure(scope, item, channel="CHANnel1"):
    return float(scope.query(f":MEASure:ITEM? {item},{channel}"))

def measureFunc(scope, args):
    scope.write(":AUToscale")
    vpp  = measure(scope, "VPP")
    freq = measure(scope, "FREQuency")
    vavg = measure(scope, "VAVG")

    print(f"Vpp = {vpp:.3f} V, f = {freq:.1f} Hz, Vavg = {vavg:.3f} V")


def captureFunc(scope, args):
    global previous_voltage_capture

    # getting some raw binary data from device
    scope.write(":WAVeform:SOURce CHANnel1")
    scope.write(":WAVeform:MODE NORMal")
    scope.write(":WAVeform:FORMat BYTE")

    # scaling factors
    xinc  = float(scope.query(":WAVeform:XINCrement?"))
    yinc  = float(scope.query(":WAVeform:YINCrement?"))
    yorig = float(scope.query(":WAVeform:YORigin?"))
    yref  = float(scope.query(":WAVeform:YREFerence?"))

    scope.write(":WAVeform:DATA?")
    # for some reason the code from the ref times out here
    # so we just have to manually pass the header our selfs
    #
    # ref: https://helpfiles.keysight.com/csg/n5106a/commands_for_downloading_waveform_data.htm
    #
    header = scope.read_bytes(2) # '#' + digit count
    n_digits = int(header[1:2])
    len_str = scope.read_bytes(n_digits) # ASCII length of payload
    n_bytes = int(len_str)
    payload = scope.read_bytes(n_bytes + 1) # +1 for trailing newline
    raw = np.frombuffer(payload[:-1], dtype=np.uint8)

    volts = (raw - yorig - yref) * yinc
    time_s = np.arange(len(volts)) * xinc

    previous_voltage_capture = volts

    # plotting some data
    plt.plot(time_s * 1e3, volts)
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage (V)")
    plt.title("Rigol DS1054Z capture")
    plt.savefig("capture.png", dpi=150)
    np.savetxt("capture.csv", np.column_stack([time_s, volts]), delimiter=",", header="time_s,volts")


def triggerFunc(scope, args):
    """
    trigger source on rising or falling etc...
    """

    pass


def playPrevCapture(scope, args):
    import audio.pitch as pitch
    """
    play the previous capture from channel 1 as a pitch
    """

    global previous_voltage_capture

    if len(previous_voltage_capture) == 0:
        raise Exception("error previous capture is empty") 

    pitch.play_from_voltage(previous_voltage_capture)


def llmDescribeCapture(scope, args):
    chat = llm()

    if not Path("capture.png").is_file():
        print("Capture does not exist! Please capture waveform first.")
        return

    print("What would you like described? Type q or ctrl+ c to exit.")
    prompt = input("Chat: ")

    with open("capture.png", "rb") as image_file:
        image_bytes = image_file.read()

    chat.query(prompt=prompt, image_bytes=image_bytes)

    while True:
        prompt = input("\nChat: ")
        if (prompt == 'q') or (prompt == 'Q'): break
        chat.query(prompt=prompt)

        
class Action :
    def __init__(self, argc, func):
        self.argc = argc
        self.func = func


#stores all possible actions and there corrisponding cmd string
actionMap = {
    "test": Action(1, testFunc),
    "auto": Action(0, autoFunc),
    "measure": Action(0, measureFunc),
    "capture": Action(0, captureFunc),
    "playback": Action(0, playPrevCapture),
    "describe": Action(0, llmDescribeCapture),
}

#unique error action that is the default value for the map
errorAction=Action(0, errorFunc)


import numpy as np
import matplotlib.pyplot as plt
import os
from llm import llm
from pathlib import Path


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

    chn = args[0]
    
    chn_col = {
        "1": "y",
        "2": "a",
        "3": "m",
        "4": "b",
    }

    # getting some raw binary data from device
    scope.write(f":WAVeform:SOURce CHANnel{chn}")
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

    plt.clf()  # clear the current figure
    plt.plot(time_s * 1e3, volts, c=chn_col[chn])
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage (V)")
    plt.title("Rigol DS1054Z capture")
    plt.savefig("capture.png", dpi=150)
    plt.close()  # free memory, avoids figure buildup
    np.savetxt("capture.csv", np.column_stack([time_s, volts]), delimiter=",", header="time_s,volts")

triggerModes = {
    "edge": "EDGe",
    "pulse": "PULSe",
    "runt": "RUNT",
    "wind": "WIND",
    "window": "WIND",
    "windows": "WIND",
    "nedg": "NEDG",
    "nedge": "NEDG",
    "slope": "SLOPe",
    "video": "VIDeo",
    "pattern": "PATTern",
    "delay": "DELay",
    "timeout": "TIMeout",
    "duration": "DURation",
    "shold": "SHOLd",
    "rs232": "RS232",
    "iic": "IIC",
    "i2c": "IIC",
    "spi": "SPI",
}

triggerSlopes = {
    "pos": "POSitive",
    "positive": "POSitive",
    "rising": "POSitive",
    "rise": "POSitive",
    "+": "POSitive",
    "neg": "NEGative",
    "negative": "NEGative",
    "falling": "NEGative",
    "fall": "NEGative",
    "-": "NEGative",
    "rfall": "RFALl",
    "rfal": "RFALl",
    "both": "RFALl",
}


def triggerFunc(scope, args):
    """
    trigger source on rising or falling etc...
    usage: trigger <mode> <slope> <level>
    e.g.   trigger edge pos 1.5
    """
    mode = triggerModes.get(args[0].lower(), args[0].upper())
    slope = triggerSlopes.get(args[1].lower(), args[1].upper())
    level = args[2]

    scope.write(f":TRIGger:MODE {mode}")
    scope.write(f":TRIGger:{mode}:SOURce CHANnel1")
    scope.write(f":TRIGger:{mode}:SLOPe {slope}")
    scope.write(f":TRIGger:{mode}:LEVel {level}")

    print(f"Trigger updated: Mode={mode}, Source=CHANnel1, Slope={slope}, Level={level} V")


def triggerInfoFunc(scope, args):
    """
    Displays the current trigger settings (mode, source, slope, level, sweep, coupling, status).
    """
    try:
        mode = scope.query(":TRIGger:MODE?").strip()
    except Exception:
        mode = "EDGe"

    try:
        sweep = scope.query(":TRIGger:SWEep?").strip()
    except Exception:
        sweep = "N/A"

    try:
        coupling = scope.query(":TRIGger:COUPling?").strip()
    except Exception:
        coupling = "N/A"

    try:
        status = scope.query(":TRIGger:STATus?").strip()
    except Exception:
        status = "N/A"

    source = "N/A"
    slope = "N/A"
    level_str = "N/A"

    for m in (mode, "EDGe"):
        if source == "N/A":
            try:
                source = scope.query(f":TRIGger:{m}:SOURce?").strip()
            except Exception:
                pass
        if slope == "N/A":
            try:
                slope = scope.query(f":TRIGger:{m}:SLOPe?").strip()
            except Exception:
                pass
        if level_str == "N/A":
            try:
                lvl = float(scope.query(f":TRIGger:{m}:LEVel?").strip())
                level_str = f"{lvl:.3f} V"
            except Exception:
                pass

    print(f"Trigger Settings: Mode={mode}, Source={source}, Slope={slope}, Level={level_str}, Sweep={sweep}, Coupling={coupling}, Status={status}")

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


def idFunc(scope, args):
    print(scope.query("*IDN?"))


def clearFunc(scope, args):
    os.system("clear")
        

class Action :
    def __init__(self, argc, func, des):
        self.argc = argc
        self.func = func
        self.des = des


def divScaleFunc(scope, args):
    """
    usage: divscale <channel> <volts/div> <time/div>
    e.g.   divscale 1 0.5 0.001   -> 0.5 V/div, 1 ms/div
    """
    chn, vdiv, tdiv = args[0], args[1], args[2]

    scope.write(f":CHANnel{chn}:SCALe {vdiv}")
    scope.write(f":TIMebase:SCALe {tdiv}")

    print(f"CH{chn}: {vdiv} V/div, {tdiv} s/div")


#stores all possible actions and there corrisponding cmd string
actionMap = {
    "clear": Action(0, clearFunc, "Clear console contents"),
    "test": Action(1, testFunc, "A test action"),
    "divscale": Action(3, divScaleFunc, "Sets the scale for a channel"),
    "id": Action(0, idFunc, "Identify the device connected"),    
    "auto": Action(0, autoFunc, "Adjusts scale and position to view the signal"),
    "measure": Action(0, measureFunc, "Provides a summary of the signal"),
    "capture": Action(1, captureFunc, "Saves a png and csv and updates the program state"),
    "trigger": Action(3, triggerFunc, "Configures a trigger on channel 1"),
    "triggerinfo": Action(0, triggerInfoFunc, "Displays current trigger settings"),
    "triggersettings": Action(0, triggerInfoFunc, "Displays current trigger settings"),
    "playback": Action(0, playPrevCapture, "Plays an audio representation of the signal"),
    "describe": Action(0, llmDescribeCapture, "Enters a conversation with a LLM to allow the generated graph to be queried."),
}


def getActionNames() -> []:
    return actionMap.keys()

  
def helpFunc(scope, args):
    print("""o-see-lloscope -- help
    
    An application for the Visually impared to allow full access to oscilloscope measuring
    """)
    for key, value in actionMap.items():
        print (key + " : ", value.argc, " args.\n    " + value.des)

#unique error action that is the default value for the map
errorAction=Action(0, errorFunc, "(error)")

#add to map after so helpFunc has accesss to the map
actionMap["help"] = Action(0, helpFunc, "Provides help messages for each available command")

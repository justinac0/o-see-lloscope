import os
from pathlib import Path
import numpy as np
import osee.actions.llm as llm
import matplotlib.pyplot as plt
import threading

#try:
#    from classify_action import classifyFunc
#except ImportError:
#    classifyFunc = None  # classifier not set up yet -- registered conditionally below


# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

previous_voltage_capture: list = []

VALID_CHANNELS = {"1", "2", "3", "4"}
CHANNEL_COLORS = {"1": "y", "2": "a", "3": "m", "4": "b"}


# ---------------------------------------------------------------------------
# Action functions
# ---------------------------------------------------------------------------

def testFunc(scope, args):
    print("test: ", args[0])


def errorFunc(scope, args):
    print("cmd not found")


def clearFunc(scope, args):
    os.system("clear")


def idFunc(scope, args):
    print(scope.query("*IDN?"))


def autoFunc(scope, args):
    scope.write(":AUToscale")


def measure(scope, item, channel="CHANnel1"):
    return float(scope.query(f":MEASure:ITEM? {item},{channel}"))


def measureFunc(scope, args):
    scope.write(":AUToscale")
    vpp = measure(scope, "VPP")
    freq = measure(scope, "FREQuency")
    vavg = measure(scope, "VAVG")
    print(f"Vpp = {vpp:.3f} V, f = {freq:.1f} Hz, Vavg = {vavg:.3f} V")


def divScaleFunc(scope, args):
    """
    usage: divscale <channel> <volts/div> <time/div>
    e.g.   divscale 1 0.5 0.001   -> 0.5 V/div, 1 ms/div
    """
    chn, vdiv, tdiv = args[0], args[1], args[2]

    if chn not in VALID_CHANNELS:
        print(f"invalid channel: {chn} (expected 1-4)")
        return

    scope.write(f":CHANnel{chn}:SCALe {vdiv}")
    scope.write(f":TIMebase:SCALe {tdiv}")
    print(f"CH{chn}: {vdiv} V/div, {tdiv} s/div")


def couplingFunc(scope, args):
    """
    usage: coupling <channel> <AC|DC|GND>
    e.g.   coupling 1 AC
    """
    chn, mode = args[0], args[1].upper()

    if chn not in VALID_CHANNELS:
        print(f"invalid channel: {chn} (expected 1-4)")
        return
    if mode not in ("AC", "DC", "GND"):
        print(f"invalid coupling mode: {mode} (expected AC, DC, or GND)")
        return

    scope.write(f":CHANnel{chn}:COUPling {mode}")
    print(f"CH{chn}: coupling set to {mode}")


def captureFunc(scope, args):
    """
    usage: capture <channel>
    e.g.   capture 1
    """
    global previous_voltage_capture

    chn = args[0]
    if chn not in VALID_CHANNELS:
        print(f"invalid channel: {chn} (expected 1-4)")
        return

    # getting raw binary data from device
    scope.write(f":WAVeform:SOURce CHANnel{chn}")
    scope.write(":WAVeform:MODE NORMal")
    scope.write(":WAVeform:FORMat BYTE")

    # scaling factors
    xinc = float(scope.query(":WAVeform:XINCrement?"))
    yinc = float(scope.query(":WAVeform:YINCrement?"))
    yorig = float(scope.query(":WAVeform:YORigin?"))
    yref = float(scope.query(":WAVeform:YREFerence?"))

    scope.write(":WAVeform:DATA?")
    # for some reason the code from the ref times out here, so we
    # manually parse the SCPI block-data header ourselves
    #
    # ref: https://helpfiles.keysight.com/csg/n5106a/commands_for_downloading_waveform_data.htm
    header = scope.read_bytes(2)          # '#' + digit count
    n_digits = int(header[1:2])
    len_str = scope.read_bytes(n_digits)  # ASCII length of payload
    n_bytes = int(len_str)
    payload = scope.read_bytes(n_bytes + 1)  # +1 for trailing newline
    raw = np.frombuffer(payload[:-1], dtype=np.uint8)

    volts = (raw - yorig - yref) * yinc
    time_s = np.arange(len(volts)) * xinc

    previous_voltage_capture = volts

    plt.clf()
    plt.plot(time_s * 1e3, volts, c=CHANNEL_COLORS[chn])
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
    """
    usage: playback
    Plays the previous capture from channel 1 as a pitch.
    """
    import audio.pitch as pitch

    global previous_voltage_capture
    if len(previous_voltage_capture) == 0:
        raise Exception("error: previous capture is empty")

    pitch.play_from_voltage(previous_voltage_capture)


def llmDescribeCapture(scope, args):
    """
    usage: describe
    Enters a conversation with an LLM about the last captured graph.
    """
    chat = llm.llm()

    if not Path("capture.png").is_file():
        print("capture does not exist! Please capture waveform first.")
        return

    with open("capture.png", "rb") as image_file:
        image_bytes = image_file.read()

    print("what would you like described? Type 'q' or 'exit' to exit.")
    print("\n------------------\n")
    prompt = input("Chat: ")

    kwargs = {
        "prompt": prompt,
        "image_bytes": image_bytes,
    }

    while True:        
        if (prompt.upper() == 'Q') or (prompt.upper() == 'EXIT'): break

        t = threading.Thread(target=chat.loading)
        t.start()
        print(chat.query(**kwargs))
        t.join()

        print("\n------------------\n")

        prompt = input("Chat: ")
        kwargs = {"prompt": prompt}


# ---------------------------------------------------------------------------
# Action registry
# ---------------------------------------------------------------------------


def clearFunc(scope, args):
    os.system("clear")
    

class Action:
    def __init__(self, argc, func, des, usage=None, example=None):
        self.argc = argc
        self.func = func
        self.des = des
        self.usage = usage or ""
        self.example = example or ""


def divScaleFunc(scope, args):
    """
    usage: divscale <channel> <volts/div> <time/div>
    e.g.   divscale 1 0.5 0.001   -> 0.5 V/div, 1 ms/div
    """
    chn, vdiv, tdiv = args[0], args[1], args[2]

    scope.write(f":CHANnel{chn}:SCALe {vdiv}")
    scope.write(f":TIMebase:SCALe {tdiv}")

    print(f"CH{chn}: {vdiv} V/div, {tdiv} s/div")

    
def couplingFunc(scope, args):
    """
    usage: coupling <channel> <AC|DC|GND>
    e.g.   coupling 1 AC
    """
    chn, mode = args[0], args[1].upper()

    if mode not in ("AC", "DC", "GND"):
        print(f"invalid coupling mode: {mode} (expected AC, DC, or GND)")
        return

    scope.write(f":CHANnel{chn}:COUPling {mode}")
    print(f"CH{chn}: coupling set to {mode}")


def stopFunc(scope, args):
    """
    Stops waveform acquisition (equivalent to pressing STOP on the oscilloscope).
    """
    scope.write(":STOP")
    print("Acquisition stopped.")


def runFunc(scope, args):
    """
    Starts waveform acquisition (equivalent to pressing RUN on the oscilloscope).
    """
    scope.write(":RUN")
    print("Acquisition running.")

 
def helpFunc(scope, args):
    cmd = args[0]
    action = actionMap.get(cmd)

    if cmd == "all":
        for key, value in actionMap.items():
            print(f"{key}: {value.des}")
            if value.usage:
                print(f"    usage: {value.usage}")
            if value.example:
                print(f"    e.g.   {value.example}")
            print()
    else:
        print(f"{cmd}: {action.des}")
        if action.usage:
            print(f"    usage: {action.usage}")
        if action.example:
            print(f"    e.g.   {action.example}")
        print()


actionMap = {
    "clear": Action(0, clearFunc, "Clear console contents",
        usage="clear",
        example="clear"),

    "test": Action(1, testFunc, "A test action",
        usage="test <message>",
        example="test hello"),

    "divscale": Action(3, divScaleFunc, "Sets the scale for a channel",
        usage="divscale <channel> <volts/div> <time/div>",
        example="divscale 1 0.5 0.001"),

    "coupling": Action(2, couplingFunc, "Sets the coupling for a channel",
        usage="coupling <channel> <AC|DC|GND>",
        example="coupling 1 AC"),

    "id": Action(0, idFunc, "Identify the device connected",
        usage="id",
        example="id"),

    "auto": Action(0, autoFunc, "Adjusts scale and position to view the signal",
        usage="auto",
        example="auto"),

    "measure": Action(0, measureFunc, "Provides a summary of the signal",
        usage="measure",
        example="measure"),

    "capture": Action(1, captureFunc, "Saves a png and csv and updates the program state",
        usage="capture <channel>",
        example="capture 1"),

    "trigger": Action(3, triggerFunc, "Configures a trigger on channel 1",
        usage="trigger <edge|falling> <pos> <level>",
        example="trigger edge pos 2"),  
  
    "triggerinfo": Action(0, triggerInfoFunc, "Displays current trigger settings",
        usage="triggerinfo",
        example="triggerinfo"),
  
    "triggersettings": Action(0, triggerInfoFunc, "Displays current trigger settings",
        usage="triggersettings",
        example="triggersettings"),

    "stop": Action(0, stopFunc, "Stops waveform acquisition on the oscilloscope",
        usage="stop",
        example="stop"),
 
    "run": Action(0, runFunc, "Starts waveform acquisition on the oscilloscope",
        usage="run",
        example="run"),

    "describe": Action(0, llmDescribeCapture, "Enters a conversation with an LLM to query the generated graph",
        usage="describe",
        example="describe"),
}


def getActionNames() -> []:
    return actionMap.keys()


errorAction=Action(0, errorFunc, "(error)")

#add to map after so helpFunc has accesss to the map
actionMap["help"] = Action(1, helpFunc, "Provides help messages for each available command")

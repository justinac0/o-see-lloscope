import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from llm import llm

try:
    from classify_action import classifyFunc
except ImportError:
    classifyFunc = None  # classifier not set up yet -- registered conditionally below


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
    plt.close()
    np.savetxt("capture.csv", np.column_stack([time_s, volts]),
               delimiter=",", header="time_s,volts")


def triggerFunc(scope, args):
    """
    usage: trigger <edge|falling> <pos|neg> <level>
    e.g.   trigger edge pos 2
    """
    edge_type, slope_arg, level_arg = args[0], args[1], args[2]

    mode_map = {"edge": "EDGe", "falling": "FALLing"}
    slope_map = {"pos": "POSitive", "neg": "NEGative"}

    mode = mode_map.get(edge_type)
    slope = slope_map.get(slope_arg)

    if mode is None:
        print(f"invalid trigger type: {edge_type} (expected edge or falling)")
        return
    if slope is None:
        print(f"invalid slope: {slope_arg} (expected pos or neg)")
        return

    try:
        level = float(level_arg)
    except ValueError:
        print(f"invalid level: {level_arg} (expected a number)")
        return

    scope.write(f":TRIGger:{mode}:SOURce CHANnel1; SLOPe {slope}; LEVel {level}")
    print(f"trigger set: {mode}, {slope}, level={level}")


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
    chat = llm()

    if not Path("capture.png").is_file():
        print("Capture does not exist! Please capture waveform first.")
        return

    print("What would you like described? Type q or ctrl+c to exit.")
    prompt = input("Chat: ")

    with open("capture.png", "rb") as image_file:
        image_bytes = image_file.read()
    chat.query(prompt=prompt, image_bytes=image_bytes)

    while True:
        prompt = input("\nChat: ")
        if prompt.lower() == "q":
            break
        chat.query(prompt=prompt)


# ---------------------------------------------------------------------------
# Action registry
# ---------------------------------------------------------------------------

class Action:
    def __init__(self, argc, func, des, usage="", example=""):
        self.argc = argc
        self.func = func
        self.des = des
        self.usage = usage
        self.example = example


actionMap = {
    "clear": Action(0, clearFunc, "Clear console contents",
                    usage="clear", example="clear"),
    "test": Action(1, testFunc, "A test action",
                    usage="test <message>", example="test hello"),
    "id": Action(0, idFunc, "Identify the device connected",
                 usage="id", example="id"),
    "auto": Action(0, autoFunc, "Adjusts scale and position to view the signal",
                   usage="auto", example="auto"),
    "measure": Action(0, measureFunc, "Provides a summary of the signal",
                       usage="measure", example="measure"),
    "divscale": Action(3, divScaleFunc, "Sets the volts/div and time/div scale for a channel",
                        usage="divscale <channel> <volts/div> <time/div>",
                        example="divscale 1 0.5 0.001"),
    "coupling": Action(2, couplingFunc, "Sets the coupling for a channel",
                        usage="coupling <channel> <AC|DC|GND>",
                        example="coupling 1 AC"),
    "capture": Action(1, captureFunc, "Saves a png and csv and updates the program state",
                       usage="capture <channel>", example="capture 1"),
    "trigger": Action(3, triggerFunc, "Configures a trigger on channel 1",
                       usage="trigger <edge|falling> <pos|neg> <level>",
                       example="trigger edge pos 2"),
    "playback": Action(0, playPrevCapture, "Plays an audio representation of the signal",
                        usage="playback", example="playback"),
    "describe": Action(0, llmDescribeCapture,
                        "Enters a conversation with an LLM to query the generated graph",
                        usage="describe", example="describe"),
}

if classifyFunc is not None:
    actionMap["classify"] = Action(
        0, classifyFunc,
        "Classifies the last capture as sine/square/triangle/noise",
        usage="classify", example="classify",
    )


def getActionNames():
    return actionMap.keys()


def helpFunc(scope, args):
    print("""o-see-lloscope -- help

    An application for the Visually impaired to allow full access to oscilloscope measuring
    """)
    for key, value in actionMap.items():
        print(f"{key}: {value.des}")
        if value.usage:
            print(f"    usage: {value.usage}")
        if value.example:
            print(f"    e.g.   {value.example}")
        print()


actionMap["help"] = Action(0, helpFunc, "Provides help messages for each available command")

# unique error action, default value for the map -- must come after
# actionMap is fully populated in case future actions reference it
errorAction = Action(0, errorFunc, "(error)")
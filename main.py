### THE FOLLOWING IS BASE CODE ONLY ###
# it is by no means nice to look at or good quality.
# purely for testing communicating with the oscilloscope.
#
# ref: https://testflowinc.com/blog/automate-rigol-oscilloscope-python-scpi-pyvisa-guide
import pyvisa import audio.pitch as pitch


# connect to oscilliscope and return the handle
def osc_connect(resource: str):
    # connecting to device and takinng some basic measurements
    rm = pyvisa.ResourceManager()
    if len(rm.list_resources()) == 0:
        raise Exception("no visa compatible device was found")     
 
    scope = rm.open_resource(resource)
    scope.timeout = 30000 # timeout for 30s
    scope.chunk_size = 1024 * 1024

    return scope


def main():
    scope = osc_connect("USB0::6833::1230::DS1ZA281900965::0::INSTR")

    print(scope.query("*IDN?"))

    def measure(scope, item, channel="CHANnel1"):
        return float(scope.query(f":MEASure:ITEM? {item},{channel}"))
 
    scope.write(":AUToscale")
    vpp  = measure(scope, "VPP")
    freq = measure(scope, "FREQuency")
    vavg = measure(scope, "VAVG")
    
    print(f"Vpp = {vpp:.3f} V, f = {freq:.1f} Hz, Vavg = {vavg:.3f} V")
    
    # getting some raw binary data from device
    import numpy as np
 
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
    
    with open('capture.txt', 'w') as f:
        for v in range(len(volts)):
            print(volts[v], file=f)
    
    # plotting some data
    import matplotlib.pyplot as plt
    
    plt.plot(time_s * 1e3, volts)
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage (V)")
    plt.title("Rigol DS1054Z capture")
    plt.savefig("capture.png", dpi=150)
    np.savetxt("capture.csv", np.column_stack([time_s, volts]), delimiter=",", header="time_s,volts")

    pitch.play_from_voltage(volts)
 

# main entry point for o-see-lloscope
if __name__ == "__main__":
    try:
        main()   
    except Exception as e:
        print("unexpected error occured", e)


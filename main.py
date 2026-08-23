### THE FOLLOWING IS BASE CODE ONLY ###
# it is by no means nice to look at or good quality.
# purely for testing communicating with the oscilloscope.
#
# ref: https://testflowinc.com/blog/automate-rigol-oscilloscope-python-scpi-pyvisa-guide
import pyvisa
import repl


if __name__ == "__main__":
    # connecting to device and takinng some basic measurements
    rm = pyvisa.ResourceManager()
    if len(rm.list_resources()) > 0:
        uid = "USB0::6833::1230::DS1ZA281900965::0::INSTR"
        scope = rm.open_resource(uid)
        scope.timeout = 30000
        scope.chunk_size = 1024 * 1024

        repl.startREPL(scope)
    else:
        print("no devices found, is your oscilloscope connected?")

### THE FOLLOWING IS BASE CODE ONLY ###
# it is by no means nice to look at or good quality.
# purely for testing communicating with the oscilloscope.
#
# ref: https://testflowinc.com/blog/automate-rigol-oscilloscope-python-scpi-pyvisa-guide
import pyvisa
import repl

def init():
    # connecting to device and takinng some basic measurements
    rm = pyvisa.ResourceManager()
    print(rm.list_resources())

    scope = rm.open_resource("USB0::6833::1230::DS1ZA281900965::0::INSTR")
    scope.timeout = 30000
    scope.chunk_size = 1024 * 1024

    print(scope.query("*IDN?"))

#comment out to test non scope parts of app
init()

if __name__ == "__main__":
    repl.startREPL(scope)


from PythonPLC import plc
import snap7.client as c
from snap7.util import *
from snap7.snap7types import *

# Custom functions
def ReadOutput(plc,byte,bit,datatype = S7WLBit):
    result = plc.read_area(areas['PA'],0,byte,datatype)
    if datatype==S7WLBit:
        return get_bool(result,0,bit)
    elif datatype==S7WLByte or datatype==S7WLWord:
        return get_int(result,0)
    elif datatype==S7WLReal:
        return get_real(result,0)
    elif datatype==S7WLDWord:
        return get_dword(result,0)
    else:
        return None


# Setup (If you want to modify retentiveTag defualt values you need to erase db file)
sch6 = c.Client()
ready = False
try:
    sch6.connect('192.168.10.1', 0, 2)
except:
    print("PLC not reachable")
else:
    print("Connected")
    ready = True

vPLC = plc.PLC("S7 300")
counter1 = vPLC.createCounter("cont1", 10000)
timer1 = vPLC.createTimer("timer1", 5)
pulse = vPLC.Pulse()

# Main
if __name__ == "__main__":
    while ready:
        # Input and memory reading
        sensor = ReadOutput(sch6, 1, 4, S7WLBit)

        # Network 1
        if  pulse.positiveTrigger(sensor):
            counter1.countUp()
            tm = int(timer1.elapsed_time)
            if tm != None:
                print(int(60000/tm), "GPM", end=", ")
            print(counter1.current_value, "Estribos")
            timer1.reset()

        # Network 2
        if not sensor:
            timer1.energize()
            if timer1.done:
                print("0 GPM")

        # Network 3


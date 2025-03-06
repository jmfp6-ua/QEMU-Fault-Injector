import gdb
from gdb import Frame
import json

def getRegisters():
    regs = []
    frame = gdb.selected_frame()
    arch = frame.architecture()

    for r in arch.registers():
        regs.append(r.name)

    return regs

def dump(regs):
    try:
        with open("regs.json", "w") as file:
            json.dump(regs, file, indent=4)
    except:
        print("KO")

gdb.execute('target remote localhost:5000')
regs = getRegisters()
dump(regs)
print("OK")
gdb.execute('continue')
gdb.execute('exit')
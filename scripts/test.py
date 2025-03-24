import gdb
from gdb import Breakpoint
from gdb import Frame
import random
import os
import json

REGISTERS = []
      
class MainBreakpoint (gdb.Breakpoint):
      def __init__(self, location):
        super().__init__(location)
        self.fault_injected = False  # Instance variable

      def stop (self):
        try:
            reg = "v23"
            v = read_register(reg)
            print("Hi: ", v)
            set_register(reg, v)
            print(read_register(reg))
        except Exception as e:
            print("Error in MainBreakpoint:", e)
        return True

def getRegisters():
    global REGISTERS

    frame = gdb.selected_frame()
    arch = frame.architecture()

    for r in arch.registers():
        REGISTERS.append(r.name)

def getRegisterSizeInBits(reg):
    reg = gdb.parse_and_eval("$" + reg)
    return reg.type.sizeof * 8

def getRegisterSizeInBytes(reg):
    reg = gdb.parse_and_eval("$" + reg)
    return reg.type.sizeof

def countProgramLines():
    # Causing an exception on purpose because the error message has the info I need
    try:
        while True:
            gdb.execute('list', to_string=True)
    except gdb.error as error:
        lines = str(error).split("has ")[1].split(" ")[0]
        return int(lines)

def read_register(reg):
    size = getRegisterSizeInBytes(reg)
    out = gdb.execute(f"p/z (char[{size}])${reg}", to_string=True)
    hex_values = out.split(" = ")[1].strip().strip("{}").split(", ")
    print(out.split(" = ")[1].strip().strip("{}"))

    print(hex_values)

    # Convert each hex value to an integer and join them into a single number
    result = 0
    for value in hex_values:
        print(value)
        result = (result << 8) | int(value, 16)

    return result


def set_register(reg, value):
    size = getRegisterSizeInBytes(reg)
    hex_values = []
    while value > 0:
        hex_values.append(f"0x{value & 0xFF:02x}")  # Extract the last byte and format it
        value >>= 8  # Right shift the integer by 8 bits to move to the next byte

    # Reverse the order of the hex values since we processed the least significant byte first
    hex_values.reverse()

    # Join the hex values into a string
    hex_string = ", ".join(hex_values)

    # Format the output as requested
    #struct_value = f"{{ 0x{lower_bits:016X}, 0x{higher_bits:016X} }}"
    gdb.execute(f"set (char[{size}])${reg} = {{{hex_string}}}")


gdb.execute('target remote localhost:5000')

gdb.execute('set print repeats unlimited')

lines = countProgramLines()
print("Total lines of code:", lines)
random_line = random.randint(1, lines)
print("Setting breakpoint at line " + str(random_line))
MainBreakpoint(str(random_line))
print("Setting breakpoint at last line")
gdb.execute('continue')
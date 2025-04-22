import gdb
from gdb import Breakpoint
from gdb import Frame
import random
import os
import json
import re

REGISTERS = []
      
class MainBreakpoint (gdb.Breakpoint):
      def __init__(self, location):
        super().__init__(location)
        self.fault_injected = False  # Instance variable

      def stop (self):
        try:
            print("Hi: ")
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


def break_on_return_of_main():
    # Disassemble main
    disasm = gdb.execute(f"disassemble main", to_string=True)
    lines = disasm.strip().splitlines()

    # Look for either 'pop {..., pc}' or 'ret'
    for line in lines:
        line = line.strip()
        if re.search(r'\bpop\s+.*\bpc\b', line) or re.search(r'\bret\b', line):
            match = re.match(r'(0x[0-9a-fA-F]+)', line)
            if match:
                target_addr = match.group(1)
                gdb.Breakpoint(f"*{target_addr}")
                print(f"✅ Breakpoint set at return instruction of main: {target_addr}")
                return

    print("❌ Could not find return instruction (pop {..., pc} or ret) in main.")

def trace_main():
    sym = gdb.lookup_global_symbol("main")
    if sym is None:
        print("Could not find symbol 'main'")
        return

    addr = sym.value().address
    addr_str = str(addr)
    insns = gdb.execute(f"disassemble main", to_string=True)

    lines = insns.strip().splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("0x"):
            instr_addr = line.split()[0]
            gdb.Breakpoint(f"*{instr_addr}", internal=False)
            print(f"Set breakpoint at {instr_addr}")

gdb.execute('target remote localhost:5000')

gdb.execute('set print repeats unlimited')


break_on_return_of_main()
#trace_main()

#lastMain()

#lines = countProgramLines()
#print("Total lines of code:", lines)
#MainBreakpoint(str(lines))
#print("Setting breakpoint at last line")
#gdb.execute('continue')
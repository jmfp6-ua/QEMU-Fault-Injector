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
            if not self.fault_injected:
                bitFlipRegister()
                self.fault_injected = True
        except Exception as e:
            print("Error in MainBreakpoint:", e)
        return False

class LastBreakpoint (gdb.Breakpoint):
      def stop (self):
        try:
            value = gdb.parse_and_eval(os.getenv("VAR_NAME"))
            print("Result:", value)
        except Exception as e:
            print("Error in LastBreakpoint:", e)
        return False

def getRegisters():
    global REGISTERS

    frame = gdb.selected_frame()
    arch = frame.architecture()

    for r in arch.registers():
        REGISTERS.append(r.name)

def getRandomRegister():
    global REGISTERS

    reg = random.choice(REGISTERS)

    while getRegisterSizeInBits(reg) > 128:
        REGISTERS.remove(reg)
        reg = random.choice(REGISTERS)
    
    return reg

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

    # Convert each hex value to an integer and join them into a single number
    result = 0
    for value in hex_values:
        result = (result << 8) | int(value, 16)

    return result


def set_register(reg, value):
    size = getRegisterSizeInBytes(reg)
    # Convert the integer back to a list of hex values
    hex_values = []
    while value > 0:
        hex_values.append(f"0x{value & 0xFF:02x}")  # Extract the last byte and format it
        value >>= 8  # Right shift the integer by 8 bits to move to the next byte

    # Reverse the order of the hex values since we processed the least significant byte first
    hex_values.reverse()
    hex_string = ", ".join(hex_values)

    gdb.execute(f"set (char[{size}])${reg} = {{{hex_string}}}")

def bitFlipRegister():
    random_register = getRandomRegister()
    print("Reading register " + random_register)
    reg_size = getRegisterSizeInBits(random_register)
    print(f"{random_register} size: {reg_size}")
    r = read_register(random_register)

    # Convert the register value to binary.
    r_bin = "0b" + format(r, f'0{reg_size}b')
    print(f"Old {random_register}:")
    print(r_bin)

    # Flip the bits.
    r_bitFlip = bitFlip(r_bin)
    print(f"New {random_register}:")
    print(r_bitFlip)

    # Convert the flipped binary back to an integer.
    r_bitFlip_int = int(r_bitFlip, 2)

    # Set the register with the modified value.
    set_register(random_register, r_bitFlip_int)

def bitFlip(bits):
    bits = bits[2:]
    bit = random.randrange(len(bits))

    # Immutable strings (Python BAD)
    bits_list = list(bits)
    if bits_list[bit] == '0':
        bits_list[bit] = '1'
    else:
        bits_list[bit] = '0'
    
    bits = ''.join(bits_list)
    return "0b" + bits

def readRegsJson(path):
    global REGISTERS
    
    print("Path:", path)
    with open(path, "r") as file:
        REGISTERS = json.load(file)

gdb.execute('target remote localhost:5000')
gdb.execute('set print repeats unlimited')

regs_file = os.getenv("REGS_FILE", "auto")
if regs_file == "auto":
    getRegisters()
else:
    readRegsJson(regs_file)
lines = countProgramLines()
print("Total lines of code:", lines)
random_line = random.randint(1, lines)
print("Setting breakpoint at line " + str(random_line))
MainBreakpoint(str(random_line))
print("Setting breakpoint at last line")
LastBreakpoint(str(lines))
gdb.execute('continue')
gdb.execute('exit')
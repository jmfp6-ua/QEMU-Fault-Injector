import gdb
from gdb import Breakpoint
from gdb import Frame
import random
import os
import json
import re

REGISTERS = []
CRASH_SIGNALS = ['SIGILL', 'SIGSEGV', 'SIGBUS']
REG = ""
      
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
    global REGISTERS, REG

    reg = random.choice(REGISTERS)

    while getRegisterSizeInBits(reg) > 128:
        REGISTERS.remove(reg)
        reg = random.choice(REGISTERS)
    
    REG = reg
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

def setBreakOnReturnMain():
    # Disassemble main
    disasm = gdb.execute(f"disassemble main", to_string=True)
    lines = disasm.strip().splitlines()

    # Look for either 'pop {..., pc}' for arm32 or 'ret' for the rest
    for line in lines:
        line = line.strip()
        if re.search(r'\bpop\s+.*\bpc\b', line) or re.search(r'\bret\b', line):
            match = re.match(r'(0x[0-9a-fA-F]+)', line)
            if match:
                target_addr = match.group(1)
                LastBreakpoint(f"*{target_addr}")
                print(f"Breakpoint set at return instruction of main: {target_addr}")
                return

    print("Could not find return instruction (pop {..., pc} or ret) in main.")

def on_stop(event):
    global CRASH_SIGNALS, REG

    if event.stop_signal in CRASH_SIGNALS:
        print("[!] Crash detected due to bitflip.")
        val = gdb.parse_and_eval(f"${REG}")
        print(f"[!] Faulting register: {REG} = {val}")
        gdb.execute("set confirm off")
        gdb.execute("exit")

gdb.execute('target remote localhost:5000')
gdb.execute('set print repeats unlimited')
gdb.events.stop.connect(on_stop)
gdb.events.exited.connect(on_stop)

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

print("Setting breakpoint at the end of main")
setBreakOnReturnMain()

gdb.execute('continue')
gdb.execute('exit')
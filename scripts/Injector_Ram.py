import gdb
from gdb import Breakpoint
from gdb import Frame
import random
import os
import json
import re

REGISTERS = []

MEMORY_SECTIONS = []

# Define a class to hold each memory mapping
class Mapping:
    def __init__(self, start, end, size, permissions, label=None):
        self.start = int(start, 16)
        self.end = int(end, 16)
        self.size = int(size, 16)
        self.permissions = permissions
        self.label = label
    
    def __str__(self):
        return f"Start: {self.start:#018x}, End: {self.end:#018x}, Size: {self.size:#010x}, Perm: {self.permissions}, Label: {self.label}"



class MainBreakpoint (gdb.Breakpoint):
      def __init__(self, location):
        super().__init__(location)
        self.fault_injected = False  # Instance variable

      def stop (self):
        try:
            if not self.fault_injected:
                injectFault()
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

def injectFault():
    global MEMORY_SECTIONS
    parse_memory_mappings()
    addr = randomSelectAddress()

    print(f"Injecting fault at address: {addr:#018x}")
    flipBitAtAddress(addr)


# Function to parse and print memory mappings in a cleaner format
def parse_memory_mappings():
    global MEMORY_SECTIONS

    # Execute 'info proc mappings' and capture the output
    output = gdb.execute('info proc mappings', to_string=True)
    
    # Split into lines
    lines = output.splitlines()

    # Skip the header line and process the rest
    i = 0
    for line in lines[4:]:
        parts = line.strip().split()
        objfile = None
        if len(parts) == 6:
            start_addr, end_addr, size, offset, perms, objfile = parts
        else:
            start_addr, end_addr, size, offset, perms = parts

        if i < 3:
            if "x" in perms:
                objfile = ".text/.rodata"
                MEMORY_SECTIONS.append(Mapping(start_addr, end_addr, size, perms, objfile))
            elif "rw" in perms:
                objfile = ".data/.bss"
                MEMORY_SECTIONS.append(Mapping(start_addr, end_addr, size, perms, objfile))
        
        if objfile:
            if "heap" in objfile or "stack" in objfile:
                objfile = objfile[1:-1]
                MEMORY_SECTIONS.append(Mapping(start_addr, end_addr, size, perms, objfile))

        i += 1

def randomSelectAddress():
    global MEMORY_SECTIONS

    total_size = 0
    for mem in MEMORY_SECTIONS:
        total_size += mem.size
    
    rand = random.randint(0, total_size -1)

    addr = 0
    for mem in MEMORY_SECTIONS:
        if rand < mem.size:
            #print(f"Region: {mem.label}")
            addr = mem.start + rand
            return addr
        else:
            rand -= mem.size

def flipBitAtAddress(addr):
    bit_index = random.randint(0, 7)

    inferior = gdb.inferiors()[0]

    # Read 1 byte
    val = inferior.read_memory(addr, 1)
    byte = int.from_bytes(val, byteorder='little')

    print(f"Original byte at {hex(addr)}: {byte:#04x}")

    # Flip the desired bit
    flipped_byte = byte ^ (1 << bit_index)

    print(f"Flipped  byte at {hex(addr)}: {flipped_byte:#04x}")

    # Write it back
    inferior.write_memory(addr, flipped_byte.to_bytes(1, byteorder='little'))


def countProgramLines():
    # Causing an exception on purpose because the error message has the info I need
    try:
        while True:
            gdb.execute('list', to_string=True)
    except gdb.error as error:
        lines = str(error).split("has ")[1].split(" ")[0]
        return int(lines)


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

gdb.execute('target remote localhost:5000')
gdb.execute('set print repeats unlimited')

lines = countProgramLines()
print("Total lines of code:", lines)
random_line = random.randint(1, lines)
print("Setting breakpoint at line " + str(random_line))
MainBreakpoint(str(random_line))

print("Setting breakpoint at the end of main")
setBreakOnReturnMain()

gdb.execute('continue')
gdb.execute('exit')
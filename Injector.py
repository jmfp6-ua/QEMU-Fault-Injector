import random
import gdb
from gdb import Breakpoint
from gdb import Frame

REGISTERS = []
      
class MainBreakpoint (gdb.Breakpoint):
      def stop (self):
        bitFlipRegister()
        return False

def getRegisters():
    global REGISTERS

    frame = gdb.selected_frame()
    arch = frame.architecture()

    for r in arch.registers():
        REGISTERS.append(r.name)

def getRandomRegister():
    global REGISTERS
    
    return random.choice(REGISTERS)

def getRegisterSizeInBits(reg):
    reg = gdb.parse_and_eval("$" + reg)
    return reg.type.sizeof * 8

def countProgramLines():
    # Causing an exception on purpose because the error message has the info I need
    try:
        while True:
            gdb.execute('list', to_string=True)
    except gdb.error as error:
        lines = str(error).split("has ")[1].split(" ")[0]
        return int(lines)

def read_register(reg):
    # Read the register value casted to unsigned long long for raw bit access.
    g = gdb.execute(f"p (unsigned long long)${reg}", to_string=True)
    value = g.split(" = ")[1].strip()
    return int(value)

def set_register(reg, raw_value):
    # Set the register value using the raw_value directly.
    gdb.execute(f"set ${reg} = (unsigned long long){raw_value}")

def bitFlipRegister():
    random_register = getRandomRegister()
    r = read_register(random_register)

    reg_size = getRegisterSizeInBits(random_register)
    print(f"{random_register} size: {reg_size}")

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

gdb.execute('target remote localhost:5000')
getRegisters()
lines = countProgramLines()
print("Total lines of code:", lines)
random_line = random.randint(1, lines)
print("Setting breakpoint at line " + str(random_line))
MainBreakpoint(str(random_line))
gdb.execute('continue')
gdb.execute('exit')
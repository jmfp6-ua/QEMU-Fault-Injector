import random
import gdb
from gdb import Breakpoint
from gdb import Frame

REGISTERS = []

class TestBreakpoint (gdb.Breakpoint):
      def stop (self):
        # Read variables
        inf_val = gdb.parse_and_eval("nums")
        f = gdb.newest_frame()
        inf_val2 = f.read_var("nums")
        r2 = f.read_register("r2")
        print("Nums: ", inf_val)
        print("Nums2: ", inf_val2)
        gdb.execute("info r")
        print("r2: ", r2)
        gdb.execute("disassemble")
        gdb.execute("set $r3 = 0")

        # Modify variables
        #gdb.execute("set (nums[0]) = 0")

        # True = Stops, False = Does NOT stop
        return False
      
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
        

def bitFlipRegister():
    f = gdb.newest_frame()
    random_register = getRandomRegister()
    r = f.read_register(random_register)

    reg_size = getRegisterSizeInBits(random_register)
    print(random_register + " size:", reg_size)

    if reg_size == 128:
        r_binl = "0b" + format(int(r["u64"][0]), f'0{64}b')
        r_binh = "0b" + format(int(r["u64"][1]), f'0{64}b')

        print("Old " + random_register + ":")
        print(r_binl + r_binh[2:])

        r_bitFlipl = bitFlip(r_binl)
        r_bitFliph = bitFlip(r_binh)

        print("New " + random_register + ":")
        print(r_bitFlipl + r_bitFliph[2:])

        gdb.execute("set $" + random_register + ".u64[0] = " + r_bitFlipl)
        gdb.execute("set $" + random_register + ".u64[1] = " + r_bitFliph)
    else:
        u64_mode = False
        try:
            r_bin = "0b" + format(int(r), f'0{reg_size}b')
        except gdb.error:
            print("U64 MODE")
            u64_mode = True
            r_bin = "0b" + format(int(r["u64"]), f'0{reg_size}b')
        print("Old " + random_register + ":")
        print(r_bin)
        r_bitFlip = bitFlip(r_bin)
        print("New " + random_register + ":")
        print(r_bitFlip)

        if u64_mode:
            stri = "set $" + random_register + ".u64 = " + r_bitFlip
        else:
            stri = "set $" + random_register + " = " + r_bitFlip

        gdb.execute(stri)

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

gdb.execute('target remote localhost:5000')
getRegisters()
lines = countProgramLines()
print("Total lines of code:", lines)
random_line = random.randint(1, lines)
print("Setting breakpoint at line " + str(random_line))
MainBreakpoint(str(random_line))
gdb.execute('continue')
gdb.execute('exit')


#gdb.execute('continue')
#gdb.execute('continue')
#o = gdb.execute('disassemble exit', to_string=True)
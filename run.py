import subprocess
import argparse
import os
import sys
from enum import Enum
import random

LD_PREFIX_ARM = "/usr/arm-linux-gnueabihf"
LD_PREFIX_ARM64 = "/usr/aarch64-linux-gnu"
LD_PREFIX_RISCV = "/usr/riscv64-linux-gnu"

class Arch(Enum):
    x86 = 0
    x86_64 = 1
    Arm = 2
    Arm64 = 3
    riscv = 4

ARCH = ""
FILE = ""

def getBinaryWordSize(path):
    bits = subprocess.run(f"LANG=en readelf -h {path} | grep 'Class'", shell=True, capture_output=True, text=True)
    if "ELF64" in bits.stdout:
        return 64
    elif "ELF32" in bits.stdout:
        return 32
    
def getBinaryArch(path):
    bits = subprocess.run(f"LANG=en readelf -h {path} | grep 'Machine'", shell=True, capture_output=True, text=True)
    if "RISC-V" in bits.stdout:
        return Arch.riscv
    elif "X86-64" in bits.stdout:
        return Arch.x86_64
    elif "ARM" in bits.stdout:
        return Arch.Arm
    elif "AArch64" in bits.stdout:
        return Arch.Arm64

def runExecutable():
    global ARCH, FILE, LD_PREFIX_ARM, LD_PREFIX_ARM64, LD_PREFIX_RISCV

    if ARCH == Arch.Arm:
        subprocess.Popen(["qemu-arm", "-L", LD_PREFIX_ARM, "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.Arm64:
        subprocess.Popen(["qemu-aarch64", "-L", LD_PREFIX_ARM64, "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.riscv:
        subprocess.Popen(["qemu-riscv64", "-L", LD_PREFIX_RISCV, "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.x86:
        subprocess.Popen(["qemu-i386", "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.x86_64:
        subprocess.Popen(["qemu-x86_64", "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



def dumpRegisters():
    global FILE

    runExecutable()
    output = subprocess.run(["gdb-multiarch", "-q", "--command", "scripts/dumpRegisters.py", FILE], capture_output=True, text=True).stdout
    if "OK" in output:
        print("Register list saved to regs.json")
    else:
        print("Failed to dump registers")

def cleanRun(varName):
    global FILE

    runExecutable()
    os.environ["VAR_NAME"] = varName
    output = subprocess.run(["gdb-multiarch", "-q", "--command", "scripts/cleanRun.py", FILE], env=os.environ, capture_output=True, text=True).stdout
    
    if "Error:" in output:
        print("Error while running clean run:")
        printRawOutput(output)
        exit()

    result = output.split("Result: ")[1].split("\n")[0]
    return result

def registerFaultRun():
    global FILE

    runExecutable()
    process = subprocess.Popen(["gdb-multiarch", "-q", "--command", "scripts/Injector.py", FILE], env=os.environ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    captured_output = ""

    # Read output line by line in real-time
    for line in process.stdout:
        if 'Reading' in line:
            continue
        
        sys.stdout.write(line)
        sys.stdout.flush()
        captured_output += line

    # Wait for process to finish
    process.wait()

    if "Crash detected" in captured_output:
        return "Crash"
    
    result = captured_output.split("Result: ")[1].split("\n")[0]
    return result

def memoryFaultRun():
    global FILE

    runExecutable()
    process = subprocess.Popen(["gdb-multiarch", "-q", "--command", "scripts/Injector_Ram.py", FILE], env=os.environ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    captured_output = ""

    # Read output line by line in real-time
    for line in process.stdout:
        if 'Reading' in line:
            continue

        sys.stdout.write(line)
        sys.stdout.flush()
        captured_output += line

    # Wait for process to finish
    process.wait()

    if "Crash detected" in captured_output:
        return "Crash"
    
    result = captured_output.split("Result: ")[1].split("\n")[0]
    return result

def debugRun():
    global FILE

    os.environ["VAR_NAME"] = "sum"
    runExecutable()
    subprocess.run(["gdb-multiarch", "-q", "--command", "scripts/debug.py", FILE], env=os.environ)
    #subprocess.run(["gdb-multiarch", "-q", "--command", "scripts/Injector_Ram.py", FILE], env=os.environ)

    return

def printRawOutput(o):
    print("------------------------------")
    print(o)
    print("------------------------------")

# CLI Arguments
parser = argparse.ArgumentParser()
parser.add_argument("executable", help="Executable to run", type=str)
parser.add_argument("resultVar", help="Variable that holds the result to compare against a clean run", type=str)
parser.add_argument("-a", "--arch", help="Binary architecture (arm32, arm64, riscv, x86-64, default: auto)", default='auto', type=str)
parser.add_argument("-d", help="Dump register list to json file and exit", action='store_true')
parser.add_argument("-r", "--regs", help="List of registers to attack (json file)", default='auto', type=str)

args = parser.parse_args()

ARCH = args.arch
FILE = args.executable

if not os.path.isfile(FILE):
    print("Error: Executable file not found. Check path")
    exit()

if ARCH == "auto":
    ARCH = getBinaryArch(FILE)

if args.d:
    dumpRegisters()
    exit()

if args.regs != "auto":
    if not os.path.isfile(args.regs):
        print("Error: Register file not found. Check path")
        exit()
    os.environ["REGS_FILE"] = args.regs

'''
print("Debug run")
debugRun()
exit()
'''

print("Running clean run to obtain expected result")
expectedResult = cleanRun(args.resultVar)
print("Expected result:", expectedResult)

crash_counter = 0
result = ""
if random.randint(0, 1) == 0:
    result = registerFaultRun()
else:
    result = memoryFaultRun()

if result == "Crash":
    crash_counter += 1
else:
    print("Actual result:", result)
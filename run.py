import subprocess
import argparse
import os
import sys
from enum import Enum
import random
import time
import threading

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

class Results(Enum):
    Correct = 0
    Incorrect = 1
    Crash = 2
    Inf_Loop = 3

EXPECTED_TIME_S = 0
TIME_MARGIN_PERCENT = 1.5 # 50%
TIME_STOP_EVENT = threading.Event()
INF_LOOP_DETECTED = False
QEMU_HANDLER = -1

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
    global ARCH, FILE, LD_PREFIX_ARM, LD_PREFIX_ARM64, LD_PREFIX_RISCV, QEMU_HANDLER

    if ARCH == Arch.Arm:
        QEMU_HANDLER = subprocess.Popen(["qemu-arm", "-L", LD_PREFIX_ARM, "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.Arm64:
        QEMU_HANDLER = subprocess.Popen(["qemu-aarch64", "-L", LD_PREFIX_ARM64, "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.riscv:
        QEMU_HANDLER = subprocess.Popen(["qemu-riscv64", "-L", LD_PREFIX_RISCV, "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.x86:
        QEMU_HANDLER = subprocess.Popen(["qemu-i386", "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif ARCH == Arch.x86_64:
        QEMU_HANDLER = subprocess.Popen(["qemu-x86_64", "-g", "5000", FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



def dumpRegisters():
    global FILE

    runExecutable()
    output = subprocess.run(["gdb-multiarch", "-q", "--command", "scripts/dumpRegisters.py", FILE], capture_output=True, text=True).stdout
    if "OK" in output:
        print("Register list saved to regs.json")
    else:
        print("Failed to dump registers")

def cleanRun(varName):
    global FILE, EXPECTED_TIME_S

    start = time.time()
    runExecutable()
    os.environ["VAR_NAME"] = varName
    output = subprocess.run(["gdb-multiarch", "-q", "--command", "scripts/cleanRun.py", FILE], env=os.environ, capture_output=True, text=True).stdout
    end = time.time()

    EXPECTED_TIME_S = end - start

    if "Error:" in output:
        print("Error while running clean run:")
        printRawOutput(output)
        exit()

    result = output.split("Result: ")[1].split("\n")[0]
    return result

def registerFaultRun():
    global FILE, TIME_STOP_EVENT, INF_LOOP_DETECTED

    runExecutable()
    process = subprocess.Popen(["gdb-multiarch", "-q", "--command", "scripts/Injector.py", FILE], env=os.environ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    time_thread = threading.Thread(target=timeThread, args=(process,))
    time_thread.start()


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

    TIME_STOP_EVENT.set()
    time_thread.join()

    if INF_LOOP_DETECTED:
        return Results.Inf_Loop
    elif "Crash detected" in captured_output:
        return Results.Crash
            
    result = captured_output.split("Result: ")[1].split("\n")[0]
    return result

def memoryFaultRun():
    global FILE, TIME_STOP_EVENT, INF_LOOP_DETECTED

    runExecutable()
    process = subprocess.Popen(["gdb-multiarch", "-q", "--command", "scripts/Injector_Ram.py", FILE], env=os.environ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    time_thread = threading.Thread(target=timeThread, args=(process,))
    time_thread.start()

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

    TIME_STOP_EVENT.set()
    time_thread.join()

    if "Result: " not in captured_output:
        if "Crash detected" in captured_output:
            return Results.Crash
        else:
            return Results.Inf_Loop
    
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

def timeThread(process):
    global TIME_STOP_EVENT, EXPECTED_TIME_S, TIME_MARGIN_PERCENT, INF_LOOP_DETECTED, QEMU_HANDLER
    
    start = time.time()

    while not TIME_STOP_EVENT.is_set() and not INF_LOOP_DETECTED:
        if time.time() - start > EXPECTED_TIME_S * TIME_MARGIN_PERCENT:
            print("[!] Infinite loop detected")
            process.terminate()
            QEMU_HANDLER.terminate()
            INF_LOOP_DETECTED = True
        else:
            time.sleep(0.1)

# CLI Arguments
parser = argparse.ArgumentParser()
parser.add_argument("executable", help="Executable to run", type=str)
parser.add_argument("resultVar", help="Variable that holds the result to compare against a clean run", type=str)
parser.add_argument("-n", help="List of registers to attack (json file)", default=1000, type=int)
parser.add_argument("-d", help="Dump register list to json file and exit", action='store_true')
parser.add_argument("-r", "--regs", help="List of registers to attack (json file)", default='auto', type=str)

args = parser.parse_args()
FILE = args.executable

if not os.path.isfile(FILE):
    print("Error: Executable file not found. Check path")
    exit()

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
inf_loop_counter = 0
correct_counter = 0
incorrect_counter = 0

for i in range(args.n):
    TIME_STOP_EVENT.clear()
    INF_LOOP_DETECTED = False
    result = ""

    if random.randint(0, 1) == 0:
        result = registerFaultRun()
    else:
        result = memoryFaultRun()

    if result == Results.Crash:
        crash_counter += 1
    elif result == Results.Inf_Loop:
        inf_loop_counter += 1
    else:
        if result == expectedResult:
            correct_counter += 1
        else:
            incorrect_counter += 1

print("Correct counter:", correct_counter)
print("Incorrect counter:", incorrect_counter)
print("Crash counter:", crash_counter)
print("Infinite loop counter:", inf_loop_counter)


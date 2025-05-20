import gdb
from gdb import Breakpoint
from gdb import Frame
import os
import re

VAR_NAME = ""
      
class LastBreakpoint (gdb.Breakpoint):
      global VAR_NAME
      def stop (self):
        try:
            value = gdb.parse_and_eval(VAR_NAME)
            print("Result:", value)
        except gdb.error as e:
            print("Error: No symbol")
        
        return False

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
gdb.execute('set print elements 0')

VAR_NAME = os.getenv("VAR_NAME")
setBreakOnReturnMain()
gdb.execute('continue')
gdb.execute('exit')
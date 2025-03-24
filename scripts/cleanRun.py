import gdb
from gdb import Breakpoint
from gdb import Frame
import random
import os
import json

VAR_NAME = ""
      
class LastBreakpoint (gdb.Breakpoint):
      global VAR_NAME
      def stop (self):
        value = gdb.parse_and_eval(VAR_NAME)
        print("Result:", value)
        return False

def countProgramLines():
    # Causing an exception on purpose because the error message has the info I need
    try:
        while True:
            gdb.execute('list', to_string=True)
    except gdb.error as error:
        lines = str(error).split("has ")[1].split(" ")[0]
        return int(lines)

gdb.execute('target remote localhost:5000')

VAR_NAME = os.getenv("VAR_NAME")

lines = countProgramLines()
random_line = random.randint(1, lines)
LastBreakpoint(str(lines))
gdb.execute('continue')
gdb.execute('exit')
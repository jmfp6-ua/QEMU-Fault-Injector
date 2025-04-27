import gdb
from gdb import Breakpoint
from gdb import Frame
import os
import re


#gdb.execute('set sysroot /usr/arm-linux-gnueabihf')
gdb.execute('target remote localhost:5000')
gdb.execute('b main')
#gdb.execute('continue')
#gdb.execute('exit')
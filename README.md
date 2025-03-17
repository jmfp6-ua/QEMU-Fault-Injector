# Qemu Fault Injector
Fault injector using Qemu's gdb’s remote-connection facility, [gdbstub](https://www.qemu.org/docs/master/system/gdb.html). 

Currently, it has the ability to modify any register arbitrarily, regardless of the executable architecture.

## Dependecies
python, gdb-multiarch, qemu

Debian:  
`sudo apt install python3 gdb-multiarch qemu-user qemu-user-static qemu-system-x86 qemu-system-arm qemu-system-misc`

## Usage
To attack a random register you can run:  
`python3 run.py executable`

To attack specific registers run  
`python3 run.py -d executable`   
once to dump available registers to a json file. Remove unwanted ones and run:  
`python3 run.py -r regs_list.json executable`   

### Optional arguments

| Key | Value | Description |
| :---: | :---: | :---: |
| -d | None | Dump register list to json file and exit |
| -r | file path | List of registers to attack (json file) |

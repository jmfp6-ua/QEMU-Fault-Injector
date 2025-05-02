# Qemu Fault Injector
Fault injector using Qemu's gdb’s remote-connection facility, [gdbstub](https://www.qemu.org/docs/master/system/gdb.html). 

Currently, it has the ability to modify any register or memory arbitrarily, regardless of the executable architecture.

## Dependecies
python, gdb-multiarch, qemu 8.1 or above

Debian:  
`sudo apt install python3 gdb-multiarch qemu-user qemu-user-static qemu-system-x86 qemu-system-arm qemu-system-misc`

If the qemu version provided by your distribution is lower than 8.1, you will need to compile it yourself.

There is a script provided (`compile_qemu.sh`) that does this for you (apt based distros only) but it will not add the resulting binaries to your path. To do that, you can run:
`export PATH="your_qemu_source_path/build:$PATH"` on your terminal before runing the injector or add it to `.bashrc` to do it autamatically on boot.

## Usage
To attack a random register you can run:  
`python3 run.py executable resultVar`

To attack specific registers run  
`python3 run.py -d executable`   
once to dump available registers to a json file. Remove unwanted ones and run:  
`python3 run.py -r regs_list.json executable resultVar`   

### Optional arguments

| Key | Value | Description |
| :---: | :---: | :---: |
| -n | int | Number of executions to run (1000 default) |
| -d | None | Dump register list to json file and exit |
| -r | string | File path of list of registers to attack (json file) |

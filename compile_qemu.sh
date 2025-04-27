#! /bin/bash

sudo apt update
sudo apt install wget ninja-build libglib2.0-dev pkg-config flex bison

wget https://download.qemu.org/qemu-9.2.3.tar.xz
tar xvJf qemu-9.2.3.tar.xz
cd qemu-9.2.3
./configure
make

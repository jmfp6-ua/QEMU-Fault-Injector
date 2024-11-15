BUILD_DIR = build/
CFLAGS = -g
ifdef STATIC
    CFLAGS += -static
endif

.PHONY: x86 arm32 arm64 riscv

all: x86 arm32 arm64 riscv

x86: testProgram.c | $(BUILD_DIR)
	gcc $(CFLAGS) -o $(BUILD_DIR)x86 ./testProgram.c

arm32: testProgram.c | $(BUILD_DIR)
	arm-linux-gnueabihf-gcc $(CFLAGS) -o $(BUILD_DIR)arm32 ./testProgram.c

arm64: testProgram.c | $(BUILD_DIR)
	aarch64-linux-gnu-gcc $(CFLAGS) -o $(BUILD_DIR)arm64 ./testProgram.c

riscv: testProgram.c | $(BUILD_DIR)
	riscv64-linux-gnu-gcc $(CFLAGS) -o $(BUILD_DIR)riscv ./testProgram.c

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)
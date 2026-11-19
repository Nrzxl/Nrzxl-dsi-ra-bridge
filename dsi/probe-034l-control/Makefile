# SPDX-License-Identifier: MIT
# 034L control and NWRAM padding variants use same ARM9 and ARM7 runtime.
NAME          := DSIRB_034L_CONTROL
GAME_TITLE    := DSIRABRIDGE
GAME_SUBTITLE := 034L CONTROL NWRAM
GAME_AUTHOR   := DSIRB
SOURCEDIRS    := source
ARM7ELF       := arm7/build/arm7.elf
LIBS          := -lnds9
LIBDIRS       := $(BLOCKSDS)/libs/libnds
include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile

$(ROM): $(ARM7ELF)
$(ARM7ELF): $(wildcard arm7/source/*.c)
	@+$(MAKE) -C arm7 --no-print-directory
clean: clean-arm7
.PHONY: clean-arm7
clean-arm7:
	@$(MAKE) -C arm7 clean --no-print-directory

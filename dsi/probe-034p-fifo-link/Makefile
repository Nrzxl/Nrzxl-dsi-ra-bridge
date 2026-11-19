# SPDX-License-Identifier: MIT
NAME          := DSIRB_034P_FIFO_LINK
GAME_TITLE    := DSIRABRIDGE
GAME_SUBTITLE := 034P LINK TEST
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

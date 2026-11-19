# SPDX-License-Identifier: MIT
# F1 default ARM7; F2/F3 use pinned DScheevos custom ARM7 startup.
NAME          := DSIRB_034F_ARM7
GAME_TITLE    := DSIRABRIDGE
GAME_SUBTITLE := 034F ARM7 stage
GAME_AUTHOR   := DSIRB
SOURCEDIRS    := source
ARM7ELF       := arm7/build/arm7.elf
LIBS          := -lnds9
LIBDIRS       := $(BLOCKSDS)/libs/libnds
include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile

# Compile upstream DScheevos ARM7 custom core exactly at its pinned source.
$(ROM): $(ARM7ELF)
$(ARM7ELF): $(wildcard arm7/source/*.c)
	@+$(MAKE) -C arm7 --no-print-directory
clean: clean-arm7
.PHONY: clean-arm7
clean-arm7:
	@$(MAKE) -C arm7 clean --no-print-directory

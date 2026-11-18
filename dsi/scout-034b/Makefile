# SPDX-License-Identifier: MIT
# Independent DS/DSi homebrew, never boots a retail ROM.
.SUFFIXES:
.DEFAULT_GOAL := all
ifeq ($(strip $(DEVKITARM)),)
$(error DEVKITARM required)
endif
TARGET := DSIRB_Scout_034B
GAME_TITLE := DSIRABRIDGE
GAME_SUBTITLE1 := Safe 034B Scout
GAME_SUBTITLE2 := No ROM modifications
include $(DEVKITARM)/ds_rules
ARCH := -march=armv5te -mtune=arm946e-s
CFLAGS := -std=gnu11 -O2 -g -ffile-prefix-map=/work=. -Wall -Wextra \
 -ffunction-sections -fdata-sections $(ARCH) $(INCLUDE) -DARM9
CXXFLAGS := $(CFLAGS)
LDFLAGS = -specs=ds_arm9.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)
LIBS := -lfat -lnds9
ifneq ($(notdir $(CURDIR)),build)
export OUTPUT := $(CURDIR)/$(TARGET)
export VPATH := $(CURDIR)/source
export DEPSDIR := $(CURDIR)/build
export INCLUDE := -I$(CURDIR)/include -I$(LIBNDS)/include -I$(DEVKITPRO)/calico/include
export LIBPATHS := -L$(LIBNDS)/lib
export LD := $(CC)
export OFILES := main.o
.PHONY: all clean
all:
	@mkdir -p build
	@$(MAKE) --no-print-directory -C build -f $(CURDIR)/Makefile
clean:
	@rm -rf build $(TARGET).elf $(TARGET).nds $(TARGET).map
else
.PHONY: all
all: $(OUTPUT).nds
$(OUTPUT).nds: $(OUTPUT).elf
$(OUTPUT).elf: $(OFILES)
-include $(DEPSDIR)/*.d
endif

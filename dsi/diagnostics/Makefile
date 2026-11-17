# Minimal original recipe for classic devkitARM/libnds ds_rules.
.SUFFIXES:
.DEFAULT_GOAL := all
ifeq ($(strip $(DEVKITARM)),)
$(error DEVKITARM must point to devkitARM)
endif
include $(DEVKITARM)/ds_rules
TARGET := DSiRABridge_Diagnostic_020
ARCH := -march=armv5te -mtune=arm946e-s
GAME_TITLE := DSIRABRIDGE
GAME_SUBTITLE1 := Diagnostic 0.2.0
GAME_SUBTITLE2 := Controlled memory only
CFLAGS := -std=gnu11 -O2 -g -ffile-prefix-map=/work=. -Wall -Wextra -ffunction-sections -fdata-sections $(ARCH) $(INCLUDE) -DARM9
CXXFLAGS := $(CFLAGS)
LDFLAGS = -specs=ds_arm9.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)
LIBS := -lfat -lnds9
ifneq ($(notdir $(CURDIR)),build)
export OUTPUT := $(CURDIR)/$(TARGET)
export VPATH := $(CURDIR)/source
export DEPSDIR := $(CURDIR)/build
export INCLUDE := -I$(LIBNDS)/include
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

// SPDX-License-Identifier: Zlib
// SPDX-FileNotice: Incremental diagnostic adaptation of pinned
// skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3 ARM7 core.
// Copyright (C) 2005 Michael Noland (joat)
// Copyright (C) 2005 Jason Rogers (Dovoto)
// Copyright (C) 2005-2015 Dave Murphy (WinterMute)
// Copyright (C) 2023 Antonio Niño Díaz
// No game, Wi-Fi credentials, ROM, SD access, or RA.

#include <nds.h>



// DSIRB 034L: padding deliberately matches the DSWiFi7-related NWRAM growth
// seen in 034I, but does NOT link DSWiFi and does NOT access WiFi hardware.
// .twl is loaded only in DSi mode. .twl_bss reserves uninitialized DSi RAM.
// Both allocations are inert. Only their addresses are passed to an empty
// compiler barrier to prevent linker garbage collection; NO memory read/write.
static const unsigned char dsirb_twl_bytes[17848]
    __attribute__((used, aligned(4), section(".twl"))) = { 0x4C };
static unsigned char dsirb_twl_bss[13300]
    __attribute__((used, aligned(4), section(".twl_bss")));

static volatile bool exit_loop = false;

static void power_button_callback(void)
{
    exit_loop = true;
}

static void vblank_handler(void)
{
    inputGetAndSend();

}

int main(void)
{
    __asm__ volatile ("" : : "r" (dsirb_twl_bytes), "r" (dsirb_twl_bss) : "memory");
    enableSound();
    readUserSettings();
    ledBlink(0);
    touchInit();

    irqInit();
    fifoInit();

    installSoundFIFO();
    installSystemFIFO();
    if (isDSiMode())
        installCameraFIFO();

    setPowerButtonCB(power_button_callback);
    initClockIRQTimer(LIBNDS_DEFAULT_TIMER_RTC);

    irqSet(IRQ_VBLANK, vblank_handler);
    irqEnable(IRQ_VBLANK);

    while (!exit_loop)
        swiWaitForVBlank();

    return 0;
}

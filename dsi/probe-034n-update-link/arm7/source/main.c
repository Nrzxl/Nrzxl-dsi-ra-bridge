// SPDX-License-Identifier: Zlib
// SPDX-FileNotice: Incremental diagnostic adaptation of pinned
// skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3 ARM7 core.
// Copyright (C) 2005 Michael Noland (joat)
// Copyright (C) 2005 Jason Rogers (Dovoto)
// Copyright (C) 2005-2015 Dave Murphy (WinterMute)
// Copyright (C) 2023 Antonio Niño Díaz
// No game, Wi-Fi credentials, ROM, SD access, or RA.

#include <nds.h>


// This variant includes the *address* of Wifi_Update in the ARM7 link.
// The function is NEVER invoked, no WiFi IPC handler installed and no WiFi
// hardware initialized. The volatile pointer prevents dead stripping.
// A previous H1 test linked installWifiFIFO() instead, and physically failed.
#include <dswifi7.h>
static void (*volatile dsirb_wifi_update_symbol)(void) = Wifi_Update;

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
    enableSound();
    readUserSettings();
    ledBlink(0);
    touchInit();

    irqInit();
    fifoInit();

    if (!dsirb_wifi_update_symbol) exit_loop = true;
    fifoSendValue32(FIFO_USER_03, 0x4E370001u); /* ARM7 stage 1: FIFO ready */

    installSoundFIFO();
    installSystemFIFO();
    if (isDSiMode())
        installCameraFIFO();

    setPowerButtonCB(power_button_callback);
    initClockIRQTimer(LIBNDS_DEFAULT_TIMER_RTC);

    irqSet(IRQ_VBLANK, vblank_handler);
    irqEnable(IRQ_VBLANK);
    fifoSendValue32(FIFO_USER_03, 0x4E370002u); /* ARM7 stage 2: services/IRQ ready */

    while (!exit_loop)
        swiWaitForVBlank();

    return 0;
}

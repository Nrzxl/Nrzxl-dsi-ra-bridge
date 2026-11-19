// SPDX-License-Identifier: Zlib
// SPDX-FileNotice: Incremental diagnostic adaptation of pinned
// skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3 ARM7 core.
// Copyright (C) 2005 Michael Noland (joat)
// Copyright (C) 2005 Jason Rogers (Dovoto)
// Copyright (C) 2005-2015 Dave Murphy (WinterMute)
// Copyright (C) 2023 Antonio Niño Díaz
// No game, Wi-Fi credentials, ROM, SD access, or RA.

#include <nds.h>
/* 034R link-only reference; the function is NEVER called.
 * Internal DSWiFi symbol selected from the SDK 1.24.0 archive, as verified
 * in the 034Q ELF and linker maps. No Wi-Fi register writes.
 */
extern void Wifi_NTR_Update(void);
static void (*volatile dsirb_034r_symbol_pointer)(void) = Wifi_NTR_Update;



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
    /* Force linker retention without invoking the selected symbol. */
    __asm__ volatile ("" : : "r"(dsirb_034r_symbol_pointer) : "memory");

    /* 034O stage 1: send only; ARM9 may not yet be polling. */
    fifoSendValue32(FIFO_USER_03, 0x4E370001u);

    installSoundFIFO();
    installSystemFIFO();
    if (isDSiMode())
        installCameraFIFO();

    setPowerButtonCB(power_button_callback);
    initClockIRQTimer(LIBNDS_DEFAULT_TIMER_RTC);

    irqSet(IRQ_VBLANK, vblank_handler);
    irqEnable(IRQ_VBLANK);
    /* 034O stage 2: send only after normal IRQ setup. */
    fifoSendValue32(FIFO_USER_03, 0x4E370002u);

    while (!exit_loop)
        swiWaitForVBlank();

    return 0;
}

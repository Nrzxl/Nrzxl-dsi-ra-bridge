// SPDX-License-Identifier: Zlib
// SPDX-FileNotice: Incremental diagnostic adaptation of pinned
// skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3 ARM7 core.
// Copyright (C) 2005 Michael Noland (joat)
// Copyright (C) 2005 Jason Rogers (Dovoto)
// Copyright (C) 2005-2015 Dave Murphy (WinterMute)
// Copyright (C) 2023 Antonio Niño Díaz
// No game, Wi-Fi credentials, ROM, SD access, or RA. LINK tests linkage without device initialization.

#include <nds.h>
#include <dswifi7.h>


static volatile bool exit_loop = false;
/* Force archive object into link: address read, function never called by LINK. */
static void (* volatile dswifi_symbol)(void) = installWifiFIFO;
static volatile bool arm9_requested_wifi_init = false;
static volatile bool wifi_init_completed = false;
static void gate_handler(u32 value, void *userdata) {
    (void)userdata;
    if (value == 0x494E4954u)
        arm9_requested_wifi_init = true;
}


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
    /* Volatile pointer read forces genuine DSWiFi7 symbol linkage, no call. */
    if (!dswifi_symbol) exit_loop = true;
    fifoSetValue32Handler(FIFO_USER_02, gate_handler, NULL);

    installSoundFIFO();
    installSystemFIFO();
    if (isDSiMode())
        installCameraFIFO();

    setPowerButtonCB(power_button_callback);
    initClockIRQTimer(LIBNDS_DEFAULT_TIMER_RTC);

    irqSet(IRQ_VBLANK, vblank_handler);
    irqEnable(IRQ_VBLANK);

    while (!exit_loop) {
        if (arm9_requested_wifi_init && !wifi_init_completed) {
            wifi_init_completed = true;
            installWifiFIFO();
            fifoSendValue32(FIFO_USER_02, 0x444F4E45u); /* DONE */
        }
        swiWaitForVBlank();
    }

    return 0;
}

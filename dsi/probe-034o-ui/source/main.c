/* SPDX-License-Identifier: MIT
 * DSi RA Bridge 0.3.4-O: Isolate ARM7 FIFO sending from ARM9 reception.
 * This is a startup/status probe: no DSWiFi, game, SD, network, or NAND.
 */
#include <nds.h>
#include <stdio.h>

/* This is the ONLY ARM9 source delta between O1 and O2. */
#define DSIRB_ENABLE_RX 0

static PrintConsole top, bottom;

int main(void)
{
    videoSetMode(MODE_0_2D);
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 0, true, true);
    consoleInit(&bottom, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 3, false, true);
    consoleSelect(&top);
    printf("DSIRB 034O FIFO ISOLATION\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("No DSWiFi; no network\n");
    printf("No game / SD / RA\n");

    consoleSelect(&bottom);
    printf("ARM7 two stage trace\n");
    printf("STAGE 1: WAITING\n");
    printf("STAGE 2: WAITING\n");
    printf("START to exit\n");

    unsigned int stage_mask = 0;
    unsigned int frames = 0;
    for (;;)
    {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START)
            break;

#if DSIRB_ENABLE_RX
        /* Never busy-wait: drain at most 4 messages per frame. */
        for (unsigned int n = 0; n < 4 && fifoCheckValue32(FIFO_USER_03); n++)
        {
            const u32 value = fifoGetValue32(FIFO_USER_03);
            if (value == 0x4E370001u) stage_mask |= 1;
            if (value == 0x4E370002u) stage_mask |= 2;
        }
#endif

        ++frames;
        if (frames % 30 == 0)
        {
            consoleSelect(&bottom);
            printf("\x1b[1;0HSTAGE 1: %-7s  ", (stage_mask & 1) ? "REACHED" : "WAITING");
            printf("\x1b[2;0HSTAGE 2: %-7s  ", (stage_mask & 2) ? "REACHED" : "WAITING");
        }
        if (frames % 120 == 0)
        {
            consoleSelect(&bottom);
            printf("\x1b[6;0HLOOP ALIVE: %u frames    ", frames);
        }
    }
    return 0;
}

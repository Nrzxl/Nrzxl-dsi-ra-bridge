/* SPDX-License-Identifier: MIT
 * DSIRB 034L NWRAM footprint-only diagnostic.
 * ARM9 source must be byte-identical for L0/L1.
 * Does not use game loading, FAT/SD, network, credentials, or achievements.
 */
#include <nds.h>
#include <stdio.h>

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

    printf("DSIRB 034L NWRAM TEST\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("ARM7 no WiFi driver\n");
    printf("No SD/Game/RA/Network\n");
    consoleSelect(&bottom);
    printf("Diagnostic only\n");
    printf("START to exit\n");

    unsigned frames = 0;
    for (;;)
    {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START)
            break;
        ++frames;
        if (frames % 120 == 0)
            printf("\x1b[6;0HLOOP ALIVE: %u frames    ", frames);
    }
    return 0;
}

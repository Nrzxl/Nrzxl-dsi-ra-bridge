/* SPDX-License-Identifier: MIT
 * DSi RA Bridge 0.3.4-K: official BlocksDS ARM7-only A/B.
 * Identical ARM9 source, no network, no filesystem, no retail game, no RA.
 */
#include <nds.h>
#include <stdio.h>

static PrintConsole top, bottom;

static void start_ui(void) {
    videoSetMode(MODE_0_2D);
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 0, true, true);
    consoleInit(&bottom, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 3, false, true);
    consoleSelect(&top);
}

int main(void) {
    start_ui();
    consoleSelect(&top);
    printf("DSIRB 034K OFFICIAL ARM7\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("No WiFi calls/network\n");
    printf("No retail game/RA/SD\n");
    consoleSelect(&bottom);
    printf("034K official core test\n");
    printf("START to exit\n");
    unsigned frames = 0;
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START) break;
        frames++;
        if (frames % 120 == 0)
            printf("\x1b[6;0HLOOP ALIVE: %u frames    ",frames);
    }
    return 0;
}

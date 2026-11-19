/* SPDX-License-Identifier: MIT
 * Diagnostic only. DScheevos ui_init layout, ported from pinned
 * skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3
 * (UI program header and diagnostic display authored in this project).
 * Does not use ROM, RA, game load, NAND, or persistent filesystem writes.
 */
#include <nds.h>
#include <stdio.h>

static PrintConsole top, bottom;

/* Same display setup as DScheevos launcher ui_init(), not consoleDemoInit. */
static void dsirb_ui_init(void) {
    videoSetMode(MODE_0_2D);
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 0, true, true);
    consoleInit(&bottom, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 3, false, true);
    consoleSelect(&top);
}

int main(void) {
    dsirb_ui_init();
    consoleSelect(&top);
    printf("DSIRB 034G UPDATE TEST\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("DScheevos-style dual UI\n");
    printf("No ROM, RA, or WiFi connect\n");
    consoleSelect(&bottom);
    printf("034G UPDATE init OK\n\n");
    printf("No SD mount or writes\n");
    printf("START: exit\n");
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START) break;
    }
    return 0;
}

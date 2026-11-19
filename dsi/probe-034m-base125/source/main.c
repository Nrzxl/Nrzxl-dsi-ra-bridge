/* SPDX-License-Identifier: MIT
 * DSi RA Bridge 0.3.4-M: BlocksDS v1.25.0 official ARM7 control vs Wi-Fi.
 * Same ARM9 source for the A/B. No game loader/ROM, network connection,
 * filesystem, NAND/MBK manipulation, authentication, RetroAchievements.
 */
#include <nds.h>
#include <stdio.h>
static PrintConsole top, bottom;
int main(void) {
    videoSetMode(MODE_0_2D);
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 0, true, true);
    consoleInit(&bottom, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 3, false, true);
    consoleSelect(&top);
    printf("DSIRB 034M SDK125\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("No WiFi init, no network\n");
    printf("No games, SD, RA, NAND\n");
    consoleSelect(&bottom);
    printf("Official ARM7 boot A/B\n");
    printf("START: exit\n");
    unsigned frames = 0;
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START) break;
        ++frames;
        if (frames % 120 == 0)
            printf("\x1b[7;0HLOOP ALIVE: %u frames    ", frames);
    }
    return 0;
}

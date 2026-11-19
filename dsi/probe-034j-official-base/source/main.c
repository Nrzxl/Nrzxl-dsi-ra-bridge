/* SPDX-License-Identifier: MIT
 * DSi RA Bridge 0.3.4-J: official BlocksDS precompiled ARM7 A/B smoke test.
 * Exactly the same ARM9 source is built with two standard ARM7 cores.
 * No game/ROM, retail loader, FAT/SD access, Wi-Fi requests, RetroAchievements,
 * credentials, saves, NAND, power registers or persistent writes.
 */
#include <nds.h>
#include <stdio.h>

static PrintConsole top, bottom;

static void start_ui(void)
{
    videoSetMode(MODE_0_2D);
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 0, true, true);
    consoleInit(&bottom, 0, BgType_Text4bpp, BgSize_T_256x256, 31, 3, false, true);
    consoleSelect(&top);
}

int main(void)
{
    start_ui();
    consoleSelect(&top);
    printf("DSIRB 034J OFFICIAL CORE\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("ARM9 diagnostic only\n");
    printf("No network connection\n");
    printf("No retail game / RA\n");

    consoleSelect(&bottom);
    printf("Official ARM7 A/B boot\n");
    printf("No SD mount or writes\n");
    printf("START: exit\n");

    unsigned frames = 0;
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START)
            break;
        frames++;
        if (frames % 120 == 0) {
            consoleSelect(&bottom);
            printf("\x1b[7;0HLOOP ALIVE: %u frames    ", frames);
        }
    }
    return 0;
}

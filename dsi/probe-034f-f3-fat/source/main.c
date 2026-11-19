/* SPDX-License-Identifier: MIT
 * Diagnostic only. DScheevos ui_init layout, ported from pinned
 * skierrz/dscheevos@59e9978be7b9c3788357ef0a609caf9dc8ea74f3
 * (UI program header and diagnostic display authored in this project).
 * Does not use ROM, RA, game load, NAND, or persistent filesystem writes.
 */
#include <nds.h>
#include <stdio.h>
#include <fat.h>
#include <sys/stat.h>

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
    printf("DSIRB 034F FAT TEST\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("DScheevos-style dual UI\n");
    printf("No retail ROM/RA/network\n");
    consoleSelect(&bottom);
    printf("034F FAT init OK\n\n");
    printf("A: attempt FAT mount ONLY\n");
    printf("START: stop without FAT\n");
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        unsigned keys = keysDown();
        if (keys & KEY_START) return 0;
        if (keys & KEY_A) break;
    }
    consoleSelect(&top);
    printf("FAT MOUNT: attempting...\n");
    /* No fopen write, mkdir, filesystem mutations or ROM access. */
    bool ok = fatInitDefault();
    printf("FAT MOUNT: %s\n", ok ? "YES" : "NO");
    if (ok) {
        struct stat info;
        int sdOk = stat("sd:/", &info) == 0 && S_ISDIR(info.st_mode);
        printf("Internal SD dir: %s\n", sdOk ? "YES" : "NO");
    }
    consoleSelect(&bottom);
    printf("After FAT call.\n");
    printf("START: exit\n");
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START) break;
    }
    return 0;
}

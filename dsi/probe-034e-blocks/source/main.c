/* SPDX-License-Identifier: MIT
 * Diagnostic B: minimal BlocksDS startup with its DEFAULT ARM7.
 * No DSWiFi, no FAT, no files, no game, no RetroAchievements.
 */
#include <nds.h>
#include <stdio.h>

int main(void) {
    consoleDemoInit();
    printf("DSIRB 034E STARTUP B\n");
    printf("BlocksDS/libnds\n\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("No SD mount / writes\n");
    printf("No ROM / RA / Wi-Fi\n");
    printf("\nSTART: exit\n");
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START)
            break;
    }
    return 0;
}

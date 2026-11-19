/* SPDX-License-Identifier: MIT
 * Diagnostic A: proven devkitARM/libnds startup family, no SD, no ROM, no net.
 */
#include <nds.h>
#include <calico.h>
#include <stdio.h>

int main(void) {
    consoleDemoInit();
    iprintf("DSIRB 034E STARTUP A\n");
    iprintf("devkitARM/libnds\n\n");
    iprintf("MAIN REACHED: YES\n");
    iprintf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    iprintf("No SD mount / writes\n");
    iprintf("No ROM / RA / Wi-Fi\n");
    iprintf("\nSTART: exit\n");
    for (;;) {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START)
            break;
    }
    return 0;
}

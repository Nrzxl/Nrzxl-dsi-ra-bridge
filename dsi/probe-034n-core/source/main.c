/* SPDX-License-Identifier: MIT
 * 034N: same ARM9 code for N0/N1. FIFO stage markers from ARM7.
 * No ARM9 network calls or storage/firmware changes.
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
    printf("DSIRB 034N ARM7 STAGES\n");
    printf("MAIN REACHED: YES\n");
    printf("DSi mode: %s\n", isDSiMode() ? "YES" : "NO");
    printf("No WiFi calls / network\n");
    printf("No SD/game/RA/NAND\n");

    consoleSelect(&bottom);
    printf("ARM7 FIFO USER_03 trace\n");
    printf("STAGE 1: waiting\n");
    printf("STAGE 2: waiting\n");
    printf("START: exit\n");

    unsigned stage_mask = 0;
    unsigned frames = 0;
    for (;;)
    {
        swiWaitForVBlank();
        scanKeys();
        if (keysDown() & KEY_START) break;

        while (fifoCheckValue32(FIFO_USER_03))
        {
            u32 value = fifoGetValue32(FIFO_USER_03);
            if (value == 0x4E370001)
                stage_mask |= 1;
            if (value == 0x4E370002)
                stage_mask |= 2;
        }

        if ((frames % 30) == 0)
        {
            consoleSelect(&bottom);
            printf("\x1b[2;0HSTAGE 1: %-7s", (stage_mask & 1) ? "REACHED" : "WAITING");
            printf("\x1b[3;0HSTAGE 2: %-7s", (stage_mask & 2) ? "REACHED" : "WAITING");
        }
        if ((frames % 120) == 0)
        {
            consoleSelect(&bottom);
            printf("\x1b[7;0HLOOP ALIVE: %u frames    ",frames);
        }
        frames++;
    }
    return 0;
}

/* SPDX-License-Identifier: MIT
 * 0.3.4-B capability scout. Own data only. No NDA/NAND/SCFG writes,
 * no ROM loading, no SD writes unless X is explicitly pressed.
 * Not the nds-bootstrap resident module and not a RetroAchievements client. */
#include <nds.h>
#include <calico.h>
#include <fat.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>

extern void *fake_heap_start, *fake_heap_end;
static volatile uint32_t vblank_calls = 0;
static uint8_t owned_buffer[4096];

static void vblank_observer(void) { ++vblank_calls; }

static uint32_t owned_checksum(void) {
    uint32_t hash = 2166136261u;
    for (unsigned i = 0; i < sizeof(owned_buffer); ++i) {
        hash = (hash ^ owned_buffer[i]) * 16777619u;
    }
    return hash;
}

static void export_report(bool dsi_mode, bool internal_sd, uint32_t checksum) {
    if (!dsi_mode || !internal_sd) {
        iprintf("BLOCKED: DSi mode + sd:/ required.\n");
        return;
    }
    const char *folder = "sd:/DSiRABridge_034B";
    if (mkdir(folder, 0777) != 0 && errno != EEXIST) {
        iprintf("Cannot create scout folder.\n");
        return;
    }
    int fd = -1;
    char path[96];
    for (unsigned id = 0; id < 1000; ++id) {
        snprintf(path, sizeof(path), "%s/SCOUT%03u.txt", folder, id);
        fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0666);
        if (fd >= 0) break;
        if (errno != EEXIST) break;
    }
    if (fd < 0) {
        iprintf("BLOCKED: exclusive export failed.\n");
        return;
    }
    char payload[256];
    int n = snprintf(payload, sizeof(payload),
        "version=0.3.4B\n"
        "scope=OWN_BUFFER_AND_VBLANK_ONLY\n"
        "dsi_mode=1\n"
        "internal_sd=1\n"
        "vblank_calls=%lu\n"
        "owned_buffer_bytes=4096\n"
        "owned_checksum=%08lX\n"
        "retail_monitor_ready=0\n"
        "official_awards=0\n",
        (unsigned long)vblank_calls, (unsigned long)checksum);
    bool ok = n > 0 && (size_t)n < sizeof(payload);
    if (ok) {
        size_t written = 0;
        while (written < (size_t)n) {
            ssize_t step = write(fd, payload + written, (size_t)n - written);
            if (step <= 0) { ok = false; break; }
            written += (size_t)step;
        }
    }
    if (close(fd) != 0) ok = false;
    iprintf(ok ? "SCOUT report saved.\n" : "SCOUT export failed.\n");
}

int main(void) {
    consoleDemoInit();
    nocashMessage("@@ SCOUT_034B_MAIN");
    bool dsi_mode = isDSiMode();
    bool internal_sd = false;
    struct stat info;
    if (dsi_mode && fatInitDefault() &&
        stat("sd:/", &info) == 0 && S_ISDIR(info.st_mode)) {
        internal_sd = true;
    }
    for (unsigned i = 0; i < sizeof(owned_buffer); ++i) {
        owned_buffer[i] = (uint8_t)((i * 17u + 7u) & 0xFFu);
    }
    uint32_t checksum = owned_checksum();
    irqSet(IRQ_VBLANK, vblank_observer);
    irqEnable(IRQ_VBLANK);
    iprintf("DSi RA Bridge 034B SCOUT\n");
    iprintf("DSi mode: %s\n", dsi_mode ? "YES" : "NO");
    iprintf("Internal sd: %s\n", internal_sd ? "YES" : "NO");
    iprintf("Own buffer: 4096 bytes\n");
    iprintf("Own hash: %08lX\n", (unsigned long)checksum);
    iprintf("Heap start: %08lX\n", (unsigned long)(uintptr_t)fake_heap_start);
    iprintf("Heap end:   %08lX\n", (unsigned long)(uintptr_t)fake_heap_end);
    iprintf("No retail ROM, no SCFG writes\n");
    iprintf("X after 300f: export ONLY report\n");
    iprintf("START: exit\n");
    if (!dsi_mode || !internal_sd)
        iprintf("BLOCKED: no DSi internal SD gate\n");
    uint32_t shown = 0;
    bool completed = false;
    while (pmMainLoop()) {
        swiWaitForVBlank();
        scanKeys();
        uint32_t keys = keysDown();
        uint32_t now = vblank_calls;
        if (keys & KEY_START) break;
        if ((keys & KEY_X) && now >= 300)
            export_report(dsi_mode, internal_sd, checksum);
        if (now - shown >= 60) {
            shown = now;
            iprintf("\x1b[14;0HVBlank calls: %lu    \n", (unsigned long)now);
        }
        if (now >= 900 && !completed) {
            completed = true;
            nocashMessage("@@ SCOUT_034B_DONE");
        }
    }
    return 0;
}

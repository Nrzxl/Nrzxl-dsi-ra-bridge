/*
 * DSi RA Bridge 0.2.0 diagnostic. Original code, MIT.
 * Controlled memory ONLY. No firmware/NAND APIs, no Wi-Fi, no game hooks.
 * Target: classic libnds 1.8.0 / devkitARM r65.
 */
#include <nds.h>
#include <fat.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>

#define RECORDS 600
#define BYTES 64
#define GUARD 0xC0DECAFEu
static struct {
    uint32_t before;
    volatile uint32_t word[4];
    uint32_t after;
} arena __attribute__((aligned(32)));
static uint8_t records[RECORDS][BYTES];
static uint32_t count, frame, session, errors, max_ticks, bounds_checks;
static bool paused, fat_ready, dsi_mode;
static char status[80] = "No SD writes. A: collect 600 frames.";

static void put16(uint8_t *p, uint16_t x) { p[0]=x; p[1]=x>>8; }
static void put32(uint8_t *p, uint32_t x) {
    p[0]=x; p[1]=x>>8; p[2]=x>>16; p[3]=x>>24;
}
static uint32_t crc32(const uint8_t *p, uint32_t n) {
    uint32_t c=0xFFFFFFFFu;
    for(uint32_t i=0;i<n;i++){
        c^=p[i];
        for(unsigned k=0;k<8;k++) c=(c>>1)^((c&1)?0xEDB88320u:0);
    }
    return c^0xFFFFFFFFu;
}
/* No caller-controlled CPU address: offset is confined to our 16-byte object. */
static bool read_owned(uint32_t off, uint32_t n, uint8_t *dst) {
    const uint32_t size=sizeof(arena.word);
    if(!dst || !n || off>size || n>size-off) return false;
    const volatile uint8_t *src=(const volatile uint8_t*)arena.word;
    for(uint32_t i=0;i<n;i++) dst[i]=src[off+i];
    return true;
}
static void init_arena(void) {
    arena.before=GUARD; arena.after=GUARD;
    arena.word[0]=0x44534931u; arena.word[1]=0;
    arena.word[2]=0; arena.word[3]=0xA5A55A5Au;
}
static void selftest(void) {
    uint8_t tmp[16];
    const bool results[]={
        read_owned(0,16,tmp),read_owned(15,1,tmp),
        !read_owned(16,1,tmp),!read_owned(0,17,tmp),
        !read_owned(0xFFFFFFFFu,4,tmp),!read_owned(0,0,tmp),
        !read_owned(0,1,NULL)
    };
    bounds_checks=sizeof(results)/sizeof(results[0]);
    for(unsigned i=0;i<bounds_checks;i++) if(!results[i]) errors++;
    if(crc32((const uint8_t*)"123456789",9)!=0xCBF43926u) errors++;
}
static void capture(uint32_t buttons) {
    uint8_t raw[16];
    arena.word[1]=frame;
    arena.word[2]=buttons;
    arena.word[3]=frame^buttons^0xA5A55A5Au;
    cpuStartTiming(0); /* timers 0/1 belong solely to this standalone app */
    bool good=read_owned(0,16,raw);
    uint32_t ticks=cpuEndTiming();
    if(ticks>max_ticks) max_ticks=ticks;
    if(!good || arena.before!=GUARD || arena.after!=GUARD) { errors++;paused=true;return; }
    for(unsigned i=0;i<4;i++){
        uint32_t expected=arena.word[i];
        uint32_t actual=(uint32_t)raw[i*4]|((uint32_t)raw[i*4+1]<<8)|
            ((uint32_t)raw[i*4+2]<<16)|((uint32_t)raw[i*4+3]<<24);
        if(actual!=expected) { errors++;paused=true;return; }
    }
    uint8_t *p=records[count]; memset(p,0,BYTES);
    memcpy(p,"DSRB",4);p[4]=1;p[5]=1;p[6]=dsi_mode?1:0;p[7]=1;
    put32(p+8,session);put32(p+12,count);put32(p+16,frame);
    put32(p+20,ticks);put32(p+24,0);
    put16(p+28,44);put16(p+30,4);put16(p+32,16);
    put32(p+36,0xD1A60001u);put32(p+40,(uint32_t)(uintptr_t)arena.word);
    memcpy(p+44,raw,16);put32(p+60,crc32(p,60));
    count++;if(count>=RECORDS) paused=true;
}
/* Only opt-in writes under a new project-specific SD directory.
 * O_EXCL prevents replacement; a short write is left as a clearly named partial file.
 */
static void save_capture(void) {
    paused=true;
    if(!count) { snprintf(status,sizeof(status),"Collect with A first.");return; }
    if(!fat_ready) fat_ready=fatInitDefault();
    if(!fat_ready) { snprintf(status,sizeof(status),"FAT unavailable: no export.");return; }
    const char *root=NULL;
    struct stat st;
    if(stat("sd:/",&st)==0 && S_ISDIR(st.st_mode)) root="sd:";
    /* Deliberately do not fall back to R4 fat:/, NAND or a relative device. */
    if(!root) { snprintf(status,sizeof(status),"Internal sd:/ unavailable. No writes.");return; }
    const char *dir="sd:/DSiRABridge_020";
    if(mkdir(dir,0777)!=0 && errno!=EEXIST) {
        snprintf(status,sizeof(status),"Cannot create project directory.");return;
    }
    if(stat(dir,&st)!=0 || !S_ISDIR(st.st_mode)) {
        snprintf(status,sizeof(status),"Project path is not a directory.");return;
    }
    char path[96];int fd=-1;
    for(unsigned i=0;i<1000;i++){
        snprintf(path,sizeof(path),"%s/CAP%03u.drb",dir,i);
        fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0666);
        if(fd>=0)break;
        if(errno!=EEXIST){snprintf(status,sizeof(status),"Open failed: errno %d",errno);return;}
    }
    if(fd<0){snprintf(status,sizeof(status),"All CAP names used. No writes.");return;}
    uint32_t done=0,total=count*BYTES;
    while(done<total){
        ssize_t n=write(fd,((const uint8_t*)records)+done,total-done);
        if(n<=0)break;
        done+=(uint32_t)n;
    }
    int closed=close(fd);
    if(done!=total || closed!=0)
        snprintf(status,sizeof(status),"PARTIAL CAP file; no overwrite. Retry X.");
    else snprintf(status,sizeof(status),"Saved %lu bytes. CAP file closed.",(unsigned long)total);
}
int main(void) {
    consoleDemoInit();
    dsi_mode=isDSiMode();
    init_arena();selftest();paused=true;
    session=((uint32_t)(uintptr_t)arena.word)^0x44535242u; /* not a security identity */
    while(1){
        swiWaitForVBlank();scanKeys();frame++;
        uint32_t down=keysDown(), held=keysHeld();
        if(down&KEY_START)break;
        if(down&KEY_A){count=0;session++;paused=false;max_ticks=0;}
        if(down&KEY_B)paused=true;
        if(down&KEY_X)save_capture();
        if(!paused)capture(held);
        if((frame%10)==0 || down){
            iprintf("\x1b[2JDSi RA Bridge 0.2.0\nCONTROLLED DIAGNOSTIC ONLY\n\n");
            iprintf("Mode: %s\n",dsi_mode?"DSi runtime":"DS runtime");
            iprintf("Model not independently detected\n");
            iprintf("Expected main RAM: %s\n",dsi_mode?"16 MiB (not probed)":"4 MiB (not probed)");
            iprintf("Owned buffer: %08lX / 16 B\n",(unsigned long)(uintptr_t)arena.word);
            iprintf("Bounds checks: %lu\nErrors: %lu\n",(unsigned long)bounds_checks,(unsigned long)errors);
            iprintf("Samples: %lu / 600 %s\n",(unsigned long)count,paused?"STOP":"RUN");
            iprintf("Read max ticks: %lu\n",(unsigned long)max_ticks);
            iprintf("Timing units: libnds timer ticks\nNot game performance\n\n");
            iprintf("A collect | B pause\nX export to internal SD\nSTART exit\n\n%s\n",status);
        }
    }
    return 0;
}

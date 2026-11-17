/* Independent A loader + resident VBlank monitor. Original MIT fixture.
 * B is a separate cooperative ARM module, not another .nds bootstrap.
 * No NAND/firmware/ARM7 changes. Only own allocations are accessed. */
#include <nds.h>
#include <calico.h>
#include <fat.h>
#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include <string.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include "shared.h"
#include "wire.h"
#define FRAMES 600
static PocState state;
static PocRecord records[FRAMES];
static volatile uint32_t frames=0;
static volatile bool running=false;
static uint32_t max_read_ticks=0;
static void monitor_vblank(void){
 if(!running)return;
 uint32_t f=frames;
 if(f<FRAMES){
  u64 start=tickGetCount();poc_read(&state,&records[f],f,0);
  uint32_t cost=(uint32_t)(tickGetCount()-start);records[f].readTicks=cost;
  if(cost>max_read_ticks)max_read_ticks=cost;
  frames=f+1;state.frame=f+1;
 }
 if(frames>=FRAMES||!(REG_KEYINPUT&KEY_START))state.stop=1;
}
static void export_records(void){
 struct stat st;if(!fatInitDefault()||stat("sd:/",&st)||!S_ISDIR(st.st_mode)){iprintf("sd:/ unavailable.\n");return;}
 const char*dir="sd:/DSiRABridge_032_Resident";
 if(mkdir(dir,0777)&&errno!=EEXIST){iprintf("mkdir failed.\n");return;}
 char name[100];int fd=-1;
 for(unsigned i=0;i<1000;i++){snprintf(name,sizeof(name),"%s/POC%03u.csv",dir,i);fd=open(name,O_WRONLY|O_CREAT|O_EXCL,0666);if(fd>=0)break;if(errno!=EEXIST)break;}
 if(fd<0){iprintf("Exclusive export failed.\n");return;}
 FILE*f=fdopen(fd,"w");if(!f){close(fd);return;}
 fprintf(f,"frame,generation,bframe,counter,checksum,heartbeat,valid,readTicks\n");
 for(unsigned i=0;i<frames;i++){PocRecord*r=&records[i];fprintf(f,"%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu\n",
 (unsigned long)r->frame,(unsigned long)r->generation,(unsigned long)r->bframe,(unsigned long)r->counter,
 (unsigned long)r->checksum,(unsigned long)r->heartbeat,(unsigned long)r->valid,(unsigned long)r->readTicks);}
 int failed=ferror(f);int rc=fclose(f);iprintf(failed||rc?"Export FAILED.\n":"CSV saved. File closed.\n");
}
int main(void){
 consoleDemoInit();iprintf("DSi RA Bridge resident PoC032\nA + cooperative module B\nNOT a retail/NDS game loader\nPhysical test NOT_RUN\nA run 600frames | START exit\n");
 irqSet(IRQ_VBLANK,monitor_vblank);irqEnable(IRQ_VBLANK);
 while(pmMainLoop()){
  swiWaitForVBlank();scanKeys();unsigned key=keysDown();if(key&KEY_START)break;
  if(key&KEY_X){export_records();continue;}if(!(key&KEY_A))continue;
  struct stat st;
  if(!fatInitDefault()||stat("sd:/",&st)||!S_ISDIR(st.st_mode)){iprintf("sd:/ unavailable\n");continue;}
  FILE*f=fopen("sd:/DSiRABridge_032_Resident/payload.dsb","rb");if(!f){iprintf("payload.dsb missing\n");continue;}
  uint8_t header[32]={0};bool ok=fread(header,1,32,f)==32&&memcmp(header,"DSBP",4)==0&&get32(header+4)==1&&get32(header+16)==1;
  uint32_t n=ok?get32(header+8):0;
  for(unsigned i=20;i<32;i++)if(header[i])ok=false;
  if(!ok||!n||n>4096){fclose(f);iprintf("Invalid bounded header\n");continue;}
  void*code=memalign(32,(n+31)&~31u);if(!code){fclose(f);iprintf("Allocation failed\n");continue;}
  ok=fread(code,1,n,f)==n&&fgetc(f)==EOF&&crc32(code,n)==get32(header+12);fclose(f);
  if(!ok){free(code);iprintf("Payload CRC/length FAILED\n");continue;}
  memset(&state,0,sizeof(state));state.magic=POC_MAGIC;state.abi=1;state.guard=POC_GUARD;
  state.counter=7;state.checksum=7^0xA55A9321u;frames=0;max_read_ticks=0;
  armDCacheFlush(code,n);armICacheInvalidate(code,n);
  iprintf("B executing, A VBlank resident.\nSTART aborts; automatic stop ~10s\n");
  running=true;((void(*)(PocState*))code)(&state);running=false;
  free(code);unsigned valid=0;for(unsigned i=0;i<frames;i++)valid+=records[i].valid?1:0;
  iprintf("Returned to A. Frames %lu\nValid %u; rejected %lu\nMax read %lu ticks\nA rerun | X CSV | START exit\n",
   (unsigned long)frames,valid,(unsigned long)(frames-valid),(unsigned long)max_read_ticks);
 }
 return 0;
}

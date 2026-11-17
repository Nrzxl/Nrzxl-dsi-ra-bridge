/* Original MIT. Independent .nds fixture, no observer API or module imports.
 * This program has its own Calico ARM9 startup and the SDK's complete ARM7.
 * Heap budget and raw lab-window export are diagnostic app features. */
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
extern void *fake_heap_start,*fake_heap_end;
typedef struct {uint32_t generation,counter,buttons,checksum,tag;} GameState;
volatile GameState game_state;
__attribute__((used)) const char fixture_identity[]="DSI_RA_INDEPENDENT_FIXTURE_033";
void systemUserStartup(void){
 if((uintptr_t)fake_heap_end>0x02100000u)fake_heap_end=(void*)0x02100000u;
}
__attribute__((used,noinline,target("arm"))) void game_update(void){
 game_state.generation++;
 game_state.counter++;game_state.buttons=(~REG_KEYINPUT)&0x3FF;
 game_state.checksum=game_state.counter^game_state.buttons^0x9317A55Au;
 game_state.generation++;
}
__attribute__((used,noinline,naked,target("arm"))) void game_vblank(void){
 __asm__ volatile("push {r4,lr}\nbl game_update\npop {r4,pc}\n");
}
static void raw_export(void){
 /* Export only this tagged, bounded lab window. Never general RAM or a stack. */
 const uint8_t*window=(const uint8_t*)0x02200000;
 if(memcmp(window,"DSIOBS33",8)){iprintf("No tagged lab window. Nothing saved.\n");return;}
 if(*(const volatile uint32_t*)0x02202008<1200){iprintf("Wait for 1200 frames before X.\n");return;}
 struct stat st;
 if(!fatInitDefault()||stat("sd:/",&st)||!S_ISDIR(st.st_mode)){iprintf("sd:/ unavailable; no other device used.\n");return;}
 const char*dir="sd:/DSiRABridge_033";if(mkdir(dir,0777)&&errno!=EEXIST)return;
 char name[100];int fd=-1;
 for(unsigned i=0;i<1000;i++){snprintf(name,sizeof(name),"%s/OBS%03u.bin",dir,i);fd=open(name,O_WRONLY|O_CREAT|O_EXCL,0666);if(fd>=0)break;if(errno!=EEXIST)break;}
 if(fd<0){iprintf("Exclusive create failed.\n");return;}
 uint32_t done=0;
 /* The monitor stops storing records at 1200. Require that stable phase. */

 while(done<0xD000){int n=write(fd,window+done,0xD000-done);if(n<=0)break;done+=(unsigned)n;}
 int rc=close(fd);iprintf(done==0xD000&&!rc?"Tagged window saved.\n":"Export FAILED.\n");
}
int main(void){
 if((uintptr_t)fake_heap_start>=0x02100000u)return 2;
 consoleDemoInit();iprintf("%s\n",fixture_identity);
 memset((void*)&game_state,0,sizeof(game_state));game_state.tag=0x47414D33u;game_state.checksum=0x9317A55Au;
 irqSet(IRQ_VBLANK,game_vblank);irqEnable(IRQ_VBLANK);
 nocashMessage("@@ FIXTURE_B_MAIN independent NDS");
 iprintf("Independent Fixture B033\nOwn startup, IRQ, ARM7 and input\nA/B change color | X tagged export\nSTART exits; no saves or NAND.\n");
 uint32_t shown=0;bool marker=false;
 while(pmMainLoop()){
  swiWaitForVBlank();scanKeys();uint32_t keys=keysDown(),count=game_state.counter;
  if(keys&KEY_START)break;
  if(keys&KEY_A)BG_PALETTE[0]=RGB15(0,12,20);
  if(keys&KEY_B)BG_PALETTE[0]=RGB15(10,0,18);
  if(keys&KEY_X)raw_export();
  if(count-shown>=60){shown=count;iprintf("\x1b[6;0HGame frame %lu\nButtons %lu\n",(unsigned long)count,(unsigned long)game_state.buttons);}
  if(count>=1800&&!marker){marker=true;nocashMessage("@@ FIXTURE_B_DONE");}
 }
 return 0;
}

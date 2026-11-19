/* SPDX-License-Identifier: GPL-2.0-or-later
 * Original launcher glue. Uses the attributed hbmenu loader in this directory.
 * No NAND/firmware/config writes. Only a pinned fixture in a new SD directory. */
#include <nds.h>
#include <calico.h>
#include <fat.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <sys/stat.h>
#include "nds_loader_arm9.h"
#include "expected.h"
static uint32_t update_crc(uint32_t c,const uint8_t*p,unsigned n){
 for(unsigned i=0;i<n;i++){c^=p[i];for(unsigned j=0;j<8;j++)c=(c>>1)^((c&1)?0xEDB88320u:0);}return c;
}
int main(void){
 consoleDemoInit();nocashMessage("@@ LAUNCH_A_ENTER");
#ifdef RESIDENT_EMU_LAB
 const char*path="fat:/DSiRABridge_041/Fixture_B_041_observed.nds";
 iprintf("EMU LAB ONLY: synthetic FAT card\n");
#else
 const char*path="sd:/DSiRABridge_041/Fixture_B_041_observed.nds";
 iprintf("DSi RA Bridge041 Launcher A\nIndependent NDS B + external hook\n");
 if(!isDSiMode()){iprintf("BLOCKED: require DSi mode + internal SD.\n");goto wait_exit;}
#endif
 if(!fatInitDefault()){iprintf("BLOCKED: filesystem unavailable.\n");goto wait_exit;}
#ifndef RESIDENT_EMU_LAB
 struct stat sd;if(stat("sd:/",&sd)||!S_ISDIR(sd.st_mode)){iprintf("BLOCKED: no sd:/; no other device used.\n");goto wait_exit;}
#endif
 FILE*f=fopen(path,"rb");if(!f){iprintf("BLOCKED: fixture missing in new directory.\n");goto wait_exit;}
 uint8_t buffer[1024];uint32_t crc=0xFFFFFFFFu,total=0;size_t n;
 while((n=fread(buffer,1,sizeof(buffer),f))!=0){
  if(n>LAB_B_BYTES-total){total=LAB_B_BYTES+1;break;}
  total+=(uint32_t)n;crc=update_crc(crc,buffer,(unsigned)n);
 }
 int err=ferror(f);fclose(f);crc^=0xFFFFFFFFu;
 if(err||total!=LAB_B_BYTES||crc!=LAB_B_CRC){iprintf("BLOCKED: pinned fixture size/CRC mismatch.\n");goto wait_exit;}
 iprintf("Fixture integrity PASS. Mode %s\nA launch | START exit\n",isDSiMode()?"DSi":"DS");
 for(;;){
#ifdef RESIDENT_EMU_LAB
  bool launch=true;
#else
  swiWaitForVBlank();scanKeys();if(keysDown()&KEY_START)return 0;bool launch=keysDown()&KEY_A;
#endif
  if(launch){
   const char*args[1]={path};nocashMessage("@@ A_CHAINLOAD_ACCEPTED");
   eRunNdsRetCode rc=runNdsFile(path,1,args);
   iprintf("Loader returned error %d\n",(int)rc);nocashMessage("@@ A_CHAINLOAD_FAILED");break;
  }
 }
wait_exit:
 while(pmMainLoop()){swiWaitForVBlank();scanKeys();if(keysDown()&KEY_START)break;}
 return 0;
}

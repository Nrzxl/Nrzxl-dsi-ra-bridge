/* MIT. Read-only official Nintendo DS hash; no login or network. */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "rc_hash.h"
#include "rc_consoles.h"
static uint32_t le(const unsigned char*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
int main(int argc,char**argv){
 if(argc!=2){fprintf(stderr,"usage: dsirb_nds_hash ORIGINAL.nds\n");return 2;}
 FILE*f=fopen(argv[1],"rb");if(!f)return 3;
 unsigned char h[512];if(fread(h,1,512,f)!=512){fclose(f);return 4;}
 if(fseek(f,0,SEEK_END)){fclose(f);return 4;}long length=ftell(f);fclose(f);
 uint32_t a=le(h+0x20),n=le(h+0x2c),b=le(h+0x30),m=le(h+0x3c),icon=le(h+0x68);
 if(length<512||n==0||m==0||n>16*1024*1024u||m>16*1024*1024u-n||
    a<512||b<512||(uint64_t)a+n>(uint64_t)length||(uint64_t)b+m>(uint64_t)length||icon>=(uint64_t)length){fprintf(stderr,"unsupported or truncated NDS\n");return 5;}
 char hash[33];if(!rc_hash_generate_from_file(hash,RC_CONSOLE_NINTENDO_DS,argv[1]))return 6;
 printf("{\"status\":\"PASS\",\"algorithm\":\"official_rcheevos_nintendo_ds\",\"console_id\":%u,\"hash\":\"%s\",\"game_resolved\":false,\"submitted\":false}\n",RC_CONSOLE_NINTENDO_DS,hash);
 return 0;
}

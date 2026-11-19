/* Real host-compiled serializer exercise for 041 using the original 030 wire.h. */
#include <stdio.h>
#include <stdint.h>
#include "wire.h"
int main(void){
 uint8_t h[20],b[64];
 uint32_t counter=1234,buttons=3,session=0x41003341;
 uint32_t words[4]={0x44534931u,counter,buttons,counter^buttons^0xA5A55A5Au};
 wire_control(h,"DSH3",1,1,session,0xD531010Au);
 wire_sample(b,1,1,session,0,counter,2,0,0x02006400u,words);
 if(fwrite(h,1,20,stdout)!=20)return 1;
 if(fwrite(b,1,64,stdout)!=64)return 2;
 return 0;
}

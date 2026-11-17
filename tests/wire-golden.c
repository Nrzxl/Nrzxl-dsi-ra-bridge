#include <stdio.h>
#include "wire.h"
static void hex(const uint8_t*p,unsigned n){for(unsigned i=0;i<n;i++)printf("%02x",p[i]);puts("");}
int main(void){
 uint8_t h[20],p[64];const uint32_t w[4]={0x44534931u,131,0x1001,131^0x1001^0xA5A55A5Au};
 wire_control(h,"DSH3",1,1,0xFFFFFFFFu,73);hex(h,20);
 wire_sample(p,1,1,0xFFFFFFFFu,0x7FFFFFFEu,131,3,4,0x02001000,w);hex(p,64);
 return 0;
}
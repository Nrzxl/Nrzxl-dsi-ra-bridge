#ifndef DSRB_WIRE_H
#define DSRB_WIRE_H
#include <stdint.h>
#include <string.h>
static inline void put16(uint8_t*p,uint16_t v){p[0]=v;p[1]=v>>8;}
static inline void put32(uint8_t*p,uint32_t v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;}
static inline uint32_t get32(const uint8_t*p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static inline uint32_t crc32(const uint8_t*p,unsigned n){
 uint32_t c=0xFFFFFFFFu;for(unsigned i=0;i<n;i++){c^=p[i];for(int j=0;j<8;j++)c=(c>>1)^((c&1)?0xEDB88320u:0);}return c^0xFFFFFFFFu;
}

static inline void wire_control(uint8_t*p,const char*magic,uint8_t source,uint8_t mode,uint32_t session,uint32_t nonce){
 memset(p,0,20);memcpy(p,magic,4);p[4]=1;p[5]=source;p[6]=mode;
 put32(p+8,session);put32(p+12,nonce);put32(p+16,crc32(p,16));
}
static inline void wire_sample(uint8_t*p,uint8_t source,uint8_t mode,uint32_t session,uint32_t seq,
 uint32_t frame,uint32_t ticks,uint32_t dropped,uint32_t address,const uint32_t*words){
 memset(p,0,64);memcpy(p,"DSRB",4);p[4]=1;p[5]=source;p[6]=mode;p[7]=1;
 put32(p+8,session);put32(p+12,seq);put32(p+16,frame);put32(p+20,ticks);put32(p+24,dropped);
 put16(p+28,44);put16(p+30,4);put16(p+32,16);put32(p+36,0xD1A60001u);put32(p+40,address);
 for(unsigned i=0;i<4;i++){put32(p+44+i*4,words[i]);}
 put32(p+60,crc32(p,60));
}
#endif

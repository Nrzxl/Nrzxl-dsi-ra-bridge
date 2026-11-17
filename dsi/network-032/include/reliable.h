#ifndef DSRB_RELIABLE_H
#define DSRB_RELIABLE_H
#include "wire.h"
#include <stdbool.h>
#define R_SIZE 96
#define R_WIN 32
#define R_ATTEMPTS 6
enum {R_DATA=1,R_HELLO,R_ACK,R_STATUS,R_FIN,R_FINACK,R_PING,R_PONG};
typedef struct {uint32_t lo,hi,seq,a,b;uint8_t kind,source,mode,retry;const uint8_t*payload;} RPacket;
static inline void r_wire(uint8_t*p,unsigned kind,unsigned source,unsigned mode,uint32_t lo,uint32_t hi,
 uint32_t seq,uint32_t a,uint32_t b,bool retry,const uint8_t*payload){
 memset(p,0,96);memcpy(p,"DSR2",4);p[4]=2;p[5]=kind;p[6]=source;p[7]=(mode<<1)|(retry?1:0);
 put32(p+8,lo);put32(p+12,hi);put32(p+16,seq);put32(p+20,a);put32(p+24,b);
 if(payload){memcpy(p+28,payload,64);}
 put32(p+92,crc32(p,92));
}
static inline bool r_parse(RPacket*out,const uint8_t*p,unsigned n){
 if(n!=96||memcmp(p,"DSR2",4)||p[4]!=2||p[5]<1||p[5]>8||p[6]<1||p[6]>2||p[7]>3||get32(p+92)!=crc32(p,92))return false;
 out->kind=p[5];out->source=p[6];out->mode=p[7]>>1;out->retry=p[7]&1;
 out->lo=get32(p+8);out->hi=get32(p+12);out->seq=get32(p+16);out->a=get32(p+20);out->b=get32(p+24);out->payload=p+28;
 return (out->lo||out->hi)&&(!out->retry||out->kind==R_DATA);
}
typedef struct {uint8_t data[64],attempts;bool valid,sacked;
 uint32_t seq,capture_ms,first_ms,last_ms;} REntry;
typedef struct {REntry entries[32];uint32_t base,next,credit,rto,srtt,rttvar;
 uint32_t queued,original_attempts,original_accepted,retry_attempts,retry_accepted,send_failed,
 acked,ack_rx,ack_duplicate,ack_late,ack_invalid,backpressure,peak,exhausted,capture_ack_max;
 uint32_t last_ack_seq,last_ack_mask;bool has_ack,failed;} RSender;
static inline void r_init(RSender*s,uint32_t start){
 memset(s,0,sizeof(*s));s->base=s->next=start;s->credit=32;s->rto=300;
}
static inline uint32_t r_pending(const RSender*s){return s->next-s->base;}
static inline bool r_offer(RSender*s,const uint8_t*data,uint32_t now){
 if(s->failed||r_pending(s)>=32){s->backpressure++;return false;}
 REntry*e=&s->entries[s->next&31];memset(e,0,sizeof(*e));e->valid=true;e->seq=s->next++;
 e->capture_ms=now;memcpy(e->data,data,64);s->queued++;
 if(r_pending(s)>s->peak){s->peak=r_pending(s);}
 return true;
}
static inline void r_rtt(RSender*s,uint32_t ms){
 if(!s->srtt){s->srtt=ms?ms:1;s->rttvar=(ms+1)/2;}
 else{uint32_t err=s->srtt>ms?s->srtt-ms:ms-s->srtt;
 s->rttvar=(3*s->rttvar+err)/4;s->srtt=(7*s->srtt+ms)/8;}
 s->rto=s->srtt+4*s->rttvar;if(s->rto<100)s->rto=100;if(s->rto>2000)s->rto=2000;
}
static inline bool r_ack(RSender*s,uint32_t next,uint32_t mask,uint32_t credit,uint32_t now){
 s->ack_rx++;uint32_t d=next-s->base;
 if(d>=0x80000000u){s->ack_late++;return false;}
 if(d>r_pending(s)||credit>32){s->ack_invalid++;return false;}
 for(uint32_t i=0;i<d;i++){
  REntry*e=&s->entries[(s->base+i)&31];if(!e->valid||e->seq!=s->base+i||!e->attempts){s->ack_invalid++;return false;}
 }
 for(uint32_t i=0;i<32;i++)if(mask&(1u<<i)){
  if(i>=s->next-next||!s->entries[(next+i)&31].attempts){s->ack_invalid++;return false;}
 }
 if(s->has_ack&&s->last_ack_seq==next&&s->last_ack_mask==mask)s->ack_duplicate++;
 s->has_ack=true;s->last_ack_seq=next;s->last_ack_mask=mask;s->credit=credit;
 for(uint32_t i=0;i<d;i++){
  REntry*e=&s->entries[(s->base+i)&31];if(!e->valid||e->seq!=s->base+i){s->failed=true;return false;}
  if(e->attempts==1)r_rtt(s,now-e->first_ms); /* Karn: no RTT sample from retries */
  uint32_t delay=now-e->capture_ms;if(delay>s->capture_ack_max)s->capture_ack_max=delay;
  e->valid=false;s->acked++;
 }
 s->base=next;
 for(uint32_t i=0;i<32&&i<r_pending(s);i++)if(mask&(1u<<i))s->entries[(next+i)&31].sacked=true;
 return true;
}
static inline REntry*r_due(RSender*s,uint32_t now){
 if(s->failed)return NULL;
 for(uint32_t i=0;i<r_pending(s);i++){
  REntry*e=&s->entries[(s->base+i)&31];if(!e->valid||e->sacked)continue;
  if(!e->attempts){if(s->credit)return e;continue;}
  uint32_t timeout=s->rto<<(e->attempts-1);if(timeout>2000)timeout=2000;
  if(now-e->last_ms>=timeout){
   if(e->attempts>=R_ATTEMPTS){s->exhausted++;s->failed=true;return NULL;}return e;
  }
 }
 return NULL;
}
static inline void r_sent(RSender*s,REntry*e,uint32_t now,bool accepted){
 if(!e->attempts){e->first_ms=now;s->original_attempts++;if(accepted)s->original_accepted++;}
 else{s->retry_attempts++;if(accepted)s->retry_accepted++;}
 if(!accepted)s->send_failed++;
 if(!e->attempts&&accepted&&s->credit)s->credit--;
 e->attempts++;e->last_ms=now;
}
#endif

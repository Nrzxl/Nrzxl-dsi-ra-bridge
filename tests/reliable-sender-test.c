#include "../dsi/network-032/include/reliable.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
static uint8_t data[64];
static void run(unsigned count,uint32_t start){
 RSender s;r_init(&s,start);unsigned delivered=0;uint32_t now=0;bool held[32]={0};
 bool lost66=false,lost555=false;unsigned retries=0;
 while(delivered<count&&now<2000000){
  while(s.queued<count&&r_pending(&s)<32){assert(r_offer(&s,data,now));}
  for(unsigned j=0;j<8;j++){
   REntry*e=r_due(&s,now);if(!e)break;
   uint32_t off=e->seq-start;bool drop=false;
   if(off==66&&!lost66){lost66=true;drop=true;}
   if(off==555&&!lost555){lost555=true;drop=true;}
   if(e->attempts)retries++;
   r_sent(&s,e,now,true);
   if(!drop)held[e->seq&31]=true;
  }
  while(delivered<count&&held[(start+delivered)&31]){held[(start+delivered)&31]=false;delivered++;}
  uint32_t next=start+delivered,mask=0;
  for(unsigned j=0;j<32;j++)if(held[(next+j)&31])mask|=1u<<j;
  assert(r_ack(&s,next,mask,32,now+4));
  if(now%100==0)assert(r_ack(&s,next,mask,32,now+5)); /* duplicated ACK */
  now+=10;
 }
 assert(delivered==count&&s.acked==count&&s.original_attempts==count&&s.send_failed==0);
 if(count>555)assert(s.retry_attempts>=2&&retries>=2);
 assert(!s.failed&&s.peak<=32);
}
int main(void){
 run(600,0);run(1200,0);run(6000,0);run(600,0xFFFFFF00u);
 RSender s;r_init(&s,0);assert(r_offer(&s,data,0));REntry*e=r_due(&s,0);assert(e);r_sent(&s,e,0,false);
 assert(s.send_failed==1&&!r_due(&s,50));assert(r_due(&s,300));assert(!r_ack(&s,100,0,32,400));
 assert(!r_ack(&s,0,0,33,400));
 r_init(&s,0);for(unsigned i=0;i<32;i++)assert(r_offer(&s,data,0));assert(!r_offer(&s,data,0));
 assert(s.backpressure==1);assert(r_ack(&s,0,0,0,1));assert(!r_due(&s,100)); /* receiver pressure */
 r_init(&s,0);assert(r_offer(&s,data,0));
 for(unsigned attempt=0;attempt<6;attempt++){e=r_due(&s,attempt*3000);assert(e);r_sent(&s,e,attempt*3000,true);}
 assert(!r_due(&s,18000)&&s.failed&&s.exhausted==1);
 puts("{\"status\":\"PASS\",\"productionC\":true,\"sessions\":[600,1200,6000],\"loss\":[66,555],\"wrap\":true,\"retryBound\":6,\"window\":32}");
 return 0;
}

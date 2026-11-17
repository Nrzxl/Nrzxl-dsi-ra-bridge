/* Host pilot for the exact production C sender. No sockets in this helper. */
#include "../dsi/network-032/include/reliable.h"
#include <stdio.h>
#include <stdlib.h>
static int unhex(uint8_t*out,const char*hex,unsigned n){
 for(unsigned i=0;i<n;i++){unsigned x;if(sscanf(hex+2*i,"%2x",&x)!=1)return 0;out[i]=x;}return 1;
}
static void hexout(const uint8_t*b,unsigned n){for(unsigned i=0;i<n;i++)printf("%02x",b[i]);}
int main(int argc,char**argv){
 if(argc!=4)return 2;uint32_t lo=(uint32_t)strtoul(argv[1],NULL,10),hi=(uint32_t)strtoul(argv[2],NULL,10);
 RSender s;r_init(&s,(uint32_t)strtoul(argv[3],NULL,10));char line[512],hex[256],op;unsigned a,b,c,d;
 uint8_t data[64],out[96];bool fail_next=false;
 while(fgets(line,sizeof(line),stdin)){
  op=line[0];
  if(op=='O'&&sscanf(line+1,"%u %128s",&a,hex)==2&&strlen(hex)==128&&unhex(data,hex,64))
   printf("Q %u\n",r_offer(&s,data,a)?1:0);
  else if(op=='A'&&sscanf(line+1,"%u %u %u %u",&a,&b,&c,&d)==4){
   (void)r_ack(&s,a,b,c,d);puts("A");
  }else if(op=='T'&&sscanf(line+1,"%u",&a)==1){
   for(unsigned i=0;i<8;i++){
    REntry*e=r_due(&s,a);if(!e)break;
    unsigned attempt=e->attempts+1;
    r_wire(out,R_DATA,2,1,lo,hi,e->seq,attempt,e->capture_ms,attempt>1,e->data);
    r_sent(&s,e,a,!fail_next);
    if(!fail_next){printf("D ");hexout(out,96);putchar('\n');}
    else{puts("SEND_FAILED");fail_next=false;}
   }puts("T");
  }else if(op=='F'){fail_next=true;puts("F");}
  else if(op=='S'){
   printf("S {\"base\":%u,\"next\":%u,\"queued\":%u,\"acked\":%u,\"pending\":%u,"
    "\"originalAttempts\":%u,\"originalAccepted\":%u,\"retryAttempts\":%u,\"retryAccepted\":%u,"
    "\"sendFailed\":%u,\"rtoMs\":%u,\"queuePeak\":%u,\"backpressure\":%u,\"failed\":%s,\"captureToAckMaxMs\":%u,\"ackLate\":%u,\"ackDuplicate\":%u,\"ackInvalid\":%u}\n",
    s.base,s.next,s.queued,s.acked,r_pending(&s),s.original_attempts,s.original_accepted,s.retry_attempts,s.retry_accepted,
    s.send_failed,s.rto,s.peak,s.backpressure,s.failed?"true":"false",s.capture_ack_max,s.ack_late,s.ack_duplicate,s.ack_invalid);
  }else if(op=='G'){
   uint32_t words[4]={0x44534931u,66,0,66^0xA5A55A5Au};
   wire_sample(data,2,1,lo,66,396,2,0,0,words);
   r_wire(out,R_DATA,2,1,lo,hi,66,2,1234,true,data);printf("G ");hexout(out,96);putchar('\n');
  }else puts("ERROR");
  fflush(stdout);
 }
 return 0;
}

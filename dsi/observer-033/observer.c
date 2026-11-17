/* Original MIT. External ARM9 observer, no SDK, network, SD or game writes. */
#include "observer.h"
static __attribute__((always_inline)) inline uint32_t crc32(const uint8_t*p,unsigned n){
 uint32_t c=0xFFFFFFFFu;for(unsigned i=0;i<n;i++){c^=p[i];for(unsigned j=0;j<8;j++)c=(c>>1)^((c&1)?0xEDB88320u:0);}return c^0xFFFFFFFFu;
}
__attribute__((used,noinline,target("arm"))) void observer_sample(void){
 const volatile ObserverHeader*h=(const volatile ObserverHeader*)OBS_BASE;
 volatile ObserverState*s=(volatile ObserverState*)OBS_STATE;
 uint32_t sp;__asm__ volatile("mov %0, sp":"=r"(sp));
 if(!s->min_sp||sp<s->min_sp)s->min_sp=sp;
 if(*(const volatile uint32_t*)OBS_STACK_LOW!=0xA5A5A5A5u)s->guard_failed++;
 uint32_t call=s->calls++;
 if(h->version!=1||h->watch_size!=20||h->watch_address<0x02000000u||
  h->watch_address>0x02100000u-20||(h->watch_address&3)||
  h->capacity!=OBS_CAPACITY||h->record_size!=32||h->ring_address!=OBS_RING){s->bad_config++;return;}
 const volatile WatchedState*w=(const volatile WatchedState*)h->watch_address;
 uint32_t line0=*(const volatile uint16_t*)0x04000006;
 uint32_t before=w->generation,counter=w->counter,buttons=w->buttons,sum=w->checksum,tag=w->tag,after=w->generation;
 s->last_counter=counter;if(!call)s->first_counter=counter;
 if(s->stored>=OBS_CAPACITY)return; /* observation remains active; fixed recording interval */
 ObserverRecord r={call,before,counter,buttons,sum,0,0,0};
 r.valid=before==after&&!(before&1)&&tag==0x47414D33u&&sum==(counter^buttons^0x9317A55Au);
 if(!r.valid)s->invalid++;
 uint32_t line1=*(const volatile uint16_t*)0x04000006;
 r.lines=line1>=line0?line1-line0:line1+263-line0;
 if(r.lines>s->max_lines)s->max_lines=r.lines;
 r.crc=crc32((const uint8_t*)&r,28);
 volatile ObserverRecord*dest=(volatile ObserverRecord*)(OBS_RING+s->stored*32);
 const uint32_t*src=(const uint32_t*)&r;volatile uint32_t*out=(volatile uint32_t*)dest;
 for(unsigned i=0;i<8;i++)out[i]=src[i];
 s->stored++;
}

#ifndef DSRB_RESIDENT_SHARED_H
#define DSRB_RESIDENT_SHARED_H
#include <stdint.h>
#define POC_MAGIC 0x44534232u
#define POC_GUARD 0x51A9C37Du
typedef struct {volatile uint32_t magic,abi,stop,frame,generation,bframe,counter,checksum,heartbeat,guard;} PocState;
typedef struct {uint32_t frame,generation,bframe,counter,checksum,heartbeat,valid,readTicks;} PocRecord;
/* Original resident A reader. Reject a copy interrupted inside B's publication. */
static inline void poc_read(const PocState*s,PocRecord*r,uint32_t frame,uint32_t ticks){
 uint32_t before=s->generation;
 r->frame=frame;r->bframe=s->bframe;r->counter=s->counter;r->checksum=s->checksum;
 r->heartbeat=s->heartbeat;r->generation=before;r->readTicks=ticks;
 uint32_t after=s->generation;
 r->valid=before==after&&!(before&1)&&s->magic==POC_MAGIC&&s->abi==1&&s->guard==POC_GUARD&&
  r->counter==r->bframe*3+7&&r->checksum==(r->counter^0xA55A9321u)&&r->heartbeat==0xB032CAFEu;
}
#endif

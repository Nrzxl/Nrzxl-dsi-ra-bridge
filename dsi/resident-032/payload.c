/* Program B: separately compiled position-independent ARM code, no SDK imports.
 * Cooperative ABI only. Not a standalone .nds and not a retail game loader. */
#include "shared.h"
__attribute__((section(".text.entry"),used))
void payload_entry(PocState*s){
 if(s->magic!=POC_MAGIC||s->abi!=1||s->guard!=POC_GUARD)return;
 uint32_t prior=0xFFFFFFFFu;
 while(!s->stop){
  uint32_t frame=s->frame;if(frame==prior)continue;
  s->generation++; /* odd: publication in progress; ARM9 monitor must reject */
  s->bframe=frame;s->counter=frame*3+7;s->checksum=s->counter^0xA55A9321u;s->heartbeat=0xB032CAFEu;
  s->generation++; /* even: committed */
  prior=frame;
 }
}

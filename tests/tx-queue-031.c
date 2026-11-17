#include "../dsi/network/include/tx_queue.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
int main(void){
 TxQueue q={0};uint8_t p[64]={0},out[64];uint32_t seq;
 for(unsigned i=0;i<1800;i++){
  p[0]=i&255;assert(tx_offer(&q,p,i));assert(tx_take(&q,out,&seq));assert(seq==i&&out[0]==(i&255));
  tx_result(&q,i!=5);assert(!tx_take(&q,out,&seq)); /* no implicit retransmit on error */
 }
 assert(q.attempts==1800&&q.failed==1&&q.succeeded==1799);
 assert(tx_offer(&q,p,1800));assert(!tx_offer(&q,p,1801));assert(q.dropped==1);
 assert(tx_take(&q,out,&seq)&&seq==1800);q.pending=false;assert(!tx_take(&q,out,&seq));
 puts("{\"status\":\"PASS\",\"queue\":\"production C helper\",\"snapshots\":1800,\"failedSendNoRetry\":true}");
 return 0;
}

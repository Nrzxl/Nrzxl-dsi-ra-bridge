#ifndef DSRB_TX_QUEUE_H
#define DSRB_TX_QUEUE_H
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
/* Caller holds irqLock. Consume before send; errors are never silently retried. */
typedef struct {uint8_t packet[64];uint32_t sequence;bool pending;
 uint32_t offered,dropped,taken,attempts,succeeded,failed;} TxQueue;
static inline bool tx_offer(TxQueue*q,const uint8_t*p,uint32_t seq){
 q->offered++;if(q->pending){q->dropped++;return false;}
 memcpy(q->packet,p,64);q->sequence=seq;q->pending=true;return true;
}
static inline bool tx_take(TxQueue*q,uint8_t*p,uint32_t*seq){
 if(!q->pending)return false;
 memcpy(p,q->packet,64);*seq=q->sequence;q->pending=false;q->taken++;return true;
}
static inline void tx_result(TxQueue*q,bool success){
 q->attempts++;if(success)q->succeeded++;else q->failed++;
}
#endif

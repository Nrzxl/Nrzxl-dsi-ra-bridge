#ifndef DSRB_OBSERVER033_H
#define DSRB_OBSERVER033_H
#include <stdint.h>
#define OBS_BASE 0x02200000u
#define OBS_END 0x02220000u
#define OBS_STATE 0x02202000u
#define OBS_RING 0x02203000u
#define OBS_CAPACITY 1200
#define OBS_STACK_LOW 0x0221C000u
#define OBS_STACK_TOP 0x02220000u
typedef struct {char magic[8];uint32_t version,header_size,watch_size,watch_address,hook_address,resume_address,
 ring_address,record_size,capacity,state_address,stack_low,stack_top,source_word,reserved;} ObserverHeader;
typedef struct {uint32_t calls,invalid,stored,max_lines,last_counter,first_counter,min_sp,guard_failed,
 bad_config,reserved[7];} ObserverState;
typedef struct {uint32_t frame,generation,counter,buttons,checksum,lines,valid,crc;} ObserverRecord;
typedef struct {volatile uint32_t generation,counter,buttons,checksum,tag;} WatchedState;
#endif

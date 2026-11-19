/* MIT — 041 fixture-only adapter, not a universal monitor. */
#ifndef DSI_RABRIDGE_NETWORK041_H
#define DSI_RABRIDGE_NETWORK041_H
#include <stdbool.h>
#include <stdint.h>
void network041_start(void);
void network041_stop(void);
void network041_poll(void);
bool network041_done(void);
const char *network041_status(void);
uint32_t network041_sent(void);
#endif

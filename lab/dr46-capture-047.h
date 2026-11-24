#ifndef DSI_RA_DR46_CAPTURE_047_H
#define DSI_RA_DR46_CAPTURE_047_H
/* Portable, read-only wire encoder candidate for ARM9, NOT yet installed.
 * No direct hardware reads, IRQ hooks, networking, auth, awards or writes.
 * In the actual hardware integration, callback must safely read the user's
 * running game at a precise frame boundary, without touching game state.
 */
#include <stdint.h>
#include <stddef.h>

#define DR46_MAX_REGIONS 32u
#define DR46_MAX_PACKET 1080u
#define DR46_MAX_BODY 1024u
#define DR46_MAIN 0u
#define DR46_DTCM 1u

typedef struct dr46_watch_t {
  uint8_t bank;
  uint32_t offset;
  uint16_t size;
} dr46_watch_t;

typedef struct dr46_capture_input_t {
  const uint8_t* session16;
  const uint8_t* game_hash16;
  uint32_t sequence;
  uint32_t frame;
} dr46_capture_input_t;

typedef uint16_t (*dr46_read_memory_fn)(uint8_t bank, uint32_t offset,
                                       uint8_t* target, uint16_t size, void* ctx);

/* Returns packet size on success, zero on failure. Caller owns out buffer.
 * Fail closed: any unreadable address returns zero packet, no partial send.
 * Watchlist sorted by (bank,offset), disjoint, len <=256 each.
 */
size_t dr46_capture_encode(const dr46_capture_input_t* input,
                           const dr46_watch_t* watch, size_t watch_count,
                           dr46_read_memory_fn read_memory, void* ctx,
                           uint8_t* out, size_t out_capacity);
#endif

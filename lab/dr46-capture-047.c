#include "dr46-capture-047.h"
#include <string.h>

/* No zlib dependency on the ARM9 candidate. Standard CRC32/ISO-HDLC. */
static uint32_t checksum(const uint8_t* data, size_t n, uint32_t state) {
  size_t i;
  for (i = 0; i < n; ++i) {
    unsigned j;
    state ^= data[i];
    for (j = 0; j < 8u; ++j)
      state = (state >> 1) ^ ((state & 1u) ? 0xedb88320u : 0u);
  }
  return state;
}
static void set16(uint8_t* p, uint16_t n) {
  p[0] = (uint8_t)n; p[1] = (uint8_t)(n >> 8);
}
static void set32(uint8_t* p, uint32_t n) {
  p[0] = (uint8_t)n;
  p[1] = (uint8_t)(n >> 8);
  p[2] = (uint8_t)(n >> 16);
  p[3] = (uint8_t)(n >> 24);
}
static const uint8_t asmp_eu_hash[16] = {
  0xba, 0x3c, 0x40, 0x52, 0xe0, 0x0c, 0x5c, 0xc3,
  0x1d, 0xf5, 0xd5, 0x53, 0x4c, 0x39, 0xde, 0x1b
};
size_t dr46_capture_encode(const dr46_capture_input_t* input,
                           const dr46_watch_t* watch, size_t count,
                           dr46_read_memory_fn read_memory, void* ctx,
                           uint8_t* out, size_t capacity) {
  static const uint8_t zeros[16] = {0};
  size_t i, body = 0, pos;
  dr46_watch_t previous = {0,0,0};
  uint32_t crc;
  if (!input || !input->session16 || !input->game_hash16 || !watch ||
      !read_memory || !out || capacity < 56u ||
      !count || count > DR46_MAX_REGIONS ||
      input->frame == 0xffffffffu || input->sequence == 0xffffffffu ||
      !memcmp(input->session16, zeros, 16) ||
      memcmp(input->game_hash16, asmp_eu_hash, 16))
    return 0;

  /* Validate ALL regions before any memory read. */
  for (i = 0; i < count; ++i) {
    uint32_t limit = watch[i].bank == DR46_MAIN ? 0x400000u :
                     (watch[i].bank == DR46_DTCM ? 0x4000u : 0u);
    if (!limit || watch[i].size == 0 || watch[i].size > 256 ||
        watch[i].offset >= limit ||
        watch[i].size > limit - watch[i].offset ||
        (i && (watch[i].bank < previous.bank ||
         (watch[i].bank == previous.bank &&
          watch[i].offset < previous.offset + previous.size))))
      return 0;
    if (body + 7u + watch[i].size > DR46_MAX_BODY)
      return 0;
    body += 7u + watch[i].size;
    previous = watch[i];
  }
  if (capacity < 56u + body)
    return 0;

  /* Exact counterpart of Python frame-bridge-046.py BASE/CRC/REGION. */
  memcpy(out, "DR46", 4);
  out[4] = 1; out[5] = 0;
  set16(out + 6, 0);
  memcpy(out + 8, input->session16, 16);
  memcpy(out + 24, input->game_hash16, 16);
  set32(out + 40, input->sequence);
  set32(out + 44, input->frame);
  set16(out + 48, (uint16_t)count);
  set16(out + 50, (uint16_t)body);
  pos = 56;
  for (i = 0; i < count; ++i) {
    const dr46_watch_t* w = &watch[i];
    out[pos] = w->bank;
    set32(out + pos + 1, w->offset);
    set16(out + pos + 5, w->size);
    pos += 7;
    /* No memory writes: only the provided read-only callback. */
    if (read_memory(w->bank, w->offset, out + pos, w->size, ctx) != w->size)
      return 0; /* Caller MUST drop this partially assembled packet. */
    pos += w->size;
  }
  crc = 0xffffffffu;
  crc = checksum(out, 52, crc);
  crc = checksum(out + 56, body, crc) ^ 0xffffffffu;
  set32(out + 52, crc);
  return pos;
}

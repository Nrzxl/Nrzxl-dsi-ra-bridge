/* Host-only test of ARM9-candidate encoder; synthetic bytes, no hardware. */
#include "dr46-capture-047.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static const uint8_t session[16] = {
  0x04,0x60,0x04,0x60,0x04,0x60,0x04,0x60,
  0x04,0x60,0x04,0x60,0x04,0x60,0x04,0x60
};
static const uint8_t hash[16] = {
  0xba,0x3c,0x40,0x52,0xe0,0x0c,0x5c,0xc3,
  0x1d,0xf5,0xd5,0x53,0x4c,0x39,0xde,0x1b
};
static uint16_t fake_read(uint8_t bank, uint32_t off,
                          uint8_t* out, uint16_t size, void* ctx) {
  (void)ctx;
  if (bank == 0 && off == 0x100u && size == 2u) {
    out[0] = 0; out[1] = 0;
    return 2;
  }
  if (bank == 1 && off == 0x20u && size == 1u) {
    out[0] = 0;
    return 1;
  }
  return 0;
}
static uint16_t short_read(uint8_t bank, uint32_t off,
                           uint8_t* out, uint16_t size, void* ctx) {
  (void)bank; (void)off; (void)out; (void)ctx;
  return (uint16_t)(size - 1);
}
int main(int argc, char** argv) {
  dr46_capture_input_t in = {session, hash, 0, 0};
  const dr46_watch_t valid[2] = {{0,0x100u,2}, {1,0x20u,1}};
  const dr46_watch_t overlap[2] = {{0,0x100u,2}, {0,0x101u,1}};
  uint8_t packet[DR46_MAX_PACKET];
  size_t size;
  FILE* f;
  if (argc != 2)
    return 2;
  if (dr46_capture_encode(&in, overlap, 2, fake_read, NULL,
                          packet, sizeof(packet)) != 0)
    return 3;
  if (dr46_capture_encode(&in, valid, 2, short_read, NULL,
                          packet, sizeof(packet)) != 0)
    return 4;
  if (dr46_capture_encode(&in, valid, 2, fake_read, NULL,
                          packet, 56) != 0)
    return 5;
  size = dr46_capture_encode(&in, valid, 2, fake_read, NULL,
                             packet, sizeof(packet));
  if (size != 73u || memcmp(packet, "DR46", 4))
    return 6;
  f = fopen(argv[1], "wb");
  if (!f)
    return 7;
  if (fwrite(packet, 1, size, f) != size) {
    fclose(f);
    return 8;
  }
  fclose(f);
  puts("DSI047_PORTABLE_C_ENCODER_SYNTHETIC_PASS bytes=73");
  return 0;
}

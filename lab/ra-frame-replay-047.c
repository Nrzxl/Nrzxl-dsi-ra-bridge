/*
 * DSi RA Bridge 0.4.7: host-only replay of DR46 v1 memory frames using
 * REAL pinned rcheevos rc_runtime. No emulator, RA network, auth, ROM, NAND,
 * account or official award submission. Conditions are loaded only from
 * a user-local TSV. NEVER publish authorized raw trigger TSV.
 *
 * Requires -lz. Protocol is an offline REPLAY, not a live DSi capture.
 */
#include "rc_runtime.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#define MAX_PACKET 1080
#define HEADER_BYTES 52
#define CRC_BYTES 4
#define MAX_REGIONS 32
#define MAIN_BYTES 0x400000u
#define DTCM_BASE 0x1000000u
#define DTCM_BYTES 0x4000u
#define MAX_FRAMES 600000u
#define MAX_CONDITIONS 2500u
#define LINE_BYTES 32768
#define SYN_STAR_ID 46001u
#define SYN_COIN_ID 46002u

static const uint8_t g_expected_hash[16] = {
  0xba, 0x3c, 0x40, 0x52, 0xe0, 0x0c, 0x5c, 0xc3,
  0x1d, 0xf5, 0xd5, 0x53, 0x4c, 0x39, 0xde, 0x1b
};
typedef struct watched_t {
  uint32_t offset;
  uint16_t size;
  uint8_t bank;
  const uint8_t* bytes;
} watched_t;

static watched_t g_regions[MAX_REGIONS];
static unsigned g_region_count;
static uint8_t g_packet[MAX_PACKET];
static uint8_t g_session[16];
static unsigned g_have_session;
static uint32_t g_next_sequence;
static uint32_t g_next_frame;
static unsigned g_have_frame;
static unsigned g_missing_memory;
static unsigned long g_read_calls;
static unsigned long g_events;
static unsigned long g_stars;
static unsigned long g_coins;

static uint16_t u16(const uint8_t* p) {
  return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t u32(const uint8_t* p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
         ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static void die(const char* reason) {
  /* Static errors only; never emit raw logic, patch paths or private data. */
  fprintf(stderr, "DSI047_LOCAL_REPLAY_BLOCKED reason=%s official_awards=NO\n", reason);
  exit(2);
}
static uint32_t peek(uint32_t address, uint8_t* buffer, uint32_t n, void* ud) {
  uint32_t bank, offset, i;
  (void)ud;
  ++g_read_calls;
  if (!n || n > 256u) {
    g_missing_memory = 1;
    return 0;
  }
  if (address < MAIN_BYTES && n <= MAIN_BYTES - address) {
    bank = 0;
    offset = address;
  } else if (address >= DTCM_BASE &&
             address < DTCM_BASE + DTCM_BYTES &&
             n <= DTCM_BYTES - (address - DTCM_BASE)) {
    bank = 1;
    offset = address - DTCM_BASE;
  } else {
    g_missing_memory = 1;
    return 0;
  }
  for (i = 0; i < g_region_count; ++i) {
    const watched_t* r = &g_regions[i];
    if (r->bank == bank && offset >= r->offset &&
        n <= r->size && offset - r->offset <= (uint32_t)r->size - n) {
      memcpy(buffer, r->bytes + offset - r->offset, n);
      return n;
    }
  }
  g_missing_memory = 1;
  return 0;
}
static void on_event(const rc_runtime_event_t* e) {
  if (e->type == RC_RUNTIME_EVENT_ACHIEVEMENT_TRIGGERED) {
    ++g_events;              /* local event only; NOT an RA award */
    if (e->id == SYN_STAR_ID) ++g_stars;
    if (e->id == SYN_COIN_ID) ++g_coins;
  }
}
static unsigned read_manifest(FILE* mf, rc_runtime_t* runtime, int* synthetic) {
  char line[LINE_BYTES], *expr, *end;
  unsigned count = 0;
  uint32_t last_id = 0;
  unsigned long id;
  if (!fgets(line, sizeof(line), mf))
    die("empty_manifest");
  if (strncmp(line, "DSIRB047\t9983\t", 14) != 0)
    die("manifest_header_bad");
  end = line + strlen(line);
  if (end == line || end[-1] != '\n')
    die("manifest_header_unterminated");
  *synthetic = (strcmp(line + 14, "SYNTHETIC_ONLY\n") == 0);
  if (!*synthetic) {
    /* Require official catalog fingerprint exactly 64 lowercase hex. */
    const char* p = line + 14;
    unsigned i;
    if (strlen(p) != 65 || p[64] != '\n')
      die("manifest_catalog_revision_invalid");
    for (i = 0; i < 64; ++i)
      if (!((p[i] >= '0' && p[i] <= '9') ||
            (p[i] >= 'a' && p[i] <= 'f')))
        die("manifest_catalog_revision_invalid");
  }
  while (fgets(line, sizeof(line), mf)) {
    if (++count > MAX_CONDITIONS)
      die("too_many_conditions");
    end = line + strlen(line);
    if (end == line || end[-1] != '\n')
      die("condition_line_oversize");
    end[-1] = '\0';
    expr = strchr(line, '\t');
    if (!expr || strchr(expr + 1, '\t'))
      die("condition_row_bad");
    *expr++ = '\0';
    if (!*expr || strlen(expr) > 30000)
      die("raw_condition_empty_or_oversize");
    id = strtoul(line, &end, 10);
    if (*line == '\0' || *end != '\0' || id == 0 ||
        id > 0xffffffffUL || id <= last_id)
      die("condition_id_invalid_or_duplicate");
    last_id = (uint32_t)id;
    if (rc_runtime_activate_achievement(runtime, (uint32_t)id, expr, NULL, 0) != 0)
      die("rcheevos_activation_failed");
  }
  if (ferror(mf) || count == 0)
    die("manifest_read_error_or_empty");
  return count;
}
static void accept_frame(const uint8_t* p, size_t n, rc_runtime_t* runtime) {
  uint16_t count, body_len;
  uint32_t seq, frame;
  uint32_t actual_crc, claimed_crc;
  unsigned i;
  size_t pos;
  watched_t last;
  uint8_t zeros[16] = {0};
  if (n < HEADER_BYTES + CRC_BYTES || n > MAX_PACKET)
    die("frame_packet_size");
  if (memcmp(p, "DR46", 4) || p[4] != 1 || p[5] || u16(p+6))
    die("frame_version_or_flags");
  if (memcmp(p + 24, g_expected_hash, 16) || !memcmp(p+8, zeros, 16))
    die("game_hash_or_session_invalid");
  seq = u32(p + 40);
  frame = u32(p + 44);
  count = u16(p + 48);
  body_len = u16(p + 50);
  if (!count || count > MAX_REGIONS ||
      body_len > 1024 || n != HEADER_BYTES + CRC_BYTES + body_len)
    die("region_count_or_body_size");
  claimed_crc = u32(p + 52);
  actual_crc = (uint32_t)crc32(0L, Z_NULL, 0);
  actual_crc = (uint32_t)crc32(actual_crc, p, HEADER_BYTES);
  actual_crc = (uint32_t)crc32(actual_crc, p + HEADER_BYTES + CRC_BYTES, body_len);
  if (actual_crc != claimed_crc)
    die("crc32_mismatch");
  if (seq != g_next_sequence || seq == 0xffffffffu || frame == 0xffffffffu)
    die("missing_or_duplicate_sequence");
  if (g_have_frame && frame != g_next_frame)
    die("missing_or_duplicate_frame");
  if (!g_have_session) {
    memcpy(g_session, p + 8, 16);
    g_have_session = 1;
  } else if (memcmp(g_session, p + 8, 16)) {
    die("session_changed");
  }
  pos = HEADER_BYTES + CRC_BYTES;
  memset(&last, 0, sizeof(last));
  for (i = 0; i < count; ++i) {
    uint8_t bank;
    uint32_t offset, limit;
    uint16_t len;
    if (pos + 7u > n)
      die("truncated_region_header");
    bank = p[pos];
    offset = u32(p + pos + 1u);
    len = u16(p + pos + 5u);
    pos += 7;
    limit = bank == 0 ? MAIN_BYTES : (bank == 1 ? DTCM_BYTES : 0);
    if (!limit || len == 0 || len > 256 ||
        offset >= limit || len > limit - offset || pos + len > n)
      die("invalid_region_bounds");
    if (i && (bank < last.bank ||
         (bank == last.bank && offset < last.offset + last.size)))
      die("unordered_or_overlapping_regions");
    g_regions[i].offset = offset;
    g_regions[i].size = len;
    g_regions[i].bank = bank;
    g_regions[i].bytes = p + pos;
    last = g_regions[i];
    pos += len;
  }
  if (pos != n)
    die("trailing_packet_bytes");
  g_region_count = count;
  g_missing_memory = 0;
  rc_runtime_do_frame(runtime, on_event, peek, NULL, NULL);
  if (g_missing_memory)
    die("watchlist_missing_required_memory");
  g_next_sequence = seq + 1;
  g_next_frame = frame + 1;
  g_have_frame = 1;
}
int main(int argc, char** argv) {
  FILE* input;
  FILE* manifest;
  rc_runtime_t runtime;
  unsigned frames = 0, conditions;
  int synthetic = 0, expect_synthetic = 0;
  unsigned char length_bytes[2];
  if (argc < 3 || argc > 4)
    die("usage_manifest_stream_optional_synthetic_expect");
  if (argc == 4) {
    if (strcmp(argv[3], "--expect-synthetic"))
      die("unknown_flag");
    expect_synthetic = 1;
  }
  manifest = fopen(argv[1], "rb");
  if (!manifest) die("manifest_not_found");
  input = fopen(argv[2], "rb");
  if (!input) die("frame_stream_not_found");
  rc_runtime_init(&runtime);
  conditions = read_manifest(manifest, &runtime, &synthetic);
  fclose(manifest);
  if (expect_synthetic && !synthetic)
    die("synthetic_flag_requires_synthetic_manifest");
  while (1) {
    size_t got = fread(length_bytes, 1, 2, input);
    uint16_t n;
    if (got == 0) {
      if (ferror(input)) die("stream_io_error");
      break;
    }
    if (got != 2) die("partial_frame_length");
    n = u16(length_bytes);
    if (n < HEADER_BYTES + CRC_BYTES || n > MAX_PACKET)
      die("framed_length_invalid");
    if (fread(g_packet, 1, n, input) != n)
      die("partial_frame_packet");
    if (frames >= MAX_FRAMES)
      die("excess_frames");
    accept_frame(g_packet, n, &runtime);
    ++frames;
  }
  fclose(input);
  if (!frames) die("no_frames");
  if (expect_synthetic && (frames != 5 || conditions != 3 ||
         g_events != 2 || g_stars != 1 || g_coins != 1))
    die("synthetic_expected_events_missing");
  printf("DSI047_HOST_RCHEEVOS_REPLAY_PASS frames=%u conditions=%u "
         "local_trigger_events=%lu read_callbacks=%lu synthetic=%s "
         "physical_dsi=NOT_RUN official_awards=NO\n",
         frames, conditions, g_events, g_read_calls, synthetic ? "YES" : "NO");
  rc_runtime_destroy(&runtime);
  return 0;
}

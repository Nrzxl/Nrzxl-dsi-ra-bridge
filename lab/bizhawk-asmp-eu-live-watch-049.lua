-- DSi RA Bridge 049 PC-only read-only BizHawk monitor for EU ASMP.
-- No memory writes, cheats, saves, RA requests or network.
-- Coin counter observed in real PC captures; other fields unverified.
-- Compatibility: only use read_bytes_as_binary_string already exercised in 048.
local DOMAIN, SIZE = "Main RAM", 4194304
local FIELDS = {
  {"yellow_coins", "Moedas", 0x09F358, 1},
  {"red_coins", "Vermelhas?", 0x09F30C, 1},
  {"silver_stars", "Prateadas?", 0x09F310, 1},
  {"lives", "Vidas?", 0x09F2F4, 1},
  {"level_id", "Fase?", 0x09F2F8, 1},
  {"health_primary", "Saude A?", 0x11117C, 2},
  {"health_alternate", "Saude B?", 0x092144, 2},
  {"player_select", "Personagem?", 0x09CAE1, 1}
}
assert(type(memory.read_bytes_as_binary_string) == "function",
       "BizHawk does not expose binary read used by 048 captures")
local has_main, has_asmp, wrong_cart = false, false, false
for _, name in pairs(memory.getmemorydomainlist()) do
  if name == DOMAIN then has_main = true end
  if type(name) == "string" and name:lower():find("rom",1,true)
      and not name:lower():find("bios",1,true) then
    local ok, code = pcall(memory.read_bytes_as_binary_string, 0x0C, 4, name)
    if ok and code == "ASMP" then has_asmp = true end
    if ok and type(code) == "string" and #code == 4
        and code:match("^[A-Z0-9]+$") and code ~= "ASMP" then
      wrong_cart = true
    end
  end
end
assert(has_main and memory.getmemorydomainsize(DOMAIN) == SIZE,
       "DS 4MiB Main RAM required")
assert(has_asmp and not wrong_cart,
       "ASMP cartridge header absent/contradicted; blocked")

-- A proven 048 API returns raw bytes. Decode 1/2-byte little-endian
-- manually instead of relying on read_u8/read_u16_le availability.
local function read_value(offset, width)
  assert((width == 1 or width == 2) and offset + width <= SIZE,
         "Unsupported known-memory field")
  local bytes = memory.read_bytes_as_binary_string(offset, width, DOMAIN)
  assert(type(bytes) == "string" and #bytes == width,
         "Incomplete read at Main RAM " .. string.format("0x%06X", offset))
  local low = string.byte(bytes, 1)
  if width == 1 then return low end
  return low + 256 * string.byte(bytes, 2)
end

print("[DSIRB049] READ ONLY, ASMP header only; no active-ROM RA hash proof.")
print("[DSIRB049] Uses 048 verified binary read API (8-/16-bit decoder).")
print("[DSIRB049] ? fields are hypotheses; stop script to exit.")
local previous = {}
while true do
  local frame = emu.framecount()
  gui.text(2,2,"DSIRB049 ASMP EU - read only")
  for i, field in ipairs(FIELDS) do
    local value = read_value(field[3], field[4])
    if previous[i] ~= nil and previous[i] ~= value then
      print(string.format("[DSIRB049] frame=%d %s 0x%08X %d -> %d",
        frame, field[1], 0x02000000 + field[3], previous[i], value))
    end
    previous[i] = value
    gui.text(2,13+i*12,string.format("%s: %d",field[2],value))
  end
  emu.frameadvance()
end

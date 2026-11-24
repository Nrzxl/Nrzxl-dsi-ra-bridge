-- 049 ASMP EU PC-only read-only BizHawk monitor; source: 049 catalog.
-- ABSOLUTELY no memory writes, cheats, saves, RA requests or network.
-- Yellow coins replicated 0->1,3->4,4->5 on PC; other fields tentative.
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
local main, asmp, other = false, false, false
for _, name in pairs(memory.getmemorydomainlist()) do
  if name == DOMAIN then main = true end
  if type(name) == "string" and name:lower():find("rom",1,true)
      and not name:lower():find("bios",1,true) then
    local ok, code = pcall(memory.read_bytes_as_binary_string,0x0C,4,name)
    if ok and code == "ASMP" then asmp = true end
    if ok and type(code) == "string" and #code == 4
        and code:match("^[A-Z0-9]+$") and code ~= "ASMP" then other = true end
  end
end
assert(main and memory.getmemorydomainsize(DOMAIN) == SIZE, "DS 4MiB Main RAM required")
assert(asmp and not other, "ASMP cartridge header absent/contradicted; blocked")
assert(type(memory.read_u8) == "function" and type(memory.read_u16_le) == "function",
       "BizHawk memory read API missing")
print("[DSIRB049] READ ONLY; ASMP header match is NOT ROM RA hash verification.")
print("[DSIRB049] Fields marked ? are UNVERIFIED; stop script to exit.")
local prev = {}
while true do
  local frame = emu.framecount()
  gui.text(2,2,"DSIRB049 ASMP EU - read only")
  for i, field in ipairs(FIELDS) do
    local val = field[4] == 1 and memory.read_u8(field[3],DOMAIN)
                             or memory.read_u16_le(field[3],DOMAIN)
    assert(type(val) == "number", "Memory read failed")
    if prev[i] ~= nil and prev[i] ~= val then
      print(string.format("[DSIRB049] frame=%d %s 0x%08X %d -> %d",
        frame,field[1],0x02000000+field[3],prev[i],val))
    end
    prev[i] = val
    gui.text(2,13+i*12,string.format("%s: %d",field[2],val))
  end
  emu.frameadvance()
end

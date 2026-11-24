-- DSi RA Bridge 049: PC-only ASMP EU known-address watch, READ ONLY.
-- No memory writes, cheats, savestates, ROM dumps, RA awards or network.
-- PAL coin address 0x0209F358 correlated with HUD 0->1, 3->4, 4->5.
-- Other field widths and meanings remain provisional/unverified.
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

local function good(bytes, count)
  if type(bytes) ~= "table" then return false end
  for i=1,count do
    local value = bytes[i]
    if type(value) ~= "number" or value < 0 or value > 255 or value%1 ~= 0 then
      return false
    end
  end
  return true
end

-- Probe actual callable behavior, NOT type(method) == "function". Some
-- BizHawk versions do not offer binary string reads (added in v2.11).
local readers = {
  {"binary_string", function(offset,count,domain)
    local raw = memory.read_bytes_as_binary_string(offset,count,domain)
    assert(type(raw) == "string" and #raw == count, "Invalid binary RAM read")
    local bytes = {}
    for i=1,count do bytes[i]=string.byte(raw,i) end
    return bytes
  end},
  {"bytes_array", function(offset,count,domain)
    local raw = memory.read_bytes_as_array(offset,count,domain)
    assert(raw ~= nil, "Missing RAM array")
    local one = {}
    for i=1,count do one[i]=raw[i] end
    if good(one,count) then return one end
    local zero = {}
    for i=1,count do zero[i]=raw[i-1] end
    assert(good(zero,count), "Invalid RAM array indexing")
    return zero
  end},
  {"read_u8", function(offset,count,domain)
    local bytes = {}
    for i=1,count do bytes[i]=memory.read_u8(offset+i-1,domain) end
    return bytes
  end},
  {"readbyte", function(offset,count,domain)
    local bytes = {}
    for i=1,count do bytes[i]=memory.readbyte(offset+i-1,domain) end
    return bytes
  end}
}

local has_main=false
local rom_domains={}
for _,domain in pairs(memory.getmemorydomainlist()) do
  if domain == DOMAIN then has_main=true end
  if type(domain) == "string" and domain:lower():find("rom",1,true)
      and not domain:lower():find("bios",1,true) then
    rom_domains[#rom_domains+1]=domain
  end
end
assert(has_main and memory.getmemorydomainsize(DOMAIN)==SIZE,
       "DS mode 4MiB Main RAM required")

local selected=nil
for _,entry in ipairs(readers) do
  local ok,bytes=pcall(entry[2],0,2,DOMAIN)
  if ok and good(bytes,2) then selected=entry; break end
end
assert(selected, "No compatible read-only BizHawk memory API (binary/array/u8/readbyte)")
print("[DSIRB049] Reader selected: " .. selected[1] .. " (actual successful probe)")
local read=selected[2]

local asmp,wrong_code=false,false
for _,domain in ipairs(rom_domains) do
  local ok,bytes=pcall(read,0x0C,4,domain)
  if ok and good(bytes,4) then
    local code=string.char(bytes[1],bytes[2],bytes[3],bytes[4])
    if code=="ASMP" then
      asmp=true
    elseif code:match("^[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]$") then
      wrong_code=true
    end
  end
end
assert(asmp and not wrong_code,
       "ASMP cartridge header unavailable or contradictory; LIVE watch blocked")

local function read_value(offset,width)
  assert((width==1 or width==2) and offset>=0 and offset+width<=SIZE,
         "Unsupported known-memory field")
  local bytes=read(offset,width,DOMAIN)
  assert(good(bytes,width),string.format("RAM read invalid at 0x%06X",offset))
  return width==1 and bytes[1] or bytes[1]+256*bytes[2]
end

print("[DSIRB049] ASMP HEADER ONLY; loaded ROM RA hash NOT attested.")
print("[DSIRB049] Read-only EU hypotheses. No official conditions/awards.")
local previous={}
while true do
  local frame=emu.framecount()
  gui.text(2,2,"DSIRB049 ASMP EU - read only")
  for i,field in ipairs(FIELDS) do
    local value=read_value(field[3],field[4])
    if previous[i]~=nil and previous[i]~=value then
      print(string.format("[DSIRB049] frame=%d %s 0x%08X %d -> %d",
        frame,field[1],0x02000000+field[3],previous[i],value))
    end
    previous[i]=value
    gui.text(2,13+i*12,string.format("%s: %d",field[2],value))
  end
  emu.frameadvance()
end

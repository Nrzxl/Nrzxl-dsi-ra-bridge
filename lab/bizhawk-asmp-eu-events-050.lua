-- DSi RA Bridge 0.5.0: ASMP/EU BizHawk event detector (PC LAB ONLY).
-- OBSERVATION, NOT official RA conditions or awards. No ROM writes/saves/SD/network.
-- Source observations: coins 0x0209F358, HP 0x0211117C, HP2 0x02092144.
-- HP2 == HP * 256 + 128 ONLY demonstrated at 7/8; lower values tentative.
local DOMAIN, SIZE = "Main RAM", 4194304
local WARMUP_FRAMES, PAIR_WINDOW, COIN_WINDOW = 45, 2, 2

local function valid(bytes,n)
  if type(bytes) ~= "table" then return false end
  for i=1,n do
    local x=bytes[i]
    if type(x)~="number" or x<0 or x>255 or x%1~=0 then return false end
  end
  return true
end
-- Use the 049 real-run compatibility strategy: successfully probe actual reads.
-- No assertions about NLua proxy type or presence of a particular method.
local readers={
  {"binary_string",function(offset,n,domain)
    local b=memory.read_bytes_as_binary_string(offset,n,domain)
    assert(type(b)=="string" and #b==n,"bad binary read")
    local out={}
    for i=1,n do out[i]=string.byte(b,i) end
    return out
  end},
  {"bytes_array",function(offset,n,domain)
    local b=memory.read_bytes_as_array(offset,n,domain)
    assert(b~=nil,"array missing")
    local one={}
    for i=1,n do one[i]=b[i] end
    if valid(one,n) then return one end
    local zero={}
    for i=1,n do zero[i]=b[i-1] end
    assert(valid(zero,n),"bad array read")
    return zero
  end},
  {"read_u8",function(offset,n,domain)
    local out={}
    for i=1,n do out[i]=memory.read_u8(offset+i-1,domain) end
    return out
  end},
  {"readbyte",function(offset,n,domain)
    local out={}
    for i=1,n do out[i]=memory.readbyte(offset+i-1,domain) end
    return out
  end}
}
local main,roms=false,{}
for _,domain in pairs(memory.getmemorydomainlist()) do
  if domain==DOMAIN then main=true end
  if type(domain)=="string" and domain:lower():find("rom",1,true)
      and not domain:lower():find("bios",1,true) then
    roms[#roms+1]=domain
  end
end
assert(main and memory.getmemorydomainsize(DOMAIN)==SIZE,
       "050 requires DS mode Main RAM 4MiB")
local selected=nil
for _,candidate in ipairs(readers) do
  local ok,read=pcall(candidate[2],0,2,DOMAIN)
  if ok and valid(read,2) then selected=candidate; break end
end
assert(selected,"050 no supported read-only memory API")
local read=selected[2]
print("[DSIRB050] Reader selected: "..selected[1].." (probed)")
local matched,contradicted=false,false
for _,domain in ipairs(roms) do
  local ok,header=pcall(read,0x0C,4,domain)
  if ok and valid(header,4) then
    local code=string.char(header[1],header[2],header[3],header[4])
    if code=="ASMP" then matched=true
    elseif code:match("^[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]$") then
      contradicted=true
    end
  end
end
assert(matched and not contradicted,"050 ASMP header missing/contradicted; blocked")

local function read_num(offset,n)
  assert(n==1 or n==2,"unsupported width")
  assert(offset>=0 and offset+n<=SIZE,"offset outside Main RAM")
  local b=read(offset,n,DOMAIN)
  assert(valid(b,n),string.format("Main RAM read failed 0x%06X",offset))
  if n==1 then return b[1] end
  return b[1]+256*b[2]
end
local function sample()
  return {
    coins=read_num(0x09F358,1),
    lives=read_num(0x09F2F4,1),
    level=read_num(0x09F2F8,1),
    hp=read_num(0x11117C,2),
    alt=read_num(0x092144,2),
    character=read_num(0x09CAE1,1)
  }
end

local previous=nil
local last_level_frame=nil
local ready_since=nil
local armed=false
local accepted_hp=nil
local mismatch_since=nil
local hp_change,alt_change=nil,nil
local last_coin_frame=nil
local events=0
local function notify(frame,kind,detail)
  events=events+1
  print(string.format("[DSIRB050] frame=%d EVENT %s %s [PC OBSERVED, NO RA AWARD]",
    frame,kind,detail or ""))
end
local function disarm()
  armed=false
  ready_since=nil
  accepted_hp=nil
  mismatch_since=nil
  hp_change=nil
  alt_change=nil
  last_coin_frame=nil
end

print("[DSIRB050] ASMP HEADER ONLY; loaded ROM RA hash NOT attested.")
print("[DSIRB050] 45-frame loading guard; HP dual-source pairing <=2 frames.")
print("[DSIRB050] No official RA conditions/awards, no DSi hardware, read only.")
while true do
  local frame=emu.framecount()
  local now=sample()
  local level_changed=previous~=nil and now.level~=previous.level
  if level_changed then
    notify(frame,"PHASE_TRANSITION_OBSERVED",
      string.format("level=%d->%d; loading gate reset",previous.level,now.level))
    last_level_frame=frame
    disarm()
  end
  if last_level_frame==nil then last_level_frame=frame end

  if previous and now.hp~=previous.hp then hp_change=frame end
  if previous and now.alt~=previous.alt then alt_change=frame end

  local primary_valid=now.hp>=1 and now.hp<=8
  -- This correspondence is observed at 7/8 and still needs other values tested.
  local coherent=primary_valid and (now.alt==now.hp*256+128)
  if now.level==0 or not primary_valid then
    if armed then
      print(string.format("[DSIRB050] frame=%d GUARD invalid/load health=%d alt=%d",
        frame,now.hp,now.alt))
    end
    disarm()
  elseif not coherent then
    if mismatch_since==nil then mismatch_since=frame end
    if frame-mismatch_since>PAIR_WINDOW then
      if armed then
        print(string.format("[DSIRB050] frame=%d GUARD unpaired health values; no event",frame))
      end
      disarm()
    end
  else
    mismatch_since=nil
    if not armed then
      if ready_since==nil then ready_since=frame end
      if frame-last_level_frame>=WARMUP_FRAMES
          and frame-ready_since>=WARMUP_FRAMES then
        armed=true
        accepted_hp=now.hp
        hp_change=nil
        alt_change=nil
        last_coin_frame=nil
        print(string.format("[DSIRB050] frame=%d ARMED level=%d hp=%d (observation only)",
          frame,now.level,now.hp))
      end
    end
  end

  -- A coin pickup can precede a health field update by 1-2 emulator frames.
  if previous and now.coins==previous.coins+1 and armed
      and not level_changed then
    last_coin_frame=frame
    notify(frame,"COIN_UP_OBSERVED",string.format("%d->%d",
      previous.coins,now.coins))
  elseif previous and now.coins~=previous.coins and
      now.coins~=previous.coins+1 then
    last_coin_frame=nil
  end

  if armed and coherent and accepted_hp~=nil and now.hp~=accepted_hp then
    local synchronized=hp_change~=nil and alt_change~=nil
        and math.abs(hp_change-alt_change)<=PAIR_WINDOW
    if synchronized and math.abs(now.hp-accepted_hp)==1 then
      if now.hp<accepted_hp then
        notify(frame,"DAMAGE_OBSERVED",string.format(
          "hp=%d->%d alt=%d (dual-source)",accepted_hp,now.hp,now.alt))
      else
        local correlated=last_coin_frame~=nil
            and frame>=last_coin_frame and frame-last_coin_frame<=COIN_WINDOW
        if correlated then
          notify(frame,"HEALTH_RECOVERY_COIN_CORRELATED",string.format(
            "hp=%d->%d alt=%d coin_frame=%d (correlation not causality)",
            accepted_hp,now.hp,now.alt,last_coin_frame))
        else
          notify(frame,"HEALTH_RECOVERY_UNATTRIBUTED",string.format(
            "hp=%d->%d alt=%d (no recent coin)",accepted_hp,now.hp,now.alt))
        end
      end
      accepted_hp=now.hp
      hp_change=nil
      alt_change=nil
      last_coin_frame=nil
    else
      -- No claim for out-of-window updates or unexplained multi-unit changes.
      print(string.format("[DSIRB050] frame=%d GUARD health change not synchronized; disarmed",frame))
      disarm()
    end
  end

  gui.text(2,2,"DSIRB050 PC detector - no RA awards")
  gui.text(2,15,string.format("Fase %d  Moedas %d  Vidas %d",now.level,now.coins,now.lives))
  gui.text(2,28,string.format("HP %d  Alt %d  Armado: %s",now.hp,now.alt,
    armed and "SIM" or "NAO"))
  gui.text(2,41,string.format("Eventos observados: %d",events))
  previous=now
  emu.frameadvance()
end

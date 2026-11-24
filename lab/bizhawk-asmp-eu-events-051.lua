-- DSi RA Bridge 0.5.1: ASMP EU event validation on PC / BizHawk ONLY.
-- READ-ONLY; no ROM, save, SD, NAND, rcheevos/RA login, award or network calls.
-- Addresses other than yellow coins remain hypotheses pending real-game QA.
local DOMAIN, SIZE = "Main RAM", 4194304
local WARMUP, PAIR_WINDOW, COIN_WINDOW = 45, 2, 2
local STABLE_CANDIDATE_FRAMES = 3
local COUNTS = { DAMAGE_OBSERVED=0, HEALTH_RECOVERY_COIN_CORRELATED=0,
  HEALTH_RECOVERY_UNATTRIBUTED=0, COIN_UP_OBSERVED=0,
  PHASE_TRANSITION_OBSERVED=0, LIVES_DROP_STABLE_CANDIDATE=0,
  CHARACTER_VALUE_STABLE_CANDIDATE=0 }

local function valid(a,n)
  if type(a)~="table" then return false end
  for i=1,n do
    local v=a[i]
    if type(v)~="number" or v%1~=0 or v<0 or v>255 then return false end
  end
  return true
end
-- Keep the known-working 049/050 NLua runtime probe, not type(method).
local readers = {
  {"binary_string",function(offset,n,domain)
    local raw=memory.read_bytes_as_binary_string(offset,n,domain)
    assert(type(raw)=="string" and #raw==n,"invalid binary string")
    local a={}
    for i=1,n do a[i]=string.byte(raw,i) end
    return a
  end},
  {"bytes_array",function(offset,n,domain)
    local raw=memory.read_bytes_as_array(offset,n,domain)
    assert(raw~=nil,"empty array")
    local one={}
    for i=1,n do one[i]=raw[i] end
    if valid(one,n) then return one end
    local zero={}
    for i=1,n do zero[i]=raw[i-1] end
    assert(valid(zero,n),"invalid array indexing")
    return zero
  end},
  {"read_u8",function(offset,n,domain)
    local a={}
    for i=1,n do a[i]=memory.read_u8(offset+i-1,domain) end
    return a
  end},
  {"readbyte",function(offset,n,domain)
    local a={}
    for i=1,n do a[i]=memory.readbyte(offset+i-1,domain) end
    return a
  end}
}
local has_main,rom_domains=false,{}
for _,domain in pairs(memory.getmemorydomainlist()) do
  if domain==DOMAIN then has_main=true end
  if type(domain)=="string" and domain:lower():find("rom",1,true)
      and not domain:lower():find("bios",1,true) then
    rom_domains[#rom_domains+1]=domain
  end
end
assert(has_main and memory.getmemorydomainsize(DOMAIN)==SIZE,
  "051 requires DS 4MiB Main RAM")
local selected=nil
for _,candidate in ipairs(readers) do
  local ok,a=pcall(candidate[2],0,2,DOMAIN)
  if ok and valid(a,2) then selected=candidate; break end
end
assert(selected,"051 no supported read-only memory API")
local read=selected[2]
print("[DSIRB051] Reader selected: "..selected[1].." (actual probe)")
local asmp,wrong=false,false
for _,domain in ipairs(rom_domains) do
  local ok,b=pcall(read,0x0C,4,domain)
  if ok and valid(b,4) then
    local code=string.char(b[1],b[2],b[3],b[4])
    if code=="ASMP" then asmp=true
    elseif code:match("^[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]$") then wrong=true
    end
  end
end
assert(asmp and not wrong,"051 ASMP cartridge header absent/contradicted; blocked")

local function get(off,n)
  assert((n==1 or n==2) and off>=0 and off+n<=SIZE,"invalid RAM field")
  local b=read(off,n,DOMAIN)
  assert(valid(b,n),string.format("bad Main RAM bytes at %06X",off))
  if n==1 then return b[1] end
  return b[1]+256*b[2]
end
local function snapshot()
  return {
    coins=get(0x09F358,1),
    lives=get(0x09F2F4,1),
    level=get(0x09F2F8,1),
    hp=get(0x11117C,2),
    alt=get(0x092144,2),
    character=get(0x09CAE1,1)
  }
end
local previous,previous_frame=nil,nil
local level_frame,ready_since=nil,nil
local armed,accepted_hp=false,nil
local hp_changed,alt_changed=nil,nil
local mismatch_since=nil
local last_coin_frame=nil
local pending_lives,pending_character=nil,nil
local total=0

local function event(frame,kind,detail)
  total=total+1
  if COUNTS[kind]~=nil then COUNTS[kind]=COUNTS[kind]+1 end
  print(string.format("[DSIRB051] frame=%d EVENT %s %s [PC LAB ONLY, NO RA AWARD]",
    frame,kind,detail or ""))
end
local function guard(frame,detail)
  print(string.format("[DSIRB051] frame=%d GUARD %s",frame,detail))
end
local function disarm()
  armed=false
  ready_since=nil
  accepted_hp=nil
  hp_changed=nil
  alt_changed=nil
  mismatch_since=nil
  last_coin_frame=nil
end
local function health_supported(s)
  -- Published observations only corroborated the 7 and 8 mapping.
  return (s.hp==7 or s.hp==8) and s.alt==256*s.hp+128
end

print("[DSIRB051] ASMP HEADER ONLY; loaded ROM RA hash NOT authenticated.")
print("[DSIRB051] Only HP 7/8 are classified; lower HP values are research-only.")
print("[DSIRB051] Life/character numeric values are CANDIDATES, not proven meaning.")
print("[DSIRB051] READ-ONLY PC; no official conditions/awards, no physical DSi.")

while true do
  local frame=emu.framecount()
  local s=snapshot()
  local contiguous=(previous_frame==nil or frame==previous_frame+1)
  if not contiguous then
    guard(frame,string.format("FRAME_DISCONTINUITY old=%d new=%d; state reset",
      previous_frame,frame))
    disarm()
    pending_lives,pending_character=nil,nil
    level_frame=frame
    previous=nil
  end

  local phase_change=previous~=nil and s.level~=previous.level
  local char_change=previous~=nil and s.character~=previous.character
  local life_change=previous~=nil and s.lives~=previous.lives
  local blocked_this_frame=phase_change or char_change or life_change

  if phase_change then
    event(frame,"PHASE_TRANSITION_OBSERVED",
      string.format("level=%d->%d (raw numeric ID; not stage name)",
        previous.level,s.level))
    level_frame=frame
    disarm()
    pending_lives=nil
    pending_character=nil
  end
  if level_frame==nil then level_frame=frame end

  if life_change then
    print(string.format("[DSIRB051] frame=%d OBSERVED LIVES_RAW_CHANGE_CANDIDATE %d->%d (may be load/death/UI)",
      frame,previous.lives,s.lives))
    -- Do not treat a drop observed during a phase switch as a confirmed death.
    pending_lives=nil
    if not phase_change and s.level~=0 and s.lives==previous.lives-1
        and previous.lives>=1 and previous.lives<=99 then
      pending_lives={
        old=previous.lives,new=s.lives,frame=frame,
        level=s.level,character=s.character
      }
    end
    disarm()
  end
  if char_change then
    print(string.format("[DSIRB051] frame=%d OBSERVED CHARACTER_RAW_CHANGE_CANDIDATE %d->%d (mapping unknown)",
      frame,previous.character,s.character))
    pending_character=nil
    if not phase_change and s.level~=0 then
      pending_character={
        old=previous.character,new=s.character,frame=frame,level=s.level
      }
    end
    disarm()
  end

  -- Pending candidates require 3 subsequent same-value consecutive frames,
  -- stable phase; no official death or character assertions.
  if pending_lives and frame>pending_lives.frame then
    if s.level~=pending_lives.level or s.lives~=pending_lives.new
        or s.character~=pending_lives.character then
      guard(frame,"LIVES_CANDIDATE_CANCELLED unstable context")
      pending_lives=nil
    elseif frame-pending_lives.frame>=STABLE_CANDIDATE_FRAMES then
      event(frame,"LIVES_DROP_STABLE_CANDIDATE",string.format(
        "%d->%d level=%d; NOT verified death",pending_lives.old,
        pending_lives.new,pending_lives.level))
      pending_lives=nil
    end
  end
  if pending_character and frame>pending_character.frame then
    if s.level~=pending_character.level
        or s.character~=pending_character.new then
      guard(frame,"CHARACTER_CANDIDATE_CANCELLED unstable context")
      pending_character=nil
    elseif frame-pending_character.frame>=STABLE_CANDIDATE_FRAMES then
      event(frame,"CHARACTER_VALUE_STABLE_CANDIDATE",string.format(
        "%d->%d level=%d; NO character name inferred",
        pending_character.old,pending_character.new,pending_character.level))
      pending_character=nil
    end
  end

  if previous and s.hp~=previous.hp then hp_changed=frame end
  if previous and s.alt~=previous.alt then alt_changed=frame end
  local coherent=health_supported(s)
  local hp_range=(s.hp==7 or s.hp==8)
  if s.level==0 or not hp_range then
    if armed then guard(frame,string.format("LOADING_OR_UNVALIDATED_HP hp=%d alt=%d",s.hp,s.alt)) end
    disarm()
  elseif not coherent then
    if mismatch_since==nil then mismatch_since=frame end
    if frame-mismatch_since>=PAIR_WINDOW then
      if armed then guard(frame,"HEALTH_PAIR_TIMEOUT no event") end
      disarm()
    end
  else
    mismatch_since=nil
    if not armed then
      if ready_since==nil then ready_since=frame end
      if frame-level_frame>=WARMUP and frame-ready_since>=WARMUP then
        armed=true
        accepted_hp=s.hp
        hp_changed,alt_changed=nil,nil
        last_coin_frame=nil
        print(string.format("[DSIRB051] frame=%d ARMED level=%d hp=%d (PC-only)",
          frame,s.level,s.hp))
      end
    end
  end

  if previous and armed and not blocked_this_frame and
      s.coins==previous.coins+1 then
    last_coin_frame=frame
    event(frame,"COIN_UP_OBSERVED",
      string.format("%d->%d",previous.coins,s.coins))
  elseif previous and s.coins~=previous.coins and
      s.coins~=previous.coins+1 then
    last_coin_frame=nil
  end

  if armed and coherent and accepted_hp and s.hp~=accepted_hp
      and not blocked_this_frame then
    local paired=hp_changed~=nil and alt_changed~=nil
        and math.abs(hp_changed-alt_changed)<=PAIR_WINDOW
    if paired and math.abs(s.hp-accepted_hp)==1 then
      if s.hp<accepted_hp then
        event(frame,"DAMAGE_OBSERVED",string.format(
          "hp=%d->%d alt=%d (paired)",accepted_hp,s.hp,s.alt))
      else
        local recent=last_coin_frame and frame>=last_coin_frame
            and frame-last_coin_frame<=COIN_WINDOW
        if recent then
          event(frame,"HEALTH_RECOVERY_COIN_CORRELATED",string.format(
            "hp=%d->%d alt=%d coin_frame=%d (temporal correlation only)",
            accepted_hp,s.hp,s.alt,last_coin_frame))
        else
          event(frame,"HEALTH_RECOVERY_UNATTRIBUTED",
            string.format("hp=%d->%d alt=%d",accepted_hp,s.hp,s.alt))
        end
      end
      accepted_hp=s.hp
      hp_changed,alt_changed=nil,nil
      last_coin_frame=nil
    else
      guard(frame,"UNPAIRED_OR_MULTISTEP_HP_CHANGE; disarmed")
      disarm()
    end
  end

  gui.text(2,2,"DSIRB051 ASMP PC LAB - no RA awards")
  gui.text(2,15,string.format("Level %d Coins %d Lives? %d Character? %d",
    s.level,s.coins,s.lives,s.character))
  gui.text(2,28,string.format("HP %d Alt %d Armed %s",
    s.hp,s.alt,armed and "YES" or "NO"))
  gui.text(2,41,string.format("Damage %d  Coin recoveries %d  Life candidates %d",
    COUNTS.DAMAGE_OBSERVED,COUNTS.HEALTH_RECOVERY_COIN_CORRELATED,
    COUNTS.LIVES_DROP_STABLE_CANDIDATE))

  previous=s
  previous_frame=frame
  emu.frameadvance()
end

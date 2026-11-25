-- DSi RA Bridge 0.5.2: ASMP EU one-pass observer on PC / BizHawk ONLY.
-- Game RAM read-only; optional text-only PC journal under Downloads.
-- Never writes ROM/save/SD/NAND, sends achievements, or uses the network.
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
print("[DSIRB052] Reader selected: "..selected[1].." (actual probe)")
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

-- PC journal (Windows user Downloads only), never a RAM dump.
local journal=nil
do
  local home=(os and os.getenv and os.getenv("USERPROFILE")) or nil
  if home and io and io.open then
    local basename=home.."\\Downloads\\DSIRB052_"..tostring(emu.framecount())
    for n=1,30 do
      local filename=basename..(n==1 and "" or "_"..n)..".txt"
      local exists=io.open(filename,"r")
      if exists then exists:close() else
        local f=io.open(filename,"w")
        if f then journal=f;break end
      end
    end
  end
end
local console_print=print
print=function(...)
  console_print(...)
  if journal then
    local p={}
    for i=1,select("#",...) do p[#p+1]=tostring(select(i,...)) end
    local line=table.concat(p," ")
    if line:sub(1,10)=="[DSIRB052]" then
      journal:write(line,"\n")
      journal:flush()
    end
  end
end
print("[DSIRB052] PC_JOURNAL "..(journal and "ACTIVE (Downloads)" or "DISABLED (copy console)"))


local function get(off,n)
  assert((n==1 or n==2) and off>=0 and off+n<=SIZE,"invalid RAM field")
  local b=read(off,n,DOMAIN)
  assert(valid(b,n),string.format("bad Main RAM bytes at %06X",off))
  if n==1 then return b[1] end
  return b[1]+256*b[2]
end

local function readbytes(off,n)
  assert(off>=0 and off+n<=SIZE and n>=1 and n<=64,"invalid bounded window")
  local b=read(off,n,DOMAIN)
  assert(valid(b,n),"invalid Main RAM read")
  return b
end
local function read32(off)
  local b=readbytes(off,4)
  return b[1]+b[2]*256+b[3]*65536+b[4]*16777216
end
-- EU research: player pointer 0x0209F394 (Kuribo64); actor+8 is a
-- character/cap field. Not a confirmed effective-character sensor yet.
local function actor_candidate()
  local ptr=read32(0x09F394)
  if ptr<0x02000000 or ptr+8>=0x02400000 or ptr%4~=0 then return ptr,nil end
  local ok,b=pcall(readbytes,ptr-0x02000000+8,1)
  if not ok then return ptr,nil end
  return ptr,b[1]
end

local function snapshot()
  local actor_ptr,actor_field=actor_candidate()
  return {
    coins=get(0x09F358,1),
    lives=get(0x09F2F4,1),
    level=get(0x09F2F8,1),
    hp=get(0x11117C,2),
    alt=get(0x092144,2),
    character=get(0x09CAE1,1),
    stars=readbytes(0x09CAB4,15),
    record_coins=readbytes(0x09CAD2,15),
    cap_save_flag=get(0x09CAA7,1),
    red_coins=get(0x09F30C,1),
    silver_stars=get(0x09F310,1),
    actor_ptr=actor_ptr,
    actor_field=actor_field
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
local event

-- One-pass extra research channels: buffered candidate events, no RAM dumps.
COUNTS.STAR_FLAG_STABLE_GAIN_CANDIDATE=0
COUNTS.CAP_OR_EFFECTIVE_CHARACTER_CANDIDATE=0
COUNTS.GAME_OVER_RESET_CANDIDATE=0
local pending_star,pending_actor=nil,nil
local last_zero_lives,hp_zero_after_zero_lives=nil,false
local last_summary=nil
local function equal(a,b)
  if not a or not b or #a~=#b then return false end
  for i=1,#a do if a[i]~=b[i] then return false end end
  return true
end
local function bitdiff(a,b)
  local gain,loss,first=0,0,nil
  for i=1,#a do
    for bit=0,7 do
      local p=2^bit
      local x=math.floor(a[i]/p)%2
      local y=math.floor(b[i]/p)%2
      if x==0 and y==1 then
        gain=gain+1
        if not first then first=string.format("0x%08X:bit%d",0x0209CAB4+i-1,bit) end
      elseif x==1 and y==0 then loss=loss+1 end
    end
  end
  return gain,loss,first
end
local function count_bits(a)
  local n=0
  for i=1,#a do
    local v=a[i]
    while v>0 do n=n+(v%2); v=math.floor(v/2) end
  end
  return n
end
local function research_sample(frame,s,p,phase,life_change)
  if p and not equal(s.stars,p.stars) then
    local g,l,where=bitdiff(p.stars,s.stars)
    print(string.format("[DSIRB052] frame=%d OBSERVED STAR_FLAGS_RAW_CHANGE gained=%d lost=%d first=%s total_bits=%d level=%d during_phase=%s",
      frame,g,l,where or "none",count_bits(s.stars),s.level,tostring(phase)))
    pending_star={frame=frame,st=s.stars,g=g,l=l,where=where,level=s.level}
  elseif pending_star and frame>pending_star.frame then
    local c=pending_star
    if not equal(s.stars,c.st) then pending_star=nil
    elseif frame-c.frame>=3 then
      if c.g==1 and c.l==0 and s.level~=0 then
        event(frame,"STAR_FLAG_STABLE_GAIN_CANDIDATE",
          (c.where or "unknown").." +1 bit persisted 3 frames; verify HUD")
      else
        event(frame,"STAR_FLAGS_CHANGE_STABLE_CANDIDATE",
          string.format("gained=%d lost=%d (save/slot/load possible)",c.g,c.l))
      end
      pending_star=nil
    end
  end
  if p and not equal(s.record_coins,p.record_coins) then
    local changes=0
    for i=1,#s.record_coins do
      if s.record_coins[i]~=p.record_coins[i] then
        changes=changes+1
        if changes<=3 then
          print(string.format("[DSIRB052] frame=%d OBSERVED COIN_RECORD_BYTE_CHANGE 0x%08X %d->%d (candidate)",
            frame,0x0209CAD2+i-1,p.record_coins[i],s.record_coins[i]))
        end
      end
    end
    if changes>3 then
      print(string.format("[DSIRB052] frame=%d OBSERVED COIN_RECORD_BATCH changed=%d (possible slot load)",frame,changes))
    end
  end
  if p and s.cap_save_flag~=p.cap_save_flag then
    print(string.format("[DSIRB052] frame=%d OBSERVED CAP_SAVE_FLAG_RAW_CHANGE %d->%d (NOT evidence cap equipped)",
      frame,p.cap_save_flag,s.cap_save_flag))
  end
  if p and s.red_coins~=p.red_coins then
    print(string.format("[DSIRB052] frame=%d OBSERVED RED_COIN_CANDIDATE %d->%d",
      frame,p.red_coins,s.red_coins))
  end
  if p and s.silver_stars~=p.silver_stars then
    print(string.format("[DSIRB052] frame=%d OBSERVED SILVER_STAR_CANDIDATE %d->%d",
      frame,p.silver_stars,s.silver_stars))
  end
  if p and s.actor_ptr~=p.actor_ptr then
    print(string.format("[DSIRB052] frame=%d OBSERVED PLAYER_PTR_CANDIDATE 0x%08X->0x%08X",
      frame,p.actor_ptr,s.actor_ptr))
    pending_actor=nil
  end
  if p and s.actor_field~=p.actor_field then
    print(string.format("[DSIRB052] frame=%d OBSERVED ACTOR_CHAR_OR_CAP_RAW %s->%s base_char=%d",
      frame,tostring(p.actor_field),tostring(s.actor_field),s.character))
    pending_actor=nil
    if s.actor_ptr==p.actor_ptr and s.actor_field~=nil and
        s.actor_field<=3 and s.level~=0 and not phase then
      pending_actor={frame=frame,ptr=s.actor_ptr,val=s.actor_field,
        old=p.actor_field,level=s.level,base=s.character}
    end
  elseif pending_actor and frame>pending_actor.frame then
    local c=pending_actor
    if s.actor_ptr~=c.ptr or s.actor_field~=c.val or s.level~=c.level then
      pending_actor=nil
    elseif frame-c.frame>=3 then
      event(frame,"CAP_OR_EFFECTIVE_CHARACTER_CANDIDATE",
        string.format("field=%s->%d base=%d ptr=0x%08X (visual check)",
          tostring(c.old),c.val,c.base,c.ptr))
      pending_actor=nil
    end
  end
  if p and life_change and p.lives>0 and s.lives==0 then
    last_zero_lives=frame
    hp_zero_after_zero_lives=false
  end
  if last_zero_lives and s.hp==0 and frame>last_zero_lives then
    hp_zero_after_zero_lives=true
  end
  if p and life_change and p.lives==0 and s.lives>=3 and
      last_zero_lives and hp_zero_after_zero_lives and
      frame-last_zero_lives<=12000 then
    event(frame,"GAME_OVER_RESET_CANDIDATE",
      string.format("lives 0->%d after HP zero; confirm Game Over visually",s.lives))
    last_zero_lives=nil
    hp_zero_after_zero_lives=false
  end
  if last_zero_lives and frame-last_zero_lives>12000 then
    last_zero_lives=nil
    hp_zero_after_zero_lives=false
  end
  if not last_summary or frame-last_summary>=900 then
    print(string.format("[DSIRB052] frame=%d SNAPSHOT level=%d lives=%d hp=%d alt=%d coins=%d star_bits=%d red=%d silver=%d base_char=%d actor_field=%s ptr=0x%08X",
      frame,s.level,s.lives,s.hp,s.alt,s.coins,count_bits(s.stars),
      s.red_coins,s.silver_stars,s.character,tostring(s.actor_field),s.actor_ptr))
    last_summary=frame
  end
end


event=function(frame,kind,detail)
  total=total+1
  if COUNTS[kind]~=nil then COUNTS[kind]=COUNTS[kind]+1 end
  print(string.format("[DSIRB052] frame=%d EVENT %s %s [PC LAB ONLY, NO RA AWARD]",
    frame,kind,detail or ""))
end
local function guard(frame,detail)
  print(string.format("[DSIRB052] frame=%d GUARD %s",frame,detail))
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

print("[DSIRB052] ASMP HEADER ONLY; loaded ROM RA hash NOT authenticated.")
print("[DSIRB052] Only HP 7/8 are classified; lower HP values are research-only.")
print("[DSIRB052] Life/character numeric values are CANDIDATES, not proven meaning.")
print("[DSIRB052] READ-ONLY PC; no official conditions/awards, no physical DSi.")

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
    print(string.format("[DSIRB052] frame=%d OBSERVED LIVES_RAW_CHANGE_CANDIDATE %d->%d (may be load/death/UI)",
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
    print(string.format("[DSIRB052] frame=%d OBSERVED CHARACTER_RAW_CHANGE_CANDIDATE %d->%d (mapping unknown)",
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
    -- Log newly encountered invalid load states even when already disarmed.
    -- Do not print on every frame of a persistent loading screen.
    if armed or (previous and (previous.hp~=s.hp or previous.alt~=s.alt)) then
      guard(frame,string.format("LOADING_OR_UNVALIDATED_HP hp=%d alt=%d",s.hp,s.alt))
    end
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
        print(string.format("[DSIRB052] frame=%d ARMED level=%d hp=%d (PC-only)",
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

  research_sample(frame,s,previous,phase_change,life_change)
  gui.text(2,2,"DSIRB052 ASMP PC LAB - no RA awards")
  gui.text(2,15,string.format("Level %d Coins %d Lives? %d Character? %d",
    s.level,s.coins,s.lives,s.character))
  gui.text(2,28,string.format("HP %d Alt %d Armed %s",
    s.hp,s.alt,armed and "YES" or "NO"))
  gui.text(2,41,string.format("Damage %d  Coin recoveries %d  Life candidates %d",
    COUNTS.DAMAGE_OBSERVED,COUNTS.HEALTH_RECOVERY_COIN_CORRELATED,
    COUNTS.LIVES_DROP_STABLE_CANDIDATE))

  gui.text(2,54,string.format("Stars? %d Cap actor? %s",count_bits(s.stars),tostring(s.actor_field)))
  previous=s
  previous_frame=frame
  emu.frameadvance()
end

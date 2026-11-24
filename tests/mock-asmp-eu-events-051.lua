-- DSIRB051 synthetic memory, exercising ACTUAL 051 BizHawk Lua.
-- No ROM, save, physical device, network or RetroAchievements traffic.
local source=assert(arg[1],"provide Lua source")
local mode=arg[2] or "normal"
local frame,stop_frame=0,405
local log={}
local native_print=print
print=function(...)
  local ss={}
  for i=1,select("#",...) do ss[#ss+1]=tostring(select(i,...)) end
  log[#log+1]=table.concat(ss," ")
end
local function values(f)
  local level=f>=300 and 7 or f>=10 and 6 or 0
  local lives=f>=300 and 2 or f>=200 and 3 or f>=5 and 4 or 0
  local character=f>=260 and 3 or f>=230 and 1 or f>=5 and 3 or 0
  local coins=f>=375 and 3 or f>=170 and 2 or f>=120 and 1 or 0
  if mode=="no_coin" then coins=0 end
  local hp,alt=8,2176
  if f>=100 and f<120 then
    alt=1920
    if mode=="unpaired" then
      if f>=104 then hp=7 end
    elseif f>=101 then hp=7 end
  elseif f==120 then
    hp=7;alt=2176
  elseif f>=150 and f<170 then
    alt=1920
    if f>=151 then hp=7 end
  end
  -- Explicitly model loading values; these must not be classified as damage.
  if f==301 then hp=16;alt=2176 end
  if f==302 then hp=0;alt=2176 end
  return {
    [0x09F358]=coins, [0x09F2F4]=lives,[0x09F2F8]=level,
    [0x11117C]=hp%256,[0x11117D]=math.floor(hp/256),
    [0x092144]=alt%256,[0x092145]=math.floor(alt/256),
    [0x09CAE1]=character
  }
end
memory={}
function memory.getmemorydomainlist() return {[0]="Main RAM",[1]="CartROM"} end
function memory.getmemorydomainsize(domain)
  assert(domain=="Main RAM")
  return mode=="wrong_ram" and 2097152 or 4194304
end
local function getbytes(offset,n,domain)
  assert(n>=1 and n<=4)
  local a={}
  if domain=="CartROM" then
    local code=mode=="wrong_code" and "ASME" or "ASMP"
    for i=1,n do a[i]=code:byte(offset-0x0C+i) or 0 end
  else
    assert(domain=="Main RAM")
    local d=values(frame)
    for i=1,n do a[i]=d[offset+i-1] or 0 end
  end
  return a
end
local function binary(offset,n,domain)
  return string.char(table.unpack(getbytes(offset,n,domain)))
end
if mode=="normal" or mode=="no_coin" or mode=="unpaired" or
    mode=="skip_frame" or mode=="wrong_code" or mode=="wrong_ram" then
  memory.read_bytes_as_binary_string=binary
elseif mode=="proxy" then
  memory.read_bytes_as_binary_string=setmetatable({},{
    __call=function(_,offset,n,domain) return binary(offset,n,domain) end})
elseif mode=="array_one" or mode=="array_zero" then
  memory.read_bytes_as_array=function(offset,n,domain)
    local data=getbytes(offset,n,domain)
    if mode=="array_one" then return data end
    local zero={}
    for i=1,n do zero[i-1]=data[i] end
    return zero
  end
elseif mode=="u8" then
  memory.read_u8=function(offset,domain)
    return getbytes(offset,1,domain)[1]
  end
elseif mode=="readbyte" then
  memory.readbyte=function(offset,domain)
    return getbytes(offset,1,domain)[1]
  end
elseif mode=="none" then
  -- fail closed
else
  error("unknown mode "..mode)
end
emu={}
function emu.framecount()
  if mode=="skip_frame" and frame>=100 then return frame+5 end
  return frame
end
function emu.frameadvance()
  frame=frame+1
  if frame>=stop_frame then error("DSIRB051_TEST_END") end
end
gui={}
function gui.text(x,y,s)
  assert(type(x)=="number" and type(y)=="number" and type(s)=="string")
end

local ok,err=pcall(dofile,source)
local lines=table.concat(log,"\n")
local function count(kind)
  local n=0
  for _,line in ipairs(log) do
    if line:find(" EVENT "..kind.." ",1,true) then n=n+1 end
  end
  return n
end
local function contains(s)
  return lines:find(s,1,true)~=nil
end
if mode=="none" then
  assert(not ok and tostring(err):find("no supported read-only memory API",1,true),tostring(err))
elseif mode=="wrong_code" then
  assert(not ok and tostring(err):find("ASMP cartridge header absent/contradicted",1,true),tostring(err))
elseif mode=="wrong_ram" then
  assert(not ok and tostring(err):find("requires DS 4MiB Main RAM",1,true),tostring(err))
else
  assert(not ok and tostring(err):find("DSIRB051_TEST_END",1,true),tostring(err))
  assert(contains("Reader selected:"),lines)
  assert(count("PHASE_TRANSITION_OBSERVED")==2,lines)
  assert(count("LIVES_DROP_STABLE_CANDIDATE")==1,lines)
  assert(count("CHARACTER_VALUE_STABLE_CANDIDATE")==2,lines)
  assert(count("COIN_UP_OBSERVED")==(mode=="no_coin" and 0 or 3),lines)
  assert(contains("LIVES_RAW_CHANGE_CANDIDATE 4->3"),lines)
  assert(contains("CHARACTER_RAW_CHANGE_CANDIDATE 3->1"),lines)
  assert(contains("CHARACTER_RAW_CHANGE_CANDIDATE 1->3"),lines)
  assert(not contains("EVENT DAMAGE_OBSERVED hp=16"),lines)
  if mode=="no_coin" then
    assert(count("DAMAGE_OBSERVED")==2,lines)
    assert(count("HEALTH_RECOVERY_COIN_CORRELATED")==0,lines)
    assert(count("HEALTH_RECOVERY_UNATTRIBUTED")==2,lines)
  elseif mode=="unpaired" or mode=="skip_frame" then
    assert(count("DAMAGE_OBSERVED")==1,lines)
    assert(count("HEALTH_RECOVERY_COIN_CORRELATED")==1,lines)
    assert(count("HEALTH_RECOVERY_UNATTRIBUTED")==0,lines)
    if mode=="skip_frame" then assert(contains("FRAME_DISCONTINUITY"),lines) end
    if mode=="unpaired" then assert(contains("HEALTH_PAIR_TIMEOUT"),lines) end
  else
    assert(count("DAMAGE_OBSERVED")==2,lines)
    assert(count("HEALTH_RECOVERY_COIN_CORRELATED")==2,lines)
    assert(count("HEALTH_RECOVERY_UNATTRIBUTED")==0,lines)
  end
  assert(contains("GUARD LOADING_OR_UNVALIDATED_HP hp=16"),lines)
end
native_print(string.format(
  "DSIRB051_MOCK_PASS %s damage=%d coin_recoveries=%d phase=%d lives=%d character=%d",
  mode,count("DAMAGE_OBSERVED"),count("HEALTH_RECOVERY_COIN_CORRELATED"),
  count("PHASE_TRANSITION_OBSERVED"),count("LIVES_DROP_STABLE_CANDIDATE"),
  count("CHARACTER_VALUE_STABLE_CANDIDATE")))

-- DSi 050: run REAL PC read-only detector against synthetic emulated frames.
local source=assert(arg[1],"Need detector script path")
local mode=arg[2] or "binary"
local frame, limit=0,185
local log={}
local oldprint=print
print=function(...)
  local parts={}
  for i=1,select("#",...) do parts[#parts+1]=tostring(select(i,...)) end
  log[#log+1]=table.concat(parts," ")
end
local function state(f)
  local coins=f>=99 and 3 or f>=95 and 2 or f>=90 and 1 or 0
  if mode=="no_coin" then coins=0 end
  local hp,alt=8,2176
  if f>=80 and f<90 then
    alt=1920
    if mode=="lagged" then
      if f>=85 then hp=7 end
    elseif f>=81 then hp=7 end
  elseif f==90 then hp=7;alt=2176
  elseif f>=91 then hp=8;alt=2176 end
  if f==111 then hp=16 end
  if f==112 then hp=0 end
  return {
    [0x09F358]=coins,
    [0x09F2F4]=4,
    [0x09F2F8]=f>=110 and 7 or 6,
    [0x11117C]=hp%256,[0x11117D]=math.floor(hp/256),
    [0x092144]=alt%256,[0x092145]=math.floor(alt/256),
    [0x09CAE1]=3
  }
end
memory={}
function memory.getmemorydomainlist() return {[0]="Main RAM",[1]="CartROM"} end
function memory.getmemorydomainsize(name)
  assert(name=="Main RAM")
  return 4194304
end
local function bytes(off,n,name)
  assert(n>=1 and n<=4)
  local vals={}
  if name=="CartROM" then
    local code=mode=="wrong_code" and "ASME" or "ASMP"
    for i=1,n do vals[i]=code:byte(off-0x0C+i) or 0 end
    return vals
  end
  assert(name=="Main RAM")
  local data=state(frame)
  for i=1,n do vals[i]=data[off+i-1] or 0 end
  return vals
end
local function binary(off,n,name) return string.char(table.unpack(bytes(off,n,name))) end
if mode=="binary" or mode=="no_coin" or mode=="lagged" or mode=="wrong_code" then
  memory.read_bytes_as_binary_string=binary
elseif mode=="proxy" then
  memory.read_bytes_as_binary_string=setmetatable({},{
    __call=function(_,off,n,name) return binary(off,n,name) end})
elseif mode=="array_zero" then
  memory.read_bytes_as_array=function(off,n,name)
    local src=bytes(off,n,name)
    local arr={}
    for i=1,n do arr[i-1]=src[i] end
    return arr
  end
elseif mode=="readbyte" then
  memory.readbyte=function(off,name) return bytes(off,1,name)[1] end
elseif mode=="none" then
  -- intentionally missing readers: detector must fail closed
else error("Bad mock mode "..mode) end
emu={}
function emu.framecount() return frame end
function emu.frameadvance()
  frame=frame+1
  if frame>=limit then error("DSIRB050_MOCK_STOP") end
end
gui={}
function gui.text(x,y,s)
  assert(type(x)=="number" and type(y)=="number" and type(s)=="string")
end
local ok,err=pcall(dofile,source)
local lines=table.concat(log,"\n")
local function count(tag)
  local n=0
  for _,line in ipairs(log) do
    if line:find(" EVENT "..tag.." ",1,true) then n=n+1 end
  end
  return n
end
if mode=="none" then
  assert(not ok and tostring(err):find("no supported read-only memory API",1,true),tostring(err))
elseif mode=="wrong_code" then
  assert(not ok and tostring(err):find("ASMP header missing/contradicted",1,true),tostring(err))
else
  assert(not ok and tostring(err):find("DSIRB050_MOCK_STOP",1,true),tostring(err))
  assert(lines:find("Reader selected:",1,true),lines)
  assert(count("PHASE_TRANSITION_OBSERVED")==1,lines)
  if mode=="lagged" then
    assert(count("DAMAGE_OBSERVED")==0,lines)
    assert(count("HEALTH_RECOVERY_COIN_CORRELATED")==0,lines)
    assert(count("HEALTH_RECOVERY_UNATTRIBUTED")==0,lines)
  elseif mode=="no_coin" then
    assert(count("DAMAGE_OBSERVED")==1,lines)
    assert(count("HEALTH_RECOVERY_UNATTRIBUTED")==1,lines)
    assert(count("HEALTH_RECOVERY_COIN_CORRELATED")==0,lines)
    assert(count("COIN_UP_OBSERVED")==0,lines)
  else
    assert(count("DAMAGE_OBSERVED")==1,lines)
    assert(count("HEALTH_RECOVERY_COIN_CORRELATED")==1,lines)
    assert(count("HEALTH_RECOVERY_UNATTRIBUTED")==0,lines)
    assert(count("COIN_UP_OBSERVED")==3,lines)
  end
  assert(not lines:find("hp=16->0",1,true),lines)
end
oldprint("DSIRB050_MOCK_PASS mode="..mode.." frames="..frame..
 " damage="..count("DAMAGE_OBSERVED")..
 " recovery_coin="..count("HEALTH_RECOVERY_COIN_CORRELATED")..
 " phase="..count("PHASE_TRANSITION_OBSERVED"))

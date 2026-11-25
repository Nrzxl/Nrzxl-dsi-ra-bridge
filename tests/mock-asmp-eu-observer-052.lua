-- Run the actual 052 one-pass observer against synthetic memory snapshots.
-- NO ROM, physical DSi, cheat, save, RAM dump or RA account.
local file=assert(arg[1],"Lua source path expected")
local mode=arg[2] or "normal"
local frame,limit=0,415
local log={}
local originalprint=print
print=function(...)
 local a={}
 for i=1,select("#",...) do a[#a+1]=tostring(select(i,...)) end
 log[#log+1]=table.concat(a," ")
end
local function state(f)
 local level=f>=300 and 7 or f>=10 and 6 or 0
 local lives=f>=385 and 4 or f>=325 and 0 or f>=200 and 3 or f>=5 and 4 or 0
 local character=f>=260 and 3 or f>=230 and 1 or f>=5 and 3 or 0
 local coins=f>=170 and 2 or f>=120 and 1 or 0
 local hp,alt=8,2176
 if f>=100 and f<120 then
   alt=1920
   if f>=101 then hp=7 end
 elseif f==120 then hp=7;alt=2176
 elseif f>=150 and f<170 then
   alt=1920
   if f>=151 then hp=7 end
 end
 if f==301 then hp=16 end
 if f==302 then hp=0 end
 if f>=330 and f<337 then hp=0;alt=0 end
 local ptr=mode=="invalid_actor" and 0xF1234000 or 0x02123400
 local cap=mode=="no_cap" and 3 or ((f>=350 and f<390) and 0 or 3)
 local flags=mode=="no_star" and 0 or (f>=195 and 6 or f>=130 and 2 or 0)
 local d={
   [0x09F358]=coins,[0x09F2F4]=lives,[0x09F2F8]=level,
   [0x11117C]=hp%256,[0x11117D]=math.floor(hp/256),
   [0x092144]=alt%256,[0x092145]=math.floor(alt/256),
   [0x09CAE1]=character,
   [0x09CAB4]=flags,
   [0x09CAD2]=f>=220 and 10 or 0,
   [0x09CAA7]=f>=350 and 128 or 0,
   [0x09F30C]=f>=215 and 1 or 0,
   [0x09F310]=f>=250 and 1 or 0,
   [0x123408]=cap
 }
 for i=0,3 do d[0x09F394+i]=math.floor(ptr/256^i)%256 end
 return d
end
memory={}
function memory.getmemorydomainlist() return {[0]="Main RAM",[1]="CartROM"} end
function memory.getmemorydomainsize(name)
 assert(name=="Main RAM")
 return mode=="wrong_ram" and 1048576 or 4194304
end
local function bytes(off,n,name)
 assert(n>=1 and n<=64)
 local a={}
 if name=="CartROM" then
   local code=mode=="wrong_code" and "ASME" or "ASMP"
   for i=1,n do a[i]=code:byte(off-0x0C+i) or 0 end
 else
   assert(name=="Main RAM")
   local d=state(frame)
   for i=1,n do a[i]=d[off+i-1] or 0 end
 end
 return a
end
local function binary(off,n,name) return string.char(table.unpack(bytes(off,n,name))) end
if mode=="normal" or mode=="no_star" or mode=="no_cap" or
   mode=="invalid_actor" or mode=="wrong_code" or mode=="wrong_ram" then
 memory.read_bytes_as_binary_string=binary
elseif mode=="proxy" then
 memory.read_bytes_as_binary_string=setmetatable({},{__call=function(_,o,n,d) return binary(o,n,d) end})
elseif mode=="array_zero" or mode=="array_one" then
 memory.read_bytes_as_array=function(off,n,name)
   local src=bytes(off,n,name)
   if mode=="array_one" then return src end
   local arr={}
   for i=1,n do arr[i-1]=src[i] end
   return arr
 end
elseif mode=="u8" then
 memory.read_u8=function(off,name) return bytes(off,1,name)[1] end
elseif mode=="readbyte" then
 memory.readbyte=function(off,name) return bytes(off,1,name)[1] end
elseif mode=="no_api" then
else error("Unknown mock mode "..mode) end
emu={}
function emu.framecount() return frame end
function emu.frameadvance()
 frame=frame+1
 if frame>=limit then error("DSIRB052_MOCK_STOP") end
end
gui={}
function gui.text(x,y,s)
 assert(type(x)=="number" and type(y)=="number" and type(s)=="string")
end
local ok,err=pcall(dofile,file)
local lines=table.concat(log,"\n")
local function count(label)
 local n=0
 for _,line in ipairs(log) do
   if line:find(" EVENT "..label.." ",1,true) then n=n+1 end
 end
 return n
end
local function has(needle) return lines:find(needle,1,true)~=nil end
if mode=="wrong_code" then
 assert(not ok and tostring(err):find("ASMP cartridge header absent/contradicted",1,true),tostring(err))
elseif mode=="wrong_ram" then
 assert(not ok and tostring(err):find("requires DS 4MiB Main RAM",1,true),tostring(err))
elseif mode=="no_api" then
 assert(not ok and tostring(err):find("no supported read-only memory API",1,true),tostring(err))
else
 assert(not ok and tostring(err):find("DSIRB052_MOCK_STOP",1,true),tostring(err))
 assert(has("Reader selected:"),lines)
 assert(count("STAR_FLAG_STABLE_GAIN_CANDIDATE")==(mode=="no_star" and 0 or 2),lines)
 assert(count("CAP_OR_EFFECTIVE_CHARACTER_CANDIDATE")==(
   (mode=="no_cap" or mode=="invalid_actor") and 0 or 2),lines)
 assert(count("GAME_OVER_RESET_CANDIDATE")==1,lines)
 assert(count("DAMAGE_OBSERVED")==2,lines)
 assert(count("HEALTH_RECOVERY_COIN_CORRELATED")==2,lines)
 assert(count("LIVES_DROP_STABLE_CANDIDATE")==1,lines)
 assert(count("PHASE_TRANSITION_OBSERVED")==2,lines)
 assert(has("OBSERVED COIN_RECORD_BYTE_CHANGE"),lines)
 assert(has("OBSERVED RED_COIN_CANDIDATE"),lines)
 assert(has("OBSERVED SILVER_STAR_CANDIDATE"),lines)
 assert(has("GUARD LOADING_OR_UNVALIDATED_HP hp=16"),lines)
 assert(has("SNAPSHOT level="),lines)
 assert(not has("EVENT DAMAGE_OBSERVED hp=16"),lines)
end
originalprint("DSIRB052_MOCK_PASS mode="..mode..
  " star_candidates="..count("STAR_FLAG_STABLE_GAIN_CANDIDATE")..
  " cap_candidates="..count("CAP_OR_EFFECTIVE_CHARACTER_CANDIDATE")..
  " gameover_candidates="..count("GAME_OVER_RESET_CANDIDATE"))

-- Mock the actual BizHawk API that worked in 048.
-- Deliberately NO memory.read_u8 or memory.read_u16_le functions.
local source=assert(arg[1],"Lua monitor file required")
local frame=0
local calls=0
local two_byte_calls=0
local outputs={}
local real_print=print
print=function(...)
  local xs={}
  for i=1,select("#",...) do xs[#xs+1]=tostring(select(i,...)) end
  local value=table.concat(xs," ")
  outputs[#outputs+1]=value
  real_print(...)
end
memory={}
function memory.getmemorydomainlist() return {[0]="Main RAM",[1]="CartROM"} end
function memory.getmemorydomainsize(domain)
  assert(domain=="Main RAM")
  return 4194304
end
function memory.read_bytes_as_binary_string(off,width,domain)
  if domain=="CartROM" then
    assert(off==0x0C and width==4)
    return "ASMP"
  end
  assert(domain=="Main RAM", "unexpected domain")
  assert(width==1 or width==2,"read width unsupported")
  calls=calls+1
  local value=0
  if off==0x09F358 then value=3+frame end
  if off==0x11117C then value=0x1234+frame end
  if off==0x092144 then value=0x5678-frame end
  if width==2 then
    two_byte_calls=two_byte_calls+1
    return string.char(value%256,math.floor(value/256)%256)
  end
  return string.char(value%256)
end
emu={}
function emu.framecount() return frame end
function emu.frameadvance()
  frame=frame+1
  if frame==3 then error("DSIRB049_MOCK_STOP") end
end
gui={}
function gui.text(x,y,txt)
  assert(type(x)=="number" and type(y)=="number")
  assert(type(txt)=="string")
end
local ok,err=pcall(dofile,source)
assert(not ok and tostring(err):find("DSIRB049_MOCK_STOP",1,true),tostring(err))
assert(frame==3 and calls==24 and two_byte_calls==6)
local log=table.concat(outputs,"\n")
assert(log:find("yellow_coins 0x0209F358 3 -> 4",1,true),log)
assert(log:find("yellow_coins 0x0209F358 4 -> 5",1,true),log)
assert(log:find("health_primary 0x0211117C 4660 -> 4661",1,true),log)
print("DSIRB049_LUA_BINARY_READ_COMPAT_MOCK_PASS")

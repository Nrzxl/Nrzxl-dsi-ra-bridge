-- Mock the actual 049 Lua monitor across old and new BizHawk APIs.
-- Never runs a game/ROM. CLI: lua mock.lua monitor.lua MODE
local source=assert(arg[1],"monitor.lua path required")
local mode=arg[2] or "binary"
local frame, calls, two_byte_calls=0,0,0
local outputs={}
local real_print=print
print=function(...)
  local texts={}
  for i=1,select("#",...) do texts[#texts+1]=tostring(select(i,...)) end
  local value=table.concat(texts," ")
  outputs[#outputs+1]=value
  real_print(...)
end
memory={}
function memory.getmemorydomainlist()
  return {[0]="Main RAM",[1]="CartROM"}
end
function memory.getmemorydomainsize(domain)
  assert(domain=="Main RAM")
  return 4194304
end
local function value_at(off,domain)
  if domain=="CartROM" then
    local header=mode=="wrong_header" and "ASME" or "ASMP"
    return header:byte(off-0x0C+1) or 0
  end
  assert(domain=="Main RAM","Bad memory domain")
  if off==0x09F358 then return 3+frame end
  if off==0x11117C then return (0x1234+frame)%256 end
  if off==0x11117D then return math.floor((0x1234+frame)/256) end
  if off==0x092144 then return (0x5678-frame)%256 end
  if off==0x092145 then return math.floor((0x5678-frame)/256) end
  return 0
end
local function val_read(off,count,domain)
  assert(count>=1 and count<=4)
  local arr={}
  for i=1,count do arr[i]=value_at(off+i-1,domain) end
  if domain=="Main RAM" then
    calls=calls+1
    if count==2 then two_byte_calls=two_byte_calls+1 end
  end
  return arr
end
local function bin_reader(off,count,domain)
  local vals=val_read(off,count,domain)
  return string.char(table.unpack(vals))
end
local function array_reader(off,count,domain)
  local vals=val_read(off,count,domain)
  if mode=="array_zero" then
    local out={}
    for i=1,count do out[i-1]=vals[i] end
    return out
  end
  return vals
end
if mode=="binary" or mode=="wrong_header" then
  memory.read_bytes_as_binary_string=bin_reader
elseif mode=="proxy" then
  memory.read_bytes_as_binary_string=setmetatable({},{
    __call=function(_,off,count,domain) return bin_reader(off,count,domain) end
  })
elseif mode=="array_one" or mode=="array_zero" then
  memory.read_bytes_as_array=array_reader
elseif mode=="binary_fails_then_array" then
  memory.read_bytes_as_binary_string=function() error("Old binary read unavailable") end
  memory.read_bytes_as_array=array_reader
elseif mode=="u8" then
  memory.read_u8=function(off,domain)
    return val_read(off,1,domain)[1]
  end
elseif mode=="readbyte" then
  memory.readbyte=function(off,domain)
    return val_read(off,1,domain)[1]
  end
elseif mode=="none" then
  -- fail-closed: no memory reads exposed
else error("Unknown mock mode " .. mode) end

emu={}
function emu.framecount() return frame end
function emu.frameadvance()
  frame=frame+1
  if frame==3 then error("DSIRB049_MOCK_STOP") end
end
gui={}
function gui.text(x,y,txt)
  assert(type(x)=="number" and type(y)=="number" and type(txt)=="string")
end

local ok,err=pcall(dofile,source)
if mode=="none" then
  assert(not ok and tostring(err):find("No compatible read-only BizHawk",1,true),tostring(err))
  real_print("DSIRB049_MOCK_FAIL_CLOSED_NONE_PASS")
elseif mode=="wrong_header" then
  assert(not ok and tostring(err):find("ASMP cartridge header",1,true),tostring(err))
  real_print("DSIRB049_MOCK_FAIL_CLOSED_WRONG_HEADER_PASS")
else
  assert(not ok and tostring(err):find("DSIRB049_MOCK_STOP",1,true),tostring(err))
  assert(frame==3 and calls>=24, "Did not read all 8 fields x 3 frames")
  if mode=="u8" or mode=="readbyte" then
    assert(two_byte_calls==0, "Byte-level fallback must read one byte at a time")
  else
    assert(two_byte_calls==7, "Binary/array reader must decode 6 field reads plus 1 probe")
  end
  local log=table.concat(outputs,"\n")
  assert(log:find("yellow_coins 0x0209F358 3 -> 4",1,true),log)
  assert(log:find("yellow_coins 0x0209F358 4 -> 5",1,true),log)
  assert(log:find("health_primary 0x0211117C 4660 -> 4661",1,true),log)
  assert(log:find("Reader selected:",1,true),log)
  real_print("DSIRB049_READONLY_COMPAT_MOCK_PASS " .. mode)
end

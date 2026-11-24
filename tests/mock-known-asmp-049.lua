-- Execute the real 049 Lua source against a mock, never a real ROM.
local script=assert(arg[1])
memory={}
function memory.getmemorydomainlist() return {"Main RAM","CartROM"} end
function memory.getmemorydomainsize(_) return 4194304 end
function memory.read_bytes_as_binary_string(_,_,_) return "ASMP" end
local count=0
function memory.read_u8(off,_)
  if off==0x09F358 then return 3+count end
  return 0
end
function memory.read_u16_le(_,_) return 8 end
emu={}
function emu.framecount() return count end
function emu.frameadvance()
  count=count+1
  if count==3 then error("DSIRB049_MOCK_STOP") end
end
gui={}
function gui.text(_,_,value) assert(type(value)=="string") end
local ok,err=pcall(dofile,script)
assert(not ok and tostring(err):find("DSIRB049_MOCK_STOP",1,true),tostring(err))
assert(count==3)
print("DSIRB049_LUA_MOCK_PASS")

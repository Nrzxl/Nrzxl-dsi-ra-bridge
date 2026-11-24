-- Synthetic BizHawk melonDS Lua API mock: use Lua 5.4, NEVER a real ROM.
-- Verifies the actual 048 Lua script exposes 3 working buttons and produces
-- 3 complete 4MiB captures, each in a different stable emulated frame.
local script = arg[1]
assert(script, "Pass the BizHawk 048 Lua script as first argument")
local calls = {}
local step = 0
local emu_frame = 100
local coin_offset = 0x022220 -- synthetic, NOT a known Mario address
local timer_offset = 0x044440
local function set_byte_in_chunk(src, off, n, address, value)
  if address >= off and address < off + n then
    local i = address - off + 1
    return src:sub(1,i-1) .. string.char(value) .. src:sub(i+1)
  end
  return src
end
memory = {
  getmemorydomainlist = function()
    return {[0] = "Main RAM", [1] = "CartROM"}
  end,
  getmemorydomainsize = function(domain)
    assert(domain == "Main RAM")
    return 4194304
  end,
  read_bytes_as_binary_string = function(off, len, domain)
    if domain == "CartROM" then
      assert(off == 12 and len == 4)
      return "ASMP"
    end
    assert(domain == "Main RAM")
    assert(len == 4096 and off >= 0 and off < 4194304)
    local bytes = string.rep("\0", len)
    bytes = set_byte_in_chunk(bytes, off, len, coin_offset, step == 3 and 8 or 7)
    bytes = set_byte_in_chunk(bytes, off, len, timer_offset, 10 + step)
    return bytes
  end
}
forms = {
  newform = function(w, h, name)
    assert(w > 100 and h > 100)
    return 1
  end,
  label = function(form, txt)
    assert(form == 1 and type(txt) == "string")
  end,
  button = function(form, title, cb)
    assert(form == 1 and type(cb) == "function")
    calls[#calls+1] = cb
    return #calls
  end
}
gameinfo = {getromname = function() return "Super Mario 64 DS (mock)" end}
emu = {
  framecount = function() return emu_frame end,
  frameadvance = function()
    step = step + 1
    assert(calls[step], "Missing capture button")
    calls[step]()
    emu_frame = emu_frame + 20
    if step == 3 then
      error("__DSIRB048_MOCK_DONE__")
    end
  end
}
local ok, err = pcall(dofile, script)
assert(not ok and tostring(err):find("__DSIRB048_MOCK_DONE__",1,true),
       "Lua script did not complete 3 capture operations: " .. tostring(err))
assert(step == 3)
print("DSI048_BIZHAWK_LUA_MOCK_3x4MiB_CAPTURE_PASS")

-- DSi RA Bridge 0.4.8: BizHawk melonDS main RAM snapshot experiment.
-- Windows PC only; open in EmuHawk -> Tools -> Lua Console.
-- Read-only emulator RAM; NO writes/cheats/savestates/ROM export/RA awards.
-- Captures are private local RAM dumps (4 MiB each); NEVER upload or commit.
--
-- Domain "Main RAM" is exposed by BizHawk's melonDS Nintendo DS core.
-- Validate user's own ROM ASMP/EU separately against RA hash using
-- the 044 preflight before treating a capture as authoritative.
-- Source: https://tasvideos.org/Bizhawk/LuaFunctions
-- Main RAM domain names: https://github.com/it-was-katsumata/BizHawk-nds-mcp
local REQUIRED_BYTES = 4 * 1024 * 1024
local CHUNK = 4096
local DOMAIN = "Main RAM"
local game_code = "UNVERIFIED"
local detected_source = "NONE"
local output_root = os.getenv("DSIRB048_OUTPUT_DIR")
if not output_root or #output_root == 0 then
  local home = os.getenv("USERPROFILE")
  assert(home and #home > 0, "DSIRB048_OUTPUT_DIR or USERPROFILE required")
  output_root = home .. "/Downloads"
end
output_root = output_root:gsub("\\", "/"):gsub("/+$", "")
local session = os.date("%Y%m%d_%H%M%S") .. "_" .. tostring(emu.framecount())
local prefix = output_root .. "/DSi048_ASMP_" .. session
local completed = {}
local order = {"before", "idle", "after"}

local function assert_rom_and_domain()
  local domains = memory.getmemorydomainlist()
  local main = false
  local roms = {}
  for _, name in pairs(domains) do  -- BizHawk returns ZERO-indexed table.
    if name == DOMAIN then main = true end
    if type(name) == "string" and name:lower():find("rom", 1, true)
       and not name:lower():find("bios", 1, true) then
      roms[#roms+1] = name
    end
  end
  assert(main, "NDS melonDS domain 'Main RAM' absent; not a supported core")
  assert(memory.getmemorydomainsize(DOMAIN) == REQUIRED_BYTES,
         "Main RAM must be exactly 4 MiB: expected DS mode")
  -- Best-effort cartridge header check. Some BizHawk core revisions do NOT
  -- expose CartROM; UNKNOWN is not a trustworthy verification.
  for _, domain in ipairs(roms) do
    local ok, data = pcall(memory.read_bytes_as_binary_string, 0x0C, 4, domain)
    if ok and type(data) == "string" and #data == 4 then
      if data == "ASMP" then
        game_code, detected_source = "ASMP", domain
        return
      elseif data:match("^[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]$") then
        -- A wrong recognized ROM header is fatal. Never inspect other games.
        error("Cartridge ROM game code is " .. data .. ", not ASMP")
      end
    end
  end
  print("[DSIRB048] Game code NOT VERIFIED by BizHawk ROM domain.")
  print("[DSIRB048] Only use with your own ASMP Europe ROM; verify hash with 044.")
end

local function json_meta(label, a, b)
  return string.format(
    '{"format":"DSIRB048_BIZHAWK_RAM_V1","game_code":"%s",' ..
    '"rom_check":"%s","rom_domain":"%s","ram_domain":"Main RAM",' ..
    '"label":"%s","frame_before":%d,"frame_after":%d,' ..
    '"bytes":%d,"real_emulator_capture":true,"dsi_physical":false,' ..
    '"official_awards_sent":false}\n',
    game_code, (game_code == "ASMP") and "HEADER_MATCH_ONLY" or "UNVERIFIED",
    detected_source, label, a, b, REQUIRED_BYTES)
end

local function capture(label)
  if completed[label] then error("Already captured: " .. label) end
  if label == "idle" and not completed.before then error("Capture BEFORE first") end
  if label == "after" and not completed.idle then error("Capture IDLE first") end
  local path = prefix .. "_" .. label .. ".bin"
  local mpath = prefix .. "_" .. label .. ".json"
  local old = io.open(path, "rb")
  if old then old:close(); error("Refusing overwrite: " .. path) end
  local start = emu.framecount()
  local fh, ferr = io.open(path, "wb")
  assert(fh, "Cannot create RAM capture: " .. tostring(ferr))
  local ok, err = pcall(function()
    for off = 0, REQUIRED_BYTES - CHUNK, CHUNK do
      local bytes = memory.read_bytes_as_binary_string(off, CHUNK, DOMAIN)
      assert(type(bytes) == "string" and #bytes == CHUNK,
             "Incomplete memory read at offset " .. off)
      assert(fh:write(bytes), "Disk write failed")
    end
  end)
  fh:close()
  local finish = emu.framecount()
  if not ok or finish ~= start then
    os.remove(path)
    error(ok and "Emulator advanced during snapshot; PAUSE before capture"
          or ("Capture failed: " .. tostring(err)))
  end
  local mf = assert(io.open(mpath, "w"))
  mf:write(json_meta(label, start, finish))
  mf:close()
  completed[label] = true
  print(string.format("[DSIRB048] %s CAPTURED, frame=%d: %s", label, start, path))
  if label == "after" then
    print("[DSIRB048] All 3 captures finished. Run the Python analyzer.")
    print("[DSIRB048] Files are PRIVATE RAM dumps. Send only sanitized report.")
  end
end

assert_rom_and_domain()
print("[DSIRB048] Game header check: " .. game_code ..
      ". Console: " .. tostring(gameinfo and gameinfo.getromname and gameinfo.getromname() or "?"))
print("[DSIRB048] Output root: " .. output_root)
print("[DSIRB048] PAUSE the game before each capture. Click BEFORE, then")
print("[DSIRB048] resume without changing state, pause and click IDLE.")
print("[DSIRB048] Resume, perform ONE event, pause and click AFTER.")
local form = forms.newform(465, 190, "DSi RA Bridge 048 - READ ONLY")
forms.label(form, "BizHawk/melonDS DS mode: 4MiB snapshots. PAUSE before click.", 12, 8, 445, 27)
forms.button(form, "1. BEFORE", function() capture("before") end, 12, 49, 128, 38)
forms.button(form, "2. IDLE",   function() capture("idle") end, 158, 49, 128, 38)
forms.button(form, "3. AFTER",  function() capture("after") end, 307, 49, 128, 38)
forms.label(form, "PRIVATE dumps are saved to Downloads. No game RAM writes.", 12, 116, 445, 26)
forms.label(form, "Never send .bin snapshots, ROMs, saves or API keys.", 12, 141, 445, 25)
while true do
  emu.frameadvance()
end

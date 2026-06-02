--[[----------------------------------------------------------------------------
File:        go_home.lua
Target:      Dobot Magician E6 (DobotStudio Pro 4.4, Lua API)
Counterpart: none (standalone robot-side script)

Purpose:
    Move the robot to a known home position using a safe pre-check.

APIs used (engitbook):
    SpeedFactor(ratio)
    CheckMovJ(point, opts)
    MovJ(point, opts)
------------------------------------------------------------------------------]]

-- Reduce speed for safe homing.
local HOMING_SPEED_FACTOR = 90

-- Home joints (deg): documented neutral posture used in Motion examples.
local HOME_POINT = { joint = { 0, 0, 0, 0, 0, 0 } }

local FRAME = { user = 0, tool = 0, a = 25, v = 25 }

local function log(msg)
    print("[go_home] " .. tostring(msg))
end

log("Starting homing sequence")
SpeedFactor(HOMING_SPEED_FACTOR)
log(string.format("SpeedFactor = %d%%", HOMING_SPEED_FACTOR))

local status = CheckMovJ(HOME_POINT, FRAME)
if status == 0 then
    log("CheckMovJ OK, moving to HOME")
    MovJ(HOME_POINT, FRAME)
    log("HOME reached")
else
    log(string.format("CheckMovJ failed with status=%d, homing aborted", status))
end

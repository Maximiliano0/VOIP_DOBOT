--[[----------------------------------------------------------------------------
File:        go_home.lua
Target:      Dobot Magician E6 (DobotStudio Pro 4.4, Lua API)
Counterpart: none (standalone robot-side script)

Purpose:
    Move the robot to a known home position using a safe pre-check,
    forcing the suction cup off first.

APIs used (engitbook):
    SpeedFactor(ratio)
    CheckMovJ(point, opts)
    MovJ(point, opts)
    ToolDO(index,ON|OFF) / DO(index,ON|OFF)
------------------------------------------------------------------------------]]

-- Reduce speed for safe homing.
local HOMING_SPEED_FACTOR = 90

-- Suction (ES01) configuration.
-- Modes: "tool_do" | "controller_do" | "both"
local SUCTION_OUTPUT_MODE = "tool_do"
local SUCTION_TOOL_DO_INDEX = 1
local SUCTION_CTRL_DO_INDEX = 2
local SUCTION_OFF_STATE = OFF

-- Home joints (deg): documented neutral posture used in Motion examples.
local HOME_POINT = { joint = { 0, 0, 0, 0, 0, 0 } }

local FRAME = { user = 0, tool = 0, a = 25, v = 25 }

local function log(msg)
    print("[go_home] " .. tostring(msg))
end

local function set_suction_off()
    if SUCTION_OUTPUT_MODE == "tool_do" then
        ToolDO(SUCTION_TOOL_DO_INDEX, SUCTION_OFF_STATE)
        return true
    elseif SUCTION_OUTPUT_MODE == "controller_do" then
        DO(SUCTION_CTRL_DO_INDEX, SUCTION_OFF_STATE)
        return true
    elseif SUCTION_OUTPUT_MODE == "both" then
        ToolDO(SUCTION_TOOL_DO_INDEX, SUCTION_OFF_STATE)
        DO(SUCTION_CTRL_DO_INDEX, SUCTION_OFF_STATE)
        return true
    end
    log("Invalid SUCTION_OUTPUT_MODE")
    return false
end

log("Starting homing sequence")
SpeedFactor(HOMING_SPEED_FACTOR)
log(string.format("SpeedFactor = %d%%", HOMING_SPEED_FACTOR))

if set_suction_off() then
    log("Suction OFF")
else
    log("Could not force suction OFF")
end

local status = CheckMovJ(HOME_POINT, FRAME)
if status == 0 then
    log("CheckMovJ OK, moving to HOME")
    MovJ(HOME_POINT, FRAME)
    log("HOME reached")
else
    log(string.format("CheckMovJ failed with status=%d, homing aborted", status))
end

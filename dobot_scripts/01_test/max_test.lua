-- Version: Lua 5.4.4
-- This thread is the main thread and can call any commands.
--[[----------------------------------------------------------------------------
File:        joint_max_velocity_range_test.lua
Target:      Dobot Magician E6 (DobotStudio Pro 4.4, Lua API)
Counterpart: none (standalone robot-side script)

Purpose:
    Test each joint through a wide range at maximum command velocity.
    Sequence per joint:
      HOME -> joint max -> joint min -> HOME

IMPORTANT:
    1) Set JOINT_LIMITS to your real robot limits before running.
    2) Run with empty workspace and E-stop accessible.
    3) This script uses high speed settings on purpose.

APIs used (engitbook):
    SpeedFactor(ratio)
    CheckMovJ(point, opts)
    MovJ(point, opts)
------------------------------------------------------------------------------]]

-- ---------------------------------------------------------------------------
-- Configuration
-- ---------------------------------------------------------------------------
local SPEED_FACTOR = 100
local FRAME_MAX = { user = 0, tool = 0, a = 100, v = 100 }

-- Neutral home posture used in Dobot motion examples.
local HOME = { joint = { 0, 0, 90, 0, 90, 0 } }

-- Set real min/max limits for each joint (degrees).
-- Defaults below are placeholders; update with your E6 limits from your setup.
local JOINT_LIMITS = {
    { min = -170, max = 170 }, -- J1
    { min = -45,  max = 45  }, -- J2
    { min = -140,  max = 140 }, -- J3
    { min = -170, max = 170 }, -- J4
    { min = -120, max = 120 }, -- J5
    { min = -360, max = 360 }, -- J6
}

local function log(msg)
    print("[joint_max_test] " .. tostring(msg))
end

local function clone_joints(j)
    return { j[1], j[2], j[3], j[4], j[5], j[6] }
end

local function safe_movj(point, label)
    local status = CheckMovJ(point, FRAME_MAX)
    if status == 0 then
        log("MovJ -> " .. label)
        MovJ(point, FRAME_MAX)
        return true
    end
    log(string.format("Blocked (%s), CheckMovJ status=%d", label, status))
    return false
end

local function joint_target(base_joint, joint_index, angle)
    local j = clone_joints(base_joint)
    j[joint_index] = angle
    return { joint = j }
end

log("=== Joint max velocity/range test start ===")
SpeedFactor(SPEED_FACTOR)
log(string.format("SpeedFactor = %d%%", SPEED_FACTOR))

if not safe_movj(HOME, "HOME") then
    log("Cannot reach HOME, aborting")
    return
end

for i = 1, 6 do
    local lim = JOINT_LIMITS[i]
    log(string.format("--- Testing J%d (min=%d, max=%d) ---", i, lim.min, lim.max))

    local to_max = joint_target(HOME.joint, i, lim.max)
    local to_min = joint_target(HOME.joint, i, lim.min)

    if not safe_movj(to_max, string.format("J%d_MAX", i)) then
        log(string.format("Skipping J%d: max point not reachable", i))
    else
        if not safe_movj(to_min, string.format("J%d_MIN", i)) then
            log(string.format("J%d min point not reachable after max", i))
        end
    end

    if not safe_movj(HOME, string.format("J%d_HOME", i)) then
        log(string.format("Cannot return HOME after J%d test, aborting", i))
        return
    end
end

log("=== Joint max velocity/range test complete ===")
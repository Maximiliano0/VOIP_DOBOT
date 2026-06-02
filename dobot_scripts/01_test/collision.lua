--[[----------------------------------------------------------------------------
File:        collision_prevention_test.lua
Target:      Dobot Magician E6 (DobotStudio Pro 4.4, Lua API)
Counterpart: none (standalone test, runs entirely on the controller)

Purpose:
    Validate the collision-prevention features of the Magician E6 before
    running production motion. Configures and exercises:
        * Controller collision detection  (SetCollisionLevel / SetBackDistance)
        * SafeSkin proximity sensors      (EnableSafeSkin / SetSafeSkin)
        * Safety wall + interference area (SetSafeWallEnable / SetWorkZoneEnable)
        * Pre-flight reachability checks  (CheckMovJ / CheckMovL)

    The script also issues a deliberately UNREACHABLE target to confirm
    that CheckMovJ / CheckMovL refuse the motion, so an operator can
    observe the protective behaviour without crashing the robot.

Safety notes:
    - Run with the workspace clear and global SpeedFactor low.
    - Safety walls 1 and interference area 1 must already be defined in
      DobotStudio Pro before this script can enable them; if they are not,
      delete or comment out the SetSafeWallEnable / SetWorkZoneEnable calls.
        - SafeSkin sensitivities are configured in this script at level 3 (high).
            If there are false triggers, lower to level 2.
    - The script never moves into the unreachable target; it only asks the
      controller to check it.

APIs used (all from engitbook/):
    SpeedFactor(ratio)               -- script/Motion Params.html#speedfactor
    SetCollisionLevel(level)         -- script/Motion Params.html#setcollisionlevel
    SetBackDistance(distance)        -- script/Motion Params.html#setbackdistance
    EnableSafeSkin(ON|OFF)           -- script/Safety Skin.html#enablesafeskin
    SetSafeSkin(part, status)        -- script/Safety Skin.html#setsafeskin
    SetSafeWallEnable(idx, value)    -- script/Motion Params.html#setsafewallenable
    SetWorkZoneEnable(idx, value)    -- script/Motion Params.html#setworkzoneenable
    CheckMovJ(P, opts)               -- script/Motion Params.html#checkmovj
    CheckMovL(P, opts)               -- script/Motion Params.html#checkmovl
    MovJ / MovL                      -- script/Motion.html
    GetPose / GetAngle               -- script/Motion Params.html
    Wait(ms)                         -- script/Program Manage.html#wait
------------------------------------------------------------------------------]]

-- ---------------------------------------------------------------------------
-- Configuration
-- ---------------------------------------------------------------------------
local GLOBAL_SPEED      = 50    -- global rate, % (softer demo motion)
local A                 = 20    -- per-command acceleration, %
local V                 = 20    -- per-command velocity, %
local DWELL_MS          = 500
local COLLISION_LEVEL   = 3     -- 1..5 (lower than 5 to reduce abrupt protective stops)
local BACK_DISTANCE_MM  = 10    -- 0..50 mm, shorter retreat for smoother visual response
local SAFESKIN_LEVEL    = 3     -- 0=off, 1=low(<=5cm), 2=med(<=10cm), 3=high(<=15cm)
local USE_SAFE_WALL_1   = false -- set true if safety wall #1 is configured
local USE_WORK_ZONE_1   = false -- set true if interference area #1 is configured
local HAND_TEST_CYCLES  = 12    -- repeated path cycles for manual hand approach test
local LINEAR_SPEED_MM_S = 150   -- absolute linear speed (mm/s)
local LINEAR_BLEND_R_MM = 35    -- larger blend radius for smoother path

-- Runtime payload tuning to reduce false collision triggers.
-- Set to your real tool/load mass and CoG offset.
local USE_RUNTIME_PAYLOAD = true
local PAYLOAD_KG = 0.5
local PAYLOAD_COG_MM = { 0, 0, 10 }

-- Reachable home / test poses
local HOME       = { joint = { 0, 0, 90, 0, 90, 0 } }
local SAFE_POSE  = { pose  = { 300,   0, 300, 180, 0, 0 } }

-- Hand-test route near the front-right area. Keep your hand near this area
-- (without touching) so SafeSkin can trigger visibly while the robot moves.
local HAND_PATH = {
    { pose = { 300,  140, 300, 180, 0, 0 } },
    { pose = { 360,  140, 235, 180, 0, 0 } },
    { pose = { 360, -140, 235, 180, 0, 0 } },
    { pose = { 300, -140, 300, 180, 0, 0 } },
    { pose = { 240,    0, 330, 180, 0, 0 } },
    { pose = { 300,   0, 300, 180, 0, 0 } },
}

-- Deliberately UNREACHABLE target (far outside the E6 workspace).
-- Used only for CheckMovJ / CheckMovL — never executed.
local UNREACHABLE_POSE = { pose = { 5000, 5000, 5000, 0, 0, 0 } }

local FRAME_J = { user = 0, tool = 0, a = A, v = V }
local FRAME_L = { user = 0, tool = 0, a = A, speed = LINEAR_SPEED_MM_S, r = LINEAR_BLEND_R_MM }

-- Decode table for CheckMovJ / CheckMovL return codes (engitbook).
local CHECK_ERRORS = {
    [0]  = "no error",
    [16] = "end point near shoulder singularity",
    [17] = "end point IK has no solution",
    [18] = "end point IK out of working area",
    [22] = "arm orientation error",
    [26] = "end point near wrist singularity",
    [27] = "end point near elbow singularity",
    [29] = "speed parameter error",
    [32] = "shoulder singularity in trajectory",
    [33] = "IK no solution in trajectory",
    [34] = "IK out of working area in trajectory",
    [35] = "wrist singularity in trajectory",
    [36] = "elbow singularity in trajectory",
    [37] = "joint angle changes over 180 deg",
}

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------
local function log(msg)
    print("[collision_test] " .. tostring(msg))
end

local function describe_check(code)
    local txt = CHECK_ERRORS[code] or "unknown code"
    return string.format("status=%d (%s)", code, txt)
end

-- Pre-flight a joint motion. Only execute MovJ if the controller reports OK.
local function safe_movj(point, label)
    local status = CheckMovJ(point, FRAME_J)
    log(string.format("CheckMovJ[%s]  %s", label, describe_check(status)))
    if status == 0 then
        MovJ(point, FRAME_J)
        Wait(DWELL_MS)
        return true
    end
    log(string.format("MovJ[%s] BLOCKED by pre-flight check", label))
    return false
end

-- Pre-flight a linear motion.
local function safe_movl(point, label)
    local status = CheckMovL(point, FRAME_L)
    log(string.format("CheckMovL[%s]  %s", label, describe_check(status)))
    if status == 0 then
        MovL(point, FRAME_L)
        return true
    end
    log(string.format("MovL[%s] BLOCKED by pre-flight check", label))
    return false
end

-- ---------------------------------------------------------------------------
-- Step 1 - Lower speeds and configure controller collision detection
-- ---------------------------------------------------------------------------
log("=== Magician E6 collision-prevention test starting ===")
SpeedFactor(GLOBAL_SPEED)
log(string.format("SpeedFactor = %d%%", GLOBAL_SPEED))

SetCollisionLevel(COLLISION_LEVEL)
log(string.format("SetCollisionLevel(%d)", COLLISION_LEVEL))

SetBackDistance(BACK_DISTANCE_MM)
log(string.format("SetBackDistance(%d) mm", BACK_DISTANCE_MM))

if USE_RUNTIME_PAYLOAD then
    SetPayload(PAYLOAD_KG, PAYLOAD_COG_MM)
    log(string.format("SetPayload(%.2f kg, {%d,%d,%d} mm)",
        PAYLOAD_KG, PAYLOAD_COG_MM[1], PAYLOAD_COG_MM[2], PAYLOAD_COG_MM[3]))
end

-- ---------------------------------------------------------------------------
-- Step 2 - Configure SafeSkin (forearm + J4..J6)
-- ---------------------------------------------------------------------------
log("Configuring SafeSkin sensitivity per part")
SetSafeSkin(3, SAFESKIN_LEVEL)  -- forearm
SetSafeSkin(4, SAFESKIN_LEVEL)  -- J4
SetSafeSkin(5, SAFESKIN_LEVEL)  -- J5
SetSafeSkin(6, SAFESKIN_LEVEL)  -- J6

local skinTriggered = EnableSafeSkin(ON)
log(string.format("EnableSafeSkin(ON) returned %s",
    tostring(skinTriggered)))
if skinTriggered == 1 then
    log("WARNING: SafeSkin reports a contact at startup -- clear before motion")
end

-- ---------------------------------------------------------------------------
-- Step 3 - Optional virtual safety boundaries
-- ---------------------------------------------------------------------------
if USE_SAFE_WALL_1 then
    SetSafeWallEnable(1, true)
    log("SetSafeWallEnable(1, true)")
end
if USE_WORK_ZONE_1 then
    SetWorkZoneEnable(1, true)
    log("SetWorkZoneEnable(1, true)")
end

-- ---------------------------------------------------------------------------
-- Step 4 - Move to home using pre-flight check
-- ---------------------------------------------------------------------------
safe_movj(HOME, "HOME")
log("Joints at home: " .. tostring(GetAngle()))

-- ---------------------------------------------------------------------------
-- Step 5 - Pre-flight a deliberately unreachable target.
-- The controller MUST refuse it; the script must NOT issue MovJ/MovL.
-- ---------------------------------------------------------------------------
log("---- Pre-flight test: deliberately unreachable target ----")
local bad_j = CheckMovJ(UNREACHABLE_POSE, FRAME_J)
log("CheckMovJ[UNREACHABLE]  " .. describe_check(bad_j))
if bad_j ~= 0 then
    log("OK - joint pre-flight correctly refused the unreachable target")
else
    log("FAIL - controller accepted an unreachable target; abort")
    return
end

local bad_l = CheckMovL(UNREACHABLE_POSE, FRAME_L)
log("CheckMovL[UNREACHABLE]  " .. describe_check(bad_l))
if bad_l ~= 0 then
    log("OK - linear pre-flight correctly refused the unreachable target")
else
    log("FAIL - controller accepted an unreachable target; abort")
    return
end

-- ---------------------------------------------------------------------------
-- Step 6 - Reachable motion sequence with pre-flight checks
-- ---------------------------------------------------------------------------
log("---- Reachable motion sequence ----")
safe_movj(SAFE_POSE, "SAFE_POSE")
log("Pose: " .. tostring(GetPose()))

log(string.format("Starting smooth hand-stop demo cycles: %d", HAND_TEST_CYCLES))
log(string.format("Linear mode: speed=%d mm/s, blend r=%d mm",
    LINEAR_SPEED_MM_S, LINEAR_BLEND_R_MM))
for i = 1, HAND_TEST_CYCLES do
    log(string.format("Cycle %d/%d", i, HAND_TEST_CYCLES))
    for j, p in ipairs(HAND_PATH) do
        if not safe_movl(p, string.format("HAND_PATH_%d", j)) then
            log("Stopping cycles because motion was blocked")
            break
        end
    end
end

safe_movj(HOME,      "HOME")

-- ---------------------------------------------------------------------------
-- Step 7 - Tear-down (leave SafeSkin enabled; collision settings are
-- restored automatically when the project stops, per engitbook).
-- ---------------------------------------------------------------------------
log("=== Collision-prevention test complete ===")
log("Note: SetCollisionLevel/SetBackDistance values revert when the")
log("project stops, as documented in Motion Params.html.")

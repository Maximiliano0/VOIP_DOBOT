--[[----------------------------------------------------------------------------
File:        mobility_test.lua
Target:      Dobot Magician E6 (DobotStudio Pro 4.4, Lua API)
Counterpart: none (standalone test, runs entirely on the controller)

Purpose:
    Exercise each of the 6 joints and verify Cartesian (linear) motion to
    confirm basic mobility of the robot after setup or reconnection.

Safety notes:
    - Run with the workspace clear and the speed override (global rate) low
      from the DobotStudio Pro panel the first time.
    - The script also lowers the global SpeedFactor at start.
    - All joint targets are small deltas around the safe home pose
      {0, 0, 90, 0, 90, 0} (deg), which is the documented neutral pose for
      the Magician E6 in the Lua reference.
    - Cartesian (MovL) motion is restricted to a small box near the home
      pose. Verify the pose values fit your installed user/tool frames
      before running.

APIs used (all from engitbook/):
    SpeedFactor(ratio)            -- Motion Params.html#speedfactor
    MovJ(point, opts)             -- Motion.html#movj
    MovL(point, opts)             -- Motion.html#movl
    GetAngle(), GetPose()         -- Motion Params.html
    Wait(ms)                      -- Program Manage.html#wait
------------------------------------------------------------------------------]]

-- ---------------------------------------------------------------------------
-- Configuration
-- ---------------------------------------------------------------------------
local GLOBAL_SPEED = 20         -- global rate, %  (kept low for testing)
local A            = 30         -- per-command acceleration, %
local V            = 30         -- per-command velocity, %
local DWELL_MS     = 500        -- pause between motions, ms

-- Safe home joint posture (degrees)
local HOME = { joint = { 0, 0, 90, 0, 90, 0 } }

-- Per-joint test deltas (degrees). Kept small to stay inside the workspace.
local JOINT_DELTAS = {
    { dj = 1, delta =  20 },    -- J1
    { dj = 2, delta = -15 },    -- J2
    { dj = 3, delta = -15 },    -- J3
    { dj = 4, delta =  30 },    -- J4
    { dj = 5, delta = -20 },    -- J5
    { dj = 6, delta =  45 },    -- J6
}

-- Cartesian test box (mm / deg). Adjust to match your installed user frame.
-- Pose layout: { x, y, z, rx, ry, rz }
local CART_HOME    = { pose = { 300, 0, 300, 180, 0, 0 } }
local CART_TARGETS = {
    { pose = { 300,  80, 300, 180, 0, 0 } },   -- +Y
    { pose = { 300,  80, 250, 180, 0, 0 } },   -- -Z
    { pose = { 300, -80, 250, 180, 0, 0 } },   -- -Y
    { pose = { 300, -80, 300, 180, 0, 0 } },   -- +Z
    { pose = { 300,   0, 300, 180, 0, 0 } },   -- back to center
}

local FRAME = { user = 0, tool = 0, a = A, v = V }

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------
local function log(msg)
    print("[mobility_test] " .. tostring(msg))
end

local function clone_joints(j)
    return { j[1], j[2], j[3], j[4], j[5], j[6] }
end

local function move_joint_delta(base, idx, delta)
    local target = clone_joints(base)
    target[idx] = target[idx] + delta
    log(string.format("MovJ J%d %+d deg", idx, delta))
    MovJ({ joint = target }, FRAME)
    Wait(DWELL_MS)
end

-- ---------------------------------------------------------------------------
-- Test sequence
-- ---------------------------------------------------------------------------
log("=== Magician E6 mobility test starting ===")
SpeedFactor(GLOBAL_SPEED)
log(string.format("Global SpeedFactor = %d%%", GLOBAL_SPEED))

-- 1. Move to safe home
log("Step 1: MovJ -> HOME")
MovJ(HOME, FRAME)
Wait(DWELL_MS)

local startAngle = GetAngle()
log("Joint angles at home: " .. tostring(startAngle))

-- 2. Per-joint test: move +delta, return to home
log("Step 2: per-joint MovJ test")
local home_joints = HOME.joint
for _, t in ipairs(JOINT_DELTAS) do
    move_joint_delta(home_joints, t.dj, t.delta)
    log(string.format("MovJ J%d back to home", t.dj))
    MovJ(HOME, FRAME)
    Wait(DWELL_MS)
end

-- 3. Cartesian (linear) motion test
log("Step 3: Cartesian MovL test box")
MovJ(CART_HOME, FRAME)
Wait(DWELL_MS)

local startPose = GetPose()
log("Pose at Cartesian home: " .. tostring(startPose))

for i, p in ipairs(CART_TARGETS) do
    log(string.format("MovL -> target %d", i))
    MovL(p, FRAME)
    Wait(DWELL_MS)
end

-- 4. Return to safe home
log("Step 4: MovJ -> HOME (final)")
MovJ(HOME, FRAME)

log("=== Magician E6 mobility test complete ===")

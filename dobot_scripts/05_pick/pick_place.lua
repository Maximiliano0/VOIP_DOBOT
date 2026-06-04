-- Version: Lua 5.4.4
-- This thread is the main thread and can call any commands.
-- pick_place.lua
-- Target: Dobot Magician E6 (DobotStudio Pro 4.4)
-- Points taught in DobotStudio:
--   P1  alias HOME
--   P2  alias PICK

SpeedFactor(40)

print("MovJ -> HOME (P1)")
MovJ(P1)

print("MovJ -> PICK (P2)")
MovJ(P2)

print("Ventosa ON")
ToolDO(1, ON)

print("MovJ -> PLACE (P3)")
MovJ(P3)

print("Ventosa OFF")
ToolDO(1, OFF)

print("MovJ -> HOME (P1)")
MovJ(P1)

print("done")

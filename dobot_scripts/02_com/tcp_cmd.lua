-- tcp_cmd.lua
-- Robot-side TCP command server for Dobot Magician E6
-- Counterpart: pc_scripts/02_com/send_cmd/send_cmd.py
--
-- Behavior:
--  * Creates a TCP server.
--  * Accepts one client at a time.
--  * If the client disconnects (TCPRead/TCPWrite fails), destroys the
--    socket and recreates it to accept a new client. This avoids the
--    "server hangs after one command" problem caused by reusing a dead
--    socket.

local ROBOT_IP = "192.168.5.1"
local PORT = 6001
local READ_TIMEOUT_S = 2

local TURN_DEG = 45
local TILT_DEG = 25
local MOTION = { a = 60, v = 60, cp = 0 }
local HOME = { joint = { 0, 0, 90, 0, 90, 0 } }

-- Adjust to your gripper wiring.
local GRIPPER_DO_INDEX = 1
local GRIPPER_OPEN_STATE = OFF
local GRIPPER_CLOSE_STATE = ON

-- Adjust to your ES01 suction cup wiring.
-- Typical behavior: ON enables suction, OFF disables suction.
local SUCTION_DO_INDEX = 2
local SUCTION_ON_STATE = ON
local SUCTION_OFF_STATE = OFF

local function log(msg)
    print("[tcp_cmd] " .. tostring(msg))
end

local function trim(s)
    return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function exec_cmd(cmd)
    if cmd == "derecha" then
        RelJointMovJ({ -TURN_DEG, 0, 0, 0, 0, 0 }, MOTION)
        return "ok derecha", false
    elseif cmd == "izquierda" then
        RelJointMovJ({ TURN_DEG, 0, 0, 0, 0, 0 }, MOTION)
        return "ok izquierda", false
    elseif cmd == "arriba" then
        RelJointMovJ({ 0, -TILT_DEG, 0, 0, 0, 0 }, MOTION)
        return "ok arriba", false
    elseif cmd == "abajo" then
        RelJointMovJ({ 0, TILT_DEG, 0, 0, 0, 0 }, MOTION)
        return "ok abajo", false
    elseif cmd == "home" or cmd == "origen" then
        MovJ(HOME, MOTION)
        return "ok home", false
    elseif cmd == "abrir_gripper" then
        DO(GRIPPER_DO_INDEX, GRIPPER_OPEN_STATE)
        return "ok abrir_gripper", false
    elseif cmd == "cerrar_gripper" then
        DO(GRIPPER_DO_INDEX, GRIPPER_CLOSE_STATE)
        return "ok cerrar_gripper", false
    elseif cmd == "activar_ventosa" or cmd == "suction_on" then
        DO(SUCTION_DO_INDEX, SUCTION_ON_STATE)
        return "ok activar_ventosa", false
    elseif cmd == "desactivar_ventosa" or cmd == "suction_off" then
        DO(SUCTION_DO_INDEX, SUCTION_OFF_STATE)
        return "ok desactivar_ventosa", false
    elseif cmd == "ping" then
        return "pong", false
    elseif cmd == "salir" or cmd == "exit" then
        return "bye", true
    end

    return "err comando no reconocido", false
end

local function open_server()
    local err, sock = TCPCreate(true, ROBOT_IP, PORT)
    if err ~= 0 then
        log(string.format("TCPCreate failed: %d", err))
        return nil
    end
    log("Waiting for client...")
    err = TCPStart(sock, 0)
    if err ~= 0 then
        log(string.format("TCPStart failed: %d", err))
        TCPDestroy(sock)
        return nil
    end
    log("Client connected.")
    return sock
end

local function serve_session(sock)
    local pending = ""
    local idle_cycles = 0
    while true do
        local rerr, buf = TCPRead(sock, READ_TIMEOUT_S, "string")
        if rerr == 0 and buf and buf ~= "" then
            idle_cycles = 0
            pending = pending .. buf
            while true do
                local nl = string.find(pending, "[\r\n]")
                if not nl then break end
                local line = string.sub(pending, 1, nl - 1)
                pending = string.sub(pending, nl + 1)
                local cmd = string.lower(trim(line))
                if cmd ~= "" then
                    log("RX: " .. cmd)
                    local reply, should_quit = exec_cmd(cmd)
                    local werr = TCPWrite(sock, tostring(reply) .. "\n", 1)
                    if werr ~= 0 then
                        log("write error, closing session")
                        return false
                    end
                    if should_quit then
                        return true
                    end
                end
            end
        else
            -- read failed: could be timeout (idle) or peer closed.
            -- Probe by attempting a zero-length write; if it fails, peer is gone.
            local werr = TCPWrite(sock, "", 1)
            if werr ~= 0 then
                log("client disconnected")
                return false
            end
            idle_cycles = idle_cycles + 1
        end
    end
end

log(string.format("TCP server starting on %s:%d", ROBOT_IP, PORT))

local stop = false
while not stop do
    local sock = open_server()
    if sock then
        local quit = serve_session(sock)
        TCPDestroy(sock)
        if quit then
            stop = true
        else
            log("re-opening listener...")
        end
    else
        log("server open failed; retrying...")
        Wait(500)
    end
end

log("TCP server stopped")

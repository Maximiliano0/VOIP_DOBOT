"""
File:        send_cmd.py
Target:      Operator PC (Python)
Counterpart: dobot_scripts/02_com/tcp_cmd.lua

Purpose:
    Send Ethernet commands to the robot TCP command server.
    Includes a Tkinter GUI for simplified operation.

Design:
    The robot Lua server accepts one client at a time. To avoid forcing
    the server to re-open its listener on every command, the GUI/CLI
    keeps a single persistent TCP connection and reuses it. If the
    connection drops, it transparently reconnects on the next command.

Usage examples:
    python pc_scripts/02_com/send_cmd/send_cmd.py --ip 192.168.5.1 --port 6001
    python pc_scripts/02_com/send_cmd/send_cmd.py --cli --ip 192.168.5.1 --port 6001
    python pc_scripts/02_com/send_cmd/send_cmd.py --ip 192.168.5.1 --port 6001 derecha
    pc_scripts/02_com/send_cmd/dist/send_cmd_gui.exe --ip 192.168.5.1 --port 6001 ping

Commands supported by tcp_cmd.lua:
    derecha, izquierda, arriba, abajo,
    abrir_gripper, cerrar_gripper,
    home, origen,
    activar_ventosa, desactivar_ventosa,
    ping, salir
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from typing import Optional


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "send_cmd_config.json")

COMMAND_ALIASES = {
    "origen": "home",
    "suction_on": "activar_ventosa",
    "suction_off": "desactivar_ventosa",
}


def normalize_command(cmd: str) -> str:
    normalized = " ".join(cmd.strip().lower().split())
    return COMMAND_ALIASES.get(normalized, normalized)


def load_defaults() -> dict[str, object]:
    defaults: dict[str, object] = {
        "ip": os.environ.get("DOBOT_IP", ""),
        "port": int(os.environ.get("DOBOT_PORT", "6001")),
        "timeout": float(os.environ.get("DOBOT_TIMEOUT", "5.0")),
    }

    if not os.path.exists(CONFIG_PATH):
        return defaults

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return defaults

    if isinstance(cfg, dict):
        if isinstance(cfg.get("ip"), str):
            defaults["ip"] = cfg["ip"].strip()
        if isinstance(cfg.get("port"), int):
            defaults["port"] = cfg["port"]
        if isinstance(cfg.get("timeout"), (int, float)):
            defaults["timeout"] = float(cfg["timeout"])
    return defaults


def clear_console() -> None:
    # Skip when running as a windowed app (no console attached); calling
    # os.system("cls") in that case would briefly pop a console window.
    import sys
    if sys.stdout is None or not sys.stdout.isatty():
        return
    os.system("cls" if os.name == "nt" else "clear")


class RobotConnection:
    """Persistent TCP connection to the Lua command server.

    Keeps a single socket open across commands so the Lua server does
    not need to reopen its listener after every command. If the link
    drops, the next send() automatically reconnects.
    """

    def __init__(self, ip: str, port: int, timeout: float) -> None:
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self._buffer = b""

    def close(self) -> None:
        with self._lock:
            self._close_locked()

    def _close_locked(self) -> None:
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
            self._buffer = b""

    def _connect_locked(self) -> Optional[str]:
        if not self.ip.strip():
            return "ERR connection: missing IP (set --ip or send_cmd_config.json)"
        try:
            s = socket.create_connection((self.ip, self.port), timeout=self.timeout)
        except (TimeoutError, OSError) as exc:
            return f"ERR connection: {exc}"
        s.settimeout(self.timeout)
        try:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        self._sock = s
        self._buffer = b""
        return None

    def _read_line_locked(self) -> Optional[str]:
        assert self._sock is not None
        while b"\n" not in self._buffer:
            try:
                chunk = self._sock.recv(4096)
            except socket.timeout:
                return None
            except OSError:
                return None
            if not chunk:
                return None
            self._buffer += chunk
        line, _, rest = self._buffer.partition(b"\n")
        self._buffer = rest
        return line.decode("utf-8", errors="replace").strip()

    def send(self, cmd: str) -> Optional[str]:
        cmd = cmd.strip()
        if not cmd:
            return ""

        with self._lock:
            for attempt in range(2):
                if self._sock is None:
                    err = self._connect_locked()
                    if err is not None:
                        return err

                payload = (cmd + "\n").encode("utf-8")
                try:
                    assert self._sock is not None
                    self._sock.sendall(payload)
                except OSError as exc:
                    self._close_locked()
                    if attempt == 0:
                        continue
                    return f"ERR connection: {exc}"

                reply = self._read_line_locked()
                if reply is None:
                    self._close_locked()
                    if attempt == 0:
                        continue
                    return None
                return reply

            return None

    def update_target(self, ip: str, port: int, timeout: float) -> None:
        with self._lock:
            changed = (ip != self.ip) or (port != self.port)
            self.ip = ip
            self.port = port
            self.timeout = timeout
            if changed:
                self._close_locked()
            elif self._sock is not None:
                try:
                    self._sock.settimeout(timeout)
                except OSError:
                    pass


def interactive_mode(conn: RobotConnection) -> None:
    print(f"Connected target: {conn.ip}:{conn.port}")
    print(
        "Type commands: derecha | izquierda | arriba | abajo | "
        "abrir_gripper | cerrar_gripper | home | origen | "
        "activar_ventosa | desactivar_ventosa | ping | salir"
    )
    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd:
            continue
        wire_cmd = normalize_command(cmd)
        reply = conn.send(wire_cmd)
        if reply is None:
            print("(no reply: timeout)")
        elif reply.startswith("ERR connection:"):
            print(f"({reply})")
        else:
            print(f"< {reply}")
        if wire_cmd in {"salir", "exit"}:
            break


class CommandApp:
    def __init__(self, ip: str, port: int, timeout: float) -> None:
        self.root = tk.Tk()
        self.root.title("Dobot TCP Commander")
        self.root.geometry("560x540")

        self.ip_var = tk.StringVar(value=ip)
        self.port_var = tk.StringVar(value=str(port))
        self.timeout_var = tk.StringVar(value=str(timeout))

        self.conn = RobotConnection(ip, port, timeout)
        self._send_lock = threading.Lock()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        self.conn.close()
        self.root.destroy()

    def _build_ui(self) -> None:
        top = tk.Frame(self.root, padx=10, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="Robot IP:").grid(row=0, column=0, sticky="w")
        tk.Entry(top, textvariable=self.ip_var, width=18).grid(row=0, column=1, padx=(6, 12))

        tk.Label(top, text="Port:").grid(row=0, column=2, sticky="w")
        tk.Entry(top, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=(6, 12))

        tk.Label(top, text="Timeout (s):").grid(row=0, column=4, sticky="w")
        tk.Entry(top, textvariable=self.timeout_var, width=8).grid(row=0, column=5, padx=(6, 0))

        tk.Button(top, text="Reconnect", command=self.reconnect, width=10).grid(
            row=0, column=6, padx=(12, 0)
        )

        btns = tk.Frame(self.root, padx=10, pady=6)
        btns.pack(fill="x")

        commands = [
            "derecha",
            "izquierda",
            "arriba",
            "abajo",
            "origen",
            "abrir_gripper",
            "cerrar_gripper",
            "activar_ventosa",
            "desactivar_ventosa",
            "home",
            "ping",
            "salir",
        ]

        for i, cmd in enumerate(commands):
            tk.Button(
                btns,
                text=cmd,
                width=16,
                command=lambda c=cmd: self.send_command(c),
            ).grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="ew")

        custom = tk.Frame(self.root, padx=10, pady=8)
        custom.pack(fill="x")

        tk.Label(custom, text="Custom command:").pack(side="left")
        self.custom_entry = tk.Entry(custom)
        self.custom_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.custom_entry.bind("<Return>", lambda _: self.send_custom())
        tk.Button(custom, text="Send", command=self.send_custom, width=10).pack(side="left")

        log_frame = tk.Frame(self.root, padx=10, pady=8)
        log_frame.pack(fill="both", expand=True)

        self.log_widget = scrolledtext.ScrolledText(log_frame, height=16, state="disabled")
        self.log_widget.pack(fill="both", expand=True)

        self.log("GUI ready. Persistent TCP connection will open on first command.")

    def _params(self) -> tuple[str, int, float]:
        ip = self.ip_var.get().strip()
        port = int(self.port_var.get().strip())
        timeout = float(self.timeout_var.get().strip())
        return ip, port, timeout

    def log(self, text: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", text + "\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def reconnect(self) -> None:
        try:
            ip, port, timeout = self._params()
        except ValueError as exc:
            self.log(f"Invalid input: {exc}")
            return
        self.conn.update_target(ip, port, timeout)
        self.conn.close()
        self.log(f"Reconnect requested -> {ip}:{port}")

    def send_custom(self) -> None:
        cmd = self.custom_entry.get().strip()
        if not cmd:
            return
        self.send_command(cmd)
        self.custom_entry.delete(0, "end")

    def send_command(self, cmd: str) -> None:
        def worker() -> None:
            try:
                ip, port, timeout = self._params()
            except ValueError as exc:
                self.root.after(0, lambda: self.log(f"Invalid input: {exc}"))
                return

            wire_cmd = normalize_command(cmd)

            self.conn.update_target(ip, port, timeout)
            if wire_cmd != cmd:
                self.root.after(0, lambda: self.log(f"> {cmd} -> {wire_cmd}  ({ip}:{port})"))
            else:
                self.root.after(0, lambda: self.log(f"> {wire_cmd}  ({ip}:{port})"))

            with self._send_lock:
                reply = self.conn.send(wire_cmd)

            if reply is None:
                self.root.after(0, lambda: self.log("< No reply (timeout)"))
            elif reply.startswith("ERR connection:"):
                self.root.after(0, lambda: self.log(f"< {reply}"))
            elif reply == "":
                self.root.after(0, lambda: self.log("< Empty reply"))
            else:
                self.root.after(0, lambda: self.log(f"< {reply}"))

        threading.Thread(target=worker, daemon=True).start()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    clear_console()

    defaults = load_defaults()
    default_ip = str(defaults["ip"])
    default_port = int(defaults["port"])
    default_timeout = float(defaults["timeout"])

    parser = argparse.ArgumentParser(description="Send TCP commands to Dobot Lua server")
    parser.add_argument("--ip", default=default_ip, help="Robot controller IP address")
    parser.add_argument("--port", type=int, default=default_port, help="TCP server port (default: 6001)")
    parser.add_argument("--timeout", type=float, default=default_timeout, help="Socket timeout seconds")
    parser.add_argument("--cli", action="store_true", help="Use CLI mode instead of GUI")
    parser.add_argument("command", nargs="?", help="Single command to send")
    args = parser.parse_args()

    if args.command:
        wire_cmd = normalize_command(args.command)
        conn = RobotConnection(args.ip, args.port, args.timeout)
        try:
            reply = conn.send(wire_cmd)
        finally:
            conn.close()
        if reply is None:
            print("No reply (timeout)")
        elif reply.startswith("ERR connection:"):
            print(reply)
        else:
            print(reply)
        return

    if args.cli:
        conn = RobotConnection(args.ip, args.port, args.timeout)
        try:
            interactive_mode(conn)
        finally:
            conn.close()
        return

    app = CommandApp(args.ip, args.port, args.timeout)
    app.run()


if __name__ == "__main__":
    main()

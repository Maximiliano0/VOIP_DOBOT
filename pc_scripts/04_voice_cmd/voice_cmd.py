"""
File:        voice_cmd.py
Target:      Operator PC (Python)
Counterpart: dobot_scripts/02_com/tcp_cmd.lua

Purpose:
    Detect spoken robot commands from the PC microphone and send them
    automatically to the Dobot Magician E6 via TCP.

    Commands recognised and sent:
        derecha, izquierda, home, arriba, abajo

Design:
    - Voice detection uses Vosk (offline, closed grammar).
    - TCP transport reuses the persistent-connection RobotConnection class
      from pc_scripts/02_com/send_cmd/send_cmd.py.
    - Both subsystems run in background threads; the Tkinter main loop only
      polls a shared queue every 100 ms — no blocking calls on the UI thread.

Usage:
    python pc_scripts/04_voice_cmd/voice_cmd.py
    python pc_scripts/04_voice_cmd/voice_cmd.py --ip 192.168.5.1 --port 6001

Configuration:
    Robot IP / port / timeout are read from voice_cmd_config.json (same folder).
    Environment variables DOBOT_IP, DOBOT_PORT, DOBOT_TIMEOUT are also honoured.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import socket
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import sounddevice as sd
from vosk import KaldiRecognizer, Model

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "voice_cmd_config.json"
# When packaged with PyInstaller, bundled data lands in sys._MEIPASS
DEFAULT_MODEL_DIR: Path = (
    Path(sys._MEIPASS) / "model"
    if getattr(sys, "frozen", False)
    else SCRIPT_DIR / "model"
)
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_ROBOT_IP = "192.168.5.1"

TARGET_WORDS = ["derecha", "izquierda", "home", "arriba", "abajo"]


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    defaults: dict = {
        "ip": os.environ.get("DOBOT_IP", DEFAULT_ROBOT_IP),
        "port": int(os.environ.get("DOBOT_PORT", "6001")),
        "timeout": float(os.environ.get("DOBOT_TIMEOUT", "5.0")),
        "model_path": str(DEFAULT_MODEL_DIR),
        "sample_rate": DEFAULT_SAMPLE_RATE,
    }
    if not CONFIG_PATH.exists():
        return defaults
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return defaults
    if isinstance(data, dict):
        for key in ("ip", "model_path"):
            if isinstance(data.get(key), str):
                defaults[key] = data[key].strip()
        if isinstance(data.get("port"), int):
            defaults["port"] = data["port"]
        if isinstance(data.get("timeout"), (int, float)):
            defaults["timeout"] = float(data["timeout"])
        if isinstance(data.get("sample_rate"), int):
            defaults["sample_rate"] = data["sample_rate"]
    return defaults


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def list_input_devices() -> list[dict]:
    devices: list[dict] = []
    for idx, info in enumerate(sd.query_devices()):
        if info.get("max_input_channels", 0) > 0:
            devices.append({"index": idx, "name": info["name"]})
    return devices


def normalize_word(value: str) -> str:
    return " ".join(value.strip().lower().split())


# ---------------------------------------------------------------------------
# TCP connection (persistent, thread-safe)
# Based on RobotConnection from pc_scripts/02_com/send_cmd/send_cmd.py
# ---------------------------------------------------------------------------

class RobotConnection:
    """Persistent TCP connection to the Lua command server (tcp_cmd.lua)."""

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
            return "ERR: IP vacía — ingresa la IP del robot"
        try:
            s = socket.create_connection((self.ip, self.port), timeout=self.timeout)
        except (TimeoutError, OSError) as exc:
            return f"ERR conexión: {exc}"
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
            except (socket.timeout, OSError):
                return None
            if not chunk:
                return None
            self._buffer += chunk
        line, _, rest = self._buffer.partition(b"\n")
        self._buffer = rest
        return line.decode("utf-8", errors="replace").strip()

    def send(self, cmd: str) -> str:
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
                    return f"ERR envío: {exc}"
                reply = self._read_line_locked()
                if reply is None:
                    self._close_locked()
                    if attempt == 0:
                        continue
                    return "ERR: sin respuesta del robot"
                return reply
        return "ERR: fallo desconocido"

    def ping(self) -> str:
        return self.send("ping")

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

    @property
    def is_connected(self) -> bool:
        return self._sock is not None


# ---------------------------------------------------------------------------
# Voice recognizer worker (background thread)
# Based on VoiceRecognizerWorker from pc_scripts/03_ml/voice_word_gui.py
# ---------------------------------------------------------------------------

class VoiceRecognizerWorker:
    """Opens the microphone and posts events to *event_queue*.

    Event tuples: ("running", bool), ("command", word), ("final", text),
                  ("partial", text), ("status", msg), ("error", msg), ("stopped", True)
    """

    def __init__(
        self,
        model_path: Path,
        sample_rate: int,
        device_index: int | None,
        event_queue: queue.Queue,
    ) -> None:
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.event_queue = event_queue
        self.stop_event = threading.Event()
        self.audio_queue: queue.Queue[bytes | None] = queue.Queue()
        self.thread: threading.Thread | None = None
        self.stream = None
        self.recognizer = None
        self.model = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo Vosk no encontrado: {self.model_path}")
        self.model = Model(str(self.model_path))
        grammar = json.dumps(TARGET_WORDS)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar)
        self.recognizer.SetWords(True)
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.audio_queue.put(None)
        if self.stream is not None:
            try:
                self.stream.stop()
            except RuntimeError:
                pass
            try:
                self.stream.close()
            except RuntimeError:
                pass
            self.stream = None

    def _audio_callback(self, indata, _frames, _time, status) -> None:
        if status:
            self.event_queue.put(("status", f"Audio: {status}"))
        self.audio_queue.put(bytes(indata))

    def _run(self) -> None:
        self.event_queue.put(("status", "Escuchando..."))
        self.event_queue.put(("running", True))
        try:
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                device=self.device_index,
                dtype="int16",
                channels=1,
                callback=self._audio_callback,
            )
            with self.stream:
                while not self.stop_event.is_set():
                    chunk = self.audio_queue.get()
                    if chunk is None:
                        break
                    if self.recognizer.AcceptWaveform(chunk):
                        result = json.loads(self.recognizer.Result())
                        text = normalize_word(result.get("text", ""))
                        if text:
                            self.event_queue.put(("final", text))
                            if text in TARGET_WORDS:
                                self.event_queue.put(("command", text))
        except (OSError, RuntimeError, ValueError) as exc:
            self.event_queue.put(("error", str(exc)))
        finally:
            self.stop_event.set()
            self.event_queue.put(("running", False))
            self.event_queue.put(("stopped", True))


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class VoiceCmdApp(tk.Tk):
    """Combined voice + TCP command GUI for the Dobot Magician E6."""

    def __init__(self, initial_ip: str = "", initial_port: int = 6001) -> None:
        super().__init__()
        self.title("Control de voz — Dobot Magician E6")
        self.geometry("980x720")
        self.minsize(860, 600)

        cfg = load_config()
        if initial_ip:
            cfg["ip"] = initial_ip
        if initial_port != 6001 or not cfg.get("ip"):
            cfg["port"] = initial_port

        # --- Tkinter vars ---
        self.ip_var = tk.StringVar(value=cfg.get("ip", ""))
        self.port_var = tk.StringVar(value=str(cfg.get("port", 6001)))
        self.timeout_var = tk.StringVar(value=str(cfg.get("timeout", 5.0)))
        self.model_path_var = tk.StringVar(value=cfg.get("model_path", str(DEFAULT_MODEL_DIR)))
        self.sample_rate_var = tk.StringVar(value=str(cfg.get("sample_rate", DEFAULT_SAMPLE_RATE)))
        self.device_var = tk.StringVar(value="Auto")
        self.tcp_status_var = tk.StringVar(value="Desconectado")
        self.voice_status_var = tk.StringVar(value="Detenido")
        self.last_cmd_var = tk.StringVar(value="—")
        self.count_var = tk.StringVar(value="0")
        self.partial_var = tk.StringVar(value="")
        self.auto_send_var = tk.BooleanVar(value=True)

        # --- State ---
        self.event_queue: queue.Queue = queue.Queue()
        self.worker: VoiceRecognizerWorker | None = None
        self.connection: RobotConnection = RobotConnection(
            cfg.get("ip", ""), cfg.get("port", 6001), cfg.get("timeout", 5.0)
        )
        self.after_job: str | None = None
        self.device_map: dict[str, int | None] = {"Auto": None}
        self.device_combo: ttk.Combobox | None = None
        self.command_count = 0

        self._build_ui()
        self._load_devices()
        self._poll_events()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        # Header
        ttk.Label(root, text="Control de voz — Dobot Magician E6",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(root, text=(
            "Di: derecha · izquierda · home · arriba · abajo  "
            "— el comando se envía automáticamente al robot."
        )).pack(anchor="w", pady=(4, 14))

        # Two-column layout: left = settings, right = status/log
        cols = ttk.Frame(root)
        cols.pack(fill="both", expand=True)
        cols.columnconfigure(0, weight=0, minsize=380)
        cols.columnconfigure(1, weight=1)

        left = ttk.Frame(cols)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        right = ttk.Frame(cols)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_connection_panel(left)
        self._build_voice_panel(left)
        self._build_controls(left)
        self._build_status_panel(right)
        self._build_log_panel(right)

    def _build_connection_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Conexión TCP (robot)", padding=12)
        frame.pack(fill="x", pady=(0, 10))

        rows = [
            ("IP del robot", self.ip_var, False),
            ("Puerto", self.port_var, False),
            ("Timeout (s)", self.timeout_var, False),
        ]
        for i, (label, var, _) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=3, padx=(0, 10))
            ttk.Entry(frame, textvariable=var, width=28).grid(row=i, column=1, sticky="ew", pady=3)
        frame.columnconfigure(1, weight=1)

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=len(rows), column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Button(btn_row, text="Probar conexión (ping)", command=self._do_ping).pack(side="left")
        ttk.Button(btn_row, text="Desconectar", command=self._do_disconnect).pack(side="left", padx=(8, 0))

        tcp_row = ttk.Frame(frame)
        tcp_row.grid(row=len(rows) + 1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(tcp_row, text="TCP:").pack(side="left")
        ttk.Label(tcp_row, textvariable=self.tcp_status_var, foreground="#555").pack(side="left", padx=(6, 0))

    def _build_voice_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Reconocimiento de voz (Vosk)", padding=12)
        frame.pack(fill="x", pady=(0, 10))

        # Model path
        ttk.Label(frame, text="Modelo Vosk").grid(row=0, column=0, sticky="w", pady=3, padx=(0, 10))
        ttk.Entry(frame, textvariable=self.model_path_var, width=28).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(frame, text="…", width=3, command=self._browse_model).grid(row=0, column=2, padx=(4, 0), pady=3)

        # Device
        ttk.Label(frame, text="Micrófono").grid(row=1, column=0, sticky="w", pady=3, padx=(0, 10))
        combo = ttk.Combobox(frame, textvariable=self.device_var, state="readonly", width=26)
        combo.grid(row=1, column=1, sticky="ew", pady=3)
        self.device_combo = combo

        # Sample rate
        ttk.Label(frame, text="Sample rate").grid(row=2, column=0, sticky="w", pady=3, padx=(0, 10))
        ttk.Entry(frame, textvariable=self.sample_rate_var, width=28).grid(row=2, column=1, sticky="ew", pady=3)

        frame.columnconfigure(1, weight=1)

    def _build_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Control", padding=12)
        frame.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(frame, text="Enviar comando al robot automáticamente al detectar palabra",
                        variable=self.auto_send_var).pack(anchor="w", pady=(0, 10))

        btn1 = ttk.Frame(frame)
        btn1.pack(fill="x")
        self.btn_start = ttk.Button(btn1, text="▶  Iniciar escucha", command=self.start_listening)
        self.btn_start.pack(side="left")
        self.btn_stop = ttk.Button(btn1, text="■  Detener", command=self.stop_listening)
        self.btn_stop.pack(side="left", padx=(8, 0))
        ttk.Button(btn1, text="Recargar micrófonos", command=self._load_devices).pack(side="left", padx=(8, 0))

        btn2 = ttk.Frame(frame)
        btn2.pack(fill="x", pady=(8, 0))
        for word in TARGET_WORDS:
            ttk.Button(btn2, text=word.capitalize(),
                       command=lambda w=word: self._send_manual(w)).pack(side="left", padx=(0, 6))

        ttk.Label(frame, text="▲ Envío manual (sin micrófono)",
                  font=("Segoe UI", 8), foreground="#777").pack(anchor="w", pady=(4, 0))

    def _build_status_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Estado", padding=12)
        frame.pack(fill="x", pady=(0, 10))

        grid = [
            ("Voz:", self.voice_status_var),
            ("Último comando:", self.last_cmd_var),
            ("Comandos enviados:", self.count_var),
        ]
        for i, (label, var) in enumerate(grid):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2, padx=(0, 10))
            ttk.Label(frame, textvariable=var).grid(row=i, column=1, sticky="w", pady=2)

        partial_frame = ttk.LabelFrame(parent, text="Texto parcial", padding=8)
        partial_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(partial_frame, textvariable=self.partial_var, wraplength=520).pack(anchor="w")

    def _build_log_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Log", padding=8)
        frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(frame, wrap="word", height=20, state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

        ttk.Button(parent, text="Limpiar log", command=self._clear_log).pack(anchor="e", pady=(4, 0))

    # ------------------------------------------------------------------
    # Device loading
    # ------------------------------------------------------------------

    def _load_devices(self) -> None:
        devices = list_input_devices()
        self.device_map = {"Auto": None}
        values = ["Auto"]
        for d in devices:
            label = f"{d['index']}: {d['name']}"
            self.device_map[label] = d["index"]
            values.append(label)
        if self.device_combo is not None:
            self.device_combo["values"] = values
        if self.device_var.get() not in values:
            self.device_var.set("Auto")
        self._log(f"Micrófonos detectados: {len(values) - 1}")

    def _browse_model(self) -> None:
        path = filedialog.askdirectory(title="Seleccionar carpeta del modelo Vosk")
        if path:
            self.model_path_var.set(path)

    # ------------------------------------------------------------------
    # TCP helpers
    # ------------------------------------------------------------------

    def _sync_connection(self) -> None:
        """Push current UI values into the RobotConnection object."""
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            port = 6001
        try:
            timeout = float(self.timeout_var.get().strip())
        except ValueError:
            timeout = 5.0
        self.connection.update_target(self.ip_var.get().strip(), port, timeout)

    def _do_ping(self) -> None:
        self._sync_connection()
        self._log(f"Enviando ping → {self.connection.ip}:{self.connection.port} ...")

        def _ping_thread() -> None:
            reply = self.connection.ping()
            self.event_queue.put(("tcp_reply", ("ping", reply)))

        threading.Thread(target=_ping_thread, daemon=True).start()

    def _do_disconnect(self) -> None:
        self.connection.close()
        self.tcp_status_var.set("Desconectado")
        self._log("Conexión TCP cerrada.")

    def _send_cmd(self, word: str) -> None:
        """Send *word* to the robot in a background thread."""
        self._sync_connection()

        def _worker() -> None:
            reply = self.connection.send(word)
            self.event_queue.put(("tcp_reply", (word, reply)))

        threading.Thread(target=_worker, daemon=True).start()

    def _send_manual(self, word: str) -> None:
        self._log(f"Envío manual: {word}")
        self._send_cmd(word)

    # ------------------------------------------------------------------
    # Voice control
    # ------------------------------------------------------------------

    def start_listening(self) -> None:
        if self.worker and self.worker.thread and self.worker.thread.is_alive():
            self._log("La escucha ya está activa.")
            return

        try:
            sample_rate = int(self.sample_rate_var.get().strip())
        except ValueError:
            messagebox.showerror("Sample rate inválido", "El sample rate debe ser un número entero.")
            return

        model_path = Path(self.model_path_var.get().strip()).expanduser()
        device_key = self.device_var.get().strip() or "Auto"
        device_index = self.device_map.get(device_key, None)

        self.worker = VoiceRecognizerWorker(model_path, sample_rate, device_index, self.event_queue)
        try:
            self.worker.start()
        except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
            self.worker = None
            self.voice_status_var.set("Error")
            self._log(f"Error al iniciar reconocimiento: {exc}")
            messagebox.showerror("No se pudo iniciar", str(exc))
            return

        self.voice_status_var.set("Iniciando...")
        self.partial_var.set("")
        self._log(f"Modelo: {model_path}")
        self._log(f"Micrófono: {device_key}  |  Rate: {sample_rate} Hz")
        self._log(f"Gramática: {', '.join(TARGET_WORDS)}")

    def stop_listening(self) -> None:
        if self.worker:
            self.worker.stop()
        else:
            self.voice_status_var.set("Detenido")

    # ------------------------------------------------------------------
    # Event polling (Tkinter main-loop safe)
    # ------------------------------------------------------------------

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.event_queue.get_nowait()
                self._handle_event(event, payload)
        except queue.Empty:
            pass
        self.after_job = self.after(100, self._poll_events)

    def _handle_event(self, event: str, payload) -> None:  # noqa: ANN001
        if event == "running":
            if payload:
                self.voice_status_var.set("Escuchando")
            elif self.voice_status_var.get() != "Error":
                self.voice_status_var.set("Detenido")

        elif event == "stopped":
            self.voice_status_var.set("Detenido")

        elif event == "partial":
            self.partial_var.set(str(payload))

        elif event == "final":
            self._log(f"Reconocido: {payload}")

        elif event == "command":
            word = str(payload)
            self.command_count += 1
            self.count_var.set(str(self.command_count))
            self.last_cmd_var.set(word)
            self.voice_status_var.set(f"Detectada: {word}")
            self._log(f"▶ Palabra detectada: {word}")
            if self.auto_send_var.get():
                self._send_cmd(word)

        elif event == "status":
            self._log(str(payload))

        elif event == "error":
            self.voice_status_var.set("Error")
            self._log(f"Error de voz: {payload}")
            messagebox.showerror("Error de reconocimiento", str(payload))

        elif event == "tcp_reply":
            cmd, reply = payload
            ok = isinstance(reply, str) and reply.upper().startswith("OK")
            self.tcp_status_var.set("OK" if ok else reply or "Sin respuesta")
            symbol = "✓" if ok else "✗"
            self._log(f"TCP [{cmd}] → {reply}  {symbol}")

    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message.rstrip() + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Save config on close
    # ------------------------------------------------------------------

    def destroy(self) -> None:
        if self.worker:
            self.worker.stop()
        self.connection.close()
        if self.after_job is not None:
            try:
                self.after_cancel(self.after_job)
            except tk.TclError:
                pass
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            port = 6001
        try:
            timeout = float(self.timeout_var.get().strip())
        except ValueError:
            timeout = 5.0
        save_config({
            "ip": self.ip_var.get().strip(),
            "port": port,
            "timeout": timeout,
            "model_path": self.model_path_var.get().strip(),
            "sample_rate": int(self.sample_rate_var.get().strip() or DEFAULT_SAMPLE_RATE),
        })
        super().destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voice command GUI for Dobot Magician E6")
    parser.add_argument("--ip", default="", help="Robot IP address")
    parser.add_argument("--port", type=int, default=6001, help="TCP port (default 6001)")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    app = VoiceCmdApp(initial_ip=args.ip, initial_port=args.port)
    app.mainloop()

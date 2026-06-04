"""Voice word test GUI.

Detects these spoken words from the computer microphone:
- derecha
- izquierda
- home
- origen (mapped to home)
- arriba
- abajo
- activar ventosa
- desactivar ventosa
- test ventosa

Dependencies: vosk, sounddevice
Optional config: voice_word_config.json in the same folder.
"""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import sounddevice as sd
from vosk import KaldiRecognizer, Model

TARGET_WORDS = [
    "derecha",
    "izquierda",
    "home",
    "origen",
    "arriba",
    "abajo",
    "activar ventosa",
    "desactivar ventosa",
    "test ventosa",
]
COMMAND_MAP = {
    "origen": "home",
    "activar ventosa": "activar_ventosa",
    "desactivar ventosa": "desactivar_ventosa",
    "test ventosa": "test_ventosa",
}
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_MODEL_DIR = "model"
DEFAULT_CONFIG_FILE = "voice_word_config.json"


def normalize_word(value: str) -> str:
    return " ".join(value.strip().lower().split())


def load_config(script_dir: Path) -> dict:
    config_path = script_dir / DEFAULT_CONFIG_FILE
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def list_input_devices() -> list[dict]:
    devices: list[dict] = []
    for index, info in enumerate(sd.query_devices()):
        if info.get("max_input_channels", 0) > 0:
            devices.append(
                {
                    "index": index,
                    "name": info["name"],
                    "channels": info.get("max_input_channels", 0),
                }
            )
    return devices


class VoiceRecognizerWorker:
    def __init__(self, model_path: Path, sample_rate: int, device_index: int | None, event_queue: queue.Queue):
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
            raise FileNotFoundError(f"No existe el modelo Vosk en: {self.model_path}")

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

    def _audio_callback(self, indata, _frames, _time, status):  # noqa: ANN001, D401
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
                                mapped = COMMAND_MAP.get(text, text)
                                if mapped != text:
                                    self.event_queue.put(("status", f"Alias detectado: {text} -> {mapped}"))
                                self.event_queue.put(("command", mapped))
                            else:
                                self.event_queue.put(("status", f"Texto no objetivo: {text}"))
                    else:
                        partial = json.loads(self.recognizer.PartialResult()).get("partial", "")
                        partial = normalize_word(partial)
                        if partial:
                            self.event_queue.put(("partial", partial))
        except (OSError, RuntimeError, ValueError) as exc:
            self.event_queue.put(("error", str(exc)))
        finally:
            self.stop_event.set()
            self.event_queue.put(("running", False))
            self.event_queue.put(("status", "Detenido"))
            self.event_queue.put(("stopped", True))


class VoiceWordApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Prueba de voz 03_ml")
        self.geometry("920x620")
        self.minsize(840, 560)

        self.script_dir = Path(__file__).resolve().parent
        self.config_data = load_config(self.script_dir)
        self.event_queue: queue.Queue = queue.Queue()
        self.worker: VoiceRecognizerWorker | None = None
        self.after_job = None
        self.device_combo: ttk.Combobox | None = None

        self.model_path_var = tk.StringVar(
            value=str(
                Path(self.config_data.get("model_path", self.script_dir / DEFAULT_MODEL_DIR))
            )
        )
        self.sample_rate_var = tk.StringVar(value=str(self.config_data.get("sample_rate", DEFAULT_SAMPLE_RATE)))
        self.device_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Listo")
        self.partial_var = tk.StringVar(value="")
        self.last_word_var = tk.StringVar(value="-")
        self.count_var = tk.StringVar(value="0")
        self.command_count = 0
        self.device_map: dict[str, int | None] = {"Auto": None}

        self._build_ui()
        self._load_devices()
        self._poll_events()

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        header = ttk.Label(container, text="Detector de palabras por micrófono", font=("Segoe UI", 18, "bold"))
        header.pack(anchor="w")

        subtitle = ttk.Label(
            container,
            text=(
                "Habla cerca del micrófono: derecha, izquierda, home/origen, arriba, abajo, "
                "activar ventosa, desactivar ventosa o test ventosa."
            ),
        )
        subtitle.pack(anchor="w", pady=(4, 14))

        controls = ttk.LabelFrame(container, text="Configuración", padding=12)
        controls.pack(fill="x")

        self._row_entry(controls, 0, "Modelo Vosk", self.model_path_var, browse=True)
        self._row_combo(controls, 1, "Micrófono", self.device_var)
        self._row_entry(controls, 2, "Sample rate", self.sample_rate_var)

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=(12, 10))
        ttk.Button(buttons, text="Iniciar", command=self.start_listening).pack(side="left")
        ttk.Button(buttons, text="Detener", command=self.stop_listening).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Recargar micrófonos", command=self._load_devices).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Limpiar log", command=self._clear_log).pack(side="left", padx=(8, 0))

        stats = ttk.Frame(container)
        stats.pack(fill="x", pady=(0, 10))
        ttk.Label(stats, text="Estado:").grid(row=0, column=0, sticky="w")
        ttk.Label(stats, textvariable=self.status_var).grid(row=0, column=1, sticky="w", padx=(8, 20))
        ttk.Label(stats, text="Última palabra:").grid(row=0, column=2, sticky="w")
        ttk.Label(stats, textvariable=self.last_word_var).grid(row=0, column=3, sticky="w", padx=(8, 20))
        ttk.Label(stats, text="Reconocimientos:").grid(row=0, column=4, sticky="w")
        ttk.Label(stats, textvariable=self.count_var).grid(row=0, column=5, sticky="w", padx=(8, 0))
        stats.columnconfigure(6, weight=1)

        partial_box = ttk.LabelFrame(container, text="Texto parcial", padding=12)
        partial_box.pack(fill="x", pady=(0, 10))
        ttk.Label(partial_box, textvariable=self.partial_var, wraplength=820).pack(anchor="w")

        log_box = ttk.LabelFrame(container, text="Log", padding=8)
        log_box.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_box, wrap="word", height=16)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.configure(state="disabled")

    def _row_entry(self, parent, row: int, label: str, variable: tk.StringVar, browse: bool = False) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 12))
        entry = ttk.Entry(parent, textvariable=variable, width=72)
        entry.grid(row=row, column=1, sticky="ew", pady=4)
        if browse:
            ttk.Button(parent, text="Buscar", command=self._browse_model).grid(row=row, column=2, padx=(8, 0), pady=4)
        parent.columnconfigure(1, weight=1)

    def _row_combo(self, parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 12))
        combo = ttk.Combobox(parent, textvariable=variable, state="readonly", width=69)
        combo.grid(row=row, column=1, sticky="ew", pady=4)
        self.device_combo = combo

    def _browse_model(self) -> None:
        selected = filedialog.askdirectory(title="Seleccionar carpeta del modelo Vosk")
        if selected:
            self.model_path_var.set(selected)

    def _load_devices(self) -> None:
        devices = list_input_devices()
        self.device_map = {"Auto": None}
        values = ["Auto"]
        for device in devices:
            label = f"{device['index']}: {device['name']}"
            self.device_map[label] = device["index"]
            values.append(label)
        if self.device_combo is not None:
            self.device_combo["values"] = values
        current = self.device_var.get()
        if current not in values:
            self.device_var.set("Auto")
        if not self.device_var.get():
            self.device_var.set("Auto")
        self._log(f"Micrófonos detectados: {len(values) - 1}")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def _log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message.rstrip() + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

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
            self.status_var.set("Error")
            self._log(f"Error al iniciar: {exc}")
            messagebox.showerror("No se pudo iniciar", str(exc))
            return

        self.status_var.set("Iniciando...")
        self.partial_var.set("")
        self._log(f"Inicio solicitado con modelo: {model_path}")
        self._log(f"Micrófono: {device_key}")
        self._log(f"Gramática: {', '.join(TARGET_WORDS)}")

    def stop_listening(self) -> None:
        if self.worker:
            self.worker.stop()
            self._log("Deteniendo escucha...")
        else:
            self.status_var.set("Listo")

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.event_queue.get_nowait()
                if event == "status":
                    self.status_var.set(str(payload))
                    self._log(str(payload))
                elif event == "partial":
                    self.partial_var.set(str(payload))
                elif event == "final":
                    self._log(f"Reconocido: {payload}")
                elif event == "command":
                    self.command_count += 1
                    self.count_var.set(str(self.command_count))
                    self.last_word_var.set(str(payload))
                    self.status_var.set(f"Detectada: {payload}")
                    self._log(f"Palabra objetivo detectada: {payload}")
                elif event == "error":
                    self.status_var.set("Error")
                    self._log(f"Error del micrófono o modelo: {payload}")
                    messagebox.showerror("Error de reconocimiento", str(payload))
                elif event == "running":
                    if payload:
                        self.status_var.set("Escuchando")
                    elif self.status_var.get() != "Error":
                        self.status_var.set("Detenido")
                elif event == "stopped":
                    self.status_var.set("Detenido")
        except queue.Empty:
            pass
        self.after_job = self.after(100, self._poll_events)

    def destroy(self) -> None:
        if self.worker:
            self.worker.stop()
        if self.after_job is not None:
            try:
                self.after_cancel(self.after_job)
            except tk.TclError:
                pass
        super().destroy()


if __name__ == "__main__":
    app = VoiceWordApp()
    app.mainloop()

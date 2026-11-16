import os
import sys
import time
import shutil
import platform
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

try:
    import psutil
except ImportError:
    raise SystemExit("Install dependencies first: pip install -r requirements.txt")

BG = "#0b1020"
PANEL = "#121a2d"
PANEL2 = "#172239"
TEXT = "#eef3ff"
MUTED = "#91a0bd"
ACCENT = "#70e1c1"
BLUE = "#7aa7ff"
ORANGE = "#ffbd69"
RED = "#ff7272"

class NexaDesk(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NexaDesk — PC Control Center")
        self.geometry("1100x760")
        self.minsize(920, 650)
        self.configure(bg=BG)
        self.cpu_history = [0] * 48
        self.ram_history = [0] * 48
        self.last_net = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.net_down = self.net_up = 0
        self._style()
        self._build()
        self.refresh()
        self.after(1000, self.tick)

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=PANEL, foreground=TEXT, fieldbackground=PANEL,
                        rowheight=29, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=PANEL2, foreground=MUTED,
                        relief="flat", font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", "#263b59")])
        style.configure("Vertical.TScrollbar", background=PANEL2, troughcolor=BG, bordercolor=BG)

    def label(self, parent, text, size=10, color=TEXT, bold=False):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    def card(self, parent, title, value="—", subtitle=""):
        box = tk.Frame(parent, bg=PANEL, highlightbackground="#202d46", highlightthickness=1)
        tk.Label(box, text=title.upper(), bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(13, 4))
        val = tk.Label(box, text=value, bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 23))
        val.pack(anchor="w", padx=16)
        sub = tk.Label(box, text=subtitle, bg=PANEL, fg=MUTED, font=("Segoe UI", 8))
        sub.pack(anchor="w", padx=16, pady=(2, 13))
        return box, val, sub

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 16))
        tk.Label(header, text="NEXA", bg=BG, fg=ACCENT, font=("Segoe UI Black", 22)).pack(side="left")
        tk.Label(header, text="DESK", bg=BG, fg=TEXT, font=("Segoe UI Black", 22)).pack(side="left")
        tk.Label(header, text="  /  PC CONTROL CENTER", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left", pady=(9, 0))
        self.clock = tk.Label(header, text="", bg=BG, fg=MUTED, font=("Segoe UI", 10))
        self.clock.pack(side="right", pady=8)

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        self.overview = tk.Frame(self.tabs, bg=BG)
        self.processes = tk.Frame(self.tabs, bg=BG)
        self.tools = tk.Frame(self.tabs, bg=BG)
        self.tabs.add(self.overview, text="  Overview  ")
        self.tabs.add(self.processes, text="  Processes  ")
        self.tabs.add(self.tools, text="  Tools  ")
        self._overview_ui()
        self._process_ui()
        self._tools_ui()

    def _overview_ui(self):
        cards = tk.Frame(self.overview, bg=BG)
        cards.pack(fill="x", pady=(16, 14))
        for i in range(4): cards.grid_columnconfigure(i, weight=1)
        self.cpu_card = self.card(cards, "CPU load", "0%", "Processor utilization")
        self.ram_card = self.card(cards, "Memory", "0%", "RAM in use")
        self.disk_card = self.card(cards, "System drive", "—", "Used space")
        self.net_card = self.card(cards, "Network", "0 KB/s", "↓ download  •  ↑ upload")
        for i, c in enumerate([self.cpu_card, self.ram_card, self.disk_card, self.net_card]):
            c[0].grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == 3 else 7))

        mid = tk.Frame(self.overview, bg=BG)
        mid.pack(fill="both", expand=True)
        chartbox = tk.Frame(mid, bg=PANEL, highlightbackground="#202d46", highlightthickness=1)
        chartbox.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(chartbox, text="PERFORMANCE", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(14, 0))
        self.chart = tk.Canvas(chartbox, bg=PANEL, highlightthickness=0, height=250)
        self.chart.pack(fill="both", expand=True, padx=12, pady=12)
        info = tk.Frame(mid, bg=PANEL, width=270, highlightbackground="#202d46", highlightthickness=1)
        info.pack(side="right", fill="y")
        info.pack_propagate(False)
        tk.Label(info, text="DEVICE INFO", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(14, 12))
        self.info_text = tk.Label(info, text="", bg=PANEL, fg=TEXT, justify="left",
                                  anchor="nw", font=("Segoe UI", 9), wraplength=230)
        self.info_text.pack(fill="both", padx=16, pady=4)
        self.status = tk.Label(self.overview, text="●  Monitoring is active", bg=BG,
                               fg=ACCENT, font=("Segoe UI", 9))
        self.status.pack(anchor="w", pady=(10, 0))

    def _process_ui(self):
        top = tk.Frame(self.processes, bg=BG)
        top.pack(fill="x", pady=(16, 12))
        tk.Label(top, text="Running processes", bg=BG, fg=TEXT,
                 font=("Segoe UI Semibold", 16)).pack(side="left")
        tk.Button(top, text="↻  Refresh", command=self.load_processes, bg=PANEL2, fg=TEXT,
                  activebackground="#263b59", activeforeground=TEXT, relief="flat",
                  padx=14, pady=7, cursor="hand2").pack(side="right")
        tk.Label(self.processes, text="Review resource usage. Ending a process may cause unsaved work to be lost.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))
        cols = ("name", "pid", "cpu", "memory", "status")
        self.tree = ttk.Treeview(self.processes, columns=cols, show="headings")
        for col, title, width in [("name","PROCESS",300),("pid","PID",90),("cpu","CPU %",100),
                                  ("memory","MEMORY",130),("status","STATUS",130)]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w" if col == "name" else "center")
        self.tree.pack(fill="both", expand=True)
        foot = tk.Frame(self.processes, bg=BG)
        foot.pack(fill="x", pady=12)
        tk.Button(foot, text="End selected process", command=self.end_process, bg="#492b38",
                  fg="#ffb2bb", activebackground="#633747", relief="flat", padx=14, pady=8,
                  cursor="hand2").pack(side="right")

    def _tools_ui(self):
        tk.Label(self.tools, text="Maintenance tools", bg=BG, fg=TEXT,
                 font=("Segoe UI Semibold", 16)).pack(anchor="w", pady=(18, 4))
        tk.Label(self.tools, text="Small, transparent utilities. Nothing runs silently in the background.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 16))
        box = tk.Frame(self.tools, bg=PANEL, highlightbackground="#202d46", highlightthickness=1)
        box.pack(fill="x", pady=(0, 12))
        tk.Label(box, text="Temporary files cleanup", bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(box, text="Finds files in your user TEMP folder and lets you remove them. Files currently in use are skipped.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=760).pack(anchor="w", padx=18)
        tk.Button(box, text="Scan temporary files", command=self.scan_temp, bg="#203c48",
                  fg=ACCENT, activebackground="#2c5361", relief="flat", padx=15, pady=8,
                  cursor="hand2").pack(anchor="w", padx=18, pady=14)
        self.cleanup_result = tk.Label(box, text="No scan performed yet.", bg=PANEL, fg=MUTED,
                                        font=("Segoe UI", 9))
        self.cleanup_result.pack(anchor="w", padx=18, pady=(0, 15))
        about = tk.Frame(self.tools, bg=PANEL, highlightbackground="#202d46", highlightthickness=1)
        about.pack(fill="x")
        tk.Label(about, text="Privacy & safety", bg=PANEL, fg=TEXT,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=18, pady=(15, 5))
        tk.Label(about, text="NexaDesk runs locally. It does not collect analytics, send data, install drivers, edit the registry, or disable Windows services.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=760, justify="left").pack(anchor="w", padx=18, pady=(0, 16))

    def refresh(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\")
        except Exception:
            disk = psutil.disk_usage(os.path.abspath(os.sep))
        self.cpu_history.append(cpu); self.cpu_history = self.cpu_history[-48:]
        self.ram_history.append(mem.percent); self.ram_history = self.ram_history[-48:]
        self.cpu_card[1].config(text=f"{cpu:.0f}%")
        self.cpu_card[2].config(text=f"{psutil.cpu_count(logical=True)} logical cores")
        self.ram_card[1].config(text=f"{mem.percent:.0f}%")
        self.ram_card[2].config(text=f"{mem.used/1024**3:.1f} / {mem.total/1024**3:.1f} GB")
        self.disk_card[1].config(text=f"{disk.percent:.0f}%")
        self.disk_card[2].config(text=f"{disk.used/1024**3:.0f} / {disk.total/1024**3:.0f} GB")
        self.net_card[1].config(text=f"{self.net_down:.0f} KB/s")
        self.net_card[2].config(text=f"↑ {self.net_up:.0f} KB/s upload")
        self.info_text.config(text=(
            f"Device\n{platform.node()}\n\n"
            f"Operating system\n{platform.system()} {platform.release()}\n\n"
            f"Processor\n{platform.processor() or 'Not reported'}\n\n"
            f"Logical cores\n{psutil.cpu_count(logical=True)}\n\n"
            f"Boot time\n{datetime.fromtimestamp(psutil.boot_time()).strftime('%d %b %Y, %H:%M')}"
        ))
        self.draw_chart()

    def draw_chart(self):
        c = self.chart; c.delete("all")
        w = max(c.winfo_width(), 400); h = max(c.winfo_height(), 220)
        for i in range(5):
            y = 16 + i * (h - 32) / 4
            c.create_line(38, y, w-8, y, fill="#26334b")
            c.create_text(28, y, text=str(100-i*25), fill=MUTED, font=("Segoe UI", 7), anchor="e")
        for data, color in [(self.cpu_history, ACCENT), (self.ram_history, BLUE)]:
            pts = []
            for i, v in enumerate(data):
                x = 42 + i * (w - 58) / 47
                y = h - 16 - (v / 100) * (h - 32)
                pts.extend([x, y])
            if len(pts) >= 4: c.create_line(*pts, fill=color, width=2, smooth=True)
        c.create_text(w-12, 12, text="CPU  ●  RAM  ●", fill=MUTED, font=("Segoe UI", 8), anchor="e")

    def tick(self):
        try:
            now = psutil.net_io_counters(); t = time.time()
            dt = max(t - self.last_net_time, .1)
            self.net_down = max(0, (now.bytes_recv-self.last_net.bytes_recv)/dt/1024)
            self.net_up = max(0, (now.bytes_sent-self.last_net.bytes_sent)/dt/1024)
            self.last_net, self.last_net_time = now, t
            self.clock.config(text=datetime.now().strftime("%A, %d %B  •  %H:%M:%S"))
            self.refresh()
        except Exception as e:
            self.status.config(text=f"Monitoring issue: {e}", fg=ORANGE)
        self.after(1000, self.tick)

    def load_processes(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                d = p.info
                procs.append((d["name"] or "Unknown", d["pid"], d["cpu_percent"] or 0,
                              (d["memory_info"].rss/1024**2 if d["memory_info"] else 0), d["status"] or "—"))
            except (psutil.NoSuchProcess, psutil.AccessDenied): pass
        for name, pid, cpu, mem, status in sorted(procs, key=lambda x: x[3], reverse=True)[:250]:
            self.tree.insert("", "end", values=(name, pid, f"{cpu:.1f}", f"{mem:.0f} MB", status))

    def end_process(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("NexaDesk", "Select a process first."); return
        vals = self.tree.item(sel[0], "values")
        name, pid = vals[0], int(vals[1])
        if not messagebox.askyesno("Confirm", f"End process {name} (PID {pid})?\nUnsaved work may be lost."):
            return
        try:
            p = psutil.Process(pid)
            p.terminate()
            try: p.wait(timeout=3)
            except psutil.TimeoutExpired: p.kill()
            self.load_processes()
            messagebox.showinfo("NexaDesk", f"Process {name} was ended.")
        except Exception as e:
            messagebox.showerror("Could not end process", str(e))

    def scan_temp(self):
        folder = tempfile.gettempdir()
        count = total = 0
        try:
            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
                for name in files:
                    path = os.path.join(root, name)
                    try:
                        if os.path.islink(path): continue
                        total += os.path.getsize(path); count += 1
                    except OSError: pass
            mb = total / 1024**2
            self.cleanup_result.config(text=f"Found {count:,} files • approximately {mb:.1f} MB. Click again to review and clean.", fg=ACCENT)
            if messagebox.askyesno("Clean temporary files?", f"Found about {mb:.1f} MB in {count} files.\n\nDelete accessible files in your user TEMP folder? Files in use will be skipped."):
                removed = freed = 0
                for root, dirs, files in os.walk(folder):
                    dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
                    for name in files:
                        path = os.path.join(root, name)
                        try:
                            if os.path.islink(path): continue
                            size = os.path.getsize(path); os.remove(path)
                            removed += 1; freed += size
                        except OSError: pass
                self.cleanup_result.config(text=f"Removed {removed:,} files • freed {freed/1024**2:.1f} MB. In-use files were skipped.", fg=ACCENT)
        except Exception as e:
            messagebox.showerror("Scan failed", str(e))

if __name__ == "__main__":
    app = NexaDesk()
    app.mainloop()

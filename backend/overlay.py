import tkinter as tk
import time

def run_overlay(minutes_str, accent_color="#00f2ff"):
    try:
        minutes = float(minutes_str)
    except Exception:
        minutes = 5

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    
    # Semi-transparent dark background
    root.configure(bg='#111111')
    try:
        root.attributes("-alpha", 0.90)
    except Exception:
        pass

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w = 120
    h = 36
    x = (sw - w) // 2
    root.geometry(f"{w}x{h}+{x}+0") # Snapped to top edge

    # Thin colored border
    border = tk.Frame(root, bg=accent_color, bd=2)
    border.pack(expand=True, fill="both")
    
    inner = tk.Frame(border, bg="#111111")
    inner.pack(expand=True, fill="both")

    label = tk.Label(inner, text="", font=("Segoe UI", 20, "bold"), fg=accent_color, bg="#111111")
    label.pack(expand=True, fill="both")

    # Hover effect
    is_time_up = False
    def on_enter(e):
        if is_time_up: return
        try: root.attributes("-alpha", 0.15)
        except: pass

    def on_leave(e):
        if is_time_up: return
        try: root.attributes("-alpha", 0.90)
        except: pass

    root.bind("<Enter>", on_enter)
    root.bind("<Leave>", on_leave)
    label.bind("<Enter>", on_enter)
    label.bind("<Leave>", on_leave)

    end_time = time.time() + (minutes * 60)

    def update():
        rem = int(end_time - time.time())
        if rem <= 0:
            nonlocal is_time_up
            is_time_up = True
            # TIME IS UP: Big red neon text in the center
            try:
                root.attributes("-alpha", 0.95)
            except: pass
            
            gw = 800
            gh = 200
            gx = (sw - gw) // 2
            gy = (sh - gh) // 2
            root.geometry(f"{gw}x{gh}+{gx}+{gy}")
            
            border.config(bg="#ff1744", bd=4)
            inner.config(bg="#050000")
            label.config(text="SÜRE BİTTİ!", font=("Segoe UI", 72, "bold"), fg="#ff1744", bg="#050000")
            
            # Flash neon
            def flash_neon():
                current_color = label.cget("fg")
                next_color = "#ffffff" if current_color == "#ff1744" else "#ff1744"
                label.config(fg=next_color)
                root.after(150, flash_neon)
            flash_neon()
            
            # Do not destroy, api.py will kill this process when it kills the game
            return
            
        m = rem // 60
        s = rem % 60
        
        # Flash red if under 10 seconds
        if rem <= 10:
            color = "#ff1744" if rem % 2 == 0 else accent_color
            label.config(fg=color)
            border.config(bg=color)
        else:
            label.config(fg=accent_color)
            border.config(bg=accent_color)
            
        label.config(text=f"{m:02d}:{s:02d}")
        root.after(200, update)

    update()
    root.mainloop()

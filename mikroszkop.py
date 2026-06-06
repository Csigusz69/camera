import cv2
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os
from datetime import datetime

CONFIG_FILE = "beallitasok.txt"
APP_TITLE = "Saját Kamera V3.1"

# ---------------------------------------------------------------------------
# NYELVI ADATBÁZIS (Itt van az összes szöveg listája nyelvekre bontva)
# ---------------------------------------------------------------------------
NYELVEK = {
    "HU": {
        "settings_btn": "⚙ Beállítások",
        "status_line": "Kamera: #{cam} | F11: Teljes képernyő | Space: Fotó | Q/X: Kilépés",
        "photo_btn": "FOTÓ (Egér, SPACE vagy ENTER)",
        "saved_msg": "📸 KÉP ELMENTVE! -> {file}",
        "settings_title": "Beállítások",
        "cam_label": "Válaszd ki a kamera számát:",
        "lang_label": "Nyelv / Language:",
        "close_btn": "Bezárás",
        "error_cam": "A #{num}-os számon nem indítható kamera! Próbálj másikat."
    },
    "EN": {
        "settings_btn": "⚙ Settings",
        "status_line": "Camera: #{cam} | F11: Fullscreen | Space: Photo | Q/X: Exit",
        "photo_btn": "PHOTO (Mouse, SPACE or ENTER)",
        "saved_msg": "📸 PHOTO SAVED! -> {file}",
        "settings_title": "Settings",
        "cam_label": "Select camera number:",
        "lang_label": "Nyelv / Language:",
        "close_btn": "Close",
        "error_cam": "Camera cannot be started on index #{num}! Try another."
    }
}

class MicroscopeApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window_title_base = window_title
        self.window.configure(bg="black")
        
        # 1. Beállítások betöltése (kamera ÉS nyelv)
        self.video_source, self.lang_code = self.load_config()
        self.txt = NYELVEK[self.lang_code] # Aktuális nyelvi csomag kiválasztása
        
        self.setup_camera()
        
        # Felső vezérlő sáv
        self.top_bar = tk.Frame(window, bg="#111111")
        self.top_bar.pack(fill=tk.X, padx=0, pady=0)
        
        self.btn_settings = tk.Button(self.top_bar, text=self.txt["settings_btn"], 
                                      command=self.open_settings, bg="#222222", fg="white",
                                      font=('Helvetica', 10), relief=tk.FLAT, padx=10, pady=2)
        self.btn_settings.pack(side=tk.RIGHT, padx=5, pady=5)
        
        self.status_label = tk.Label(self.top_bar, text="", bg="#111111", fg="#aaaaaa", font=('Helvetica', 9))
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.update_status_label()
        
        # Élőkép vászon
        self.canvas = tk.Canvas(window, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # BILLENTYŰK
        self.window.bind('<Return>', lambda event: self.snapshot())
        self.window.bind('<space>', lambda event: self.snapshot())
        self.window.bind('<F11>', lambda event: self.toggle_fullscreen())
        self.window.bind('<Escape>', lambda event: self.handle_escape())
        self.window.bind('<q>', lambda event: self.close_app())
        self.window.bind('<Q>', lambda event: self.close_app())
        self.window.bind('<x>', lambda event: self.close_app())
        self.window.bind('<X>', lambda event: self.close_app())
        
        self.is_fullscreen = True
        self.window.attributes("-fullscreen", True)
        
        self.delay = 15
        self.is_running = True
        self.flash_active = False
        self.current_frame = None
        
        self.update()
        self.window.mainloop()

    def setup_camera(self):
        self.vid = cv2.VideoCapture(self.video_source)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 9999)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 9999)
        self.cam_w = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_h = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cam_aspect_ratio = self.cam_w / self.cam_h if self.cam_w > 0 else 4/3
        self.window.title(f"{self.window_title_base} [{self.cam_w}x{self.cam_h}]")

    def load_config(self):
        """Betölti a kamerát és a nyelvet a fájlból (formátum: kamera_szama,NYELV_KOD)"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    content = f.read().strip().split(",")
                    cam = int(content[0])
                    lang = content[1] if content[1] in NYELVEK else "HU"
                    return cam, lang
            except:
                return 0, "HU"
        return 0, "HU"

    def save_config(self):
        """Mentéssé alakítva: menti a jelenlegi beállításokat"""
        try:
            with open(CONFIG_FILE, "w") as f:
                f.write(f"{self.video_source},{self.lang_code}")
        except Exception as e:
            print(f"Hiba a mentésnél: {e}")

    def update_status_label(self):
        """Frissíti a státuszbár szövegét az aktuális nyelven"""
        self.status_label.config(text=self.txt["status_line"].format(cam=self.video_source))

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.window.attributes("-fullscreen", self.is_fullscreen)
        if not self.is_fullscreen:
            self.window.geometry("1024x768")

    def handle_escape(self):
        if self.is_fullscreen:
            self.toggle_fullscreen()
        else:
            self.close_app()

    def open_settings(self):
        self.settings_win = tk.Toplevel(self.window)
        self.settings_win.title(self.txt["settings_title"])
        self.settings_win.geometry("320x220")
        self.settings_win.configure(bg="#222222")
        self.settings_win.transient(self.window)
        
        # Kamera választó
        lbl_cam = tk.Label(self.settings_win, text=self.txt["cam_label"], bg="#222222", fg="white")
        lbl_cam.pack(pady=(10, 2))
        self.camera_combobox = ttk.Combobox(self.settings_win, values=[0, 1, 2, 3, 4, 5], state="readonly", width=10)
        self.camera_combobox.set(self.video_source)
        self.camera_combobox.pack(pady=5)
        self.camera_combobox.bind("<<ComboboxSelected>>", self.live_change_camera)
        
        # Nyelv választó
        lbl_lang = tk.Label(self.settings_win, text=self.txt["lang_label"], bg="#222222", fg="white")
        lbl_lang.pack(pady=(10, 2))
        self.lang_combobox = ttk.Combobox(self.settings_win, values=["HU", "EN"], state="readonly", width=10)
        self.lang_combobox.set(self.lang_code)
        self.lang_combobox.pack(pady=5)
        self.lang_combobox.bind("<<ComboboxSelected>>", self.live_change_language)
        
        self.btn_close_settings = tk.Button(self.settings_win, text=self.txt["close_btn"], command=self.settings_win.destroy,
                                  bg="#2ecc71", fg="white", relief=tk.FLAT, font=('Helvetica', 10, 'bold'), width=15)
        self.btn_close_settings.pack(pady=15)

    def live_change_camera(self, event):
        new_source = int(self.camera_combobox.get())
        if self.vid.isOpened():
            self.vid.release()
        self.video_source = new_source
        self.setup_camera()
        self.save_config()
        self.update_status_label()

    def live_change_language(self, event):
        """Azonnali nyelvváltás a felületen újraindítás nélkül"""
        self.lang_code = self.lang_combobox.get()
        self.txt = NYELVEK[self.lang_code] # Új szótár élesítése
        
        # UI elemek azonnali átírása
        self.btn_settings.config(text=self.txt["settings_btn"])
        self.update_status_label()
        self.settings_win.title(self.txt["settings_title"])
        self.btn_close_settings.config(text=self.txt["close_btn"])
        
        self.save_config() # Elmentjük az új nyelvi kódot a fájlba

    def snapshot(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                folder = "Sajat_Kepek"
                if not os.path.exists(folder):
                    os.makedirs(folder)
                    
                filename = os.path.join(folder, f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                cv2.imwrite(filename, frame)
                
                self.window.title(self.txt["saved_msg"].format(file=os.path.basename(filename)))
                self.flash_active = True
                self.window.after(80, self.reset_flash)
                self.window.after(3000, self.reset_window_title)

    def reset_flash(self):
        self.flash_active = False

    def reset_window_title(self):
        if self.is_running:
            self.window.title(f"{self.window_title_base} [{self.cam_w}x{self.cam_h}]")

    def update(self):
        if self.is_running and self.vid.isOpened():
            if self.flash_active:
                self.canvas.delete("all")
                self.canvas.configure(bg="white")
            else:
                ret, frame = self.vid.read()
                if ret:
                    self.current_frame = frame
                    self.canvas.configure(bg="black")
                    canvas_w = self.canvas.winfo_width()
                    canvas_h = self.canvas.winfo_height()
                    
                    if canvas_w > 10 and canvas_h > 10:
                        canvas_aspect_ratio = canvas_w / canvas_h
                        if canvas_aspect_ratio > self.cam_aspect_ratio:
                            new_h = canvas_h
                            new_w = int(new_h * self.cam_aspect_ratio)
                        else:
                            new_w = canvas_w
                            new_h = int(new_w / self.cam_aspect_ratio)
                            
                        if new_w > 0 and new_h > 0:
                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            img = Image.fromarray(rgb_frame)
                            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                            self.photo = ImageTk.PhotoImage(image=img)
                            x_offset = (canvas_w - new_w) // 2
                            y_offset = (canvas_h - new_h) // 2
                            self.canvas.create_image(x_offset, y_offset, image=self.photo, anchor=tk.NW)
                        
        self.window.after(self.delay, self.update)

    def close_app(self):
        self.is_running = False
        if hasattr(self, 'vid') and self.vid.isOpened():
            self.vid.release()
        self.window.destroy()

if __name__ == "__main__":
    MicroscopeApp(tk.Tk(), APP_TITLE)
import sys
import time
import selectors
import signal
import os
import subprocess
import pwd

try:
    from evdev import InputDevice, UInput, list_devices, ecodes as e
except ImportError:
    print("[ERROR] Library 'evdev' belum terinstal.")
    print("Silakan jalankan perintah ini di terminal:")
    print("sudo .venv/bin/pip install evdev")
    sys.exit(1)

# Variabel status
is_active = False
sensitivity = 10
step = 2  # Nilai penambahan/pengurangan sensitivitas

# Menyimpan status tombol yang sedang ditekan secara fisik
physically_pressed = set()
# Menyimpan tombol yang rilisnya harus disaring agar tidak bocor
suppressed_releases = set()

print("[INFO] Mendeteksi keyboard fisik Anda...")

# Mendeteksi semua keyboard fisik yang terhubung ke sistem
devices = [InputDevice(path) for path in list_devices()]
keyboards = []
for dev in devices:
    try:
        caps = dev.capabilities()
        if e.EV_KEY in caps:
            keys = caps[e.EV_KEY]
            # Keyboard asli minimal harus memiliki tombol huruf standar (A sampai Z)
            if e.KEY_A in keys and e.KEY_Z in keys:
                keyboards.append(dev)
    except Exception:
        pass

if not keyboards:
    print("[ERROR] Tidak menemukan keyboard fisik yang kompatibel!")
    print("Pastikan Anda menjalankan program ini dengan hak akses root (sudo).")
    sys.exit(1)

print(f"[INFO] Berhasil menemukan {len(keyboards)} keyboard:")
for kbd in keyboards:
    print(f"  - {kbd.name} ({kbd.path})")

print("\n[INFO] Sedang membuat Virtual Input (Mouse + Keyboard)...")

# Membuat satu perangkat virtual gabungan yang mendukung pergerakan mouse, roda scroll, dan keyboard
capabilities = {
    e.EV_REL: (e.REL_X, e.REL_Y, e.REL_WHEEL),
    e.EV_KEY: list(range(1, 256)) + [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE]
}

try:
    ui = UInput(
        capabilities, 
        name="LazyCursor-Virtual-Device", 
        vendor=0x1234,   # Fake Vendor ID
        product=0x5678,  # Fake Product ID
        version=0x0111
    )
except Exception as ex:
    print(f"[ERROR] Gagal membuat virtual device: {ex}")
    print("Pastikan Anda menjalankan program ini dengan 'sudo'!")
    sys.exit(1)

# Jeda krusial agar Debian/Arch KDE mengenali hardware virtual baru kami
print("[INFO] Menunggu OS mendaftarkan perangkat (2 detik)...")
time.sleep(2.5) 
print("[INFO] Virtual Device siap digunakan!")

# Mendaftarkan selector untuk memantau semua keyboard fisik sekaligus tanpa lag
selector = selectors.DefaultSelector()
for kbd in keyboards:
    try:
        kbd.grab() 
        selector.register(kbd, selectors.EVENT_READ)
    except Exception as ex:
        print(f"[WARN] Gagal mengambil kontrol eksklusif pada {kbd.name}: {ex}")

def show_help_terminal():
    help_text = """
=========================================
          LAZYCURSOR SHORTCUTS           
=========================================
 - Ctrl + M       : Toggle Active/Inactive
 - Arrow Keys     : Move Cursor
 - Shift + Arrow  : Move Slower (-5 speed)
 - Ctrl + Left    : Left Click
 - Ctrl + Right   : Right Click
 - Alt + Up       : Scroll Up
 - Alt + Down     : Scroll Down
 - Ctrl + Up      : Increase Base Speed
 - Ctrl + Down    : Decrease Base Speed
 - Ctrl + H       : Show this help panel
=========================================
"""
    try:
        # Menyimpan teks bantuan ke file sementara
        with open('/tmp/lazycursor_help.txt', 'w') as f:
            f.write(help_text)
        
        # Mendapatkan user biasa (bukan root) yang memiliki file ini agar terminal bisa terbuka di desktop Wayland
        owner_uid = os.stat(__file__).st_uid
        username = pwd.getpwuid(owner_uid).pw_name
        
        # Mencoba membuka Konsole (KDE) atau terminal emulator bawaan lainnya di environment user biasa
        cmd = f"su - {username} -c 'env XDG_RUNTIME_DIR=/run/user/{owner_uid} WAYLAND_DISPLAY=wayland-0 DISPLAY=:0 konsole -e bash -c \"cat /tmp/lazycursor_help.txt; echo; read -p \\\"Tekan Enter untuk menutup...\\\"\" || x-terminal-emulator -e bash -c \"cat /tmp/lazycursor_help.txt; echo; read -p \\\"Tekan Enter untuk menutup...\\\"\"'"
        subprocess.Popen(cmd, shell=True)
        print("[INFO] Jendela Terminal Bantuan telah diluncurkan.")
    except Exception as ex:
        print(f"[ERROR] Gagal meluncurkan jendela bantuan: {ex}")

def toggle_mode():
    global is_active
    is_active = not is_active
    status = "AKTIF" if is_active else "NONAKTIF"
    print(f"\n[INFO] Mode Mouse Keyboard: {status}")
    if is_active:
        print("[INFO] KEYBOARD DI-GRAB: Kontrol penuh kursor mouse diaktifkan!")
    else:
        print("[INFO] KEYBOARD DI-LEPAS: Tombol berfungsi normal kembali.")

def increase_sensitivity():
    global sensitivity
    if is_active:
        sensitivity += step
        print(f"[INFO] Sensitivitas dinaikkan: {sensitivity}")

def decrease_sensitivity():
    global sensitivity
    if is_active:
        sensitivity = max(1, sensitivity - step)
        print(f"[INFO] Sensitivitas diturunkan: {sensitivity}")

def left_click():
    if is_active:
        if e.KEY_LEFTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
        if e.KEY_RIGHTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_RIGHTCTRL, 0)
        ui.syn()
        
        ui.write(e.EV_KEY, e.BTN_LEFT, 1)
        ui.syn()
        ui.write(e.EV_KEY, e.BTN_LEFT, 0)
        ui.syn()
        
        if e.KEY_LEFTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)
        if e.KEY_RIGHTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_RIGHTCTRL, 1)
        ui.syn()
        print("[AKSI] Klik Kiri")

def right_click():
    if is_active:
        if e.KEY_LEFTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
        if e.KEY_RIGHTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_RIGHTCTRL, 0)
        ui.syn()
        
        ui.write(e.EV_KEY, e.BTN_RIGHT, 1)
        ui.syn()
        ui.write(e.EV_KEY, e.BTN_RIGHT, 0)
        ui.syn()
        
        if e.KEY_LEFTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)
        if e.KEY_RIGHTCTRL in physically_pressed:
            ui.write(e.EV_KEY, e.KEY_RIGHTCTRL, 1)
        ui.syn()
        print("[AKSI] Klik Kanan")

def process_event(event):
    global suppressed_releases
    
    if event.type == e.EV_KEY:
        code = event.code
        val = event.value
        
        if code in suppressed_releases:
            if val == 0:
                suppressed_releases.discard(code)
                physically_pressed.discard(code)
            return
            
        if val == 1:
            physically_pressed.add(code)
        elif val == 0:
            physically_pressed.discard(code)
            
        ctrl_active = (e.KEY_LEFTCTRL in physically_pressed) or (e.KEY_RIGHTCTRL in physically_pressed)
        alt_active = (e.KEY_LEFTALT in physically_pressed) or (e.KEY_RIGHTALT in physically_pressed)
        
        # 2. Deteksi Pintasan Aktifasi Mode: Ctrl + M
        if ctrl_active and code == e.KEY_M:
            if val == 1:
                toggle_mode()
                suppressed_releases.add(code)
            return
            
        if is_active:
            # 3. Deteksi Pengaturan Sensitivitas: Ctrl + Up / Down
            if ctrl_active and code in (e.KEY_UP, e.KEY_DOWN):
                if val == 1:
                    if code == e.KEY_UP:
                        increase_sensitivity()
                    elif code == e.KEY_DOWN:
                        decrease_sensitivity()
                    suppressed_releases.add(code)
                return
                
            # 4. Deteksi Klik Mouse: Ctrl + Left / Right
            if ctrl_active and code in (e.KEY_LEFT, e.KEY_RIGHT):
                if val == 1:
                    if code == e.KEY_LEFT:
                        left_click()
                    elif code == e.KEY_RIGHT:
                        right_click()
                    suppressed_releases.add(code)
                return
                
            # 5. Deteksi Buka Terminal Bantuan: Ctrl + H
            if ctrl_active and code == e.KEY_H:
                if val == 1:
                    show_help_terminal()
                    suppressed_releases.add(code)
                return
                
            # 6. Deteksi Scroll Layar: Alt + Up / Down
            if alt_active and code in (e.KEY_UP, e.KEY_DOWN):
                if val in (1, 2):
                    direction = 1 if code == e.KEY_UP else -1
                    ui.write(e.EV_REL, e.REL_WHEEL, direction)
                    ui.syn()
                if val == 1:
                    suppressed_releases.add(code)
                return
                
            # 7. Deteksi Pergerakan Kursor: Tombol Panah (Tanpa Ctrl/Alt)
            if not ctrl_active and not alt_active and code in (e.KEY_UP, e.KEY_DOWN, e.KEY_LEFT, e.KEY_RIGHT):
                if val == 1:
                    suppressed_releases.add(code)
                return
                
        # Teruskan ke OS jika bukan shortcut
        ui.write(event.type, event.code, event.value)
        ui.syn()

def main():
    current_file_path = os.path.abspath(sys.argv[0])
    try:
        last_mtime = os.path.getmtime(current_file_path)
    except Exception:
        last_mtime = 0
    last_check_time = time.time()

    def signal_handler(signum, frame):
        print("\n[INFO] Menerima sinyal terminasi (SIGTERM) dari OS...")
        raise KeyboardInterrupt
        
    signal.signal(signal.SIGTERM, signal_handler)

    print("\n" + "="*55)
    print(" KERNEL-LEVEL MOUSE CONTROLLER (KDE PLASMA & WAYLAND SAFE)")
    print("="*55)
    print("Panduan Shortcut:")
    print(" - Ctrl + M       : Mengaktifkan / Menonaktifkan")
    print(" - Arrow Keys     : Menggerakkan kursor (0% Gangguan Background)")
    print(" - Shift + Panah  : Bergerak Lambat (-5 Kecepatan)")
    print(" - Ctrl + Left    : Klik Kiri")
    print(" - Ctrl + Right   : Klik Kanan")
    print(" - Alt + Up       : Scroll Layar Atas")
    print(" - Alt + Down     : Scroll Layar Bawah")
    print(" - Ctrl + Up/Down : Sensitivitas Naik / Turun")
    print(" - Ctrl + H       : Tampilkan Terminal Bantuan Shortcut")
    print("\nBerjalan sebagai Background Service dengan Hot-Reload Otomatis.")
    print("="*55)

    try:
        while True:
            # FITUR HOT-RELOAD
            current_time = time.time()
            if current_time - last_check_time > 1.0:
                last_check_time = current_time
                try:
                    new_mtime = os.path.getmtime(current_file_path)
                    if new_mtime != last_mtime:
                        print("\n[INFO] PERUBAHAN KODE TERDETEKSI! Melakukan Hot-Reload Internal...")
                        for kbd in keyboards:
                            try: kbd.ungrab()
                            except: pass
                        try: ui.close()
                        except: pass
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                except Exception:
                    pass

            events = selector.select(timeout=0.015)
            for key, mask in events:
                device = key.fileobj
                try:
                    for event in device.read():
                        process_event(event)
                except Exception:
                    pass
            
            # Eksekusi pergerakan kursor jika mode aktif
            if is_active:
                dx, dy = 0, 0
                ctrl_active = (e.KEY_LEFTCTRL in physically_pressed) or (e.KEY_RIGHTCTRL in physically_pressed)
                alt_active = (e.KEY_LEFTALT in physically_pressed) or (e.KEY_RIGHTALT in physically_pressed)
                shift_active = (e.KEY_LEFTSHIFT in physically_pressed) or (e.KEY_RIGHTSHIFT in physically_pressed)
                
                if not ctrl_active and not alt_active:
                    # Menerapkan pengurangan kecepatan jika Shift ditekan
                    current_speed = max(1, sensitivity - 5) if shift_active else sensitivity

                    if e.KEY_UP in physically_pressed:
                        dy -= current_speed
                    if e.KEY_DOWN in physically_pressed:
                        dy += current_speed
                    if e.KEY_LEFT in physically_pressed:
                        dx -= current_speed
                    if e.KEY_RIGHT in physically_pressed:
                        dx += current_speed
                    
                    if dx != 0 or dy != 0:
                        if dx != 0:
                            ui.write(e.EV_REL, e.REL_X, dx)
                        if dy != 0:
                            ui.write(e.EV_REL, e.REL_Y, dy)
                        ui.syn()
                        
    except KeyboardInterrupt:
        print("\n[INFO] Menutup program...")
    finally:
        print("[INFO] Mengembalikan kontrol keyboard ke OS...")
        for kbd in keyboards:
            try:
                kbd.ungrab()
            except Exception:
                pass
        try:
            ui.close()
        except Exception:
            pass
        print("[INFO] Program selesai ditutup.")

if __name__ == "__main__":
    main()
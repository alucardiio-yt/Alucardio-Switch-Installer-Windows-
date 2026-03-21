import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import shutil
import requests
import zipfile
import threading
import time
import ctypes
import webbrowser
import sys
import os

sd_path = ""

GITHUB_OWNER = "alucardiio-yt"
GITHUB_REPO = "archives-nx"

DRIVE_REMOVABLE = 2


def ruta_recurso(nombre):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, nombre)
    return os.path.join(os.path.abspath("."), nombre)


def set_estado(texto):
    root.after(0, lambda: estado_valor.config(text=texto))


def set_progress(valor):
    root.after(0, lambda: progress.config(value=valor))
    root.after(0, lambda: progress_porcentaje.config(text=f"{valor:.0f}%"))


def set_botones_activos(activos):
    estado = "normal" if activos else "disabled"
    root.after(0, lambda: btn_auto_sd.config(state=estado))
    root.after(0, lambda: btn_sd.config(state=estado))
    root.after(0, lambda: btn_instalar.config(state=estado))
    root.after(0, lambda: btn_github.config(state=estado))
    root.after(0, lambda: btn_tegrarcm.config(state=estado))
    root.after(0, lambda: btn_guia_rcm.config(state=estado))
    root.after(0, lambda: checkbox_homebrew.config(state=estado))


def mostrar_error(titulo, mensaje):
    root.after(0, lambda: messagebox.showerror(titulo, mensaje))


def mostrar_info(titulo, mensaje):
    root.after(0, lambda: messagebox.showinfo(titulo, mensaje))


def actualizar_ruta_label(texto):
    root.after(0, lambda: ruta_valor.config(text=texto))


def abrir_github():
    webbrowser.open("https://github.com/alucardiio-yt/archives-nx/releases/latest")


def abrir_tegrarcm():
    webbrowser.open("https://github.com/eliboa/TegraRcmGUI/releases")


def mostrar_guia_rcm():
    ventana = tk.Toplevel(root)
    ventana.title("Cómo encender en modo RCM")
    ventana.geometry("720x600")
    ventana.resizable(True, True)
    ventana.minsize(580, 440)
    ventana.configure(bg="#0c0f16")
    ventana.grab_set()

    try:
        icono = ruta_recurso("alucardio.ico")
        if Path(icono).exists():
            ventana.iconbitmap(icono)
    except Exception:
        pass

    tk.Label(
        ventana,
        text="Cómo encender tu Nintendo Switch (RCM / AutoRCM)",
        font=("Segoe UI", 12, "bold"),
        bg="#0c0f16",
        fg="#ffffff"
    ).pack(anchor="w", padx=14, pady=(14, 8))

    contenedor = tk.Frame(ventana, bg="#0c0f16")
    contenedor.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    scrollbar = tk.Scrollbar(contenedor)
    scrollbar.pack(side="right", fill="y")

    texto = tk.Text(
        contenedor,
        wrap="word",
        yscrollcommand=scrollbar.set,
        bg="#121826",
        fg="#ffffff",
        font=("Segoe UI", 9),
        relief="flat",
        bd=0,
        padx=12,
        pady=12,
        insertbackground="#ffffff"
    )
    texto.pack(fill="both", expand=True)

    contenido = """Si tu consola utiliza método RCM o tiene AutoRCM activado, el proceso de encendido es diferente al de una Switch normal. Aquí te lo explico de forma clara:

⸻

🔌 Consolas con método RCM (manual)

1. Apaga completamente la consola.
2. Inserta el jig en el riel derecho (Joy-Con derecho).
3. Mantén presionado el botón VOL+.
4. Sin soltar VOL+, presiona el botón POWER.
5. La pantalla quedará en negro (esto es normal, estás en modo RCM).
6. Conecta la consola a tu PC.
7. Abre TegraRcmGUI.
8. Ve a la sección de Payload y da clic en “Browse” / “Seleccionar”.
9. Abre la carpeta donde tienes tus payloads.
10. Selecciona el archivo más reciente de Hekate (ejemplo: hekate_ctcaer_x.x.x.bin).
11. Presiona “Inject Payload”.

👉 Si todo está correcto, la consola iniciará en el entorno modificado.

⸻

⚡ Consolas con AutoRCM

1. Presiona el botón POWER normalmente.
2. La pantalla quedará en negro automáticamente (esto también es normal).
3. Conecta la consola a tu PC.
4. Abre TegraRcmGUI.
5. Ve a Payload → “Browse” / “Seleccionar”.
6. Abre la carpeta de tus payloads.
7. Selecciona el Hekate más reciente.
8. Presiona “Inject Payload”.

👉 No necesitas jig, ya que AutoRCM fuerza siempre el modo RCM.

⸻

⚠️ Importante

• Si no inyectas payload, la consola no encenderá (se quedará en negro).
• Evita dejarla sin batería, especialmente con AutoRCM.
• Usa siempre la versión más reciente de Hekate para evitar errores.

⸻

Recuerda que las consolas con Chip Físico no necesitan este procedimiento"""

    texto.insert("1.0", contenido)
    texto.config(state="disabled")
    scrollbar.config(command=texto.yview)


def validar_sd(ruta):
    p = Path(ruta)

    if str(p).lower() in ["c:\\", "c:/"]:
        return False, "No selecciones el disco C"

    posibles = ["Nintendo", "switch", "atmosphere", "bootloader"]
    encontrados = [x for x in posibles if (p / x).exists()]

    if not encontrados:
        return None, "No se detectaron carpetas típicas de Nintendo Switch"

    return True, "OK"


def obtener_unidades_removibles():
    unidades = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()

    for i in range(26):
        if bitmask & (1 << i):
            letra = chr(65 + i)
            unidad = f"{letra}:\\"
            tipo = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(unidad))

            if tipo == DRIVE_REMOVABLE:
                unidades.append(unidad)

    return unidades


def buscar_sd_switch():
    candidatos = []
    unidades = obtener_unidades_removibles()

    for unidad in unidades:
        try:
            ok, _ = validar_sd(unidad)
            if ok is True:
                candidatos.append(unidad)
        except Exception:
            pass

    return candidatos


def seleccionar_sd():
    global sd_path

    ruta = filedialog.askdirectory(title="Selecciona la microSD de tu Switch")
    if not ruta:
        return

    ok, mensaje = validar_sd(ruta)

    if ok is False:
        messagebox.showerror("Error", mensaje)
        return

    if ok is None:
        continuar = messagebox.askyesno(
            "Carpeta vacía o no detectada",
            "No se detectaron carpetas típicas de Nintendo Switch en esta ruta.\n\n"
            "Esto puede pasar si la microSD está vacía, recién formateada o le faltan archivos.\n\n"
            "¿Quieres continuar de todos modos?"
        )
        if not continuar:
            return

        sd_path = ruta
        actualizar_ruta_label(sd_path)
        set_estado("Carpeta seleccionada manualmente")
        return

    sd_path = ruta
    actualizar_ruta_label(sd_path)
    set_estado("Carpeta válida seleccionada")


def detectar_sd_automaticamente():
    global sd_path

    set_estado("Buscando microSD automáticamente...")
    candidatos = buscar_sd_switch()

    if not candidatos:
        messagebox.showwarning(
            "No encontrada",
            "No se detectó ninguna unidad removible que parezca una microSD de Switch."
        )
        set_estado("No se encontró ninguna microSD compatible")
        return

    if len(candidatos) == 1:
        sd_path = candidatos[0]
        actualizar_ruta_label(sd_path)
        set_estado("MicroSD detectada automáticamente")
        messagebox.showinfo("Detectada", f"Se detectó automáticamente la microSD:\n\n{sd_path}")
        return

    ventana = tk.Toplevel(root)
    ventana.title("Seleccionar microSD detectada")
    ventana.geometry("410x250")
    ventana.resizable(False, False)
    ventana.configure(bg="#0c0f16")
    ventana.grab_set()

    try:
        icono = ruta_recurso("alucardio.ico")
        if Path(icono).exists():
            ventana.iconbitmap(icono)
    except Exception:
        pass

    tk.Label(
        ventana,
        text="Se detectaron varias unidades compatibles",
        font=("Segoe UI", 11, "bold"),
        bg="#0c0f16",
        fg="#ffffff"
    ).pack(pady=(16, 6))

    tk.Label(
        ventana,
        text="Selecciona cuál quieres usar:",
        font=("Segoe UI", 9),
        bg="#0c0f16",
        fg="#aeb6c2"
    ).pack()

    lista = tk.Listbox(
        ventana,
        width=38,
        height=6,
        font=("Segoe UI", 9),
        bg="#131826",
        fg="#ffffff",
        selectbackground="#3ddc97",
        selectforeground="#000000",
        bd=0,
        highlightthickness=1,
        highlightbackground="#232c40",
        highlightcolor="#3ddc97"
    )
    lista.pack(pady=12)

    for unidad in candidatos:
        lista.insert(tk.END, unidad)

    def confirmar_seleccion():
        global sd_path
        seleccion = lista.curselection()
        if not seleccion:
            messagebox.showerror("Error", "Selecciona una unidad", parent=ventana)
            return

        sd_path = lista.get(seleccion[0])
        actualizar_ruta_label(sd_path)
        set_estado("MicroSD detectada automáticamente")
        ventana.destroy()

    tk.Button(
        ventana,
        text="Usar esta unidad",
        command=confirmar_seleccion,
        font=("Segoe UI", 9, "bold"),
        bg="#3ddc97",
        fg="#000000",
        activebackground="#53e7a8",
        activeforeground="#000000",
        relief="flat",
        bd=0,
        padx=14,
        pady=7,
        cursor="hand2"
    ).pack(pady=2)


def limpiar_carpetas(ruta_sd):
    carpetas_a_borrar = [
        "atmosphere",
        "bootloader",
        "config",
        "scripts",
        "Next"
    ]

    if not conservar_homebrew.get():
        carpetas_a_borrar.append("switch")

    archivos_a_borrar = [
        "boot.dat",
        "boot.ini",
        "exosphere.ini",
        "hbmenu.nro",
        "payload.bin"
    ]

    borradas = []
    no_encontradas = []

    for nombre in carpetas_a_borrar:
        ruta_carpeta = Path(ruta_sd) / nombre

        if ruta_carpeta.exists() and ruta_carpeta.is_dir():
            shutil.rmtree(ruta_carpeta)
            if nombre != "Next":
                borradas.append(nombre)
        else:
            if nombre != "Next":
                no_encontradas.append(nombre)

    for nombre in archivos_a_borrar:
        ruta_archivo = Path(ruta_sd) / nombre

        if ruta_archivo.exists() and ruta_archivo.is_file():
            ruta_archivo.unlink()
            borradas.append(nombre)
        else:
            no_encontradas.append(nombre)

    return borradas, no_encontradas


def obtener_asset_zip_latest(owner, repo):
    set_estado("Buscando latest release en GitHub...")

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Alucardio-Switch-Installer"
    }

    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    for asset in data.get("assets", []):
        nombre = asset.get("name", "").lower()
        if nombre.endswith(".zip"):
            return asset["browser_download_url"], asset["name"]

    raise Exception("No se encontró ningún archivo .zip en la latest release")


def descargar_archivo_con_reintentos(url, destino, reintentos=3):
    headers = {
        "User-Agent": "Alucardio-Switch-Installer"
    }

    ultimo_error = None

    for intento in range(1, reintentos + 1):
        try:
            set_estado(f"Descargando pack... intento {intento}/{reintentos}")
            set_progress(0)

            with requests.get(url, headers=headers, stream=True, timeout=(20, 180)) as r:
                r.raise_for_status()

                total_size = int(r.headers.get("content-length", 0))
                descargado = 0

                with open(destino, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
                            descargado += len(chunk)

                            if total_size > 0:
                                porcentaje = (descargado / total_size) * 100
                                set_progress(porcentaje)
                                set_estado(f"Descargando pack... {porcentaje:.1f}%")
                            else:
                                mb = descargado / (1024 * 1024)
                                set_estado(f"Descargando pack... {mb:.1f} MB")

            return

        except Exception as e:
            ultimo_error = e

            if destino.exists():
                try:
                    destino.unlink()
                except Exception:
                    pass

            if intento < reintentos:
                set_estado(f"Falló la descarga, reintentando en 3 segundos... ({intento}/{reintentos})")
                time.sleep(3)
            else:
                raise ultimo_error


def extraer_zip(zip_path, destino):
    set_estado("Extrayendo archivos...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(destino)


def copiar_contenido(origen, destino):
    set_estado("Instalando pack en la SD...")

    origen = Path(origen)
    destino = Path(destino)

    elementos = list(origen.iterdir())
    total = len(elementos)

    if total == 0:
        raise Exception("El ZIP se extrajo vacío")

    for i, item in enumerate(elementos, start=1):
        destino_item = destino / item.name

        if item.is_dir():
            shutil.copytree(item, destino_item, dirs_exist_ok=True)
        else:
            shutil.copy2(item, destino_item)

        porcentaje = (i / total) * 100
        set_progress(porcentaje)
        set_estado(f"Instalando pack en la SD... {porcentaje:.1f}%")


def proceso_instalacion():
    global sd_path

    try:
        set_botones_activos(False)
        set_progress(0)

        set_estado("Limpiando carpetas y archivos viejos...")
        borradas, no_encontradas = limpiar_carpetas(sd_path)

        temp_dir = Path("temp_download")
        temp_dir.mkdir(exist_ok=True)

        download_url, asset_name = obtener_asset_zip_latest(GITHUB_OWNER, GITHUB_REPO)
        destino_zip = temp_dir / asset_name

        descargar_archivo_con_reintentos(download_url, destino_zip, reintentos=3)

        extract_dir = temp_dir / "extract"

        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)

        extract_dir.mkdir(exist_ok=True)

        extraer_zip(destino_zip, extract_dir)
        set_progress(0)

        copiar_contenido(extract_dir, sd_path)

        try:
            shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception:
            pass

        try:
            destino_zip.unlink(missing_ok=True)
        except Exception:
            pass

        set_progress(100)
        set_estado("Instalación completada")

        mensaje = "Instalación terminada.\n\n"

        if borradas:
            mensaje += "Elementos borrados:\n- " + "\n- ".join(borradas) + "\n\n"

        if no_encontradas:
            mensaje += "No se encontraron:\n- " + "\n- ".join(no_encontradas) + "\n\n"

        mensaje += "El pack fue descargado, extraído e instalado correctamente."

        mostrar_info("Listo", mensaje)

    except Exception as e:
        set_estado("Error")
        mostrar_error("Error", f"Ocurrió un problema:\n{e}")

    finally:
        set_botones_activos(True)


def instalar_pack():
    global sd_path

    if not sd_path:
        messagebox.showerror("Error", "Primero selecciona una microSD")
        return

    mensaje = f"Se borrarán las siguientes carpetas y archivos en:\n\n{sd_path}\n\n"

    mensaje += "Carpetas:\n"
    mensaje += "- atmosphere\n- bootloader\n- config\n- scripts\n"

    if not conservar_homebrew.get():
        mensaje += "- switch (Apps Homebrew)\n"

    mensaje += "\nArchivos:\n"
    mensaje += "- boot.dat\n- boot.ini\n- exosphere.ini\n- hbmenu.nro\n- payload.bin\n\n"

    if conservar_homebrew.get():
        mensaje += "✔ Se conservarán tus Apps Homebrew\n\n"
    else:
        mensaje += "⚠️ Se eliminarán tus Apps Homebrew\n\n"

    mensaje += "Se descargará e instalará la última versión del pack.\n\n¿Continuar?"

    confirmar = messagebox.askyesno("Confirmar instalación", mensaje)

    if not confirmar:
        return

    hilo = threading.Thread(target=proceso_instalacion, daemon=True)
    hilo.start()


# ---------------- UI ----------------

root = tk.Tk()
root.title("Alucardio Switch Installer")
root.configure(bg="#080b12")

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

window_w = min(980, screen_w - 30)
window_h = min(760, screen_h - 60)

root.geometry(f"{window_w}x{window_h}")
root.minsize(820, 600)
root.resizable(True, True)

try:
    icono = ruta_recurso("alucardio.ico")
    if Path(icono).exists():
        root.iconbitmap(icono)
except Exception:
    pass

conservar_homebrew = tk.BooleanVar(value=True)

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Green.Horizontal.TProgressbar",
    troughcolor="#1a2132",
    background="#3ddc97",
    bordercolor="#1a2132",
    lightcolor="#3ddc97",
    darkcolor="#3ddc97"
)

bg_main = "#080b12"
card_bg = "#111522"
box_bg = "#0d1320"
line_color = "#1c2538"
text_main = "#ffffff"
text_soft = "#97a3b6"
accent = "#8b5cf6"
accent_2 = "#5da9ff"

main_wrap = tk.Frame(root, bg=bg_main)
main_wrap.pack(fill="both", expand=True, padx=16, pady=16)

card = tk.Frame(
    main_wrap,
    bg=card_bg,
    highlightthickness=1,
    highlightbackground=line_color,
    bd=0
)
card.pack(fill="both", expand=True)

header = tk.Frame(card, bg=card_bg)
header.pack(fill="x", padx=20, pady=(18, 10))

logo_circle = tk.Canvas(header, width=46, height=46, bg=card_bg, highlightthickness=0, bd=0)
logo_circle.pack(side="left")
logo_circle.create_oval(4, 4, 42, 42, fill=accent, outline=accent)

header_text = tk.Frame(header, bg=card_bg)
header_text.pack(side="left", padx=12)

tk.Label(
    header_text,
    text="Alucardio Switch Installer",
    font=("Segoe UI", 18, "bold"),
    fg=text_main,
    bg=card_bg
).pack(anchor="w")

tk.Label(
    header_text,
    text="Instalador Todo en Uno para actualizar tu Nintendo Switch",
    font=("Segoe UI", 10),
    fg=text_soft,
    bg=card_bg
).pack(anchor="w", pady=(2, 0))

line = tk.Frame(card, bg=line_color, height=1)
line.pack(fill="x", padx=20, pady=(0, 12))

content = tk.Frame(card, bg=card_bg)
content.pack(fill="both", expand=True, padx=20, pady=(0, 14))

left_panel = tk.Frame(content, bg=card_bg)
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

right_panel = tk.Frame(content, bg=card_bg, width=285)
right_panel.pack(side="right", fill="both", expand=False)

# ---------------- LEFT ----------------

section_sd = tk.Frame(left_panel, bg=box_bg, highlightthickness=1, highlightbackground=line_color)
section_sd.pack(fill="x", pady=(0, 10))

tk.Label(
    section_sd,
    text="MICROSD",
    font=("Segoe UI", 9, "bold"),
    fg=accent,
    bg=box_bg
).pack(anchor="w", padx=14, pady=(12, 8))

btn_auto_sd = tk.Button(
    section_sd,
    text="Detectar microSD automáticamente",
    command=detectar_sd_automaticamente,
    font=("Segoe UI", 9, "bold"),
    bg=accent,
    fg="#000000",
    activebackground="#a78bfa",
    activeforeground="#000000",
    relief="flat",
    bd=0,
    padx=12,
    pady=8,
    cursor="hand2"
)
btn_auto_sd.pack(fill="x", padx=14, pady=(0, 8))

btn_sd = tk.Button(
    section_sd,
    text="Seleccionar microSD manualmente",
    command=seleccionar_sd,
    font=("Segoe UI", 9, "bold"),
    bg="#1a2235",
    fg="#ffffff",
    activebackground="#26314b",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    padx=12,
    pady=8,
    cursor="hand2"
)
btn_sd.pack(fill="x", padx=14, pady=(0, 10))

tk.Label(
    section_sd,
    text="Ruta seleccionada",
    font=("Segoe UI", 9),
    fg=text_soft,
    bg=box_bg
).pack(anchor="w", padx=14)

ruta_box = tk.Label(
    section_sd,
    text="No has seleccionado ninguna SD",
    font=("Segoe UI", 9),
    fg=text_main,
    bg="#0a101b",
    justify="left",
    anchor="w",
    wraplength=520,
    padx=10,
    pady=10,
    relief="flat"
)
ruta_box.pack(fill="x", padx=14, pady=(6, 14))
ruta_valor = ruta_box

section_install = tk.Frame(left_panel, bg=box_bg, highlightthickness=1, highlightbackground=line_color)
section_install.pack(fill="x")

tk.Label(
    section_install,
    text="INSTALACIÓN",
    font=("Segoe UI", 9, "bold"),
    fg=accent_2,
    bg=box_bg
).pack(anchor="w", padx=14, pady=(12, 8))

btn_instalar = tk.Button(
    section_install,
    text="Instalar Pack",
    command=instalar_pack,
    font=("Segoe UI", 10, "bold"),
    bg=accent_2,
    fg="#000000",
    activebackground="#7bbcff",
    activeforeground="#000000",
    relief="flat",
    bd=0,
    padx=12,
    pady=9,
    cursor="hand2"
)
btn_instalar.pack(fill="x", padx=14, pady=(0, 8))

checkbox_homebrew = tk.Checkbutton(
    section_install,
    text="Conservar Apps Homebrew",
    variable=conservar_homebrew,
    font=("Segoe UI", 9),
    bg=box_bg,
    fg=text_main,
    activebackground=box_bg,
    activeforeground=text_main,
    selectcolor="#0a101b"
)
checkbox_homebrew.pack(anchor="w", padx=14, pady=(0, 8))

tk.Label(
    section_install,
    text="Estado actual",
    font=("Segoe UI", 9),
    fg=text_soft,
    bg=box_bg
).pack(anchor="w", padx=14)

estado_valor = tk.Label(
    section_install,
    text="Esperando acción",
    font=("Segoe UI", 9, "bold"),
    fg=text_main,
    bg="#0a101b",
    anchor="w",
    justify="left",
    wraplength=520,
    padx=10,
    pady=10
)
estado_valor.pack(fill="x", padx=14, pady=(6, 10))

progress_frame = tk.Frame(section_install, bg=box_bg)
progress_frame.pack(fill="x", padx=14, pady=(0, 14))

progress = ttk.Progressbar(
    progress_frame,
    orient="horizontal",
    mode="determinate",
    style="Green.Horizontal.TProgressbar"
)
progress.pack(fill="x", pady=(0, 6), ipady=6)

progress_porcentaje = tk.Label(
    progress_frame,
    text="0%",
    font=("Segoe UI", 9, "bold"),
    fg=text_main,
    bg=box_bg
)
progress_porcentaje.pack(anchor="center")

# ---------------- RIGHT ----------------

side_card = tk.Frame(right_panel, bg=box_bg, highlightthickness=1, highlightbackground=line_color)
side_card.pack(fill="both", expand=True)

tk.Label(
    side_card,
    text="VERSIONES",
    font=("Segoe UI", 9, "bold"),
    fg=accent,
    bg=box_bg
).pack(anchor="w", padx=14, pady=(12, 8))

tk.Label(
    side_card,
    text="Puedes abrir el GitHub para ver la última versión disponible del pack.",
    font=("Segoe UI", 9),
    fg=text_soft,
    bg=box_bg,
    justify="left",
    anchor="w",
    wraplength=230
).pack(anchor="w", padx=14, pady=(0, 8))

btn_github = tk.Button(
    side_card,
    text="Ver última versión (GitHub)",
    command=abrir_github,
    font=("Segoe UI", 9, "bold"),
    bg="#1a2235",
    fg="#ffffff",
    activebackground="#26314b",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    padx=12,
    pady=8,
    cursor="hand2"
)
btn_github.pack(fill="x", padx=14, pady=(0, 12))

tk.Label(
    side_card,
    text="INFO",
    font=("Segoe UI", 9, "bold"),
    fg=accent_2,
    bg=box_bg
).pack(anchor="w", padx=14, pady=(0, 8))

info_items = [
    "• No se eliminan partidas guardadas.",
    "• No se eliminan juegos instalados.",
    "• Extrae e instala el pack completo."
]

for item in info_items:
    tk.Label(
        side_card,
        text=item,
        font=("Segoe UI", 9),
        fg=text_main,
        bg=box_bg,
        justify="left",
        anchor="w",
        wraplength=230
    ).pack(anchor="w", padx=14, pady=3)

rcm_box = tk.Frame(side_card, bg="#0a101b", highlightthickness=1, highlightbackground=line_color)
rcm_box.pack(fill="x", padx=14, pady=(12, 0))

tk.Label(
    rcm_box,
    text="MODO RCM",
    font=("Segoe UI", 9, "bold"),
    fg=accent,
    bg="#0a101b"
).pack(anchor="w", padx=10, pady=(8, 4))

tk.Label(
    rcm_box,
    text="Si tu consola usa RCM, necesitas TegraRcmGUI para inyectar payloads. Si tiene chip físico no es necesario",
    font=("Segoe UI", 8),
    fg=text_soft,
    bg="#0a101b",
    justify="left",
    wraplength=215
).pack(anchor="w", padx=10, pady=(0, 8))

btn_tegrarcm = tk.Button(
    rcm_box,
    text="Descargar TegraRcmGUI",
    command=abrir_tegrarcm,
    font=("Segoe UI", 9, "bold"),
    bg="#1a2235",
    fg="#ffffff",
    activebackground="#26314b",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    padx=10,
    pady=7,
    cursor="hand2"
)
btn_tegrarcm.pack(fill="x", padx=10, pady=(0, 8))

btn_guia_rcm = tk.Button(
    rcm_box,
    text="Cómo encender en modo RCM",
    command=mostrar_guia_rcm,
    font=("Segoe UI", 9, "bold"),
    bg="#374151",
    fg="#ffffff",
    activebackground="#4b5563",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    padx=10,
    pady=7,
    cursor="hand2"
)
btn_guia_rcm.pack(fill="x", padx=10, pady=(0, 10))

tip_box = tk.Frame(side_card, bg="#0a101b", highlightthickness=1, highlightbackground=line_color)
tip_box.pack(fill="x", padx=14, pady=(12, 14))

tk.Label(
    tip_box,
    text="TIP",
    font=("Segoe UI", 9, "bold"),
    fg=accent_2,
    bg="#0a101b"
).pack(anchor="w", padx=10, pady=(8, 4))

tk.Label(
    tip_box,
    text="Si activas Conservar Apps Homebrew, no se borrará la carpeta switch.",
    font=("Segoe UI", 8),
    fg=text_soft,
    bg="#0a101b",
    justify="left",
    wraplength=215
).pack(anchor="w", padx=10, pady=(0, 8))

footer = tk.Frame(card, bg=card_bg)
footer.pack(fill="x", padx=20, pady=(0, 12))

tk.Label(
    footer,
    text="ALUCARDIO",
    font=("Segoe UI", 8, "bold"),
    fg=text_soft,
    bg=card_bg
).pack(side="right")

root.mainloop()
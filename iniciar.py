import os, sys, getpass, sqlite3, threading, webbrowser
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
if sys.version_info < (3, 12):
    raise SystemExit('Se necesita Python 3.12 o superior.')
from nucleo import DB
necesita = True
if Path(DB).is_file():
    try:
        with sqlite3.connect(DB) as c:
            necesita = c.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0] == 0
    except sqlite3.OperationalError:
        necesita = True
if necesita:
    while True:
        pin = getpass.getpass('Crea tu PIN de administrador (8 a 64 dígitos): ')
        if pin.isdigit() and 8 <= len(pin) <= 64:
            confirmar = getpass.getpass('Confirma tu PIN: ')
            if pin == confirmar:
                os.environ['PARCHE_ADMIN_PIN'] = pin
                break
        print('Los PIN deben coincidir y contener entre 8 y 64 dígitos.')
os.environ.setdefault('PARCHE_HOST', '127.0.0.1')
os.environ.setdefault('PARCHE_PORT', '8000')
print('Usuario inicial: admin')
print('Abre http://127.0.0.1:' + os.environ['PARCHE_PORT'])
print('Mantén esta consola abierta. Para detener: Ctrl+C.')
threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:' + os.environ['PARCHE_PORT'])).start()
from servidor import main
try:
    main()
except OSError as e:
    print('No se pudo iniciar el servidor:', e)
    print('Si el puerto 8000 está ocupado, detén la versión anterior con Ctrl+C y vuelve a ejecutar.')
except KeyboardInterrupt:
    print('Servidor detenido.')

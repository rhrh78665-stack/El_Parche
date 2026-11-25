import os
import sys
import threading
import webbrowser
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
if sys.version_info < (3, 12):
    raise SystemExit('Se necesita Python 3.12 o superior.')
os.environ.setdefault('PARCHE_HOST', '127.0.0.1')
os.environ.setdefault('PARCHE_PORT', '8000')
print('Restaurante: restaurante | PIN: 48261937')
print('Cliente: cliente | PIN: 73619482')
print('Abre http://127.0.0.1:' + os.environ['PARCHE_PORT'])
print('Mantén esta consola abierta. Para detener: Ctrl+C.')
threading.Timer(2, lambda: webbrowser.open('http://127.0.0.1:' + os.environ['PARCHE_PORT'])).start()
from servidor import main
try:
    main()
except OSError as e:
    print('No se pudo iniciar:', e)
    print('Detén la versión anterior con Ctrl+C si el puerto está ocupado.')
    raise SystemExit(1)
except KeyboardInterrupt:
    print('Aplicación detenida.')

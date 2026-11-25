import os
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def bloquear(ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    f = open(ruta, 'a+b')
    if f.tell() == 0:
        f.write(b'0')
        f.flush()
    try:
        f.seek(0)
        if os.name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise RuntimeError('La base está en uso. Detén el servidor antes de restaurar.')
        else:
            import fcntl
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('La base está en uso. Detén el servidor antes de restaurar.')
        yield
    finally:
        f.close()

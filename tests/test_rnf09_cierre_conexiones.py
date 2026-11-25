import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import nucleo
import respaldo
import test_operacion as soporte

class CierreConexiones(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def capturar(self):
        conexiones = []
        original = sqlite3.connect

        def conectar(*args, **kwargs):
            conexion = original(*args, **kwargs)
            conexiones.append((str(args[0]), conexion))
            return conexion
        return (conexiones, conectar)

    def verificar_cerradas(self, conexiones):
        self.assertTrue(conexiones)
        for ruta, conexion in conexiones:
            with self.subTest(ruta=ruta):
                with self.assertRaises(sqlite3.ProgrammingError):
                    conexion.execute('SELECT 1')

    def test_cierra_antes_de_renombrar(self):
        respaldo.DB = nucleo.DB
        conexiones, conectar = self.capturar()
        reemplazar_original = os.replace
        comprobadas = []

        def reemplazar(origen, destino):
            for ruta, conexion in conexiones:
                if Path(ruta) == Path(origen):
                    with self.assertRaises(sqlite3.ProgrammingError):
                        conexion.execute('SELECT 1')
                    comprobadas.append(ruta)
            return reemplazar_original(origen, destino)
        with tempfile.TemporaryDirectory() as carpeta:
            with patch('sqlite3.connect', side_effect=conectar), patch('respaldo.os.replace', side_effect=reemplazar):
                respaldo.copiar(carpeta)
            self.assertEqual(len(comprobadas), 1)
            self.verificar_cerradas(conexiones)

    def test_cierra_si_la_copia_falla(self):
        conexiones, conectar = self.capturar()
        exigir_original = respaldo.exigir

        def exigir(condicion, mensaje):
            if mensaje == 'Copia inválida':
                raise ValueError('Fallo de validación de prueba')
            return exigir_original(condicion, mensaje)
        with tempfile.TemporaryDirectory() as carpeta:
            with patch('sqlite3.connect', side_effect=conectar), patch('respaldo.exigir', side_effect=exigir):
                with self.assertRaises(ValueError):
                    respaldo.copiar(carpeta)
            self.verificar_cerradas(conexiones)

    def test_restaurar_cierra_origen_y_destino(self):
        respaldo.DB = nucleo.DB
        actual = os.getcwd()
        with tempfile.TemporaryDirectory() as carpeta:
            try:
                os.chdir(carpeta)
                archivo = respaldo.copiar()
                conexiones, conectar = self.capturar()
                with patch('sqlite3.connect', side_effect=conectar):
                    respaldo.restaurar(archivo)
                self.verificar_cerradas(conexiones)
            finally:
                os.chdir(actual)

    def test_supresion_cierra_respaldos(self):
        from privacidad import suprimir_respaldos
        respaldo.DB = nucleo.DB
        actual = os.getcwd()
        with tempfile.TemporaryDirectory() as carpeta:
            try:
                os.chdir(carpeta)
                respaldo.copiar()
                conexiones, conectar = self.capturar()
                with patch('sqlite3.connect', side_effect=conectar):
                    suprimir_respaldos('3001234567')
                self.verificar_cerradas(conexiones)
            finally:
                os.chdir(actual)

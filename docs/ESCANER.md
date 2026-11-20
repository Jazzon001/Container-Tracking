# Lector de código de barras

Las pantallas **Cargar**, **Recibir** y **Mantenimiento** están pensadas para un lector que funcione como teclado. No hay controlador ni configuración especial en la aplicación: el lector "escribe" el código en el campo que tiene el foco.

## Qué debe hacer el lector

| Ajuste | Valor | Por qué |
|---|---|---|
| Modo de conexión | **USB HID Keyboard** (teclado USB) | En modo puerto serie (COM) no escribe en ningún programa |
| Sufijo | **Enter** al final de cada lectura | Con un solo campo (Recibir), el Enter envía el formulario solo; en Cargar pasa al campo siguiente |
| Idioma del teclado de Windows | El mismo con el que se imprimió el código | Si no coincide, salen letras o símbolos cambiados |

## Si el lector no escribe

1. Probar en el Bloc de notas: si tampoco escribe ahí, el problema es del equipo, no de la aplicación.
2. Revisar que encienda y haga "beep" al leer; si no, cambiar de puerto USB o de cable (sin hubs).
3. En el Administrador de dispositivos debe verse en *Teclados* o *Dispositivos de interfaz humana*; si aparece en *Puertos (COM y LPT)*, está en modo serie: escanear el código de configuración "USB HID Keyboard" del manual del modelo.
4. En lectores inalámbricos, revisar la batería y el emparejamiento (Bluetooth o receptor de 2.4 GHz).

## Sin lector

La pantalla **Recibir** tiene la sección **Liberar por carro**: se busca el carro por su número en la lista de los que están en tránsito y se pulsa *Liberar* (con confirmación). Hace lo mismo que escanear el contenedor elemento.

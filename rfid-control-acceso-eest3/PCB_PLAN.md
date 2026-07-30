# Plan de PCB para la rama claude

## Objetivo

Convertir el esquema actual en una placa de prueba coherente para controlar una puerta con RFID, PIR y solenoide de 12 V.

## Alcance de esta versión

- PCB de prueba de tamaño medio, con distribución modular.
- Bloque de alimentación en un lado.
- Bloque del controlador ESP32 y RFID en el centro.
- Bloque de sensores y señalización en un lado.
- Bloque de potencia para la solenoide en un extremo, con separación física y retorno de potencia.
- Diseño orientado a montaje experimental, no a fabricación industrial.

## Convenciones de diseño

- Mantener la alimentación de 12 V y la lógica de 3,3 V separadas físicamente.
- Colocar el MOSFET de la solenoide cerca del conector de carga y del diodo flyback.
- Mantener el RC522 alejado de la ruta de corriente de la solenoide y de la antena de la cerradura.
- Reservar un espacio claro para el módulo buck y para los conectores externos.
- Usar trazas anchas en la ruta de corriente de la solenoide.

## Estado

Esta versión busca dejar el proyecto en un estado de PCB abierto y revisable en KiCad, con una topología de prueba más ordenada que el prototipo previo.

# Proyecto RFID EEST3 — reglas para Codex

## Objetivo

Diseñar en KiCad 10 una placa controladora para acceso RFID escolar, revisable y segura para prototipado educativo.

## Alcance inicial

- ESP32 DevKit como controlador.
- RC522/MIFARE alimentado exclusivamente a 3,3 V.
- Comunicación SPI entre ESP32 y RC522.
- Sensor reed para detectar el estado de la puerta.
- Entrada opcional para sensor PIR.
- Buzzer y LED verde/rojo.
- MOSFET lógico canal N para controlar una cerradura o solenoide de 12 V.
- Diodo flyback sobre la carga inductiva.
- Entrada de 12 V y conversión regulada para la electrónica.
- Masa común controlada.
- Conectores claramente identificados.

## Reglas obligatorias

1. Trabajar primero en arquitectura y esquemático.
2. No rutear PCB sin aprobación humana explícita.
3. No inventar pinouts, corrientes, footprints ni valores críticos.
4. Marcar datos faltantes como PENDIENTE_DATASHEET.
5. El RC522 debe funcionar únicamente con 3,3 V.
6. El solenoide no debe alimentarse desde el ESP32.
7. La carga debe manejarse mediante MOSFET y diodo flyback.
8. Separar visualmente potencia, alimentación, lógica y sensores.
9. Ejecutar ERC y explicar cada advertencia.
10. Guardar versiones antes de modificaciones importantes.
11. No generar Gerber ni usar autorouter todavía.

## Primer entregable

Crear:

- arquitectura por bloques;
- lista preliminar de componentes;
- propuesta de GPIO;
- proyecto KiCad;
- esquemático inicial;
- informe de ERC.

Detenerse antes de diseñar o rutear la PCB.

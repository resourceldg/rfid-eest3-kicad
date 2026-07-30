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
11. No generar Gerber hasta que se levanten los bloqueos de
    [PENDIENTES.md](rfid-control-acceso-eest3/PENDIENTES.md).

## Estado de las reglas 2 y 11

La regla 2 se cumplió: el ruteo se autorizó explícitamente y quedó registrado en
el commit `c100552`.

La regla 11 decía además "ni usar autorouter todavía", y esa parte **quedó
derogada por esa misma autorización**: la placa se ruteó con Freerouting. Se
deja constancia acá porque durante un tiempo el repositorio se contradijo a sí
mismo, y un agente que leyera solo este archivo habría concluido que el board
está mal hecho.

Lo que sigue vigente de la regla 11 es la prohibición de generar Gerber. El
autorouter produce cobre revisable; un Gerber es una orden de compra.

## Primer entregable

Entregado. Existen la arquitectura por bloques, la lista de componentes, la
propuesta de GPIO, el proyecto KiCad, los seis esquemas y el informe de ERC.

## Dónde está cada cosa

- Revisión técnica y riesgos: [INFORME_ESQUEMA.md](rfid-control-acceso-eest3/INFORME_ESQUEMA.md)
- Qué bloquea la fabricación: [PENDIENTES.md](rfid-control-acceso-eest3/PENDIENTES.md)
- Mediciones que faltan: [CHECKLIST_PREPCB.md](rfid-control-acceso-eest3/CHECKLIST_PREPCB.md)
- Por qué el cobre está donde está: [GUIA_RUTEO.md](rfid-control-acceso-eest3/GUIA_RUTEO.md)

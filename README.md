# Control de acceso RFID EEST3

Diseño electrónico en KiCad 10 para un sistema de acceso escolar basado en ESP32, RC522, sensores y control de cerradura de 12 V.

## Estado actual del proyecto

Hay una placa de prueba de 140 × 100 mm, doble cara, **ruteada y con el DRC
limpio**: 348 pistas, 8 vías, dos planos de masa separados que se tocan en un
solo punto, y ninguna infracción de margen, cobre, alivio térmico ni
serigrafía. Los tres "no conectados" que informa el DRC son deliberados.

**No está lista para fabricar.** Faltan las mediciones de banco, la
verificación mecánica de los conectores y, sobre todo, medir el módulo ESP32-S3
para borrar la hilera de pines que sobra en J13. Los tres bloqueos están
detallados en [PENDIENTES.md](rfid-control-acceso-eest3/PENDIENTES.md).

## Documentos de referencia

- Qué falta para fabricar: [rfid-control-acceso-eest3/PENDIENTES.md](rfid-control-acceso-eest3/PENDIENTES.md)
- Revisión técnica y riesgos: [rfid-control-acceso-eest3/INFORME_ESQUEMA.md](rfid-control-acceso-eest3/INFORME_ESQUEMA.md)
- Mediciones que faltan: [rfid-control-acceso-eest3/CHECKLIST_PREPCB.md](rfid-control-acceso-eest3/CHECKLIST_PREPCB.md)
- Por qué el cobre está donde está: [rfid-control-acceso-eest3/GUIA_RUTEO.md](rfid-control-acceso-eest3/GUIA_RUTEO.md)

## Próximo paso recomendado

Medir la separación real entre hileras del ESP32-S3 DevKit y borrar la hilera
sobrante de J13. Es el único bloqueo que no necesita instrumental: alcanza con
un calibre y el módulo en la mano.

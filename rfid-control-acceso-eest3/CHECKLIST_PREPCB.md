# Checklist de depuración pre-PCB

## Estado: ningún ítem tildado, y la PCB ya existe

Conviene decirlo de entrada porque cambia cómo se lee el resto del documento.
Este checklist se escribió como condición para *empezar* la PCB. La placa se
emplazó y se ruteó igual, con autorización explícita, y hoy pasa el DRC sin
infracciones.

Eso no invalida el checklist: lo reubica. Las mediciones que están acá abajo
seguían siendo necesarias antes y siguen siéndolo ahora, con la diferencia de
que ahora hay una placa concreta contra la cual medirlas en vez de una
estimación. Lo que **no** se puede hacer sin ellas es fabricar.

El criterio de pase del final de este archivo queda vigente tal cual, corrido
un casillero: ya no es el permiso para empezar el layout, es el permiso para
mandar a fabricar. La lista completa de bloqueos está en
[PENDIENTES.md](PENDIENTES.md).

## Objetivo

Convertir el diseño actual en un prototipo de laboratorio con mayor robustez eléctrica y menor riesgo de falla antes de avanzar a una PCB de prueba.

## Bloqueadores técnicos prioritarios

1. Alimentación y protección
   - Verificar que la fuente de 12 V tenga margen real para la cerradura y la electrónica.
   - Definir fusible o PTC con base en mediciones reales de corriente y arranque.
   - Separar físicamente la ruta de potencia de la cerradura del retorno lógico.

2. Etapa de cerradura
   - Medir corriente de arranque de la cerradura y consumo estacionario.
   - Validar el MOSFET con margen térmico, SOA y conducción a gate de 3,3 V.
   - Confirmar el flyback, su ubicación y su capacidad para absorber energía sin dañar el interruptor.

3. Interfaz con el controlador y sensores
   - Confirmar el pinout físico del ESP32-S3 y del módulo RC522.
   - Validar que la alimentación de 3,3 V sea estable bajo carga del RC522.
   - Revisar el comportamiento de los contactos secos y la lógica de seguridad frente a fallos de cableado.

4. Manufactura y montaje
   - Confirmar conectores, borneras y paso físico real antes de asignar footprints.
   - Definir separación entre antena RFID, cerradura, buck y partes metálicas.
   - Revisar que la caja y el montaje no comprometan la antena ni la disipación térmica.

## Lista de verificación

- [ ] Medir corriente de arranque de la cerradura.
- [ ] Medir consumo estacionario del sistema completo.
- [ ] Verificar tensión de 12 V, 5 V y 3,3 V bajo carga dinámica.
- [ ] Verificar temperatura del MOSFET en el peor caso de activación.
- [ ] Confirmar el flyback y protección de sobrecorriente con el componente real.
- [ ] Validar el pinout físico del ESP32-S3 y RC522.
- [ ] Definir la fuente definitiva de 12 V con margen suficiente.
- [ ] Confirmar borneras y conectores con capacidad real de corriente.
- [ ] Documentar resultados y actualizar el informe de diseño.

## Criterio de pase para mandar a fabricar

Se considera que el diseño está listo solo cuando:

- la fuente de alimentación no cae durante la activación de la cerradura;
- el MOSFET no supera temperatura crítica;
- el RC522 funciona sin reinicios ni interferencia visible;
- los conectores y la mecánica están confirmados físicamente;
- el esquema y la documentación están alineados con los datos medidos.

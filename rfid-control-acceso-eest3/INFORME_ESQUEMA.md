# Informe técnico — Control de acceso RFID EEST3

Fecha: 2026-07-29  
Etapa: PCB prototipo Rev. A — transferencia y prelayout autorizados; ruteo no autorizado.

Datos físicos y comerciales disponibles:

- Marca publicada: Roa/Olipe SEB.
- Modelo publicado: 150.
- Tipo: cerradura eléctrica empotrable para portero eléctrico.
- Alimentación confirmada físicamente: 12 VCC.
- Consumo nominal confirmado: 1,8 A.
- Potencia nominal: 12 V × 1,8 A = 21,6 W.
- Fuente disponible: 12 VCC / 2,5 A (30 W).
- Pendientes: medición de corriente de arranque y comprobación térmica
  del MOSFET.

## Arquitectura implementada

El esquema se organizó jerárquicamente en seis bloques:

1. Alimentación y protección de 12 V, buck a 5 V y distribución de 3,3 V.
2. Controlador ESP32-S3-DevKitC-1 N16R8 de 44 pines representado mediante
   dos conectores funcionales de 1×22.
3. Lector RC522 representado mediante conector funcional de ocho vías.
4. Sensor reed, PIR opcional y entrada futura de sensor de gabinete.
5. LEDs de estado y buzzer con etapa MOSFET.
6. Etapa MOSFET canal N low-side para la cerradura inductiva de 12 VCC.

Las redes globales principales son `+12V_IN`, `+12V_LOCK`, `+5V`, `+3V3`
y `GND`. El RC522 solo está conectado a `+3V3`.

## Componentes

### Alimentación

- J1: entrada de 12 V.
- D1: protección serie Schottky, selección pendiente.
- F1: fusible lento o PTC de aproximadamente 2,5 A, valor preliminar;
  debe validarse después de medir la corriente de arranque.
- C1: 1000 µF / 25 V preliminar como reserva local de 12 V.
- C2: 100 nF preliminar.
- J2: interfaz funcional para módulo buck 12 V a 5 V.
- C3: 470 µF / 10 V preliminar en la salida de 5 V.
- C4: 100 nF preliminar.
- D5: TVS bidireccional para la línea de 12 V, selección pendiente.

### Controlador y RFID

- J13: representación unificada de 44 contactos (dos hileras de 22) del
  `ESP32_S3_DEVKITC1_N16R8_44PIN`, basada en el pinout del
  ESP32-S3-DevKitC-1. La equivalencia mecánica del clon YD-ESP32-S3 sigue
  pendiente de medición.
- C5: desacoplamiento de 100 nF preliminar.
- J5: interfaz funcional RC522; orden físico `PENDIENTE_DATASHEET`.
- C6: desacoplamiento de 100 nF preliminar.
- C9: reserva local de 10 µF preliminar.
- R9/R10/R11/R12: 33 Ω serie en `RFID_SS`, `RFID_SCK`, `RFID_MOSI` y
  `RFID_RST`, respectivamente.

### Sensores

- J6: reed de puerta, previsto para contacto normalmente cerrado.
- R1: pull-up 10 kΩ preliminar.
- C7: filtro 100 nF preliminar.
- J7: alimentación y contacto NC de alarma del DSC LC-100.
- J8: sensor óptico/de gabinete futuro.
- J10: contacto NC de tamper del DSC LC-100.
- R2: pull-up externo 10 kΩ para `CABINET_SENSOR` en GPIO6.
- D6: TVS para `DOOR_REED`, selección 3,3 V pendiente.
- D7: TVS preliminar sobre `PIR_CONTACT`; selección pendiente.
- D8: TVS para `CABINET_SENSOR`, selección 3,3 V pendiente.
- C8: filtro de 100 nF preliminar para `CABINET_SENSOR`.
- R13/R15: pull-ups externos de 10 kΩ para alarma y tamper.
- R14/R16: resistencias serie de 1 kΩ hacia GPIO5 y GPIO7.
- C10/C11: filtros de 100 nF desde `PIR_IN` y `PIR_TAMPER` a GND.

### Señalización

- R3/D2: LED verde con 330 Ω preliminar.
- R4/D3: LED rojo con 330 Ω preliminar.
- BZ1: `PENDIENTE_TIPO_BUZZER`.
- Q1, R5 y R6: driver MOSFET, 100 Ω serie y 10 kΩ pull-down.

### Cerradura

- J9: cerradura inductiva confirmada de 12 VCC, 1,8 A y 21,6 W.
- Q2: AO3400A preliminar, MOSFET canal N de nivel lógico.
- R7: 100 Ω en serie con el gate.
- R8: 10 kΩ entre gate y `GND_POWER`.
- D4: SS3A4 preliminar, Schottky de 3 A / 40 V.
- NT1: unión explícita en estrella entre `GND_POWER` y `GND`.

No hay footprints asignados.

## Presupuesto de alimentación de la placa

El consumo de la electrónica todavía es una estimación porque faltan la
revisión física exacta del clon ESP32-S3, PIR, buzzer y buck.

| Carga | Reserva estimada | Potencia aproximada |
|---|---:|---:|
| ESP32 DevKit, incluyendo picos de radio y regulador | 500 mA a 5 V | 2,50 W |
| RC522 y pérdidas de regulación asociadas | 50 mA a 3,3 V | 0,17 W |
| DSC LC-100 y sensores externos | consumo pendiente a 12 V | debe medirse |
| Dos LEDs | 20 mA total a 3,3 V | 0,07 W |
| Buzzer | 100 mA a 5 V | 0,50 W |
| Margen/pérdidas del buck | eficiencia supuesta 85 % | aproximadamente 0,6 W |

La electrónica de baja tensión demanda aproximadamente 0,4 A desde 12 V.
Sumada a la cerradura, la corriente nominal estimada es aproximadamente
2,2 A. La fuente de 12 VCC / 2,5 A puede utilizarse para el prototipo, pero
deja solamente unos 0,3 A de margen nominal y debe verificarse durante el
arranque y la activación de la cerradura.

Para la instalación definitiva se recomienda una fuente regulada de
12 V / 4 A o superior, con protección y respuesta transitoria apropiadas.

## Etapa principal de cerradura 12 VCC

La cerradura está conectada entre `+12V_LOCK` y `LOCK_OUT`.
El drain de Q2 se conecta a `LOCK_OUT`; el source, a `GND_POWER`.
`LOCK_GATE` llega al gate mediante R7 de 100 Ω y R8 mantiene el gate apagado
con 10 kΩ hacia `GND_POWER`.

D4 está conectado en paralelo con la carga inductiva: cátodo hacia
`+12V_LOCK` y ánodo hacia `LOCK_OUT`. La selección preliminar es SS3A4,
3 A / 40 V.

Q2 se mantiene preliminarmente como AO3400A. Usando 1,8 A y
`RDS(on) = 48 mΩ`, la disipación conductiva teórica es:

`P = I² × R = (1,8 A)² × 0,048 Ω ≈ 0,156 W`.

Este cálculo no sustituye la comprobación térmica, el análisis del
encapsulado ni la verificación de `RDS(on)` a la tensión de gate real.

## Protección de sobrecorriente

F1 queda preliminarmente como fusible lento o PTC de aproximadamente 2,5 A.
No debe utilizarse una protección rápida de 2 A porque podría actuar durante
el funcionamiento nominal. La elección definitiva depende de medir la
corriente de arranque y revisar la curva tiempo-corriente.

## Retornos y filtrado

El esquema distingue:

- `GND_POWER`: retorno de Q2, cerradura, TVS de alimentación y capacitores
  de 12 V;
- `GND`: retorno lógico de buck, ESP32, RC522, sensores y señalización;
- NT1 `STAR_GND`: única unión lógica entre ambos retornos, próxima a la
  entrada de alimentación.

La masa es común porque Q2 es controlado desde el ESP32. El retorno de
1,8 A de la cerradura debe mantenerse físicamente separado del retorno
lógico y unirse a éste solamente en NT1, cerca de la entrada de alimentación.

Filtrado preliminar:

- 1000 µF / 25 V más 100 nF sobre 12 V;
- 470 µF / 10 V más 100 nF sobre 5 V;
- 100 nF locales en ESP32 y RC522.

Los electrolíticos deben seleccionarse por ESR, ripple, temperatura y
tolerancia. Estos valores reducen transitorios breves pero no sustituyen una
fuente con margen ni una distribución de masa correcta.

## Controlador ESP32-S3

Controlador confirmado por la publicación:

- familia ESP32-S3;
- placa ESP32-S3-DevKitC-1 N16R8 o clon compatible YD-ESP32-S3;
- flash de 16 MB;
- PSRAM de 8 MB;
- 44 pines físicos, 22 por lado;
- representación temporal:
  `ESP32_S3_DEVKITC1_N16R8_44PIN`.

No se utiliza ningún símbolo ni pinout de ESP32-WROOM-32 clásico de 30 o
38 pines. No se asume que el clon tenga las dimensiones mecánicas de la
placa oficial.

Restricciones aplicadas:

- GPIO22, GPIO23, GPIO24 y GPIO25 no existen en ESP32-S3.
- GPIO26 a GPIO32 quedan excluidos por su relación con flash/PSRAM.
- GPIO33 a GPIO37 quedan excluidos por la PSRAM de la variante N16R8.
- GPIO0, GPIO3, GPIO45 y GPIO46 quedan excluidos por strapping.
- GPIO19 y GPIO20 quedan reservados para USB nativo.
- GPIO43 y GPIO44 quedan reservados para UART de diagnóstico.
- GPIO38 se evita porque puede controlar el LED RGB según la revisión.

Continúan como `PENDIENTE_MEDICIÓN`: separación entre hileras, dimensiones,
posición de ambos USB-C del clon, distancia de los pines al borde, botones y
orientación de la antena.

## Mapa GPIO

| Señal | GPIO | Uso |
|---|---:|---|
| RFID_SCK | 12 | salida SPI; R10 = 33 Ω |
| RFID_MISO | 13 | entrada SPI |
| RFID_MOSI | 11 | salida SPI; R11 = 33 Ω |
| RFID_SS | 10 | salida chip-select; R9 = 33 Ω |
| RFID_RST | 9 | salida reset; R12 = 33 Ω |
| DOOR_REED | 4 | entrada con pull-up externo |
| PIR_IN | 5 | entrada desde contacto NC, serie 1 kΩ y filtro 100 nF |
| CABINET_SENSOR | 6 | entrada con pull-up externo |
| PIR_TAMPER | 7 | entrada desde contacto NC, serie 1 kΩ y filtro 100 nF |
| LED_OK | 15 | salida |
| LED_ERROR | 16 | salida |
| BUZZER | 17 | salida hacia driver |
| LOCK_GATE | 18 | salida hacia driver |

## Sensor PIR DSC LC-100

El sensor confirmado es un DSC LC-100 alimentado desde `+12V_AUX` y GND.
La alimentación está separada conceptualmente de las señales de alarma y
tamper, que son contactos secos de relé normalmente cerrados.

La interfaz física quedó dividida en tres borneras independientes:

- J11 `PIR_PWR`: pin 1 a `+12V_AUX`, pin 2 a GND;
- J12 `PIR_ALARM`: pin 1 COM a GND, pin 2 NC a `PIR_CONTACT`;
- J10 `PIR_TAMPER`: pin 1 T1 a `PIR_TAMPER_CONTACT`, pin 2 T2 a GND.

Contacto de alarma:

- COM a GND;
- NC a `PIR_CONTACT`;
- R13 de 10 kΩ entre `PIR_CONTACT` y `+3V3`;
- R14 de 1 kΩ entre `PIR_CONTACT` y `PIR_IN`;
- C10 de 100 nF entre `PIR_IN` y GND.

En estado normal el contacto está cerrado y GPIO5 permanece en nivel bajo.
Una alarma, corte del cable o desconexión abre el circuito y el pull-up lleva
GPIO5 a nivel alto.

Contacto tamper:

- un terminal a GND;
- otro terminal a `PIR_TAMPER_CONTACT`;
- R15 de 10 kΩ entre `PIR_TAMPER_CONTACT` y `+3V3`;
- R16 de 1 kΩ entre `PIR_TAMPER_CONTACT` y `PIR_TAMPER`;
- C11 de 100 nF entre `PIR_TAMPER` y GND.

La rama `+12V_AUX` se deriva de `+12V_LOCK` mediante F2
`AUX_PROTECTION_PENDING`. Para el DSC LC-100 solo quedan pendientes la
numeración física exacta de sus borneras, la medición del cableado y la
ubicación física del sensor.

## RC522

El conector funcional J5 representa, en este orden lógico:

1. `RFID_SS`
2. `RFID_SCK`
3. `RFID_MOSI`
4. `RFID_MISO`
5. `RFID_IRQ`, marcado explícitamente No Connect
6. `GND`
7. `RFID_RST`
8. `+3V3`

Este orden no autoriza fabricar un conector físico. Debe verificarse el módulo
real y su datasheet antes de asignar footprint.

## Datos pendientes

- Capacidad de corriente disponible en 3,3 V de la revisión física del
  ESP32-S3 DevKit/clon.
- Correspondencia física final del clon YD-ESP32-S3 con los headers oficiales.
- Pinout físico exacto del módulo RC522.
- Modelo del buck y disposición de terminales.
- Medir la corriente de arranque de la cerradura.
- Comprobar térmicamente Q2 en las condiciones reales de activación.
- Confirmar la `RDS(on)` del AO3400A a la tensión de gate real del ESP32.
- Curva exacta del fusible lento o PTC de placa.
- Numeración física exacta de las borneras del DSC LC-100.
- Medición del cableado del DSC LC-100.
- Ubicación física del DSC LC-100.
- Tipo, tensión y corriente del buzzer; necesidad de diodo si fuera inductivo.

## Lista de comprobación física previa a footprints

Estados utilizados:

- `CONFIRMADO`: dato físico disponible y utilizable.
- `PENDIENTE_MEDICIÓN`: requiere medir el ejemplar real o el montaje.
- `PENDIENTE_MODELO`: requiere seleccionar o identificar el componente y
  consultar su documentación.

No debe asignarse ningún footprint hasta completar los datos aplicables de
esta lista.

Conteo verificado de filas de comprobación —sin contar la leyenda de
estados—:

- 10 `CONFIRMADO`.
- 24 `PENDIENTE_MEDICIÓN`.
- 21 `PENDIENTE_MODELO`.
- Total: **55 verificaciones**.

El conteo anterior de 7, 25 y 26 incluía una vez adicional cada estado por
su aparición en la leyenda. No se encontraron filas duplicadas y no se
eliminó ninguna verificación válida.

| Estado | Bloque | Dato físico o eléctrico | Criterio de aceptación / acción requerida |
|---|---|---|---|
| `CONFIRMADO` | ESP32-S3 DevKit | Familia y variante objetivo | ESP32-S3-DevKitC-1 N16R8 o clon YD-ESP32-S3 compatible; 16 MB flash y 8 MB PSRAM. |
| `CONFIRMADO` | ESP32-S3 DevKit | Cantidad de pines | 44 pines, 22 por hilera. |
| `PENDIENTE_MEDICIÓN` | ESP32-S3 DevKit | Separación entre hileras | Medir entre centros con calibre; no asumir la dimensión oficial para el clon. |
| `PENDIENTE_MEDICIÓN` | ESP32-S3 DevKit | Paso de pines | Medir y contrastar con el módulo físico antes de crear el footprint. |
| `PENDIENTE_MEDICIÓN` | ESP32-S3 DevKit | Largo, ancho y altura máxima | Medir placa, componentes salientes y conectores montados. |
| `PENDIENTE_MEDICIÓN` | ESP32-S3 DevKit | USB, botones y antena | Medir ambos USB-C del clon, EN, BOOT, orientación de antena y distancias a bordes. |
| `CONFIRMADO` | ESP32-S3 DevKit | Pinout lógico de referencia | J3/J4 representan los headers J1/J3 del DevKitC-1 oficial; validar continuidad contra el clon físico antes de PCB. |
| `PENDIENTE_MEDICIÓN` | RC522 | Orden real del conector | Verificar continuidad y serigrafía pin por pin; el orden lógico de J5 no define el orden físico. |
| `PENDIENTE_MEDICIÓN` | RC522 | Paso, posición y orientación | Medir conector, distancia a bordes y sentido de inserción. |
| `PENDIENTE_MEDICIÓN` | RC522 | Dimensiones y agujeros | Medir largo, ancho, altura y centros de fijación del módulo real. |
| `PENDIENTE_MODELO` | RC522 | Zona de exclusión de antena | Obtener la recomendación del fabricante sobre cobre, planos de masa, metal y batería/cerradura. |
| `PENDIENTE_MEDICIÓN` | RC522 | Separación en el montaje | Validar experimentalmente lectura RFID con la antena alejada de cobre, cableado de 1,8 A, MOSFET, buck y cerradura. |
| `PENDIENTE_MODELO` | Buck | Modelo exacto | Seleccionar módulo o regulador y conseguir plano mecánico y datasheet. |
| `PENDIENTE_MODELO` | Buck | Entrada, salida y polaridad | Confirmar rango de entrada, tensión de salida regulada a 5 V y orden real de terminales. |
| `PENDIENTE_MEDICIÓN` | Buck | Dimensiones y altura | Medir PCB, componentes, inductor, disipador, potenciómetro y agujeros. |
| `PENDIENTE_MEDICIÓN` | Buck | Terminales | Medir paso, posición, orientación y acceso para ajuste o cableado. |
| `PENDIENTE_MODELO` | Buck | Capacidad de corriente | Debe cubrir la electrónica con picos de radio y margen térmico; objetivo mínimo recomendado: 5 V / 1 A continuo, sujeto al consumo real. |
| `CONFIRMADO` | MOSFET Q2 | Corriente nominal de carga | 1,8 A con la cerradura activada. |
| `CONFIRMADO` | MOSFET Q2 | Cálculo conductivo preliminar | Para 48 mΩ: `(1,8 A)² × 0,048 Ω ≈ 0,156 W`. |
| `PENDIENTE_MODELO` | MOSFET Q2 | AO3400A y fabricante | Verificar datasheet del fabricante concreto, `VDS`, corriente, SOA y `RDS(on)` garantizada con `VGS` de 2,5 V o compatible con 3,3 V. No aceptar únicamente el dato a 10 V. |
| `PENDIENTE_MEDICIÓN` | MOSFET Q2 | Gate real | Medir la tensión de gate en nivel alto con el ESP32 y la etapa funcionando. |
| `PENDIENTE_MEDICIÓN` | MOSFET Q2 | Temperatura | Medir temperatura ambiente y elevación de Q2 durante el peor tiempo de activación. |
| `PENDIENTE_MEDICIÓN` | MOSFET Q2 | Cobre disponible | Definir área de cobre, vías térmicas y espesor de cobre antes de validar SOT-23. |
| `PENDIENTE_MODELO` | MOSFET Q2 | Alternativa térmica | Comparar AO3400A SOT-23 con un MOSFET lógico en SO-8 térmico, PowerPAK/LFPAK o DPAK; elegir por `RDS(on)` a gate real, SOA, disipación, disponibilidad y montaje educativo. |
| `PENDIENTE_MEDICIÓN` | MOSFET Q2 | Transitorios | Medir `VDS` durante apertura y cierre; mantener margen respecto de la tensión máxima del dispositivo. |
| `CONFIRMADO` | Gate Q2 | Red de control | R7 = 100 Ω y R8 = 10 kΩ pull-down. |
| `CONFIRMADO` | Flyback D4 | Requisitos preliminares | Schottky de al menos 3 A y 40 V; cátodo a `+12V_LOCK`, ánodo a `LOCK_OUT`. |
| `PENDIENTE_MODELO` | Flyback D4 | SS3A4 exacto | Confirmar fabricante, código completo, corriente media, corriente de pulso, tensión inversa, fuga y curva térmica. |
| `PENDIENTE_MODELO` | Flyback D4 | Encapsulado | Confirmar encapsulado y dimensiones reales; el nombre comercial no autoriza asumir SMA/SMB. |
| `PENDIENTE_MEDICIÓN` | Flyback D4 | Régimen térmico | Comprobar temperatura y energía por maniobra con la corriente y frecuencia reales. |
| `PENDIENTE_MEDICIÓN` | Flyback D4 | Ubicación física | Reservar ubicación inmediatamente junto a J9 y al lazo de corriente de la cerradura; minimizar el área del lazo. |
| `CONFIRMADO` | Protección | Fuente de prototipo | 12 VCC / 2,5 A; utilizable para el prototipo con margen nominal limitado. |
| `CONFIRMADO` | Protección | Fuente definitiva recomendada | Fuente regulada de 12 V / 4 A o superior. |
| `PENDIENTE_MEDICIÓN` | Protección | Corriente de arranque | Medir pico, duración y repetibilidad antes de fijar fusible o PTC. |
| `PENDIENTE_MODELO` | Protección | Fusible lento | Comparar corriente nominal, curva tiempo-corriente, poder de corte, tensión máxima y portafusible. |
| `PENDIENTE_MODELO` | Protección | PTC | Comparar corriente de mantenimiento, corriente de disparo, tensión máxima, resistencia fría/caliente y tiempo de recuperación. |
| `PENDIENTE_MODELO` | Protección | Separación por ramas | Proponer una protección para la electrónica después de la derivación y otra para `+12V_LOCK`; sus valores se eligen después de medir consumos y arranque. |
| `PENDIENTE_MODELO` | Conectores de potencia | Corriente nominal | J1 y J9 deben superar la corriente continua y de arranque con margen; objetivo preliminar mínimo 5 A por contacto. |
| `PENDIENTE_MODELO` | Conectores de potencia | Paso y cable | Seleccionar paso, sección admitida, temperatura, tensión y sistema de tornillo/resorte según el cable real. |
| `PENDIENTE_MODELO` | Conectores | Polaridad y retención | Elegir conectores polarizados o rotulado inequívoco; definir punteras, terminales y alivio de tracción. |
| `PENDIENTE_MEDICIÓN` | Conectores | Separación física | Definir distancia entre potencia, señales, antena y bordes; evitar recorridos paralelos largos entre `LOCK_OUT` y sensores. |
| `PENDIENTE_MODELO` | Reed | Modelo físico | Confirmar contacto NC, corriente/tensión de contacto, cable, carcasa, fijación y conector. |
| `CONFIRMADO` | PIR DSC LC-100 | Modelo e interfaz | Alimentación a 12 V y contactos secos NC independientes para alarma y tamper; no es una salida electrónica de 5 V. |
| `PENDIENTE_MEDICIÓN` | PIR DSC LC-100 | Instalación física | Confirmar numeración de borneras, medir cableado y definir ubicación física. |
| `PENDIENTE_MODELO` | Sensor de gabinete | Modelo físico | Confirmar tipo de salida, tensión, consumo, cable y conector. |
| `PENDIENTE_MODELO` | Buzzer | Tipo físico | Confirmar activo/pasivo, tensión, corriente, polaridad, diámetro, altura, paso y necesidad de diodo. |
| `PENDIENTE_MODELO` | LEDs | Formato | Elegir THT/SMD, color, corriente objetivo, polaridad, dimensiones y visibilidad a través de la caja. |
| `PENDIENTE_MODELO` | Capacitores | Tecnología y tensión | Confirmar electrolíticos de 1000 µF/25 V y 470 µF/10 V, ESR, ripple y temperatura; revisar margen de tensión. |
| `PENDIENTE_MEDICIÓN` | Capacitores | Geometría | Medir diámetro, altura y paso; comprobar polaridad y espacio de montaje. |
| `PENDIENTE_MODELO` | Capacitores | Cerámicos | Elegir encapsulado, tensión, dieléctrico y tolerancia para los 100 nF. |
| `PENDIENTE_MEDICIÓN` | Mecánica | Dimensiones de placa | Definir largo, ancho, altura máxima y zonas prohibidas de la caja. |
| `PENDIENTE_MEDICIÓN` | Mecánica | Fijación | Definir cantidad, diámetro, posición y despeje de agujeros, separadores y tornillos. |
| `PENDIENTE_MODELO` | Mecánica | Caja | Seleccionar material, ventilación, grado de protección, acceso de mantenimiento y puesta a tierra si correspondiera. |
| `PENDIENTE_MEDICIÓN` | Mecánica | Acceso | Validar acceso a USB, botones, fusible, buck, conectores y tornillos sin desmontaje peligroso. |
| `PENDIENTE_MEDICIÓN` | Mecánica/RFID | Separación funcional | Ensayar distancia entre antena RC522, etapa MOSFET, buck, cableado de cerradura y cualquier pieza metálica de la caja. |

### Evaluación del MOSFET

- El IRFZ44N queda descartado para control directo desde un GPIO de 3,3 V.
- Su `RDS(on)` está garantizada únicamente con `VGS = 10 V`.
- Su `VGS(th)` de 2 a 4 V indica solamente el comienzo de conducción y no
  representa plena conducción ni baja resistencia para manejar 1,8 A.
- Solo podría utilizarse con un driver de gate que entregue aproximadamente
  10 V, lo que agregaría componentes y complejidad innecesarios.
- Se mantiene el AO3400A como selección preliminar mientras se evalúa una
  alternativa logic-level de encapsulado mayor, con `RDS(on)` garantizada a
  una tensión compatible con el GPIO de 3,3 V.

### Relevamiento físico necesario

| Componente | Marca/modelo | Foto frontal | Foto posterior | Largo | Ancho | Altura | Paso entre pines | Separación entre hileras | Orden físico de pines | Tensión | Corriente | Estado de confirmación |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |  |  |  |

### Tratamiento propuesto de las advertencias ERC

- `RFID_IRQ`: IRQ no se utiliza y el pin 5 de J5 quedó marcado
  explícitamente como No Connect.
- `PIR_IN`: la advertencia quedó resuelta mediante el contacto seco NC del
  DSC LC-100, R13/R14 y C10.
- `PIR_TAMPER`: contacto seco NC supervisado mediante R15/R16 y C11.
- No se agregaron exclusiones para ocultar advertencias.

## ERC

Comando: `kicad-cli sch erc`

Resultado final (2026-07-29 07:36:26): **0 errores y 0 advertencias**.

No quedan advertencias aceptadas. `RFID_IRQ` está marcado No Connect y las
dos entradas del DSC LC-100 están conectadas mediante sus respectivas redes
de pull-up, protección serie y filtrado.

No se agregaron exclusiones individuales ni `PWR_FLAG` innecesarios. KiCad
informó como clases de comprobación ignoradas por la configuración:
`Global label only appears once in the schematic`,
`Four connection points are joined together`, `SPICE model issue` y
`Assigned footprint doesn't match footprint filters`. No se modificó esa
configuración durante esta actualización.

## Riesgos eléctricos

- Una numeración incorrecta de las borneras del LC-100 podría intercambiar
  alimentación y contactos; debe verificarse físicamente antes de energizar.
- La corriente de arranque aún desconocida puede producir caídas de tensión
  o disparar la protección.
- La fuente disponible deja solamente unos 0,3 A de margen nominal después
  de sumar la cerradura y la estimación de la electrónica.
- La disipación calculada de Q2 no incluye transitorios ni aumento de
  `RDS(on)` por temperatura.
- El retorno de 1,8 A puede reiniciar o perturbar al ESP32 si no se respeta
  la separación física y la unión en estrella.
- La salida de 3,3 V del DevKit debe verificarse antes de alimentar el RC522.
- Los TVS agregados son topologías preliminares: tensión de trabajo, clamp,
  energía, fuga y capacitancia deben seleccionarse con los cables y módulos reales.

## Preparación de footprints y fabricación

La PCB continúa vacía y no se ejecutó **Update PCB from Schematic**. En el
esquema solamente se asignó `Package_TO_SOT_SMD:SOT-23` a Q1 y Q2 después de
verificar el pinout; las borneras permanecen sin footprint. Los nombres se verificaron contra el
índice de footprints de KiCad 10, sincronizado el 2026-07-29: 155 bibliotecas y
15 447 footprints.

Estados:

- `CONFIRMADO`: componente físico y encapsulado suficientemente definidos.
- `PRELIMINAR`: footprint existente y eléctricamente plausible, pendiente de
  comparación con el componente comprado.
- `PENDIENTE_MEDICIÓN`: no debe asignarse hasta medir o identificar el modelo.

| Referencia | Componente | Valor | Footprint propuesto | Estado | Corriente o tensión relevante | Observaciones de montaje | Riesgo de pinout incorrecto |
|---|---|---|---|---|---|---|---|
| R1–R17 | Resistencias THT | 33 Ω, 100 Ω, 330 Ω, 1 kΩ y 10 kΩ según referencia | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | PRELIMINAR | 3,3 V/5 V; R7 es serie de gate | DIN0207, 0,25 W, cuerpo 6,3 × 2,5 mm y paso 10,16 mm; confirmar potencia y tamaño real | Bajo: componente no polarizado |
| C2, C4–C8, C10, C11 | Cerámicos THT | 100 nF | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | PRELIMINAR | Confirmar tensión nominal; C2/C4 están en alimentación | Disco 5 × 2,5 mm y paso 5 mm; comparar con el lote comprado | Bajo: no polarizado |
| C1 | Electrolítico radial | 1000 µF / 25 V preliminar | Radial THT por definir | PENDIENTE_MEDICIÓN | 25 V mínimo indicado; entrada de 12 V | Medir diámetro, altura, paso, ESR y ripple; respetar polaridad | Alto si se invierte polaridad o se asume el paso |
| C3 | Electrolítico radial | 470 µF / 10 V preliminar | Radial THT por definir | PENDIENTE_MEDICIÓN | 10 V mínimo indicado; salida de 5 V | Medir diámetro, altura, paso, ESR y ripple; respetar polaridad | Alto si se invierte polaridad o se asume el paso |
| C9 | Capacitor local RC522 | 10 µF preliminar | Radial THT o cerámico por definir | PENDIENTE_MEDICIÓN | 3,3 V | Definir tecnología, polaridad, diámetro/encapsulado y paso | Medio |
| D2, D3 | LED verde/rojo | 5 mm | `LED_THT:LED_D5.0mm` | PRELIMINAR | Corriente limitada por R3/R4 de 330 Ω | Paso 2,54 mm; orientar cara plana/cátodo y asegurar visibilidad desde la caja | Alto si se intercambian A/K |
| Q2 | MOSFET de cerradura | AO3400A preliminar | `Package_TO_SOT_SMD:SOT-23`, asignado al esquema | PRELIMINAR | 12 V, 1,8 A; disipación conductiva teórica ≈0,156 W | Datasheet oficial AOS y símbolo verificados: 1=G, 2=S, 3=D. Validar térmicamente el SOT-23 | Crítico si se compra una variante con pinout diferente |
| Q2 alternativa | MOSFET logic-level reparable | Modelo TO-220 pendiente | `Package_TO_SOT_THT:TO-220-3_Vertical` | PENDIENTE_MEDICIÓN | ≥30 V, ≥5 A y `RDS(on)` garantizada a 2,5/3,3 V | Alternativa para montaje, disipación y reparación; no reemplaza al AO3400A sin aprobación | Crítico: seleccionar modelo real y verificar G-D-S |
| — | MOSFET descartado | IRFZ44N | No asignar | CONFIRMADO | No garantiza conducción adecuada con gate de 3,3 V | Solo sería utilizable con driver de gate cercano a 10 V | Crítico si se conecta directamente al GPIO |
| D4 | Flyback de cerradura | SS3A4, 3 A / 40 V preliminar | `Diode_SMD:D_SMA` | PRELIMINAR | Pulso inicial de al menos 1,8 A | SMA/DO-214AC; colocar junto a J9; pad 1 es K y pad 2 es A en el esquema actual | Alto: confirmar encapsulado SS3A4 y polaridad física |
| Q1 | Driver de buzzer NMOS | AO3400A preliminar | `Package_TO_SOT_SMD:SOT-23`, asignado al esquema | PRELIMINAR | Buzzer a +5 V; corriente pendiente | GPIO17 → R5 100 Ω → gate; R6 10 kΩ gate-source; source a GND; drain al negativo de BZ1. Datasheet oficial AOS y símbolo verificados: 1=G, 2=S, 3=D | Crítico si se adapta por apariencia en vez de verificar pads |
| D9 | Protección opcional del buzzer | `DNP_HASTA_CONFIRMAR_TIPO_BUZZER` | Sin footprint hasta confirmar el buzzer | PENDIENTE_MEDICIÓN | Cátodo a +5 V; ánodo al drain/negativo del buzzer | Montar solamente si BZ1 es magnético/inductivo. Un piezoeléctrico normalmente no requiere flyback | Alto: tipo y polaridad pendientes |
| BZ1 | Buzzer THT | `BUZZER?` | `Buzzer_Beeper:Buzzer_12x9.5RM7.6` | PRELIMINAR | 5 V; consumo pendiente | Diámetro 12 mm, altura 9,5 mm y paso 7,6 mm; confirmar buzzer activo/pasivo, tensión y polaridad | Alto si polarizado o si el paso no coincide |
| J1 | Entrada de alimentación | 12 VCC / 2,5 A prototipo | Bornera THT 1×2, paso 5,08 mm, modelo ≥5 A por definir | PENDIENTE_MEDICIÓN | Mínimo 5 A por contacto solicitado | Los alias `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` no existen en las bibliotecas KiCad 10 instaladas; elegir footprint del fabricante comprado | Alto: dimensiones, taladro y orientación |
| J9 | Cerradura | 12 VCC / 1,8 A | Bornera THT 1×2, paso 5,08 mm, modelo ≥5 A por definir | PENDIENTE_MEDICIÓN | Mínimo 5 A por contacto solicitado | Preferir bornera con margen térmico, cable adecuado y acceso frontal; ubicar D4 junto a ella | Alto: polaridad y capacidad real |
| J6, J8 | Reed y gabinete | Contactos externos | Bornera THT, paso esperado 5,08 mm, modelo por definir | PENDIENTE_MEDICIÓN | Señales de 3,3 V y GND | Separar físicamente de J1/J9 y del lazo de cerradura; confirmar sección de cable | Medio |
| J10 | DSC LC-100 tamper | `PIR_TAMPER`, T1/T2 | Bornera THT 1×2, paso esperado 5,08 mm, sin asignar | PENDIENTE_MEDICIÓN | Contacto seco con pull-up a 3,3 V | T1 a `PIR_TAMPER_CONTACT`; T2 a GND | Alto: numeración física pendiente |
| J11 | DSC LC-100 alimentación | `PIR_PWR` | Bornera THT 1×2, paso esperado 5,08 mm, sin asignar | PENDIENTE_MEDICIÓN | +12V_AUX y GND | Conector independiente de las señales | Alto: polaridad y numeración física |
| J12 | DSC LC-100 alarma | `PIR_ALARM`, COM/NC | Bornera THT 1×2, paso esperado 5,08 mm, sin asignar | PENDIENTE_MEDICIÓN | Contacto seco con pull-up a 3,3 V | COM a GND; NC a `PIR_CONTACT`; conserva lógica fail-safe | Alto: identificar COM/NC físicamente |
| J2 | Módulo buck externo | `BUCK?` | Sin footprint de LM2596; interfaz de borneras por definir | PENDIENTE_MEDICIÓN | Entrada 12 V, salida 5 V/GND; capacidad mínima recomendada 1 A | Mantener módulo fuera de la PCB. Confirmar si J2 será una bornera de cuatro polos o dos borneras de dos polos y el orden físico | Alto |
| J3, J4 | Zócalos ESP32-S3 | 22 pines por lado | Dos `Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical` | PENDIENTE_MEDICIÓN | 5 V, 3,3 V y GPIO | Footprint de cada hilera verificado: 22 pads, paso 2,54 mm y largo entre centros 53,34 mm. Usar headers hembra y módulo removible | Crítico: separación entre hileras, orientación y correspondencia J3/J4 |
| J5 | RC522 externo | Header 1×8 | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` | PRELIMINAR | Exclusivamente 3,3 V | 8 pads, paso 2,54 mm y 17,78 mm entre centros extremos; usar cable corto o header y verificar orden real del módulo | Crítico: el orden físico del RC522 sigue pendiente |
| D1 | Protección de polaridad | `SCHOTTKY?` | Por definir con el componente | PENDIENTE_MEDICIÓN | Debe soportar la corriente total y la tensión inversa | Seleccionar encapsulado por corriente, caída y disipación; no asumir diodo axial pequeño | Alto: A/K |
| D5 | TVS de entrada | `TVS_12V?` | Por definir con el componente | PENDIENTE_MEDICIÓN | Entrada 12 V y transitorios | Definir VRWM, potencia de pulso, encapsulado y polaridad si es unidireccional | Alto |
| D6, D8 | Protección de sensores | `TVS_3V3?` | Por definir con el componente | PENDIENTE_MEDICIÓN | Entradas GPIO de 3,3 V | Seleccionar baja fuga y capacitancia adecuada; colocar cerca de conectores | Alto |
| D7 | Protección PIR | `TVS_CONTACT_PENDING` | Por definir con el componente | PENDIENTE_MEDICIÓN | Contacto seco con pull-up de 3,3 V | Seleccionar tensión de trabajo y fuga compatibles con la entrada | Alto |
| F1 | Protección principal | `2.5A_SLOW_OR_PTC_PRELIM` | Portafusible o PTC por definir | PENDIENTE_MEDICIÓN | Corriente de arranque de cerradura aún pendiente | Elegir después de medir pico y curva; comprobar tensión, poder de corte y temperatura | Medio |
| F2 | Protección auxiliar | `AUX_PROTECTION_PENDING` | Portafusible o PTC por definir | PENDIENTE_MEDICIÓN | Consumo DSC LC-100 y rama AUX pendiente | Protección independiente de electrónica/sensor; seleccionar con el consumo real | Medio |
| NT1 | Unión estrella de masas | `STAR_GND` | `NetTie:NetTie-2_THT_Pad1.0mm` como opción documental | PRELIMINAR | Retorno de cerradura de 1,8 A | La geometría final debe imponer unión única cerca de la entrada; revisar si un net-tie THT es adecuado para la corriente | Medio |

### Decisiones mecánicas previas a PCB

| Decisión | Estado | Criterio antes de asignar footprints |
|---|---|---|
| Modelo físico de cada bornera | PENDIENTE_MEDICIÓN | Fabricante, código, corriente nominal, paso real, taladro, tamaño, orientación de entrada del cable y sección admitida |
| Borneras J1/J9 | PENDIENTE_MEDICIÓN | Certificar al menos 5 A por contacto; no aceptar el paso 5,08 mm como prueba suficiente de corriente |
| Interfaz DSC LC-100 | PENDIENTE_MEDICIÓN | Tres conectores de dos polos ya separados lógicamente: J11 alimentación, J12 alarma y J10 tamper. Falta confirmar numeración física |
| ESP32-S3 removible | PENDIENTE_MEDICIÓN | Medir paso, separación entre hileras, largo/ancho, voladizo, USB-C, botones, antena y orientación de pin 1 |
| RC522 externo | PENDIENTE_MEDICIÓN | Confirmar pin 1, paso y cable; definir soporte mecánico y zona sin cobre/metal alrededor y debajo de la antena |
| Zona RFID | PENDIENTE_MEDICIÓN | Definir distancia experimental a PCB, planos de masa, buck, MOSFET, cable de 1,8 A, cerradura y piezas metálicas |
| Buck externo | PENDIENTE_MEDICIÓN | Modelo, capacidad térmica, bornes IN/OUT, orden, acceso al ajuste y fijación fuera de la PCB principal |
| Q2 SOT-23 | PENDIENTE_MEDICIÓN | Validar mapa G-S-D, temperatura ambiente, cobre disipador, pulsos de cerradura y transitorios VDS |
| Alternativa Q2 TO-220 | PENDIENTE_MEDICIÓN | Elegir MOSFET logic-level real con `RDS(on)` garantizada a 2,5/3,3 V; confirmar G-D-S y método de fijación/disipador |
| Driver de buzzer Q1 | PRELIMINAR | AO3400A confirmado como selección común con Q2; footprint SOT-23 y orden 1=G, 2=S, 3=D verificados. Falta confirmar corriente y tipo del buzzer |
| Capacitores electrolíticos | PENDIENTE_MEDICIÓN | Medir diámetro, altura, paso y polaridad; verificar ESR, ripple y temperatura |
| Caja y placa | PENDIENTE_MEDICIÓN | Dimensiones máximas, agujeros, separadores, ventilación y acceso seguro a fusibles, USB y terminales |
| Separación potencia/lógica | PENDIENTE_MEDICIÓN | Reservar recorridos y retornos separados, unión estrella y distancia entre conectores de potencia y señales |
| Protección ESD/cables externos | PENDIENTE_MEDICIÓN | Seleccionar TVS con datos reales de cableado; ubicar protección en la entrada física de cada conector |

### Buzzer y protección opcional

## Plan de depuración inmediato para la rama claude

El objetivo de esta fase es convertir el esquema actual en un prototipo mejor validado antes de avanzar a una PCB de prueba.

1. Medir corriente de arranque y consumo estacionario de la cerradura de 12 V.
2. Validar el MOSFET y el flyback con margen térmico real y con la carga inductiva instalada.
3. Confirmar que la fuente de 12 V tenga margen suficiente para la cerradura y la electrónica simultáneamente.
4. Ajustar la ruta de retorno y la separación entre potencia y lógica para reducir ruido y caídas de tensión.
5. Verificar físicamente el pinout del ESP32-S3, el módulo RC522 y todas las borneras antes de asignar footprints finales.
6. Usar la checklist de depuración pre-PCB como gate de avance: [CHECKLIST_PREPCB.md](CHECKLIST_PREPCB.md).

Este plan es prioritario porque el mayor riesgo actual no está en el ERC, sino en la validación de potencia, protección y montaje físico.

Q1 permanece como MOSFET N-channel AO3400A, controlado directamente desde
`BUZZER`/GPIO17 mediante R5 de 100 Ω. R6 de 10 kΩ mantiene el gate apagado;
source va a GND, drain al terminal negativo de BZ1 y el positivo de BZ1 a
`+5V`. El mismo AO3400A se utiliza preliminarmente en Q1 y Q2 para simplificar
la BOM.

D9 está conectado en antiparalelo con BZ1, con cátodo a `+5V` y ánodo al
drain, pero su valor es `DNP_HASTA_CONFIRMAR_TIPO_BUZZER`:

- un buzzer magnético puede necesitar protección flyback;
- un buzzer piezoeléctrico normalmente no necesita ese diodo;
- el driver MOSFET sirve para buzzer activo o pasivo, pero el firmware será
  nivel fijo/intermitente para uno activo y PWM/tono para uno pasivo.

No debe sustituirse Q1 por 2N2222A.

### Requisitos y candidatas de borneras

Todas las borneras azules permanecen sin footprint. Se espera un paso de
5,08 mm, pero antes de asignar debe medirse:

- diámetro o sección de los pines;
- ancho y profundidad del cuerpo;
- distancia necesaria al borde de placa;
- orientación y acceso al tornillo;
- sección de cable admisible.

J1 y J9 deben soportar al menos 5 A por contacto. Las borneras de sensores
pueden tener una corriente nominal menor.

Candidatas verificadas en la biblioteca KiCad 10, todavía sin asignar:

| Candidata | Biblioteca completa | Datos de biblioteca | Estado |
|---|---|---|---|
| TB007-508-02 | `TerminalBlock_CUI:TerminalBlock_CUI_TB007-508-02_1x02_P5.08mm_Horizontal` | 2 polos, 10,8 × 10,2 mm, taladro 1,6 mm | PENDIENTE_MEDICIÓN |
| TB007-508-03 | `TerminalBlock_CUI:TerminalBlock_CUI_TB007-508-03_1x03_P5.08mm_Horizontal` | 3 polos, 15,8 × 10,2 mm, taladro 1,6 mm | PENDIENTE_MEDICIÓN |
| MKDS-1,5-2-5.08 | `TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal` | 2 polos, 10,2 × 9,8 mm, taladro 1,3 mm | PENDIENTE_MEDICIÓN |

Si ninguna coincide con la bornera física, se preparará posteriormente la
biblioteca local `rfid_eest3.pretty`. No se descargará ni copiará ningún
footprint sin contrastar primero todas las medidas.

### Estado de la PCB antes de transferencia

- Footprints: **0**.
- Redes: **0**.
- Segmentos/pistas: **0**.
- Vías: **0**.
- Zonas de cobre: **0**.
- Keepouts: **0**.
- Contorno de placa: no definido.
- `Update PCB from Schematic`: **no ejecutado**.

## PCB prototipo Rev. A — footprints y prelayout

Rama Git: `pcb-rev-a-prelayout`.

La transferencia desde el esquema fue ejecutada de forma controlada. No se
modificaron conexiones, redes, GPIO ni valores eléctricos. La placa supone
provisionalmente FR4 de 1,6 mm, dos capas (`F.Cu` y `B.Cu`) y cobre de 1 oz.
El espesor de cobre continúa siendo un requisito documental hasta definir el
fabricante.

### Auditoría de footprints aplicada

| Referencia | Valor / componente | Footprint aplicado o propuesto | Estado | Pinout comprobado | Riesgo mecánico y observaciones |
|---|---|---|---|---|---|
| R1–R17 | Resistencias THT 1/4 W | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal` | CONFIRMADO | Sí, pads 1–2 | Confirmar potencia y diámetro reales antes de comprar |
| C2, C4–C8, C10, C11 | 100 nF THT | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` | PRELIMINAR_REV_A | Sí | Verificar ancho y paso del capacitor adquirido |
| D2, D3 | LED THT 5 mm | `LED_THT:LED_D5.0mm` | PRELIMINAR_REV_A | Sí: pad 1 cátodo, pad 2 ánodo | Verificar polaridad física y altura |
| Q1, Q2 | AO3400A | `Package_TO_SOT_SMD:SOT-23` | PRELIMINAR_REV_A | Sí: 1=G, 2=S, 3=D | Q2 requiere ensayo térmico a 1,8 A y área de cobre; prever revisión robusta |
| D4 | SS3A4 3 A / 40 V | `Diode_SMD:D_SMA` | PRELIMINAR_REV_A | Sí: cátodo a `+12V_LOCK`, ánodo a `LOCK_OUT` | Confirmar encapsulado y banda; colocar junto a J9 |
| D9 | DNP según tipo de buzzer | `Diode_THT:D_DO-35_SOD27_P10.16mm_Horizontal` | PRELIMINAR_REV_A | Sí: pad 1=K | No montar hasta confirmar buzzer |
| BZ1 | Buzzer | `Buzzer_Beeper:Buzzer_12x9.5RM7.6` | PRELIMINAR_REV_A | Sí | Confirmar tipo, tensión, polaridad, altura y paso |
| J5 | RC522 externo | `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical` | PRELIMINAR_REV_A | Sí, orden lógico 1–8 documentado | Verificar orientación física antes de conectar |
| J13 | ESP32-S3 DevKitC-1 N16R8 44P | `rfid_eest3:ESP32-S3-DevKitC-1-44P_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | Sí, 44 pads unificados | Separación entre hileras usada: 25,4 mm provisional; no fabricar |
| J1, J6, J9–J12 | Borneras 2P 5,08 | `rfid_eest3:KF301_2P_P5.08_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | Sí | Medir cuerpo, pin, tornillo y taladro; J1/J9 ≥5 A |
| J8 | Bornera 3P 5,08 | `rfid_eest3:KF301_3P_P5.08_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | Sí | Medición física obligatoria |
| J2 | Bornera 4P 5,08 | `rfid_eest3:KF301_4P_P5.08_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | Sí | Interfaz del buck externo; medición física obligatoria |
| C1 | 1000 µF / 25 V | `rfid_eest3:CP_Radial_D16_P7.50_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | Sí, polarizado | Confirmar diámetro, altura, paso y fabricante |
| C3 | 470 µF / 10 V | `rfid_eest3:CP_Radial_D10_P5.00_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | Sí, polarizado | Confirmar diámetro, altura, paso y fabricante |
| C9 | 10 µF preliminar | `rfid_eest3:CP_Radial_D5_P2.00_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | Sí, geometría provisional | Pads ajustados a 1,6 mm para cumplir clearance; medir componente |
| NT1 | Unión estrella GND/GND_POWER | `NetTie:NetTie-2_THT_Pad1.0mm` | PRELIMINAR_REV_A | Sí | No sustituir por puente accidental |
| H1–H4 | Agujeros M3, Ø3,2 mm | `rfid_eest3:MOUNTING_HOLE_3.2_PLACEHOLDER_NO_FABRICAR` | PLACEHOLDER_NO_FABRICAR | No aplica | Posiciones provisionales; confirmar caja y separadores |
| D1, D5–D8 | Protección Schottky/TVS pendiente | Sin footprint | PENDIENTE_MEDICIÓN | No | Requiere componente y encapsulado definitivos |
| F1, F2 | Fusible/PTC pendiente | Sin footprint | PENDIENTE_MEDICIÓN | No | Requiere curva, corriente de arranque y encapsulado |

IRFZ44N continúa descartado para control directo a 3,3 V. Q2 conserva el
AO3400A preliminar: disipación fría calculada ≈0,156 W a 1,8 A y 48 mΩ,
pendiente de corriente de arranque, temperatura ambiente, cobre disponible y
ensayo térmico.

### Reglas y distribución provisional

| Clase | Redes principales | Ancho | Clearance | Vía / taladro |
|---|---|---:|---:|---:|
| `LOGIC` | GPIO, SPI, sensores y control | 0,25 mm | 0,20 mm | 0,80 / 0,40 mm |
| `POWER_3V3_5V` | `+3V3`, `+5V`, `GND` | 0,50 mm | 0,25 mm | Heredada provisional |
| `POWER_12V_AUX` | `+12V_IN`, `+12V_AUX` | 0,80 mm | 0,30 mm | Heredada provisional |
| `LOCK_POWER` | `+12V_LOCK`, `LOCK_OUT`, `GND_POWER` | 2,00 mm mínimo | 0,50 mm | Evitar; si fueran necesarias, varias en paralelo |

Para `LOCK_POWER` se prefiere 2,50 mm o cobre vertido, sujeto al cálculo
térmico y al stackup final. No se creó cobre ni se rutearon redes.

Contorno provisional: rectángulo de **120 × 80 mm**, con cuatro agujeros
provisionales de Ø3,2 mm. Zonas del floorplan:

- A: potencia/cerradura en el sector inferior izquierdo.
- B: alimentación lógica contigua, separada de `LOCK_OUT`.
- C: ESP32-S3 junto al borde derecho, antena orientada al borde superior.
- D: RC522/SPI en el borde superior izquierdo, opuesto a potencia.
- E: sensores y DSC LC-100 accesibles desde el borde inferior.
- F: LEDs y buzzer en el sector central, visibles y alejados de potencia.

Se crearon dos keepouts de antena, uno en F.Cu y otro en B.Cu, que prohíben
pistas, vías y cobre entre X=106,5…139,5 mm e Y=20,2…32 mm. No existen zonas
de cobre.

### Auditoría de colocación y DRC preliminar

- Footprints: **50** (46 eléctricos + 4 agujeros mecánicos).
- Redes: **57**.
- Pistas/segmentos: **0**.
- Vías: **0**.
- Zonas de cobre: **0**.
- Keepouts: **2**.
- Contorno: **120 × 80 mm**.
- Ratsnest aproximado de kicad-ai: **483 pares**.
- DRC de KiCad: **88 elementos no conectados**, esperados por ausencia de
  ruteo; no deben excluirse.
- Violaciones geométricas no relacionadas con ruteo: **20 advertencias de
  serigrafía** (9 solapamientos y 11 recortes por máscara). No hay errores de
  clearance después de ajustar el placeholder C9.
- `score_placement`: HPWL 1946,79 mm; congestión pico 2; proximidad de
  desacoplos 38,29 mm. Son métricas de prelayout, no aceptación para fabricar.
- No se detectaron courtyards fuera del contorno; NT1 carece de courtyard.
- La miniatura automática no estuvo disponible en la herramienta.

Las advertencias de serigrafía se conservan documentadas porque varias nacen
de placeholders que serán reemplazados. Deben resolverse al confirmar
footprints y antes de cualquier salida de fabricación; no se crearon
exclusiones DRC.

### Mediciones físicas aún necesarias

- ESP32-S3: separación entre hileras, largo/ancho/altura, USB-C, botones,
  borde de antena y posición de pines.
- RC522: orientación real del header, dimensiones, cable y separación de
  antena respecto de cobre/metal.
- Borneras: cuerpo, altura, diámetro de pin/taladro, acceso de tornillo,
  sección de cable y corriente nominal; J1/J9 deben admitir al menos 5 A.
- C1, C3 y C9: diámetro, altura, paso y polaridad.
- Buzzer: tipo activo/pasivo, magnético/piezoeléctrico, consumo y pinout.
- Caja: dimensiones internas, separadores, accesos, tolerancias y altura.
- Cerradura: corriente de arranque y temperatura de Q2 en operación.
- Protección: modelos/encapsulados de D1, D5–D8, F1 y F2.

### Puntos de prueba propuestos, no agregados

`+12V_IN`, `+12V_LOCK`, `+5V`, `+3V3`, `GND`, `GND_POWER`, `LOCK_GATE`,
`LOCK_OUT`, `RFID_SCK`, `RFID_MOSI`, `RFID_MISO`, `RFID_SS`, `PIR_IN` y
`PIR_TAMPER`.

Agregar estos puntos requiere autorización para modificar el esquema y una
nueva transferencia controlada.

## Snapshots

- Base: `20260729_051129_190283`.
- Raíz final: `20260729_053102_540897`.
- Alimentación: `20260729_053102_550681`.
- Controlador: `20260729_053102_563916`.
- RFID: `20260729_053102_572818`.
- Sensores: `20260729_053102_581116`.
- Señalización: `20260729_053102_589677`.
- Cerradura: `20260729_053102_597993`.
- Antes de actualizar alimentación: `20260729_055745_414782`.
- Antes de actualizar salida de cerradura: `20260729_055745_424431`.
- Alimentación actualizada: `20260729_061124_222735`.
- Salida de cerradura actualizada: `20260729_061126_968215`.
- Cerradura CC definitiva: `20260729_061551_779914`.
- Alimentación con protección 2,5 A preliminar: `20260729_061557_470129`.
- Raíz previa/final sin cambios: `20260729_053102_540897`.
- Controlador ESP32-S3 final: `20260729_070338_507833`.
- RC522 con resistencias serie y filtrado final: `20260729_070338_536833`.
- Sensores con `PIR_TAMPER`: `20260729_070338_557390`.
- Señalización sin cambios eléctricos: `20260729_055404_690955`.
- Cerradura sin cambios eléctricos: `20260729_061551_779914`.
- Alimentación con rama protegida `+12V_AUX`: `20260729_071440_883552`.
- Controlador con EN conectado mediante pull-up: `20260729_071440_909956`.
- Sensores con interfaz DSC LC-100 por contactos NC: `20260729_071440_967749`.
- PCB vacía previa a preparación de footprints: `20260729_072036_391223`.
- PCB transferida, previa a reglas y floorplan: `20260729_081110_872753`.
- PCB Rev. A con prelayout final: `20260729_082246_498656`.
- Señalización con Q1 AO3400A y D9 DNP: `20260729_073541_470080`.
- Sensores con PIR_PWR, PIR_ALARM y PIR_TAMPER separados: `20260729_073541_494917`.
- Cerradura con footprint SOT-23 verificado para Q2: `20260729_073541_519945`.
- Señalización final con datasheet de Q1: `20260729_073634_601985`.
- Sensores finales con terminales físicos pendientes documentados: `20260729_073634_619789`.

## Próximos pasos

1. En KiCad 10, usar **File → Revert** para recargar el esquema modificado.
2. Revisar visualmente las seis hojas.
3. Confirmar modelos y datasheets pendientes.
4. Confirmar numeración de borneras, cableado y ubicación del DSC LC-100.
5. No iniciar PCB hasta recibir la autorización textual requerida.

## Cierre de floorplan PCB Rev. A — 2026-07-29

- Rama de trabajo: `pcb-rev-a-prelayout`.
- Snapshot PCB previo a la reorganización: `20260729_180844_606658`.
- Snapshot PCB final: `20260729_181948_558376`.
- Esquema validado: siete archivos reconocidos, sin referencias duplicadas.
- ERC exacto: **0 infracciones**.
- PCB: **71 footprints**, **58 redes**, **0 pistas**, **0 vías** y
  **0 zonas de cobre**.
- Keepouts: **2**, uno en `F.Cu` y otro en `B.Cu`, para la antena.
- Contorno: `X=20…140 mm`, `Y=20…100 mm`, es decir **120 × 80 mm**.
- Bounding box de footprints: `X=21,9…138,9 mm`,
  `Y=20,5…99,8 mm`; ningún footprint queda fuera del contorno.
- H2 quedó en `(90, 25) mm`, a **16,5 mm** del comienzo del keepout de
  antena en `X=106,5 mm`.
- HPWL: **2493,32 mm** luego de la sincronización inicial y
  **2315,78 mm** después de reorganizar, mejora de 177,54 mm.
- Congestión pico: **2**.
- La métrica automática global de proximidad de desacoplos cambió de
  **49,57 mm** a **50,51 mm**. No se acepta como criterio de fabricación:
  mezcla capacitores de reserva y filtros con cargas no equivalentes.
  C6/C9 quedaron junto a J5; los filtros de sensores quedaron próximos
  al corredor hacia el ESP32; C1 está en la zona de potencia y C3 en la
  alimentación lógica. La validación definitiva depende de footprints y
  geometría física medidos.
- DRC de prelayout: **0 errores geométricos**, **0 solapamientos de
  courtyard**, **0 pads solapados**, **0 infracciones de keepout** y
  **117 conexiones sin rutear**, esperadas.
- Permanecen **10 advertencias `silk_over_copper`**, todas asociadas a
  gráficos internos de footprints preliminares/placeholders o marcadores
  de polaridad. No se creó ninguna exclusión. Deben corregirse al
  reemplazar los placeholders por footprints medidos, antes de fabricar.
- La advertencia extensa del RC522 y la nota del ESP32-S3 se trasladaron
  a `Dwgs.User`; no quedan solapamientos entre textos de serigrafía.
- El ESP32-S3 conserva estado `PLACEHOLDER_NO_FABRICAR`; los headers están
  dentro del contorno y la antena queda orientada hacia el borde superior.
- Miniatura generada:
  `rfid-control-acceso-eest3_thumbnail.svg`.

### Mediciones físicas bloqueantes antes de fabricar

- ESP32-S3: separación entre hileras, cuerpo, USB, botones, antena y
  extracción vertical con sockets.
- Borneras: taladro, cuerpo, acceso de tornillo, altura y corriente real;
  J1/J9 deben soportar al menos 5 A.
- C1, C3 y C9: diámetro, paso, altura y polaridad del componente comprado.
- Caja y agujeros H1–H4: separadores, cabeza de tornillo y accesos.
- Buzzer: tecnología, polaridad, consumo y necesidad de D9.
- Cerradura: corriente de arranque y temperatura de Q2.

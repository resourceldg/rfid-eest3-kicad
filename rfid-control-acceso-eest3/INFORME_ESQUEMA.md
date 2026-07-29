# Informe técnico — Control de acceso RFID EEST3

Fecha: 2026-07-29  
Etapa: arquitectura y esquema preliminar; PCB no autorizada.

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

- J3/J4: headers de 22 pines del
  `ESP32_S3_DEVKITC1_N16R8_44PIN`, basados en el pinout del
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

Resultado final (2026-07-29 07:13:31): **0 errores y 0 advertencias**.

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

## Próximos pasos

1. En KiCad 10, usar **File → Revert** para recargar el esquema modificado.
2. Revisar visualmente las seis hojas.
3. Confirmar modelos y datasheets pendientes.
4. Confirmar numeración de borneras, cableado y ubicación del DSC LC-100.
5. No iniciar PCB hasta recibir la autorización textual requerida.

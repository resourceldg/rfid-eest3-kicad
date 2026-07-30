# Guía de ruteo — RFID EEST3 Rev. A

Escrita para esta placa en concreto. No es un tutorial general de KiCad.

## Qué es rutear

Ahora mismo el board tiene los componentes colocados y **122 líneas finas**
que van de un pad a otro. Eso se llama *ratsnest*: son las conexiones que el
esquema dice que tienen que existir, pero que todavía no tienen cobre.

Rutear es dibujar el cobre que reemplaza esas líneas. Cada vez que conectás
dos pads, la línea correspondiente desaparece. Ese contador de abajo a la
derecha —**Sin enrutar: 122**— es tu barra de progreso. Terminaste cuando
llega a 0.

Hay dos caras de cobre: **F.Cu** (frente, rojo) y **B.Cu** (dorso, azul). Una
**vía** es un agujerito metalizado que pasa una pista de una cara a la otra.

## Lo único que tenés que saber de la interfaz

| Tecla | Qué hace |
|---|---|
| `X` | Empieza a rutear desde el pad que está bajo el cursor |
| clic | Fija una esquina y sigue |
| `End` o doble clic | Termina la pista ahí |
| `Esc` | Cancela la pista que estás dibujando |
| `V` | Mientras ruteás: pone una vía y sigue por la otra cara |
| `Re Pág` / `Av Pág` | Cambia la cara activa (F.Cu / B.Cu) |
| `D` | Arrastra una pista sin desconectarla |
| `U` | Selecciona toda la pista conectada (para borrarla entera) |
| `Supr` | Borra lo seleccionado |
| `/` | Cambia el sentido del codo de 45° |
| `Ctrl+Z` | Deshacer |
| `B` | Rellena todas las zonas de cobre |

Si alguna no coincide, están todas en Preferencias → Atajos de teclado.

### El ancho ya está resuelto

No tenés que elegir el ancho de ninguna pista. En la barra superior dice
**"Pista: usar el ancho de clase de nodo"**, o sea que KiCad toma el ancho de
la clase de red. Dejalo así. Cada red ya tiene el suyo asignado:

- **2,0 mm** las de potencia (llevan 1,8 A)
- **0,5 mm** las de alimentación lógica
- **0,25 mm** las de señal

Si en algún momento ves que una pista de potencia te sale finita, es que la
clase de red no se aplicó: pará y avisá antes de seguir.

### El modo del router

Barra superior del router: dejalo en **"Empujar"** (Shove). Cuando una pista
nueva choca con una existente, la corre sola en lugar de bloquearte.

## El orden importa

Ruteá de lo más restringido a lo más libre. Las pistas de 2 mm casi no tienen
margen de maniobra; las de señal pasan por cualquier lado. Si dejás la
potencia para el final, no te va a entrar.

### Fase 1 — Potencia (2,0 mm, esquina inferior izquierda)

| Orden | Red | Pads | Recorrido |
|---:|---|---:|---|
| 1 | `+12V_IN` | 3 | J1 pin 1 → D1 ánodo, y TP1 |
| 2 | `Net-(D1-K)` | 3 | D1 cátodo → F1 |
| 3 | `+12V_LOCK` | 10 | F1 → C1, C2, D5, J9, D4, J2, F2, TP2 |
| 4 | `GND_POWER` | 8 | J1 pin 2 → C1, C2, D5, Q2 source, R8, NT1, TP6 |
| 5 | `LOCK_OUT` | 4 | J9 pin 2 → Q2 drain, D4, TP8 |

**Lo más importante de toda la placa** está en los pasos 3 a 5. La cerradura
es una bobina: cuando Q2 la apaga, la corriente tiene que seguir circulando y
se va por D4. Ese lazo —J9 → D4 → Q2 → vuelta— tiene que ser **lo más chico
posible**. Ruteálo corto y compacto, aunque quede feo. Si ese lazo es grande,
genera picos de tensión que pueden resetear el ESP32 o romper el MOSFET.

`GND_POWER` es el retorno de los 1,8 A. Va solo por esta esquina. **No lo
conectes a `GND` en ningún lado**: se tocan únicamente en NT1, que está pegado
a J1 justamente para eso.

### Fase 2 — Alimentación lógica (0,5 mm)

| Orden | Red | Pads |
|---:|---|---:|
| 6 | `+5V` | 8 |
| 7 | `+3V3` | 13 |
| 8 | `+12V_AUX` | 2 |

`+3V3` sale del DevKit (J13 pines 1 y 3) y alimenta el RC522, los pull-ups y
J8. `+5V` viene del buck por J2 y entra al DevKit por el pin 41.

### Fase 3 — Masa lógica: usá un plano, no pistas

`GND` tiene 34 pads. Rutearlos uno por uno a mano es una tortura innecesaria.
Se hace con un **plano de cobre** (zona rellena):

1. Poné la cara activa en **B.Cu** (`Av Pág`).
2. Herramienta **"Añadir zona rellena"** (barra derecha) o `Ctrl+Shift+Z`.
3. Dibujá un rectángulo que cubra **de y=20 a y=80**, todo el ancho. Es decir,
   los dos tercios superiores de la placa: toda la zona lógica.
4. En el diálogo elegí la red **GND** y aceptá.
5. Presioná `B` para rellenar.

Todos los pads de GND que caigan adentro quedan conectados solos, con sus
patitas térmicas. Vas a ver el contador de "sin enrutar" desplomarse.

**Por qué el plano no baja hasta abajo:** la esquina inferior izquierda es la
de potencia. Si el plano de masa lógica se metiera ahí, el retorno de 1,8 A de
la cerradura compartiría cobre con la masa del ESP32, que es exactamente lo
que este diseño evita. El plano se queda arriba, y la unión con la masa de
potencia se hace en un solo punto:

6. Ruteá **una** pista de 0,5 mm desde el pad 2 de NT1 hasta el plano.

Esa pista es la estrella de masa. Es la única.

### Fase 4 — Señales (0,25 mm)

Las 25 redes restantes, casi todas de 2 o 3 pads. Acá ya es relleno: van por
F.Cu y donde no puedan, una vía y siguen por B.Cu.

Dos detalles:

- **RFID_SS, SCK, MOSI, RST** salen de J13, pasan por R9–R12 y siguen a J5.
  Mantenelas juntas y parejas, sin desvíos raros.
- **LOCK_GATE** va de J13 hasta Q2 y son unos 50 mm. Tratá de que no corra
  pegada y en paralelo a las señales de sensores por tramos largos.

### Los pads dobles de J13

J13 tiene la hilera par duplicada en 22,86 y 25,40 mm, porque no medimos el
módulo. Los pines **2, 42 y 44** son GND y por eso tienen **dos pads cada
uno**. Uní cada par con un tramo corto de cobre, si no el DRC te los va a
marcar como no conectados. Los demás pines duplicados no tienen red y no hay
que tocarlos.

## Cómo saber que vas bien

- El contador **"Sin enrutar"** baja y no vuelve a subir.
- Corré el **DRC** (Inspeccionar → Comprobador de reglas de diseño) cada
  tanto, no solo al final. Es mucho más fácil arreglar un choque recién hecho
  que quince juntos.
- Las de serigrafía (`silk_overlap`) ignoralas hasta el final: son textos
  pisándose, no afectan el cobre.

## Si te trabás

- **No entra una pista**: en vez de forzarla, poné una vía (`V`), pasá a la
  otra cara, cruzá por abajo y volvé a subir con otra vía. Es normal y no
  tiene nada de malo.
- **Una pista quedó horrible**: `U` para seleccionarla entera, `Supr`, y de
  nuevo. Borrar y rehacer es más rápido que corregir.
- **Moviste algo sin querer**: `Ctrl+Z`. Y guardá seguido.

Nada de lo que hagas acá es irreversible mientras no se fabrique. Equivocarse
ruteando no rompe nada.

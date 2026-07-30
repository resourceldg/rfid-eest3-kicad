# Lo que falta — RFID EEST3 Rev. A

La placa está ruteada y el DRC pasa sin infracciones. Eso significa que el
diseño es **coherente consigo mismo**, no que sea correcto: el DRC verifica
geometría, no que los componentes aguanten lo que se les va a pedir ni que el
módulo que compraste tenga la forma que dice el footprint.

Este archivo es la respuesta a "¿ya se puede mandar a fabricar?". Hoy la
respuesta es no, por tres bloqueos.

## Bloqueo 1 — J13 tiene la hilera par duplicada

**Es el único bloqueo puramente geométrico, y alcanza para arruinar el lote.**

El footprint tiene 66 pads en tres filas: la impar en y = 73,00 y **dos**
hileras pares, una en y = 95,86 (paso 22,86 mm) y otra en y = 98,40 (paso
25,40 mm). Están las dos porque nunca se midió el módulo físico. La serigrafía
lo avisa —"USAR UNA SOLA HILERA PAR"— pero una serigrafía no arregla una placa
fabricada.

Qué hay que hacer:

1. Conseguir el ESP32-S3 DevKit que se va a usar y medir con calibre la
   separación real entre las dos hileras de pines.
2. Editar `rfid_eest3:ESP32-S3-44P_SOCKET_DUAL_22.86_25.40` y borrar la hilera
   que no corresponda, junto con sus dos textos de referencia.
3. Reruteo local de lo que colgaba de esa hilera y DRC de vuelta.

Mientras las dos hileras existan, cualquier Gerber que se genere trae 22
agujeros de más.

## Bloqueo 2 — ninguna de las nueve mediciones está hecha

[CHECKLIST_PREPCB.md](CHECKLIST_PREPCB.md) tiene nueve ítems y ninguno tildado.
Los que bloquean de verdad son estos cuatro, porque de ellos dependen valores
de componentes que ya están puestos en la placa:

| Qué medir | De qué depende |
|---|---|
| Corriente de arranque de la cerradura | El calibre de F1 y el margen de las pistas de 2,0 mm |
| Consumo estacionario del conjunto | El dimensionado de F2 y del buck |
| Temperatura de Q2 en el peor caso | Si el SOT-23 alcanza o hay que ir a un encapsulado con disipación |
| Energía que tiene que absorber D4 | Si el SMA alcanza |

Los cuatro son mediciones de banco sobre el prototipo actual, no simulaciones.
Ninguna se puede deducir del esquema.

## Bloqueo 3 — la mecánica no está verificada

Ocho borneras (J1, J2, J6, J8, J9, J10, J11, J12) y el zócalo J13 **no tienen
modelo 3D asignado**. En el render aparecen como pads pelados. El DRC valida
sus courtyards, así que en el plano no se pisan, pero nadie miró todavía si los
cuerpos reales entran donde tienen que entrar.

Medidas concretas a confirmar contra las piezas que se vayan a comprar:

- **Tres de los cuatro agujeros de montaje tienen un componente cerca**, medido
  desde el borde del courtyard al centro del agujero:

  | Componente | Agujero | Distancia |
  |---|---|---:|
  | J6 (bornera) | H4 | 4,78 mm |
  | J8 (bornera) | H1 | 4,95 mm |
  | C1 (electrolítico ⌀ 16 mm) | H2 | 4,96 mm |

  En los tres entra un tornillo M3 con arandela (⌀ 6–7 mm). En ninguno entra un
  separador hexagonal o de nylon de 8 mm. El de C1 es el más incómodo de los
  tres: el capacitor es alto, así que no solo estorba el separador sino
  también el destornillador. H3 es el único agujero despejado.

  Si el montaje va sobre separadores —que es lo habitual en una caja— hay que
  correr esos tres componentes o los agujeros antes de fabricar.

- Las cinco borneras del borde superior están a 2,00 mm del canto. Hay que
  confirmar que el cable entra de frente sin pelear con la caja.

También falta definir la separación entre la antena del RC522 y las partes
metálicas de la caja, que es lo que dice el ítem 4 del checklist.

## No bloquea, pero conviene saberlo

- **Los pines 1 y 2 de J13 están sin conectar a propósito.** Caen dentro de las
  áreas de reglas de la antena del ESP32-S3 (x 147..159), donde el proyecto
  prohíbe cobre. Son los tres únicos "no conectados" del DRC y no son un error:
  los rieles entran por el pin 3 (`+3V3`) y por 42/43/44 (`GND`). Meter cobre
  bajo la antena sería peor que dejar el pin libre.
- **`plano_gnd` quedó partido en 8 islas**, cada una conectada por pista. El
  retorno funciona y el DRC lo acepta. Un plano entero sería mejor, pero
  unirlas implica reordenar señales en B.Cu, o sea rehacer el ruteo.
  `plano_gnd_power`, que es el que lleva los 1,8 A, sí quedó de una pieza.

## Qué ya está resuelto

Para que nadie vuelva a abrir estos temas:

- Clases de red: los anchos del `.kicad_pro` coinciden con el cobre de la placa
  (2,0 mm potencia, 1,0 mm `+12V_AUX`, 0,8 mm alimentación lógica, 0,4 mm
  señal).
- Lazo de recirculación de la cerradura: D4 se movió al lado de J9 y las dos
  ramas bajaron de 15,8 y 14,7 mm a 6,97 mm cada una. Ver
  [GUIA_RUTEO.md](GUIA_RUTEO.md).
- Alivios térmicos: J5 pad 6 y J2 pad 4 pasaron a conexión sólida a plano.
- Serigrafía: sin superposiciones ni textos sobre cobre.
- La contradicción entre [AGENTS.md](../AGENTS.md) y el hecho de que la placa
  se ruteó con autorouter: aclarada en ese archivo.

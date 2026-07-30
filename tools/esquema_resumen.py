#!/usr/bin/env python3
"""Genera una hoja unica que resume los seis bloques del esquema.

El proyecto esta dividido en seis hojas y la hoja raiz son seis cajas vacias:
no tiene un solo pin jerarquico ni un solo cable, porque todo se conecta por
etiquetas globales. Abrirla no dice nada de como se relacionan los bloques.

Esta herramienta arma RESUMEN_ELECTRICO.kicad_sch: los 67 componentes reales
con sus simbolos y sus valores, el cableado local de cada bloque, y el ESP32
en el centro como lo que es, el nodo del que cuelga todo lo demas. Las redes
que cruzan de un bloque a otro van por etiqueta global, que es exactamente el
mecanismo que usa el diseño real.

IMPORTANTE: la hoja es documentacion y NO forma parte de la jerarquia del
proyecto. No esta referenciada por la hoja raiz. Si se la agregara, KiCad
tomaria estos 67 simbolos como componentes nuevos, duplicaria las referencias
y romperia la correspondencia con el board. Se abre sola, con
`eeschema RESUMEN_ELECTRICO.kicad_sch`, o desde tools/:

    python3 tools/esquema_resumen.py
    kicad-cli sch export pdf rfid-control-acceso-eest3/RESUMEN_ELECTRICO.kicad_sch

Los datos salen del netlist real exportado de las seis hojas, asi que los
valores y la conectividad no se pueden desfasar de lo que hay: si cambia el
esquema, se vuelve a correr esto y la hoja se regenera.
"""
import glob
import math
import os
import re
import subprocess
import sys
import tempfile
import uuid as _uuid

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROY = os.path.join(RAIZ, "rfid-control-acceso-eest3")
SALIDA = os.path.join(PROY, "RESUMEN_ELECTRICO.kicad_sch")
HOJA_UUID = "5eb7f9a0-0000-4000-8000-000000000001"

# Encabezado y pie del recuadro. Cambiar aca si la hoja se entrega como
# practica numerada o con otro titulo.
TITULO = "CONTROL DE ACCESO RFID - E.E.S.T. N 3"
EPIGRAFE = "ESQUEMA ELECTRICO UNIFICADO - 67 componentes, 34 redes"

REJILLA = 1.27


# ---------------------------------------------------------------- s-expresiones

def parse(t):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', t)
    def rd(i):
        out = []
        while i < len(tok):
            x = tok[i]
            if x == '(':
                sub, i = rd(i + 1); out.append(sub)
            elif x == ')':
                return out, i + 1
            else:
                out.append(x[1:-1].replace('\\"', '"') if x.startswith('"') else x); i += 1
        return out, i
    return rd(0)[0][0]


def find(n, k):
    return [x for x in n if isinstance(x, list) and x and x[0] == k]


def get(n, k):
    r = find(n, k)
    return r[0] if r else None


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def uid(semilla):
    """uuid estable: regenerar la hoja no tiene que ensuciar el diff."""
    return str(_uuid.uuid5(_uuid.UUID(HOJA_UUID), semilla))


# ---------------------------------------------------------------- datos reales

def cargar_simbolos():
    """Devuelve (parseado, texto_crudo) por lib_id.

    El texto crudo se copia tal cual del archivo de origen en vez de
    reconstruirlo: en una s-expresion de KiCad hay atomos que van con comillas
    y otros que no (`default`, `left`, `none`, `yes`), y no hay forma de saber
    cual es cual desde el arbol parseado. Reserializar rompe el archivo.
    """
    defs, crudo = {}, {}
    for f in sorted(glob.glob(os.path.join(PROY, "0*.kicad_sch"))):
        txt = open(f).read()
        for s in find(get(parse(txt), 'lib_symbols'), 'symbol'):
            defs.setdefault(s[1], s)
        for lib_id, bloque in bloques_simbolo(txt):
            crudo.setdefault(lib_id, bloque)
    return defs, crudo


def bloques_simbolo(txt):
    """Extrae el texto exacto de cada (symbol "lib_id" ...) de lib_symbols."""
    i = txt.index("(lib_symbols")
    prof, j = 0, i
    while True:
        if txt[j] == '(':
            prof += 1
        elif txt[j] == ')':
            prof -= 1
            if prof == 0:
                break
        j += 1
    seccion = txt[i:j]
    for m in re.finditer(r'\n\t\t\(symbol "([^"]+)"', seccion):
        ini = m.start() + 1
        prof, k = 0, ini
        while True:
            if seccion[k] == '(':
                prof += 1
            elif seccion[k] == ')':
                prof -= 1
                if prof == 0:
                    break
            k += 1
        yield m.group(1), seccion[ini:k + 1]


def cargar_netlist():
    with tempfile.NamedTemporaryFile(suffix=".net", delete=False) as tmp:
        ruta = tmp.name
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
                    "-o", ruta, os.path.join(PROY, "rfid-control-acceso-eest3.kicad_sch")],
                   check=True, capture_output=True)
    d = parse(open(ruta).read())
    os.unlink(ruta)
    comps = {}
    for c in find(get(d, 'components'), 'comp'):
        ref = get(c, 'ref')[1]
        ls = get(c, 'libsource')
        fp = get(c, 'footprint')
        comps[ref] = {
            "valor": get(c, 'value')[1],
            "lib_id": get(ls, 'lib')[1] + ":" + get(ls, 'part')[1],
            "footprint": fp[1] if fp and len(fp) > 1 else "",
        }
    return comps


def pines_def(sdef):
    out = {}
    for sub in find(sdef, 'symbol'):
        for p in find(sub, 'pin'):
            at = get(p, 'at')
            out[get(p, 'number')[1]] = (float(at[1]), float(at[2]), float(at[3]))
    return out


# ---------------------------------------------------------------- geometria

class Hoja:
    def __init__(self, defs, comps):
        self.defs, self.comps = defs, comps
        self.colocados = {}   # ref -> (x, y, rot, mirror)
        self.pines = {}       # (ref, pin) -> (x, y)
        self.cables = []      # ((x1,y1),(x2,y2))
        self.etiquetas = []   # (nombre, x, y, rot, forma)
        self.textos = []      # (texto, x, y, tam, negrita)
        self.cajas = []       # (x1, y1, x2, y2)

    def poner(self, ref, x, y, rot=0, mirror=''):
        lib = self.comps[ref]["lib_id"]
        self.colocados[ref] = (x, y, rot, mirror, lib)
        for num, (px, py, pa) in pines_def(self.defs[lib]).items():
            ax, ay = px, py
            if mirror == 'y': ax = -ax
            if mirror == 'x': ay = -ay
            t = math.radians(rot); c, s = math.cos(t), math.sin(t)
            self.pines[(ref, num)] = (round(x + ax * c - ay * s, 4),
                                      round(y - (ax * s + ay * c), 4))
        return self

    def p(self, ref, num):
        return self.pines[(ref, str(num))]

    def cable(self, *puntos):
        for a, b in zip(puntos, puntos[1:]):
            if a != b:
                self.cables.append((a, b))

    def unir(self, a, b, modo='h'):
        """Une dos puntos con un codo. 'h' sale horizontal, 'v' sale vertical."""
        (x1, y1), (x2, y2) = a, b
        if x1 == x2 or y1 == y2:
            self.cable(a, b)
        elif modo == 'h':
            self.cable(a, (x2, y1), b)
        else:
            self.cable(a, (x1, y2), b)

    def etiqueta(self, punto, nombre, hacia='izq', largo=7.62, forma='bidirectional'):
        """Stub desde un pin hasta una etiqueta global."""
        x, y = punto
        dx = {'izq': -largo, 'der': largo, 'arr': 0, 'aba': 0}[hacia]
        dy = {'izq': 0, 'der': 0, 'arr': -largo, 'aba': largo}[hacia]
        fin = (round(x + dx, 4), round(y + dy, 4))
        self.cable(punto, fin)
        rot = {'izq': 180, 'der': 0, 'arr': 90, 'aba': 270}[hacia]
        self.etiquetas.append((nombre, fin[0], fin[1], rot, forma))
        return fin

    def texto(self, s, x, y, tam=2.0, negrita=True):
        self.textos.append((s, x, y, tam, negrita))

    def rotulo(self, titulo, x, y):
        """Nombre de bloque, sin caja: el marco es uno solo para toda la hoja."""
        self.texto(titulo, x, y, 2.5, True)

    def marco(self, titulo, epigrafe, margen=8.0):
        """Un solo recuadro alrededor de todo, con titulo arriba y nombre abajo.

        Los limites salen de lo que efectivamente se dibujo, no de numeros
        escritos a mano: asi el marco sigue quedando bien si se mueve un bloque.
        """
        puntos = [p for c in self.cables for p in c]
        puntos += [(e[1], e[2]) for e in self.etiquetas]
        puntos += [(t[1], t[2]) for t in self.textos]
        puntos += list(self.pines.values())
        # el cuerpo de un simbolo sobresale de sus pines: si solo se miran los
        # pines, el marco termina cortando al conector del borde
        for x, y, _, _, _ in self.colocados.values():
            puntos += [(x - 5, y - 5), (x + 5, y + 5)]
        xs = [p[0] for p in puntos]; ys = [p[1] for p in puntos]
        x1, y1 = min(xs) - margen, min(ys) - margen
        x2, y2 = max(xs) + margen, max(ys) + margen
        self.cajas.append((x1, y1, x2, y2))
        centro = (x1 + x2) / 2.0
        self.texto(titulo, centro - len(titulo) * 4.5 * 0.31, y1 - 6.0, 4.5, True)
        self.texto(epigrafe, centro - len(epigrafe) * 3.0 * 0.31, y2 + 8.0, 3.0, True)
        return (x1, y1, x2, y2)

    # ------------------------------------------------------------ emision

    def resolver(self):
        """Parte los cables donde otro cable termina en su interior.

        Sin esto un nodo en T no genera juntura: el punto cae en el medio de un
        segmento y no cuenta como extremo. KiCad lo interpretaria como dos
        cables que se cruzan sin conectarse, que es justo lo contrario de lo
        que dice el esquema.
        """
        extremos = set()
        for a, b in self.cables:
            extremos.add(a); extremos.add(b)
        salida = []
        for a, b in self.cables:
            (x1, y1), (x2, y2) = a, b
            cortes = []
            for p in extremos:
                if p == a or p == b:
                    continue
                px, py = p
                if x1 == x2 == px and min(y1, y2) < py < max(y1, y2):
                    cortes.append(p)
                elif y1 == y2 == py and min(x1, x2) < px < max(x1, x2):
                    cortes.append(p)
            if not cortes:
                salida.append((a, b)); continue
            orden = sorted([a] + cortes + [b],
                           key=lambda p: (p[0] - x1) ** 2 + (p[1] - y1) ** 2)
            salida += list(zip(orden, orden[1:]))
        self.cables = salida

    def junturas(self):
        from collections import Counter
        cnt = Counter()
        for a, b in self.cables:
            cnt[a] += 1; cnt[b] += 1
        # tres o mas extremos en el mismo punto es una conexion real
        return [p for p, n in cnt.items() if n >= 3]

    def render(self, defs_usadas, crudo):
        L = []
        A = L.append
        A('(kicad_sch')
        A('\t(version 20260306)')
        A('\t(generator "esquema_resumen.py")')
        A('\t(generator_version "10.0")')
        A('\t(uuid "%s")' % HOJA_UUID)
        A('\t(paper "A2")')
        A('\t(title_block')
        A('\t\t(title "RESUMEN ELECTRICO - Control de acceso RFID EEST3")')
        A('\t\t(company "EEST3")')
        A('\t\t(comment 1 "Hoja de documentacion. NO forma parte de la jerarquia del proyecto.")')
        A('\t\t(comment 2 "Generada por tools/esquema_resumen.py desde el netlist real de las 6 hojas.")')
        A('\t\t(comment 3 "El esquema valido para fabricacion son 01..06_*.kicad_sch.")')
        A('\t)')
        A('\t(lib_symbols')
        for lib in sorted(defs_usadas):
            A(crudo[lib])
        A('\t)')

        for (x1, y1, x2, y2) in self.cajas:
            A('\t(rectangle')
            A('\t\t(start %s %s)' % (n(x1), n(y1)))
            A('\t\t(end %s %s)' % (n(x2), n(y2)))
            A('\t\t(stroke (width 0.4) (type solid) (color 60 60 130 1))')
            A('\t\t(fill (type none))')
            A('\t\t(uuid "%s")' % uid("caja%s%s" % (x1, y1)))
            A('\t)')

        for a, b in self.cables:
            A('\t(wire')
            A('\t\t(pts (xy %s %s) (xy %s %s))' % (n(a[0]), n(a[1]), n(b[0]), n(b[1])))
            A('\t\t(stroke (width 0) (type default))')
            A('\t\t(uuid "%s")' % uid("w%s%s%s%s" % (a[0], a[1], b[0], b[1])))
            A('\t)')

        for (x, y) in self.junturas():
            A('\t(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))'
              % (n(x), n(y), uid("j%s%s" % (x, y))))

        for (s, x, y, tam, neg) in self.textos:
            A('\t(text "%s"' % esc(s))
            A('\t\t(exclude_from_sim yes)')
            A('\t\t(at %s %s 0)' % (n(x), n(y)))
            A('\t\t(effects (font (size %s %s) %s) (justify left))'
              % (n(tam), n(tam), '(bold yes)' if neg else ''))
            A('\t\t(uuid "%s")' % uid("t%s%s%s" % (s, x, y)))
            A('\t)')

        for (nom, x, y, rot, forma) in self.etiquetas:
            just = 'left' if rot == 0 else ('right' if rot == 180 else 'left')
            A('\t(global_label "%s"' % esc(nom))
            A('\t\t(shape %s)' % forma)
            A('\t\t(at %s %s %d)' % (n(x), n(y), rot))
            A('\t\t(effects (font (size 1.27 1.27)) (justify %s))' % just)
            A('\t\t(uuid "%s")' % uid("g%s%s%s" % (nom, x, y)))
            A('\t)')

        for ref, (x, y, rot, mirror, lib) in sorted(self.colocados.items()):
            c = self.comps[ref]
            A('\t(symbol')
            A('\t\t(lib_id "%s")' % esc(lib))
            A('\t\t(at %s %s %d)' % (n(x), n(y), rot))
            if mirror:
                A('\t\t(mirror %s)' % mirror)
            A('\t\t(unit 1)')
            A('\t\t(exclude_from_sim no)')
            A('\t\t(in_bom yes)')
            A('\t\t(on_board yes)')
            A('\t\t(dnp no)')
            A('\t\t(uuid "%s")' % uid("s" + ref))
            (rx, ry), (vx, vy) = campos_offset(lib, rot, pines_def(self.defs[lib]))
            # KiCad hereda al texto solo el eje del simbolo (horizontal o
            # vertical), no el giro de 180. Compensar 180 lo da vuelta.
            giro = {90: 270, 270: 90}.get(rot, 0)
            A(propiedad("Reference", ref, x + rx, y + ry, giro, tam=1.27))
            A(propiedad("Value", c["valor"], x + vx, y + vy, giro, tam=1.0,
                        oculto=lib == "Connector:TestPoint"))
            A(propiedad("Footprint", c["footprint"], x, y, oculto=True))
            A(propiedad("Datasheet", "", x, y, oculto=True))
            A(propiedad("Description", "", x, y, oculto=True))
            for num in sorted(pines_def(self.defs[lib])):
                A('\t\t(pin "%s" (uuid "%s"))' % (num, uid("p%s%s" % (ref, num))))
            A('\t\t(instances')
            A('\t\t\t(project "RESUMEN_ELECTRICO"')
            A('\t\t\t\t(path "/%s" (reference "%s") (unit 1))' % (HOJA_UUID, ref))
            A('\t\t\t)')
            A('\t\t)')
            A('\t)')

        A('\t(sheet_instances')
        A('\t\t(path "/" (page "1"))')
        A('\t)')
        A(')')
        return "\n".join(L) + "\n"


def n(v):
    """Numero como lo escribe KiCad: sin ceros de mas."""
    s = "%.4f" % float(v)
    s = s.rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


def campos_offset(lib, rot, pines):
    """Donde van referencia y valor para no pisar al simbolo ni al cable.

    Lo que decide no es la rotacion sino como queda acostada la pieza. Una
    resistencia nace vertical y un diodo nace horizontal, asi que con la misma
    rotacion terminan en ejes distintos. Si el componente queda horizontal los
    textos van arriba y abajo, porque a los costados esta el cable; si queda
    vertical van a la derecha, que es donde hay lugar.
    """
    if lib.startswith("Connector_Generic:Conn_02x22"):
        return (10.16, -31.0), (10.16, -28.4)
    if lib.startswith("Connector_Generic"):
        return (-2.0, -10.5), (-2.0, -7.9)
    if lib == "Connector:TestPoint":
        return (1.8, -1.6), (1.8, 1.0)
    if lib.startswith("Transistor_FET"):
        return (4.2, -3.2), (4.2, -0.6)

    xs = [p[0] for p in pines.values()]
    ys = [p[1] for p in pines.values()]
    nace_horizontal = (max(xs) - min(xs)) > (max(ys) - min(ys))
    acostado = nace_horizontal != (rot in (90, 270))
    if acostado:
        return (-4.4, -3.4), (-4.4, 4.4)
    return (2.9, -2.4), (2.9, 0.9)


def propiedad(nombre, valor, x, y, giro=0, tam=1.27, oculto=False):
    return ('\t\t(property "%s" "%s"\n'
            '\t\t\t(at %s %s %d)\n'
            '\t\t\t(effects (font (size %s %s)) (justify left)%s)\n'
            '\t\t)' % (nombre, esc(valor), n(x), n(y), giro, n(tam), n(tam),
                       ' (hide yes)' if oculto else ''))


def sexp_a_texto(nodo, nivel):
    """Reserializa una definicion de simbolo tal cual vino."""
    ind = '\t' * nivel
    if isinstance(nodo, str):
        if re.fullmatch(r'-?\d+(\.\d+)?', nodo) or nodo in ('yes', 'no'):
            return nodo
        return '"%s"' % esc(nodo)
    partes = [nodo[0] if isinstance(nodo[0], str) else '']
    simple = all(not isinstance(x, list) for x in nodo[1:])
    if simple:
        return ind + '(' + ' '.join([nodo[0]] + [sexp_a_texto(x, 0) for x in nodo[1:]]) + ')'
    out = [ind + '(' + nodo[0]]
    for x in nodo[1:]:
        if isinstance(x, list):
            out.append(sexp_a_texto(x, nivel + 1))
        else:
            out[-1] += ' ' + sexp_a_texto(x, 0)
    out.append(ind + ')')
    return '\n'.join(out)


# ---------------------------------------------------------------- el dibujo

def armar(h):
    """Tres columnas: los bloques de potencia a la izquierda, el ESP32 en el
    medio como nodo central, y los perifericos a la derecha. Todo lo que cruza
    de una columna a otra va por etiqueta global, igual que en el diseño real."""

    # ===================================== BLOQUE 2 - CONTROLADOR (columna central)
    h.rotulo("2 - CONTROLADOR ESP32-S3", 241, 31.5)
    h.poner("J13", 285, 200)
    izq = {5: "ESP_EN", 7: "DOOR_REED", 9: "PIR_IN", 11: "CABINET_SENSOR",
           13: "PIR_TAMPER", 15: "LED_OK", 17: "LED_ERROR", 19: "BUZZER",
           21: "LOCK_GATE", 29: "RFID_RST", 31: "RFID_SS", 33: "RFID_MOSI",
           35: "RFID_SCK", 37: "RFID_MISO"}
    for pin, red in izq.items():
        h.etiqueta(h.p("J13", pin), red, 'izq', 11.43)
    for pin in (1, 3):
        h.etiqueta(h.p("J13", pin), "+3V3", 'izq', 11.43)
    h.etiqueta(h.p("J13", 41), "+5V", 'izq', 11.43)
    h.etiqueta(h.p("J13", 43), "GND", 'izq', 11.43)
    for pin in (2, 42, 44):
        h.etiqueta(h.p("J13", pin), "GND", 'der', 11.43)

    h.poner("C5", 258, 300); h.poner("R17", 288, 300); h.poner("TP4", 316, 296, 180)
    for ref in ("C5", "R17"):
        h.etiqueta(h.p(ref, 1), "+3V3", 'arr', 8.89)
    h.etiqueta(h.p("C5", 2), "GND", 'aba', 8.89)
    h.etiqueta(h.p("R17", 2), "ESP_EN", 'aba', 8.89)
    h.etiqueta(h.p("TP4", 1), "+3V3", 'aba', 8.89)
    h.texto("El modulo genera +3V3 y lo entrega por los pines 1 y 3.", 243, 330, 1.7, False)
    h.texto("Se alimenta con +5V por el pin 41.", 243, 335, 1.7, False)
    h.texto("C5 desacopla, R17 mantiene EN arriba.", 243, 340, 1.7, False)

    # ===================================== BLOQUE 1 - ALIMENTACION
    h.rotulo("1 - ALIMENTACION Y PROTECCION", 17, 31.5)
    h.poner("J1", 32, 52, 0, 'y')
    h.poner("D1", 60, 52, 180)
    h.poner("F1", 86, 52, 90)
    h.poner("TP1", 44, 38, 180)
    h.poner("TP2", 102, 40, 180)
    h.cable(h.p("J1", 1), h.p("D1", 2))
    h.cable(h.p("D1", 1), h.p("F1", 1))
    h.cable(h.p("TP1", 1), (44, 52))
    h.etiqueta((52, 52), "+12V_IN", 'arr', 8.89)
    h.cable(h.p("TP2", 1), (102, 52))
    h.cable(h.p("F1", 2), (200, 52))
    h.etiqueta((200, 52), "+12V_LOCK", 'der', 10.16)

    for ref, x in (("C1", 122), ("C2", 144), ("D5", 166)):
        h.poner(ref, x, 82, 270 if ref == "D5" else 0)
        h.cable(h.p(ref, 1), (x, 52))
        h.cable(h.p(ref, 2), (x, 112))

    h.poner("F2", 176, 70, 90)
    h.cable((156, 52), (156, 70), h.p("F2", 1))
    h.etiqueta(h.p("F2", 2), "+12V_AUX", 'der', 8.89)

    # El riel de masa de potencia MUERE en el pin 1 de NT1. Si lo atravesara,
    # las dos masas quedarian unidas por cobre en todo su recorrido y el net-tie
    # no significaria nada: es justo lo que este diseño evita.
    h.poner("NT1", 176, 112)
    h.cable(h.p("J1", 2), (37.08, 112), h.p("NT1", 1))
    h.etiqueta((104, 112), "GND_POWER", 'aba', 10.16)
    h.cable(h.p("NT1", 2), (196, 112))
    h.etiqueta((196, 112), "GND", 'der', 10.16)
    h.poner("TP6", 158, 124, 180)
    h.cable(h.p("TP6", 1), (158, 112))
    h.texto("NT1 es el unico puente entre la masa de potencia y la de la logica.", 62, 64, 1.6, False)
    h.texto("En la placa esta pegado a J1, a proposito.", 62, 69, 1.6, False)

    h.poner("J2", 34, 132, 0, 'y')
    h.poner("TP3", 84, 122, 180)
    h.cable(h.p("J2", 3), (96, 134.54))
    h.cable(h.p("TP3", 1), (84, 134.54))
    h.etiqueta((96, 134.54), "+5V", 'der', 8.89)
    h.etiqueta(h.p("J2", 1), "+12V_LOCK", 'der', 26.67)
    h.etiqueta(h.p("J2", 2), "GND", 'der', 26.67)
    h.etiqueta(h.p("J2", 4), "GND", 'der', 26.67)
    h.texto("modulo buck 12 V -> 5 V", 20, 116, 1.6, False)
    for ref, x in (("C3", 120, ), ("C4", 140, )):
        h.poner(ref, x, 134)
        h.etiqueta(h.p(ref, 1), "+5V", 'arr', 8.89)
        h.etiqueta(h.p(ref, 2), "GND", 'aba', 8.89)
    h.poner("TP5", 210, 124, 180)
    h.cable(h.p("TP5", 1), (210, 112), (196, 112))

    # ===================================== BLOQUE 6 - CERRADURA
    h.rotulo("6 - CERRADURA / SOLENOIDE 12 V", 17, 159.5)
    h.poner("J9", 206, 188)
    h.poner("D4", 176, 189, 270)
    h.poner("Q2", 110, 205.08)
    h.poner("R7", 74, 205.08, 90)
    h.poner("R8", 92, 224)
    h.poner("TP7", 56, 195, 180)
    h.poner("TP8", 150, 190, 180)

    # +12V_LOCK entra por arriba al pin 1 de J9, con el catodo de D4 colgado
    h.cable((124, 178), (200.92, 178), h.p("J9", 1))
    h.cable(h.p("D4", 1), (176, 178))
    h.etiqueta((124, 178), "+12V_LOCK", 'izq', 10.16)

    # LOCK_OUT: drain de Q2, anodo de D4 y pin 2 de J9 son el mismo nodo
    h.cable(h.p("Q2", 3), (200.92, 200), h.p("J9", 2))
    h.cable(h.p("D4", 2), (176, 200))
    h.cable(h.p("TP8", 1), (150, 200))
    h.etiqueta((166, 200), "LOCK_OUT", 'aba', 8.89)

    h.cable(h.p("R7", 2), h.p("Q2", 1))
    h.cable((92, 205.08), h.p("R8", 1))
    h.cable(h.p("TP7", 1), (56, 205.08), h.p("R7", 1))
    h.etiqueta(h.p("R7", 1), "LOCK_GATE", 'izq', 10.16)
    h.etiqueta(h.p("R8", 2), "GND_POWER", 'aba', 10.16)
    h.etiqueta(h.p("Q2", 2), "GND_POWER", 'aba', 11.43)
    h.texto("D4 va pegado a J9: cuando Q2 corta, la corriente de la bobina", 20, 240, 1.6, False)
    h.texto("sigue circulando y se va por el diodo. Ese lazo tiene que", 20, 245, 1.6, False)
    h.texto("encerrar la menor superficie posible.", 20, 250, 1.6, False)
    h.texto("R8 mantiene la compuerta abajo mientras el ESP32 arranca.", 20, 258, 1.6, False)

    # ===================================== BLOQUE 5 - SENALIZACION
    h.rotulo("5 - SEÑALIZACION", 17, 271.5)
    for ref, led, y, red in (("R3", "D2", 288, "LED_OK"), ("R4", "D3", 308, "LED_ERROR")):
        h.poner(ref, 74, y, 90)
        h.poner(led, 106, y, 180)
        h.cable(h.p(ref, 2), h.p(led, 2))
        h.etiqueta(h.p(ref, 1), red, 'izq', 10.16)
        h.etiqueta(h.p(led, 1), "GND", 'der', 12.7)

    h.poner("R5", 74, 336, 90)
    h.poner("Q1", 110, 336)
    h.poner("R6", 92, 349)
    h.poner("BZ1", 168, 328.38)
    h.poner("D9", 200, 327.11, 270)
    h.cable(h.p("R5", 2), h.p("Q1", 1))
    h.cable((92, 336), h.p("R6", 1))
    h.etiqueta(h.p("R5", 1), "BUZZER", 'izq', 10.16)
    h.etiqueta(h.p("R6", 2), "GND", 'aba', 6.35)
    h.etiqueta(h.p("Q1", 2), "GND", 'aba', 8.89)
    # D9 queda en paralelo con el buzzer, que tambien es una bobina
    h.cable(h.p("Q1", 3), h.p("BZ1", 2))
    h.cable(h.p("BZ1", 2), h.p("D9", 2))
    h.cable(h.p("BZ1", 1), (165.46, 318), (200, 318), h.p("D9", 1))
    h.etiqueta((182, 318), "+5V", 'arr', 8.89)
    h.texto("D9 absorbe el pico del buzzer al cortar.", 20, 358, 1.6, False)

    # ===================================== BLOQUE 3 - RFID
    h.rotulo("3 - LECTOR RFID RC522 (solo 3,3 V)", 345, 31.5)
    h.poner("J5", 540, 70)
    for ref, pin, red, jog, y in (("R9", 1, "RFID_SS", 476, 38),
                                  ("R10", 2, "RFID_SCK", 490, 50),
                                  ("R11", 3, "RFID_MOSI", 504, 62),
                                  ("R12", 7, "RFID_RST", 518, 74)):
        h.poner(ref, 452, y, 90)
        destino = h.p("J5", pin)
        h.cable(h.p(ref, 2), (jog, y), (jog, destino[1]), destino)
        h.etiqueta(h.p(ref, 1), red, 'izq', 10.16)
    h.etiqueta(h.p("J5", 4), "RFID_MISO", 'izq', 8.89)
    h.etiqueta(h.p("J5", 6), "GND", 'izq', 8.89)
    h.etiqueta(h.p("J5", 8), "+3V3", 'izq', 8.89)
    h.texto("33 R en serie: amortiguan el flanco a lo largo de 20-40 cm de cable.", 348, 100, 1.7, False)
    h.texto("El RC522 se alimenta solo con 3,3 V. Nunca con 5 V.", 348, 105, 1.7, False)

    h.poner("C6", 360, 124); h.poner("C9", 382, 124)
    for ref in ("C6", "C9"):
        h.etiqueta(h.p(ref, 1), "+3V3", 'arr', 8.89)
        h.etiqueta(h.p(ref, 2), "GND", 'aba', 8.89)
    for tp, red, x in (("TP9", "RFID_SCK", 432), ("TP10", "RFID_MOSI", 468),
                       ("TP11", "RFID_MISO", 504), ("TP12", "RFID_SS", 540)):
        h.poner(tp, x, 142, 180)
        h.etiqueta(h.p(tp, 1), red, 'arr', 8.89)

    # ===================================== BLOQUE 4 - SENSORES
    h.rotulo("4 - SENSORES", 345, 167.5)
    for conn, spin, y, red, rpu, cf, tvs, nota, otros in (
            ("J6", 1, 192, "DOOR_REED", "R1", "C7", "D6", "reed de puerta (NC)",
             {2: "GND"}),
            ("J8", 3, 232, "CABINET_SENSOR", "R2", "C8", "D8", "tamper del gabinete",
             {1: "+3V3", 2: "GND"})):
        h.poner(conn, 354, y, 0, 'y')
        nodo = h.p(conn, spin)
        h.cable(nodo, (492, nodo[1]))
        h.poner(rpu, 414, nodo[1] - 18)
        h.cable(h.p(rpu, 2), (414, nodo[1]))
        h.etiqueta(h.p(rpu, 1), "+3V3", 'arr', 8.89)
        h.poner(cf, 444, nodo[1] + 12)
        h.cable((444, nodo[1]), h.p(cf, 1))
        h.etiqueta(h.p(cf, 2), "GND", 'aba', 8.89)
        h.poner(tvs, 470, nodo[1] + 12, 270)
        h.cable((470, nodo[1]), h.p(tvs, 1))
        h.etiqueta(h.p(tvs, 2), "GND", 'aba', 8.89)
        h.etiqueta((492, nodo[1]), red, 'der', 20.32)
        h.texto(nota, 348, y - 14, 1.6, False)
        for pin, r in otros.items():
            h.etiqueta(h.p(conn, pin), r, 'der', 8.89)

    h.poner("J11", 354, 268, 0, 'y')
    h.etiqueta(h.p("J11", 1), "+12V_AUX", 'der', 22.86)
    h.etiqueta(h.p("J11", 2), "GND", 'der', 22.86)
    h.texto("alimentacion del PIR (12 V por F2)", 348, 258, 1.6, False)

    h.poner("J12", 354, 298, 0, 'y')
    h.etiqueta(h.p("J12", 1), "GND", 'der', 8.89)
    h.poner("R13", 414, 282); h.poner("R14", 436, 300.54, 90)
    h.poner("C10", 470, 312); h.poner("D7", 386, 314, 270)
    nodo = h.p("J12", 2)
    h.cable(nodo, h.p("R14", 1))
    h.cable(h.p("R13", 2), (414, nodo[1]))
    h.etiqueta(h.p("R13", 1), "+3V3", 'arr', 8.89)
    # El TVS cuelga del contacto crudo, no de la salida del filtro: lo que hay
    # que sujetar es lo que entra por el cable, antes de la resistencia serie.
    h.cable((386, nodo[1]), h.p("D7", 1))
    h.etiqueta(h.p("D7", 2), "GND", 'aba', 8.89)
    h.etiqueta((400, nodo[1]), "PIR_CONTACT", 'aba', 8.89)
    h.cable(h.p("R14", 2), (516, 300.54))
    h.cable((470, 300.54), h.p("C10", 1))
    h.etiqueta(h.p("C10", 2), "GND", 'aba', 8.89)
    h.etiqueta((516, 300.54), "PIR_IN", 'der', 8.89)
    h.texto("contacto de alarma del PIR", 348, 288, 1.6, False)

    h.poner("J10", 354, 340, 0, 'y')
    h.etiqueta(h.p("J10", 2), "GND", 'der', 8.89)
    h.poner("R15", 414, 322); h.poner("R16", 436, 340, 90)
    h.poner("C11", 470, 346)
    nodo = h.p("J10", 1)
    h.cable(nodo, h.p("R16", 1))
    h.etiqueta((396, nodo[1]), "PIR_TAMPER_CONTACT", 'aba', 8.89)
    h.cable(h.p("R15", 2), (414, nodo[1]))
    h.etiqueta(h.p("R15", 1), "+3V3", 'arr', 8.89)
    h.cable(h.p("R16", 2), (516, 340))
    h.cable((470, 340), h.p("C11", 1))
    h.etiqueta(h.p("C11", 2), "GND", 'aba', 8.89)
    h.etiqueta((516, 340), "PIR_TAMPER", 'der', 8.89)
    h.texto("contacto de tamper del PIR", 348, 330, 1.6, False)

    h.poner("TP13", 534, 210, 180); h.poner("TP14", 560, 210, 180)
    h.etiqueta(h.p("TP13", 1), "PIR_IN", 'arr', 8.89)
    h.etiqueta(h.p("TP14", 1), "PIR_TAMPER", 'arr', 8.89)

    h.marco(TITULO, EPIGRAFE)


def redes_de(ruta):
    """Cada red como el conjunto de (referencia, pin) que toca."""
    with tempfile.NamedTemporaryFile(suffix=".net", delete=False) as tmp:
        salida = tmp.name
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr",
                    "-o", salida, ruta], check=True, capture_output=True)
    d = parse(open(salida).read())
    os.unlink(salida)
    out = {}
    for nred in find(get(d, 'nets'), 'net'):
        nodos = frozenset((get(x, 'ref')[1], get(x, 'pin')[1]) for x in find(nred, 'node'))
        if len(nodos) > 1:
            out[nodos] = get(nred, 'name')[1].split('/')[-1]
    return out


def verificar():
    """La hoja resumen tiene que describir el mismo circuito que las seis hojas.

    Es facil dibujar algo que se ve bien y esta mal: en la primera version D7
    habia quedado despues de la resistencia serie en vez de sobre el contacto
    crudo, y a simple vista no se notaba. Esto lo compara nodo por nodo contra
    el netlist real y falla si no coincide.
    """
    real = redes_de(os.path.join(PROY, "rfid-control-acceso-eest3.kicad_sch"))
    mio = redes_de(SALIDA)
    falta = set(real) - set(mio)
    sobra = set(mio) - set(real)
    distinto = [(real[k], mio[k]) for k in set(real) & set(mio) if real[k] != mio[k]]
    for k in falta:
        print("  FALTA en el resumen: %-22s %s"
              % (real[k], " ".join(sorted("%s.%s" % q for q in k))))
    for k in sobra:
        print("  SOBRA en el resumen: %-22s %s"
              % (mio[k], " ".join(sorted("%s.%s" % q for q in k))))
    for a, b in distinto:
        print("  red sin rotular: en el esquema se llama %s, aca quedo %s" % (a, b))
    if falta or sobra or distinto:
        return False
    print("verificado: las %d redes coinciden nodo por nodo con el esquema real" % len(real))
    return True


def main():
    defs, crudo = cargar_simbolos()
    comps = cargar_netlist()
    h = Hoja(defs, comps)
    armar(h)
    h.resolver()
    usadas = {v[4] for v in h.colocados.values()}
    open(SALIDA, "w").write(h.render(usadas, crudo))

    faltan = sorted(set(comps) - set(h.colocados))
    print("%d de %d componentes colocados" % (len(h.colocados), len(comps)))
    if faltan:
        print("FALTAN: %s" % ", ".join(faltan))
    print("%d cables, %d junturas, %d etiquetas globales"
          % (len(h.cables), len(h.junturas()), len(h.etiquetas)))
    print("-> %s" % SALIDA)
    return 0 if verificar() and not faltan else 1


if __name__ == "__main__":
    sys.exit(main())

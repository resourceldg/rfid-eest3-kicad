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
EPIGRAFE = "ESQUEMA ELECTRICO INTEGRADO - 67 componentes, 34 redes, todo cableado"

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
    defs, crudo = simbolos_alimentacion()
    for f in sorted(glob.glob(os.path.join(PROY, "0*.kicad_sch"))):
        txt = open(f).read()
        for s in find(get(parse(txt), 'lib_symbols'), 'symbol'):
            defs.setdefault(s[1], s)
        for lib_id, bloque in bloques_simbolo(txt):
            crudo.setdefault(lib_id, bloque)
    return defs, crudo


LIB_POTENCIA = "/usr/share/kicad/symbols/power.kicad_sym"

# red -> forma de la que se deriva el simbolo. KiCad saca el nombre de la red
# del campo Value del simbolo de alimentacion, asi que alcanza con clonar la
# forma (triangulo de masa o flecha de riel) y renombrarla.
ALIMENTACIONES = {
    "GND": "GND", "GND_POWER": "GND",
    "+3V3": "+12V", "+5V": "+12V", "+12V_IN": "+12V",
    "+12V_LOCK": "+12V", "+12V_AUX": "+12V",
}


def simbolos_alimentacion():
    """Deriva un simbolo de alimentacion por cada riel del proyecto."""
    txt = open(LIB_POTENCIA).read()
    formas = {}
    for m in re.finditer(r'\n\t\(symbol "([^"]+)"\n', txt):
        if m.group(1) not in ("GND", "+12V"):
            continue
        ini, prof, k = m.start() + 1, 0, m.start() + 1
        while True:
            if txt[k] == '(':
                prof += 1
            elif txt[k] == ')':
                prof -= 1
                if prof == 0:
                    break
            k += 1
        formas[m.group(1)] = txt[ini:k + 1]
    defs, crudo = {}, {}
    for red, forma in ALIMENTACIONES.items():
        base = formas[forma]
        nuevo = base
        for viejo in ('(symbol "%s"' % forma, '(symbol "%s_0_1"' % forma,
                      '(symbol "%s_1_1"' % forma, '(property "Value" "%s"' % forma):
            nuevo = nuevo.replace(viejo, viejo.replace(forma, red, 1))
        # De aca saca KiCad el nombre de la red. La biblioteca de sistema lo
        # deja vacio, y con el pin sin nombre los rieles se funden todos en uno.
        nuevo = nuevo.replace('(name ""', '(name "%s"' % red, 1)
        lib_id = "power:" + red
        crudo[lib_id] = nuevo.replace('(symbol "%s"' % red, '(symbol "%s"' % lib_id, 1)
        defs[lib_id] = parse(crudo[lib_id])
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
        self.potencia = []    # (ref, lib_id, x, y, red)
        self.nombres = []     # (texto, x, y)

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

    def alim(self, punto, red, largo=6.35, jog=0.0):
        """Simbolo de alimentacion al final de un tramo corto.

        La masa cuelga hacia abajo y los rieles hacia arriba, que es como se
        leen. `jog` corre el simbolo en horizontal antes de bajar o subir: hace
        falta cuando el pin sale de una hilera, porque un tramo vertical que
        arranca en el medio de un conector le pasa por encima a los pines
        vecinos y los pone en cortocircuito.
        """
        x, y = punto
        abajo = red.startswith("GND")
        codo = (round(x + jog, 4), y)
        fin = (codo[0], round(y + largo, 4) if abajo else round(y - largo, 4))
        self.cable(punto, codo)
        self.cable(codo, fin)
        ref = "#PWR%03d" % (len(self.potencia) + 1)
        self.potencia.append((ref, "power:" + red, fin[0], fin[1], red))
        return fin

    def hilera(self, ref, asignacion, sentido=-1, base=5.08, paso=3.81, largo=1.27):
        """Reparte simbolos de alimentacion sobre los pines de un conector.

        La clave es que el tramo vertical sea mas corto que el paso entre
        pines. Con 2,54 mm de paso, cualquier bajada de 8 mm sale del pin y
        entra en la fila del vecino: son dos redes distintas tocandose. Con
        1,27 mm el tramo muere antes de llegar y no hay forma de que se crucen,
        aunque uno suba y el otro baje.

        El tramo horizontal escalonado es solo para que los simbolos no se
        amontonen unos encima de otros.
        """
        pines = sorted(asignacion, key=lambda p: self.p(ref, p)[1])
        for i, pin in enumerate(pines):
            self.alim(self.p(ref, pin), asignacion[pin], largo,
                      jog=sentido * (base + paso * i))

    def nombre(self, punto, red):
        """Nombra una red que ya esta cableada.

        No conecta nada: el cobre entre los dos pines ya existe. Es una
        etiqueta local puesta encima del cable para que la red tenga el mismo
        nombre que en el esquema de origen y se pueda seguir de un lado al
        otro de la hoja. Sin esto KiCad la bautiza Net-(J13-Pin_9) y deja de
        significar nada.
        """
        self.nombres.append((red, punto[0], punto[1]))

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
        puntos += [(l[1], l[2]) for l in self.nombres]
        puntos += list(self.pines.values())
        # el cuerpo de un simbolo sobresale de sus pines: si solo se miran los
        # pines, el marco termina cortando al conector del borde
        for x, y, _, _, _ in self.colocados.values():
            puntos += [(x - 5, y - 5), (x + 5, y + 5)]
        for _, _, x, y, red in self.potencia:
            puntos += [(x, y + 4.5)] if red.startswith("GND") else [(x, y - 4.5)]
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

        for (red, x, y) in self.nombres:
            A('\t(label "%s"' % esc(red))
            A('\t\t(at %s %s 0)' % (n(x), n(y)))
            A('\t\t(effects (font (size 1.27 1.27)) (justify left bottom))')
            A('\t\t(uuid "%s")' % uid("lbl%s%s%s" % (red, x, y)))
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

        for ref, lib, x, y, red in self.potencia:
            A('\t(symbol')
            A('\t\t(lib_id "%s")' % esc(lib))
            A('\t\t(at %s %s 0)' % (n(x), n(y)))
            A('\t\t(unit 1)')
            A('\t\t(exclude_from_sim no)')
            A('\t\t(in_bom yes)')
            A('\t\t(on_board yes)')
            A('\t\t(dnp no)')
            A('\t\t(uuid "%s")' % uid("pwr" + ref))
            A(propiedad("Reference", ref, x, y + 2.54, oculto=True))
            A(propiedad("Value", red, x + 2.0, y + (3.2 if red.startswith("GND") else -1.2),
                        tam=1.27))
            A(propiedad("Footprint", "", x, y, oculto=True))
            A('\t\t(pin "1" (uuid "%s"))' % uid("pwrpin" + ref))
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

# Senales que salen del ESP32, en el orden en que aparecen sus pines. Cada una
# se lleva un canal vertical propio: es un mazo, no un manojo de etiquetas.
SENALES = [
    (5, "ESP_EN"), (7, "DOOR_REED"), (9, "PIR_IN"), (11, "CABINET_SENSOR"),
    (13, "PIR_TAMPER"), (15, "LED_OK"), (17, "LED_ERROR"), (19, "BUZZER"),
    (21, "LOCK_GATE"), (29, "RFID_RST"), (31, "RFID_SS"), (33, "RFID_MOSI"),
    (35, "RFID_SCK"), (37, "RFID_MISO"),
]


def armar(h):
    """Una sola hoja con todo cableado punta a punta.

    El ESP32 va a la izquierda, girado para que su hilera impar mire hacia
    afuera, y de ahi sale un mazo de catorce canales verticales que reparte
    cada señal a su bloque. No hay una sola etiqueta de señal: si dos pines
    estan conectados, hay cobre dibujado entre ellos. Lo unico que se resuelve
    con simbolo son los rieles de alimentacion, porque una masa de treinta
    nodos cableada a mano no se lee.
    """
    h.poner("J13", 52, 174, 0, 'y')
    canal = {}
    for i, (pin, red) in enumerate(SENALES):
        canal[red] = 66 + 2.54 * i

    def sale(red, destino, pin=None):
        """Lleva una señal desde su pin de J13 hasta donde haga falta."""
        pin = pin or dict((r, p) for p, r in SENALES)[red]
        origen = h.p("J13", pin)
        cx = canal[red]
        h.cable(origen, (cx, origen[1]), (cx, destino[1]), destino)
        h.nombre((origen[0] + 1.5, origen[1]), red)

    # ---------------------------------------------------- rieles del ESP32
    h.hilera("J13", {1: "+3V3", 3: "+3V3", 43: "GND"}, sentido=+1)
    h.hilera("J13", {2: "GND", 42: "GND", 44: "GND"}, sentido=-1)
    # el +5V no puede subir: se llevaria por delante las señales de arriba
    p41 = h.p("J13", 41)
    h.cable(p41, (72, p41[1]), (72, 214), (116, 214))
    h.alim((116, 214), "+5V", 8.89)
    h.rotulo("2 - CONTROLADOR ESP32-S3", 30, 140)

    # ---------------------------------------------------- soporte del ESP32
    h.poner("R17", 140, 118, 270)
    h.poner("C5", 165, 118)
    h.poner("TP4", 190, 110, 180)
    sale("ESP_EN", h.p("R17", 2))
    h.alim(h.p("R17", 1), "+3V3", 8.89)
    h.alim(h.p("C5", 1), "+3V3", 8.89)
    h.alim(h.p("C5", 2), "GND", 8.89)
    h.cable(h.p("TP4", 1), (190, 118))
    h.alim((190, 118), "+3V3", 8.89)
    h.cable((165, 114.19), (190, 114.19))
    h.texto("El modulo genera +3V3 y lo entrega por los pines 1 y 3.", 116, 132, 1.6, False)
    h.texto("Se alimenta con +5V por el pin 41. R17 sostiene EN.", 116, 136, 1.6, False)

    # ---------------------------------------------------- 1 ALIMENTACION
    h.rotulo("1 - ALIMENTACION Y PROTECCION", 24, 38)
    h.poner("J1", 34, 52, 0, 'y')
    h.poner("D1", 62, 52, 180)
    h.poner("F1", 90, 52, 90)
    h.poner("TP1", 48, 44, 180)
    h.poner("TP2", 108, 44, 180)
    h.cable(h.p("J1", 1), h.p("D1", 2))
    h.cable(h.p("D1", 1), h.p("F1", 1))
    h.cable(h.p("TP1", 1), (48, 52))
    h.cable(h.p("TP2", 1), (108, 52))
    h.alim((44, 52), "+12V_IN", 8.89)
    h.cable(h.p("F1", 2), (300, 52))
    h.poner("NT1", 250, 96)
    h.cable(h.p("J1", 2), (39.08, 96), h.p("NT1", 1))
    h.alim((300, 52), "+12V_LOCK", 8.89)
    h.alim((120, 96), "GND_POWER", 8.89)

    for ref, x in (("C1", 140), ("C2", 165), ("D5", 190)):
        h.poner(ref, x, 74, 270 if ref == "D5" else 0)
        h.cable(h.p(ref, 1), (x, 52))
        h.cable(h.p(ref, 2), (x, 96))

    h.poner("F2", 230, 70, 90)
    h.cable((215, 52), (215, 70), h.p("F2", 1))
    h.alim(h.p("F2", 2), "+12V_AUX", 8.89)

    h.poner("TP6", 220, 106, 180)
    h.poner("TP5", 285, 106, 180)
    h.cable(h.p("TP6", 1), (220, 96))
    h.cable(h.p("NT1", 2), (285, 96))
    h.cable(h.p("TP5", 1), (285, 96))
    h.alim((285, 96), "GND", 8.89)
    h.texto("NT1 es el unico puente entre la masa de potencia y la de la logica.", 236, 112, 1.6, False)
    h.texto("En la placa esta pegado a J1, a proposito.", 236, 116, 1.6, False)

    h.poner("J2", 350, 62)
    h.poner("TP3", 400, 46, 180)
    h.cable((300, 52), (330, 52), (330, 59.46), h.p("J2", 1))
    h.hilera("J2", {2: "GND", 4: "GND"})
    h.cable(h.p("J2", 3), (400, 64.54), (400, 54))
    h.cable(h.p("TP3", 1), (400, 54))
    h.alim((400, 54), "+5V", 8.89)
    h.texto("modulo buck 12 V -> 5 V", 330, 44, 1.6, False)
    for ref, x in (("C3", 425), ("C4", 450)):
        h.poner(ref, x, 70)
        h.cable(h.p(ref, 1), (x, 54))
        h.alim(h.p(ref, 2), "GND", 8.89)
    h.cable((400, 54), (450, 54))

    # ---------------------------------------------------- 4 SENSORES
    h.rotulo("4 - SENSORES", 288, 140)
    filas = [
        ("DOOR_REED", 160, "J6", 1, "R1", "C7", "D6", "reed de puerta (NC)"),
        ("CABINET_SENSOR", 192, "J8", 3, "R2", "C8", "D8", "tamper del gabinete"),
    ]
    for red, y, conn, spin, rpu, cf, tvs, nota in filas:
        sale(red, (240, y))
        h.poner(rpu, 240, y - 18)
        h.cable(h.p(rpu, 2), (240, y))
        h.alim(h.p(rpu, 1), "+3V3", 8.89)
        h.poner(cf, 275, y + 14)
        h.cable((240, y), (275, y), h.p(cf, 1))
        h.alim(h.p(cf, 2), "GND", 8.89)
        h.poner(tvs, 310, y + 14, 270)
        h.cable((275, y), (310, y), h.p(tvs, 1))
        h.alim(h.p(tvs, 2), "GND", 8.89)
        desfase = 2.54 if conn == "J8" else 0
        h.poner(conn, 380, y - desfase)
        h.cable((310, y), h.p(conn, spin))
        h.texto(nota, 350, y - 14, 1.6, False)
        h.hilera(conn, {1: "+3V3", 2: "GND"} if conn == "J8" else {2: "GND"})

    # PIR: contacto de alarma
    sale("PIR_IN", (240, 224))
    h.poner("C10", 250, 238); h.poner("R14", 285, 224, 270)
    h.poner("R13", 320, 206); h.poner("D7", 350, 238, 270); h.poner("J12", 400, 221.46)
    h.cable((240, 224), h.p("R14", 2))
    h.cable((250, 224), h.p("C10", 1))
    h.poner("TP13", 265, 212, 180)
    h.cable(h.p("TP13", 1), (265, 224))
    h.alim(h.p("C10", 2), "GND", 8.89)
    h.cable(h.p("R14", 1), (320, 224))
    h.cable(h.p("R13", 2), (320, 224))
    h.alim(h.p("R13", 1), "+3V3", 8.89)
    h.cable((320, 224), (350, 224), h.p("D7", 1))
    h.nombre((332, 224), "PIR_CONTACT")
    h.alim(h.p("D7", 2), "GND", 8.89)
    h.cable((350, 224), h.p("J12", 2))
    h.hilera("J12", {1: "GND"})
    h.texto("contacto de alarma del PIR", 370, 210, 1.6, False)

    # PIR: contacto de tamper
    sale("PIR_TAMPER", (240, 258))
    h.poner("C11", 250, 272); h.poner("R16", 285, 258, 270)
    h.poner("R15", 320, 240); h.poner("J10", 400, 258)
    h.cable((240, 258), h.p("R16", 2))
    h.cable((250, 258), h.p("C11", 1))
    h.poner("TP14", 265, 246, 180)
    h.cable(h.p("TP14", 1), (265, 258))
    h.alim(h.p("C11", 2), "GND", 8.89)
    h.cable(h.p("R16", 1), (320, 258))
    h.cable(h.p("R15", 2), (320, 258))
    h.alim(h.p("R15", 1), "+3V3", 8.89)
    h.cable((320, 258), h.p("J10", 1))
    h.nombre((332, 258), "PIR_TAMPER_CONTACT")
    h.hilera("J10", {2: "GND"})
    h.texto("contacto de tamper del PIR", 370, 244, 1.6, False)

    h.poner("J11", 470, 160)
    h.hilera("J11", {1: "+12V_AUX", 2: "GND"})
    h.texto("alimentacion del PIR", 440, 146, 1.6, False)



    # ---------------------------------------------------- 3 LECTOR RFID
    h.rotulo("3 - LECTOR RFID RC522 (solo 3,3 V)", 116, 282)
    h.poner("J5", 470, 300)
    serie = (("RFID_SS", "R9", 1, 250), ("RFID_SCK", "R10", 2, 290),
             ("RFID_MOSI", "R11", 3, 330), ("RFID_RST", "R12", 7, 250))
    for red, ref, jpin, x in serie:
        y = h.p("J5", jpin)[1]
        h.poner(ref, x, y, 90)
        sale(red, h.p(ref, 1))
        h.cable(h.p(ref, 2), h.p("J5", jpin))
    sale("RFID_MISO", h.p("J5", 4))
    h.hilera("J5", {6: "GND", 8: "+3V3"}, sentido=+1, base=8.89)
    h.poner("C6", 380, 316); h.poner("C9", 405, 316)
    for ref in ("C6", "C9"):
        h.alim(h.p(ref, 1), "+3V3", 8.89)
        h.alim(h.p(ref, 2), "GND", 8.89)
    h.texto("33 R en serie: amortiguan el flanco a lo largo de 20-40 cm de cable.", 116, 288, 1.6, False)
    h.texto("El RC522 se alimenta solo con 3,3 V. Nunca con 5 V.", 116, 292, 1.6, False)

    for tp, ref, x in (("TP12", "R9", 235), ("TP9", "R10", 275), ("TP10", "R11", 315)):
        y = h.p(ref, 1)[1]
        h.poner(tp, x, y - 12, 180)
        h.cable(h.p(tp, 1), (x, y), h.p(ref, 1))
    y11 = h.p("J5", 4)[1]
    h.poner("TP11", 430, y11 - 12, 180)
    h.cable(h.p("TP11", 1), (430, y11))

    # ---------------------------------------------------- 5 SENALIZACION
    h.rotulo("5 - SEÑALIZACION", 116, 332)
    for ref, led, y, red in (("R3", "D2", 342, "LED_OK"), ("R4", "D3", 360, "LED_ERROR")):
        h.poner(ref, 150, y, 90)
        h.poner(led, 195, y, 180)
        sale(red, h.p(ref, 1))
        h.cable(h.p(ref, 2), h.p(led, 2))
        h.alim(h.p(led, 1), "GND", 12.7)

    h.poner("R5", 150, 380, 90)
    h.poner("Q1", 190, 380)
    h.poner("R6", 170, 394)
    h.poner("BZ1", 250, 372.46)
    h.poner("D9", 290, 371.19, 270)
    sale("BUZZER", h.p("R5", 1))
    h.cable(h.p("R5", 2), h.p("Q1", 1))
    h.cable((170, 380), h.p("R6", 1))
    h.alim(h.p("R6", 2), "GND", 6.35)
    h.alim(h.p("Q1", 2), "GND", 8.89)
    h.cable(h.p("Q1", 3), h.p("BZ1", 2))
    h.cable(h.p("BZ1", 2), h.p("D9", 2))
    h.cable(h.p("BZ1", 1), (247.46, 362), (290, 362), h.p("D9", 1))
    h.alim((268, 362), "+5V", 8.89)

    # ---------------------------------------------------- 6 CERRADURA
    h.rotulo("6 - CERRADURA / SOLENOIDE 12 V", 400, 312)
    h.poner("R7", 430, 347, 90)
    h.poner("Q2", 465, 347)
    h.poner("R8", 450, 362)
    h.poner("D4", 520, 338.11, 270)
    h.poner("J9", 560, 339.38)
    h.poner("TP7", 415, 335, 180)
    h.poner("TP8", 540, 352, 180)
    sale("LOCK_GATE", h.p("R7", 1))
    h.cable(h.p("TP7", 1), (415, 347), h.p("R7", 1))
    h.cable(h.p("R7", 2), h.p("Q2", 1))
    h.cable((450, 347), h.p("R8", 1))
    h.alim(h.p("R8", 2), "GND_POWER", 6.35)
    h.alim(h.p("Q2", 2), "GND_POWER", 8.89)
    h.cable(h.p("Q2", 3), (520, 341.92), h.p("J9", 2))
    h.cable(h.p("D4", 2), (520, 341.92))
    h.nombre((500, 341.92), "LOCK_OUT")
    h.cable(h.p("TP8", 1), (540, 341.92))
    h.cable(h.p("D4", 1), (520, 329), (554.92, 329), h.p("J9", 1))
    h.alim((537, 329), "+12V_LOCK", 8.89)
    h.texto("D4 pegado a J9: el lazo de recirculacion tiene que ser chico.", 228, 386, 1.6, False)
    h.texto("R8 mantiene la compuerta abajo mientras el ESP32 arranca.", 228, 390, 1.6, False)

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
        # los simbolos de alimentacion agregan nodos #PWRxxx que en el esquema
        # original no existen, porque alla los rieles van por etiqueta global
        nodos = frozenset((get(x, 'ref')[1], get(x, 'pin')[1]) for x in find(nred, 'node')
                          if not get(x, 'ref')[1].startswith('#'))
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
    usadas = {v[4] for v in h.colocados.values()} | {p[1] for p in h.potencia}
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

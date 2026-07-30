#!/usr/bin/env python3
"""Acorta el lazo de recirculacion de la cerradura moviendo D4 junto a J9.

El emplazamiento original dejaba D4 en (80,50 / 85,75), o sea del lado opuesto
de Q2 respecto del conector de carga. La corriente de recirculacion tenia que
salir de J9, bajar hasta TP8, cruzar al este, subir, pasar de largo el MOSFET y
recien ahi entrar al diodo: unos 53 mm de perimetro encerrando un area grande.

Cuando Q2 corta, la bobina de la cerradura fuerza esa corriente a seguir
circulando y se va por D4. Todo lo que ese lazo encierra es inductancia
parasita, y esa inductancia se convierte en un pico de tension sobre el drain
del MOSFET. Por eso el diodo va pegado a la carga, no pegado al transistor.

D4 pasa a (65,58 / 81,95), justo arriba de J9 y con el mismo orden de pines:
el pad 1 (catodo, +12V_LOCK) cae sobre el pin 1 de J9 y el pad 2 (anodo,
LOCK_OUT) sobre el pin 2. Quedan dos bajadas paralelas de 7 mm.

Se corre despues de autorutear y antes de planos_masa.py, o solo, sobre una
placa ya ruteada: reescribe unicamente las pistas de la esquina de potencia.
"""
import sys
import pcbnew

V = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
MM = pcbnew.ToMM

D4_DESTINO = (65.58, 81.95)

# Pistas que dejan de tener sentido con D4 en su lugar nuevo.
# El ramal de +12V_LOCK por y=82,92 existia solo para alcanzar el catodo, y el
# rodeo de LOCK_OUT por TP8 era la unica forma de llegar al anodo desde el sur.
BORRAR = [
    ("+12V_LOCK", (63.04, 88.90), (69.02, 82.92)),
    ("+12V_LOCK", (69.02, 82.92), (75.67, 82.92)),
    ("+12V_LOCK", (75.67, 82.92), (78.50, 85.75)),
    ("/6_CERRADURA_12V/LOCK_OUT", (65.82, 96.82), (65.50, 96.50)),
    ("/6_CERRADURA_12V/LOCK_OUT", (74.04, 96.82), (65.82, 96.82)),
    ("/6_CERRADURA_12V/LOCK_OUT", (75.99, 94.87), (74.04, 96.82)),
    ("/6_CERRADURA_12V/LOCK_OUT", (75.99, 88.25), (75.99, 94.87)),
    ("/6_CERRADURA_12V/LOCK_OUT", (75.99, 88.25), (80.13, 88.25)),
    ("/6_CERRADURA_12V/LOCK_OUT", (80.13, 88.25), (82.50, 85.88)),
    ("/6_CERRADURA_12V/LOCK_OUT", (82.50, 85.88), (82.50, 85.75)),
]

# El lazo propiamente dicho: dos bajadas rectas y paralelas de J9 a D4.
LAZO = [
    ("+12V_LOCK", [(63.04, 88.90), (63.04, 82.49), (63.58, 81.95)], 2.0, "F.Cu"),
    ("/6_CERRADURA_12V/LOCK_OUT", [(68.12, 88.90), (68.12, 82.49), (67.58, 81.95)], 2.0, "F.Cu"),
]

# Del anodo al drain de Q2, rodeando el encapsulado por el norte y el este.
# No forma parte del lazo de recirculacion; va aparte para no estrecharlo.
DRAIN = [
    ("/6_CERRADURA_12V/LOCK_OUT",
     [(67.58, 81.95), (68.33, 82.70), (76.30, 82.70), (77.50, 83.90), (77.50, 88.25), (75.99, 88.25)],
     2.0, "F.Cu"),
]


def igual(p, q, tol=0.005):
    return abs(MM(p.x) - q[0]) < tol and abs(MM(p.y) - q[1]) < tol


def ya_existe(pistas, red, a, b, capa):
    """Para poder correr esto dos veces sin duplicar cobre encima de si mismo."""
    for t in pistas:
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != red or t.GetLayer() != capa:
            continue
        if (igual(t.GetStart(), a) and igual(t.GetEnd(), b)) or \
           (igual(t.GetStart(), b) and igual(t.GetEnd(), a)):
            return True
    return False


def perimetro_lazo(placa):
    """Suma de las dos ramas que unen J9 con D4, que es lo que hay que minimizar."""
    j9 = placa.FindFootprintByReference("J9")
    d4 = placa.FindFootprintByReference("D4")
    pares = []
    for pj in j9.Pads():
        for pd in d4.Pads():
            if pj.GetNetname() == pd.GetNetname():
                dx = MM(pj.GetPosition().x - pd.GetPosition().x)
                dy = MM(pj.GetPosition().y - pd.GetPosition().y)
                pares.append((pj.GetNetname(), (dx * dx + dy * dy) ** 0.5))
    return pares


def main():
    ruta = sys.argv[1]
    B = pcbnew.LoadBoard(ruta)
    capas = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    # GetTracks() no sobrevive a un Remove(): hay que quedarse con la lista.
    pistas = B.GetTracks()

    print("distancia pad a pad J9<->D4 ANTES:")
    for red, d in perimetro_lazo(B):
        print("   %-28s %5.2f mm" % (red, d))

    borradas = 0
    for red, a, b in BORRAR:
        for t in pistas:
            if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != red:
                continue
            if (igual(t.GetStart(), a) and igual(t.GetEnd(), b)) or \
               (igual(t.GetStart(), b) and igual(t.GetEnd(), a)):
                B.Remove(t)
                borradas += 1
    print("\npistas obsoletas borradas: %d de %d" % (borradas, len(BORRAR)))

    d4 = B.FindFootprintByReference("D4")
    d4.SetPosition(V(*D4_DESTINO))
    print("D4 reubicado en (%.2f, %.2f)" % D4_DESTINO)

    for red, puntos, ancho, capa in LAZO + DRAIN:
        nuevos = 0
        for a, b in zip(puntos, puntos[1:]):
            if ya_existe(pistas, red, a, b, capas[capa]):
                continue
            t = pcbnew.PCB_TRACK(B)
            t.SetStart(V(*a)); t.SetEnd(V(*b))
            t.SetWidth(pcbnew.FromMM(ancho))
            t.SetLayer(capas[capa])
            t.SetNet(B.FindNet(red))
            B.Add(t)
            nuevos += 1
        largo = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
                    for a, b in zip(puntos, puntos[1:]))
        print("  %-28s %d/%d tramos nuevos, %.1f mm de %.1f mm en %s" % (
            red, nuevos, len(puntos) - 1, largo, ancho, capa))

    pcbnew.ZONE_FILLER(B).Fill(B.Zones())
    B.Save(ruta)

    print("\ndistancia pad a pad J9<->D4 DESPUES:")
    for red, d in perimetro_lazo(B):
        print("   %-28s %5.2f mm" % (red, d))


if __name__ == "__main__":
    main()

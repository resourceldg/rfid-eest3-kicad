#!/usr/bin/env python3
"""Los dos retoques que quedan despues de rutear: alivios termicos y serigrafia.

1. Conexion solida a plano en dos pads de masa.

   El DRC marcaba J5 pad 6 con un solo radio termico (el minimo son dos) y J2
   pad 4 con sus cuatro radios cayendo en una isla aislada del plano. El alivio
   termico existe para que el soldador no chupe calor al plano; en un pad de
   masa de un modulo de RF, ese ahorro de calor cuesta impedancia de retorno.
   Los dos pasan a conexion solida.

2. Designadores de serigrafia que se pisan.

   No afectan al cobre, pero una serigrafia ilegible en una placa educativa
   —donde el que arma la placa es el que aprende a leerla— es un defecto real.

   La reubicacion la dirige el propio DRC, no una heuristica: se corre
   kicad-cli, se leen las infracciones silk_overlap, se mueve unicamente el
   texto que aparece en cada una y se vuelve a correr. Un chequeo por caja
   envolvente propio marca de mas —las cajas de un texto rotado son mucho mas
   grandes que su geometria real— y termina moviendo designadores que estaban
   perfectamente bien.
"""
import json
import subprocess
import sys
import tempfile

import pcbnew

MM = pcbnew.ToMM
PADS_SOLIDOS = [("J5", "6"), ("J2", "4")]
RONDAS = 20
# Mover un designador para que deje de pisar a un vecino sirve de poco si
# termina encima de un pad: se corrigen las dos cosas a la vez.
TIPOS = ("silk_overlap", "silk_over_copper")

# Candidatos de reubicacion en mm respecto del centro de la huella, del mas
# pegado al mas lejano. Cada texto avanza en esta lista cada vez que el DRC lo
# vuelve a marcar, asi que nunca oscila entre dos posiciones.
OFFSETS = [(0, -2.2), (0, 2.2), (-3.2, 0), (3.2, 0),
           (0, -3.4), (0, 3.4), (-4.8, 0), (4.8, 0),
           (-3.6, -2.6), (3.6, -2.6), (-3.6, 2.6), (3.6, 2.6),
           (0, -4.6), (0, 4.6), (-6.4, 0), (6.4, 0),
           (-5.4, -3.8), (5.4, -3.8), (-5.4, 3.8), (5.4, 3.8),
           (0, -5.8), (0, 5.8), (-8.0, 0), (8.0, 0),
           (-7.0, -5.0), (7.0, -5.0), (-7.0, 5.0), (7.0, 5.0)]


def drc(ruta):
    """Infracciones de serigrafia segun KiCad, con el uuid de cada elemento."""
    with tempfile.NamedTemporaryFile(suffix=".json") as salida:
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json",
                        "--severity-all", "-o", salida.name, ruta],
                       check=True, capture_output=True)
        d = json.load(open(salida.name))
    return [v for v in d["violations"] if v["type"] in TIPOS]


def textos_moviles(placa):
    """uuid -> (huella, texto) de todo lo que se puede reubicar en serigrafia."""
    idx = {}
    for f in placa.GetFootprints():
        for it in [f.Reference()] + list(f.GraphicalItems()):
            if it.GetLayer() != pcbnew.F_SilkS:
                continue
            if it is not f.Reference() and not isinstance(it, pcbnew.PCB_TEXT):
                continue
            idx[it.m_Uuid.AsString()] = (f, it)
    return idx


def acomodar_serigrafia(ruta):
    intento = {}
    for ronda in range(1, RONDAS + 1):
        viol = drc(ruta)
        print("  ronda %2d: %d infracciones de serigrafia" % (ronda, len(viol)))
        if not viol:
            return True, []
        placa = pcbnew.LoadBoard(ruta)
        idx = textos_moviles(placa)
        movio = False
        for v in viol:
            for item in v["items"]:
                if item["uuid"] not in idx:
                    continue
                f, texto = idx[item["uuid"]]
                clave = item["uuid"]
                i = intento.get(clave, -1) + 1
                if i >= len(OFFSETS):
                    continue
                intento[clave] = i
                dx, dy = OFFSETS[i]
                centro = f.GetPosition()
                texto.SetPosition(pcbnew.VECTOR2I(centro.x + pcbnew.FromMM(dx),
                                                  centro.y + pcbnew.FromMM(dy)))
                movio = True
                break
        placa.Save(ruta)
        if not movio:
            break
    return False, [i["description"] for v in drc(ruta) for i in v["items"]]


def main():
    ruta = sys.argv[1]
    B = pcbnew.LoadBoard(ruta)

    print("conexion solida a plano:")
    for ref, num in PADS_SOLIDOS:
        f = B.FindFootprintByReference(ref)
        for p in f.Pads():
            if p.GetNumber() == num:
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
                print("  %s pad %s [%s]" % (ref, num, p.GetNetname()))
    pcbnew.ZONE_FILLER(B).Fill(B.Zones())
    B.Save(ruta)

    print("\nserigrafia (dirigida por DRC):")
    limpio, resto = acomodar_serigrafia(ruta)
    if limpio:
        print("  serigrafia sin superposiciones")
    else:
        print("  quedan superposiciones sin resolver automaticamente:")
        for d in sorted(set(resto)):
            print("    %s" % d)

    placa = pcbnew.LoadBoard(ruta)
    pcbnew.ZONE_FILLER(placa).Fill(placa.Zones())
    placa.Save(ruta)


if __name__ == "__main__":
    main()

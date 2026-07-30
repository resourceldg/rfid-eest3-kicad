#!/usr/bin/env python3
"""Las dos conexiones que el autorouter no puede hacer. Se ruteán primero,
se bloquean, y despues el autorouter completa el resto alrededor.

1. Fuente de Q2 -> plano GND_POWER.
   La clase LOCK_POWER pide 2,0 mm y el pad de un SOT-23 mide 0,6 mm: ninguna
   pista de 2 mm sale de ahi sin pisar el drain. Se hace con un tramo corto de
   1,0 mm y una via de 0,8 mm que baja al plano, que es el retorno de 1,8 A.

2. +3V3 del pin 3 de J13 hacia el norte.
   La fila impar de J13 son 22 pads a 2,54 mm: entre dos pads contiguos quedan
   0,74 mm y no pasa ni una pista de 0,25 mm con su margen. La unica salida es
   por debajo del modulo y rodeando el extremo oeste (el este es area de antena,
   x >= 147, donde no se permite cobre). El +3V3 lo genera el DevKit y alimenta
   al RC522, asi que esta conexion es obligatoria.
"""
import sys
import pcbnew

V = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

PISTAS = [
    # (red, [puntos], ancho, capa)
    ("GND_POWER", [(72.99, 86.65), (72.99, 88.30)], 1.0, "F.Cu"),
    ("+3V3", [(146.40, 73.00), (146.40, 78.00), (94.30, 78.00), (94.30, 70.00)], 0.8, "F.Cu"),
]
VIAS = [
    # (red, x, y, diametro, taladro)
    ("GND_POWER", 72.99, 88.30, 0.8, 0.4),
]


def main():
    ruta = sys.argv[1]
    B = pcbnew.LoadBoard(ruta)
    capas = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}

    for red, puntos, ancho, capa in PISTAS:
        for a, b in zip(puntos, puntos[1:]):
            t = pcbnew.PCB_TRACK(B)
            t.SetStart(V(*a)); t.SetEnd(V(*b))
            t.SetWidth(pcbnew.FromMM(ancho))
            t.SetLayer(capas[capa])
            t.SetNet(B.FindNet(red))
            t.SetLocked(True)
            B.Add(t)
        print("%-10s %d tramos de %.2f mm en %s (bloqueados)" % (red, len(puntos) - 1, ancho, capa))

    for red, x, y, dia, taladro in VIAS:
        v = pcbnew.PCB_VIA(B)
        v.SetPosition(V(x, y))
        v.SetWidth(pcbnew.FromMM(dia))
        v.SetDrill(pcbnew.FromMM(taladro))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(B.FindNet(red))
        v.SetLocked(True)
        B.Add(v)
        print("%-10s via %.1f/%.1f mm en (%.2f,%.2f) (bloqueada)" % (red, dia, taladro, x, y))

    pcbnew.ZONE_FILLER(B).Fill(B.Zones())
    B.Save(ruta)


if __name__ == "__main__":
    main()

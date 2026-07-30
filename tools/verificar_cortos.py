#!/usr/bin/env python3
"""Busca nodos del resumen que unan pines de dos redes distintas.

Con doscientos treinta cables no alcanza con mirar el dibujo. Esto arma la
conectividad a partir de la geometria, agrupa lo que se toca y compara cada
grupo contra el netlist real: si un grupo abarca pines de dos redes, hay un
cruce mal hecho y se informa en que zona de la hoja esta.

Encontro ocho cortocircuitos la primera vez que se corrio, todos por la misma
causa: un tramo vertical de 8 mm que sale de un pin y entra en la fila del
vecino, con los pines a 2,54 mm de paso.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import esquema_resumen as E

defs, crudo = E.cargar_simbolos()
comps = E.cargar_netlist()
h = E.Hoja(defs, comps); E.armar(h); h.resolver()

real = E.redes_de(os.path.join(E.PROY, "rfid-control-acceso-eest3.kicad_sch"))
pin2red = {}
for nodos, nombre in real.items():
    for rp in nodos: pin2red[rp] = nombre

padre = {}
def find(a):
    padre.setdefault(a,a)
    while padre[a]!=a: padre[a]=padre[padre[a]]; a=padre[a]
    return a
def union(a,b):
    ra,rb=find(a),find(b)
    if ra!=rb: padre[ra]=rb
for a,b in h.cables: union(a,b)

grupos = {}
for (ref,pin),pt in h.pines.items():
    if pt in padre:
        grupos.setdefault(find(pt), []).append((ref,pin))
malos = 0
for raiz, pines in grupos.items():
    redes = {pin2red.get(rp) for rp in pines if rp in pin2red}
    redes.discard(None)
    if len(redes) > 1:
        malos += 1
        pts = [p for p in padre if find(p)==raiz]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        print("CORTO entre %s" % ", ".join(sorted(redes)))
        print("   zona x %.0f..%.0f  y %.0f..%.0f   pines: %s" % (
            min(xs),max(xs),min(ys),max(ys),
            " ".join(sorted("%s.%s"%rp for rp in pines))[:200]))
print("grupos con mas de una red:", malos)
sys.exit(1 if malos else 0)

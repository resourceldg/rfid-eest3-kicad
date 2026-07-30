#!/usr/bin/env python3
"""Crea los dos planos de masa en B.Cu antes de autorutear.

GND_POWER ocupa la esquina inferior izquierda (retorno de 1,8 A de la
cerradura). GND ocupa el resto en forma de L, e incluye la zona del DevKit.
Entre los dos planos queda un hueco: se tocan unicamente a traves de NT1.
"""
import sys
import pcbnew

# esquina de potencia: J1, D1, F1, C1, C2, D5, NT1, J9, Q2, D4, R7, R8, TP1/2/6/7/8
POTENCIA = [(21, 80.5), (87, 80.5), (87, 118), (21, 118)]
# resto de la placa, en L, dejando 1,5 mm de hueco con el plano de potencia
LOGICA = [(21, 21), (159, 21), (159, 119), (89, 119), (89, 79), (21, 79)]


def zona(placa, red, puntos, nombre):
    z = pcbnew.ZONE(placa)
    z.SetLayer(pcbnew.B_Cu)
    z.SetNet(placa.FindNet(red))
    z.SetZoneName(nombre)
    o = z.Outline()
    o.NewOutline()
    for x, y in puntos:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    placa.Add(z)
    return z


def main():
    ruta = sys.argv[1]
    placa = pcbnew.LoadBoard(ruta)

    previas = [z for z in placa.Zones() if z.GetZoneName() in ("plano_gnd_power", "plano_gnd")]
    for z in previas:
        placa.Remove(z)
    if previas:
        print("reemplazo %d plano(s) anterior(es)" % len(previas))

    zona(placa, "GND_POWER", POTENCIA, "plano_gnd_power")
    zona(placa, "GND", LOGICA, "plano_gnd")
    pcbnew.ZONE_FILLER(placa).Fill(placa.Zones())
    placa.Save(ruta)

    for z in placa.Zones():
        if z.GetZoneName():
            print("%-16s red %-10s area rellena %.1f mm2" % (
                z.GetZoneName(), z.GetNetname(),
                pcbnew.ToMM(pcbnew.ToMM(z.GetFilledArea()))))


if __name__ == "__main__":
    main()

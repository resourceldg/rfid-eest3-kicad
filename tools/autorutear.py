#!/usr/bin/env python3
"""Ida y vuelta KiCad <-> Freerouting sin abrir la GUI.

Exporta la placa a Specctra DSN, la rutea con Freerouting y vuelve a importar
el .SES sobre una copia. Nunca escribe sobre el .kicad_pcb original salvo que
se pida --en-sitio, y en ese caso guarda un .bak antes.

Las pistas *bloqueadas* se exportan como (type fix) y Freerouting no las toca.
Las zonas rellenas se exportan como (plane ...), asi que un plano de GND ya
relleno evita que el autorouter cablee GND pista por pista.

Uso tipico:
    tools/autorutear.py rfid-control-acceso-eest3/rfid-control-acceso-eest3.kicad_pcb
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

BIN_POR_DEFECTO = Path.home() / ".local/opt/freerouting-2.2.4-linux-x64/bin/freerouting"

PLANTILLA_REGLAS = """(rules PCB {nombre}
  (layer_rule F.Cu
    (active on)
    (preferred_direction horizontal)
    (preferred_direction_trace_cost 1.0)
    (against_preferred_direction_trace_cost 2.0)
  )
  (layer_rule B.Cu
    (active on)
    (preferred_direction vertical)
    (preferred_direction_trace_cost {costo})
    (against_preferred_direction_trace_cost {costo_contra})
  )
  (autoroute_settings
    (fanout off)
    (autoroute on)
    (postroute on)
    (vias on)
    (via_costs 50)
    (plane_via_costs 5)
    (start_ripup_costs 100)
    (start_pass_no 1)
  )
)
"""


def buscar_binario():
    if os.environ.get("FREEROUTING_BIN"):
        return Path(os.environ["FREEROUTING_BIN"])
    if BIN_POR_DEFECTO.exists():
        return BIN_POR_DEFECTO
    encontrado = shutil.which("freerouting")
    if encontrado:
        return Path(encontrado)
    sys.exit("No encuentro Freerouting. Definí FREEROUTING_BIN apuntando al ejecutable.")


def revisar_pistas_sueltas(placa, pcbnew):
    """Cuenta pistas sin bloquear: el autorouter las puede levantar y rehacer."""
    sueltas = 0
    bloqueadas = 0
    for t in placa.GetTracks():
        if t.IsLocked():
            bloqueadas += 1
        else:
            sueltas += 1
    return sueltas, bloqueadas


def main():
    p = argparse.ArgumentParser(description="Autoruteo de una placa KiCad con Freerouting.")
    p.add_argument("placa", type=Path, help="archivo .kicad_pcb de entrada")
    p.add_argument("-o", "--salida", type=Path, help="destino (por defecto <placa>-autorruteada.kicad_pcb)")
    p.add_argument("--en-sitio", action="store_true", help="escribir sobre la placa original (guarda .bak)")
    p.add_argument("--pasadas", type=int, default=20, help="pasadas maximas del autorouter (20)")
    p.add_argument("--hilos", type=int, default=0, help="hilos de CPU (0 = los que elija Freerouting)")
    p.add_argument("--forzar", action="store_true", help="seguir aunque haya pistas sin bloquear")
    p.add_argument("--costo-dorso", type=float, default=6.0,
                   help="penalizacion de B.Cu para que las señales vayan por F.Cu "
                        "y el dorso quede para los planos (6.0; 1.0 = sin preferencia)")
    p.add_argument("--sin-drc", action="store_true", help="no correr el DRC al terminar")
    args = p.parse_args()

    placa_orig = args.placa.resolve()
    if not placa_orig.exists():
        sys.exit(f"No existe {placa_orig}")

    binario = buscar_binario()

    import pcbnew  # se importa aca para que --help no cargue toda la libreria

    placa = pcbnew.LoadBoard(str(placa_orig))
    sueltas, bloqueadas = revisar_pistas_sueltas(placa, pcbnew)
    print(f"Placa: {placa_orig.name}")
    print(f"  pistas bloqueadas (intocables): {bloqueadas}")
    print(f"  pistas sin bloquear (se pueden rehacer): {sueltas}")
    print(f"  zonas rellenas: {len(placa.Zones())}")

    if sueltas and not args.forzar:
        sys.exit(
            "\nHay pistas sin bloquear. Freerouting las puede levantar y rehacer a su gusto.\n"
            "Bloqueá lo que rutéaste a mano (seleccionar -> Propiedades -> Bloqueado)\n"
            "o volvé a correr con --forzar si no te importa perderlas."
        )

    if args.en_sitio:
        destino = placa_orig
        respaldo = placa_orig.with_suffix(".kicad_pcb.bak")
        shutil.copy2(placa_orig, respaldo)
        print(f"  respaldo: {respaldo.name}")
    else:
        destino = args.salida or placa_orig.with_name(placa_orig.stem + "-autorruteada.kicad_pcb")

    dsn = destino.with_suffix(".dsn")
    ses = destino.with_suffix(".ses")

    print(f"\n1/4 Exportando {dsn.name} ...")
    if not pcbnew.ExportSpecctraDSN(placa, str(dsn)):
        sys.exit("Fallo el export a Specctra DSN.")

    # Freerouting lee el .rules que esta al lado del .dsn. Sin esto mete señales
    # por B.Cu, parte los planos en islas y deja pads de masa sin conectar.
    reglas = dsn.with_suffix(".rules")
    reglas.write_text(PLANTILLA_REGLAS.format(
        nombre=destino.stem, costo=args.costo_dorso, costo_contra=args.costo_dorso * 1.5))

    print("2/4 Ruteando con Freerouting ...")
    cmd = [str(binario), "-de", str(dsn), "-dr", str(reglas),
           "-do", str(ses), "-mp", str(args.pasadas)]
    if args.hilos:
        cmd += ["-mt", str(args.hilos)]
    r = subprocess.run(cmd, text=True, capture_output=True)
    for linea in r.stdout.splitlines():
        if "pass #" in linea or "session completed" in linea or "unrouted" in linea:
            print("   " + linea.split("INFO")[-1].strip())
    if r.returncode != 0 or not ses.exists():
        print(r.stdout[-2000:], file=sys.stderr)
        print(r.stderr[-2000:], file=sys.stderr)
        sys.exit("Freerouting no genero el .SES.")

    print(f"3/4 Importando {ses.name} ...")
    if not pcbnew.ImportSpecctraSES(placa, str(ses)):
        sys.exit("Fallo el import del .SES.")
    if placa.Zones():
        # sin rellenar de nuevo, cada pista nueva bajo un plano aparece como
        # infraccion de margen contra la zona vieja
        pcbnew.ZONE_FILLER(placa).Fill(placa.Zones())
        print("   zonas rellenadas de nuevo")
    placa.Save(str(destino))

    revisada = pcbnew.LoadBoard(str(destino))
    pistas = sum(1 for t in revisada.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T)
    vias = sum(1 for t in revisada.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
    print(f"   quedaron {pistas} pistas y {vias} vias en {destino.name}")

    if args.sin_drc:
        return
    print("4/4 DRC ...")
    rpt = destino.with_name(destino.stem + "-drc.rpt")
    subprocess.run(
        ["kicad-cli", "pcb", "drc", "--severity-error", "--severity-warning",
         "-o", str(rpt), str(destino)],
        text=True,
    )
    print(f"   informe: {rpt}")
    print("\nAbrí la placa en pcbnew y revisá el lazo de la cerradura antes de aceptar nada.")


if __name__ == "__main__":
    main()

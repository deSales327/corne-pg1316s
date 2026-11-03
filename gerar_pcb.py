"""Gera uma PCB reversível no formato Corne (3x6 + 3 polegares) para switches
ultrafinos Kailh PG1316S. O footprint do switch é desenhado aqui a partir da
ficha técnica da Kailh (CPG1316S01D02); díodos e interruptor de energia vêm da PCB
do dust. Cada tecla tem um LED RGB (WS2812B-2020) na cavidade do switch. Controlador
Pro Micro nRF52840 (nice!nano v2 ou clone) com a pinagem do Corne do ZMK, e um
nice!view por cima dele. O conector JST-XH da bateria, o furo para os fios e o botão
de reset são acrescentados depois por finalizar_pcb.py. Uso:

    python gerar_pcb.py <caminho/para/dust.kicad_pcb>

Saídas (na pasta deste script): corne-pg1316s.kicad_pcb e preview.svg
"""
import copy
import math
import os
import re
import sys
import uuid

from shapely import affinity
from shapely.geometry import MultiPoint, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import dumps, find, parse  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Espaçamento para keycaps PG1316S de ~16 x 16 mm (mm)
SX, SY = 17.0, 17.0
# Stagger das colunas do Corne (crkbd), em unidades, para baixo a partir da coluna mais alta.
# c0 = pinky externo ... c5 = indicador interno
STAGGER_U = [0.375, 0.375, 0.125, 0.0, 0.125, 0.25]
X0, Y0 = 100.0, 100.0
ROWS = ['r3', 'r2', 'r1']  # topo, home, baixo (r0 = polegares), como no dust
CAP = (16.5, 16.5)  # keycaps do mikefive (para checagem de colisão)
# O LED fica na cavidade por baixo do switch (y -3,9..-1,15 mm, |x| <= 2,2 mm), que é a
# janela de LED da ficha técnica. O díodo passa para o intervalo entre colunas, na face
# oposta à do switch (os pads existem nas duas faces; solda-se só na face de baixo).
LED_DY = -2.525
DIODE_DX = 8.5

# Pro Micro (vista de cima, USB em cima), pino a pino de cima para baixo. Linhas e colunas
# como no Corne do ZMK (linhas D4..D7, colunas D21..D14), nice!view como no nice_view_adapter
# (CS = D1, MOSI = D2, SCK = D3). O RAW do nice!nano v2 é o BAT+ e o VCC (3,3 V) é cortado
# pelo P0.13, por isso os LEDs ligam-se ao VCC.
MCU_LEFT = ['nv_cs', 'rgb0', 'GND', 'GND', 'nv_mosi', 'nv_sck', 'r3', 'r2', 'r1', 'r0', '', '']
MCU_RIGHT = ['BAT', 'GND', 'RST', 'VCC', 'c0', 'c1', 'c2', 'c3', 'c4', 'c5', '', '']
MCU_LABELS = (['D1', 'D0', 'GND', 'GND', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9'],
              ['RAW', 'GND', 'RST', 'VCC', 'D21', 'D20', 'D19', 'D18', 'D15', 'D14', 'D16', 'D10'])
NICE_VIEW = ['nv_mosi', 'nv_sck', 'VCC', 'GND', 'nv_cs']  # ordem física, vista de cima
# Centro do controlador e posição do interruptor de energia, relativos à tecla c5/r3
MCU_AT = (19.0, 14.75)
PWR_AT = (33.22, 17.25)
# Ordem da cadeia de LEDs: polegares, depois as colunas em serpentina da interna (c5) para a externa
LED_ORDER = [(5, 'r0'), (4, 'r0'), (3, 'r0')] + [
    (c, r) for i, c in enumerate(range(5, -1, -1)) for r in (['r1', 'r2', 'r3'] if i % 2 == 0 else ['r3', 'r2', 'r1'])]


def rot(x, y, a):
    """Roda (x, y) pelo ângulo a do KiCad (graus, anti-horário no ecrã, y para baixo)."""
    r = math.radians(a)
    return x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)


def fmt(v):
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# ---------------------------------------------------------------- layout

def layout():
    keys = []
    for c in range(6):
        x = X0 + c * SX
        for r, row in enumerate(ROWS):
            y = Y0 + STAGGER_U[c] * SY + r * SY
            keys.append(dict(x=x, y=y, a=0.0, col=c, row=row))

    def bottom(c):
        return next(k for k in keys if k['col'] == c and k['row'] == 'r1')

    # Polegares: o primeiro debaixo do indicador, os outros abrem em leque (0°, -15°, -30°),
    # cada um a rodar a partir do canto inferior direito do anterior.
    b4 = bottom(4)
    t = dict(x=b4['x'], y=b4['y'] + SY + 1.0, a=0.0)
    thumbs = [t]
    for a in (-15.0, -30.0):
        px, py = rot(SX / 2, SY / 2, t['a'])
        cx, cy = rot(-SX / 2, SY / 2, a)
        gx, gy = rot(0.5, 0, a)
        t = dict(x=t['x'] + px - cx + gx, y=t['y'] + py - cy + gy, a=a)
        thumbs.append(t)
    for i, t in enumerate(thumbs):
        keys.append(dict(t, col=3 + i, row='r0'))
    return keys


# ---------------------------------------------------------------- footprints

class Board:
    def __init__(self, dust):
        self.dust = dust
        self.nets = ['']
        self.footprints = []

    def net(self, name):
        if name not in self.nets:
            self.nets.append(name)
        return ['net', str(self.nets.index(name)), f'"{name}"']

    def place(self, tpl, x, y, a=None, ref=None, netmap=lambda pad, old: old):
        fp = copy.deepcopy(tpl)
        at = find(fp, 'at')[0]
        a0 = float(at[3]) if len(at) > 3 else 0.0
        a = a0 if a is None else a
        d = a - a0
        fp[fp.index(at)] = ['at', fmt(x), fmt(y)] + ([fmt(a)] if a else [])
        for child in fp:
            if not (isinstance(child, list) and child[0] in ('pad', 'fp_text')):
                continue
            cat = find(child, 'at')[0]
            ang = ((float(cat[3]) if len(cat) > 3 else 0.0) + d) % 360
            child[child.index(cat)] = cat[:3] + ([fmt(ang)] if ang else [])
            if child[0] == 'fp_text' and child[1] == 'reference' and ref:
                child[2] = f'"{ref}"'
            if child[0] == 'pad':
                n = find(child, 'net')
                if n:
                    new = netmap(child[1].strip('"'), n[0][2].strip('"'))
                    if new in ('', '-'):
                        child.remove(n[0])  # pino sem ligação
                    else:
                        child[child.index(n[0])] = self.net(new)
        self.footprints.append(fp)
        return fp


# Footprint reversível do PG1316S. Chassi e furos seguem a ficha técnica da Kailh. Há
# footprints testados com os contactos em sítios diferentes: x = ±2,5 mm (ficha técnica,
# mikefive, ULK) e x = -0,5 / +1,7 mm (Delta Omega rev4). Os pads aqui são largos e cobrem
# os dois (pad 1: -3,275..-0,025; pad 2: +0,925..+3,275), como o reversível do mikefive.
# Os terminais não são simétricos, por isso no verso os pads de contacto estão espelhados; o router
# liga cada contacto da frente ao do verso. Os pads do chassi têm um furo metalizado
# e servem as duas faces. Os pinos de alinhamento (Ø1,0 e Ø1,2) também não são
# simétricos: há furos para as duas faces.
SWITCH_FP = """(footprint "corne:Kailh_PG1316S_reversible" (layer "F.Cu") (tedit 0) (tstamp X)
  (at 0 0)
  (attr smd)
  (fp_text reference "S0" (at 0 -8.75) (layer "F.SilkS") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp X))
  (fp_text value "PG1316S" (at 0 8.75) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))) (tstamp X))
  (fp_rect (start -8 -8.125) (end 8 8.125) (layer "Dwgs.User") (width 0.1) (fill none) (tstamp X))
  (fp_rect (start -6.75 -6.5) (end 6.75 6.5) (layer "F.Fab") (width 0.1) (fill none) (tstamp X))
  (fp_rect (start -6.75 -6.5) (end 6.75 6.5) (layer "B.Fab") (width 0.1) (fill none) (tstamp X))
  (fp_poly (pts (xy -2.2 -3.9) (xy 2.2 -3.9) (xy 2.2 -1.15) (xy -2.2 -1.15)) (layer "Dwgs.User") (width 0.1) (fill none) (tstamp X))
  (fp_line (start -7.85 -7.85) (end -7.85 -7.25) (layer "F.SilkS") (width 0.12) (tstamp X))
  (fp_line (start -7.85 -7.85) (end -7.25 -7.85) (layer "F.SilkS") (width 0.12) (tstamp X))
  (fp_line (start 7.85 7.85) (end 7.85 7.25) (layer "F.SilkS") (width 0.12) (tstamp X))
  (fp_line (start 7.85 7.85) (end 7.25 7.85) (layer "F.SilkS") (width 0.12) (tstamp X))
  (fp_line (start 7.85 -7.85) (end 7.85 -7.25) (layer "B.SilkS") (width 0.12) (tstamp X))
  (fp_line (start 7.85 -7.85) (end 7.25 -7.85) (layer "B.SilkS") (width 0.12) (tstamp X))
  (fp_line (start -7.85 7.85) (end -7.85 7.25) (layer "B.SilkS") (width 0.12) (tstamp X))
  (fp_line (start -7.85 7.85) (end -7.25 7.85) (layer "B.SilkS") (width 0.12) (tstamp X))
  (pad "1" smd rect (at -1.65 2.65) (size 3.25 2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "x") (tstamp X))
  (pad "2" smd rect (at 2.1 2.65) (size 2.35 2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "x") (tstamp X))
  (pad "1" smd rect (at 1.65 2.65) (size 3.25 2) (layers "B.Cu" "B.Paste" "B.Mask") (net 1 "x") (tstamp X))
  (pad "2" smd rect (at -2.1 2.65) (size 2.35 2) (layers "B.Cu" "B.Paste" "B.Mask") (net 1 "x") (tstamp X))
  (pad "3" thru_hole rect (at -6.35 -6) (size 2 2) (drill 0.6) (layers *.Cu *.Mask F.Paste B.Paste) (tstamp X))
  (pad "3" thru_hole rect (at 6.35 -6) (size 2 2) (drill 0.6) (layers *.Cu *.Mask F.Paste B.Paste) (tstamp X))
  (pad "3" thru_hole rect (at -6.35 6) (size 2 2) (drill 0.6) (layers *.Cu *.Mask F.Paste B.Paste) (tstamp X))
  (pad "3" thru_hole rect (at 6.35 6) (size 2 2) (drill 0.6) (layers *.Cu *.Mask F.Paste B.Paste) (tstamp X))
  (pad "" np_thru_hole circle (at -5.8 2.75) (size 1.25 1.25) (drill 1.25) (layers *.Cu *.Mask) (tstamp X))
  (pad "" np_thru_hole circle (at 5.8 -2.75) (size 1.25 1.25) (drill 1.25) (layers *.Cu *.Mask) (tstamp X))
  (pad "" np_thru_hole circle (at 5.8 2.75) (size 1.25 1.25) (drill 1.25) (layers *.Cu *.Mask) (tstamp X))
  (pad "" np_thru_hole circle (at -5.8 -2.75) (size 1.25 1.25) (drill 1.25) (layers *.Cu *.Mask) (tstamp X))
)"""

# LED RGB endereçável WS2812B-2020 (2 x 2 x 0,84 mm), pads da biblioteca do KiCad, nas duas
# faces (espelhado no verso). Pinos: 1 DOUT, 2 GND, 3 DIN, 4 VDD.
LED_FP = """(footprint "corne:WS2812B-2020_reversible" (layer "F.Cu") (tedit 0) (tstamp X)
  (at 0 0)
  (attr smd)
  (fp_text reference "L0" (at 0 -1.6) (layer "F.Fab") hide (effects (font (size 0.5 0.5) (thickness 0.08))) (tstamp X))
  (fp_text value "WS2812B-2020" (at 0 1.6) (layer "F.Fab") hide (effects (font (size 0.5 0.5) (thickness 0.08))) (tstamp X))
  (fp_rect (start -1 -1) (end 1 1) (layer "F.Fab") (width 0.1) (fill none) (tstamp X))
  (fp_rect (start -1 -1) (end 1 1) (layer "B.Fab") (width 0.1) (fill none) (tstamp X))
  (pad "1" smd rect (at -0.915 -0.55) (size 0.7 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "x") (tstamp X))
  (pad "2" smd rect (at -0.915 0.55) (size 0.7 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "x") (tstamp X))
  (pad "3" smd rect (at 0.915 0.55) (size 0.7 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "x") (tstamp X))
  (pad "4" smd rect (at 0.915 -0.55) (size 0.7 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "x") (tstamp X))
  (pad "1" smd rect (at 0.915 -0.55) (size 0.7 0.7) (layers "B.Cu" "B.Paste" "B.Mask") (net 1 "x") (tstamp X))
  (pad "2" smd rect (at 0.915 0.55) (size 0.7 0.7) (layers "B.Cu" "B.Paste" "B.Mask") (net 1 "x") (tstamp X))
  (pad "3" smd rect (at -0.915 0.55) (size 0.7 0.7) (layers "B.Cu" "B.Paste" "B.Mask") (net 1 "x") (tstamp X))
  (pad "4" smd rect (at -0.915 -0.55) (size 0.7 0.7) (layers "B.Cu" "B.Paste" "B.Mask") (net 1 "x") (tstamp X))
)"""


def text(s, x, y, layer, size=0.8, mirror=False, kind='user', angle=0):
    j = ' (justify mirror)' if mirror else ''
    a = f' {angle}' if angle else ''
    return (f'  (fp_text {kind} "{s}" (at {fmt(x)} {fmt(y)}{a}) (layer "{layer}") (effects (font (size {size} {size}) '
            f'(thickness {fmt(size * 0.15)})){j}) (tstamp X))\n')


def mcu_fp():
    """Pro Micro reversível sem pontes: os furos são os mesmos nas duas faces. Na metade
    em que a placa fica com o verso para cima, o controlador monta-se virado para baixo
    (como no Corne), e cada pino volta a cair no mesmo furo."""
    s = '(footprint "corne:ProMicro_reversible" (layer "F.Cu") (tedit 0) (tstamp X)\n  (at 0 0)\n  (attr through_hole)\n'
    s += text('MCU1', 0, -18, 'F.Fab', 1, kind='reference')
    s += '  (fp_rect (start -9 -16.5) (end 9 16.5) (layer "F.Fab") (width 0.1) (fill none) (tstamp X))\n'
    s += '  (fp_rect (start -9 -16.5) (end 9 16.5) (layer "B.Fab") (width 0.1) (fill none) (tstamp X))\n'
    s += '  (fp_rect (start -4 -17.5) (end 4 -11) (layer "Dwgs.User") (width 0.1) (fill none) (tstamp X))\n'
    s += text('nice!nano: COMPONENTES P/ CIMA', 0, 0, 'F.SilkS', 1, angle=90)
    s += text('nice!nano: COMPONENTES P/ BAIXO', 0, 0, 'B.SilkS', 1, mirror=True, angle=90)
    for col, (nets, labels) in enumerate(((MCU_LEFT, MCU_LABELS[0]), (MCU_RIGHT, MCU_LABELS[1]))):
        x = -7.62 if col == 0 else 7.62
        for i, (n, lab) in enumerate(zip(nets, labels)):
            y = -13.97 + i * 2.54
            num = i + 1 + 12 * col
            shape = 'rect' if num == 1 else 'circle'
            s += (f'  (pad "{num}" thru_hole {shape} (at {fmt(x)} {fmt(y)}) (size 1.7 1.7) (drill 1.0) '
                  f'(layers *.Cu *.Mask) (net 1 "{n or "-"}") (tstamp X))\n')
            lx = x + (2.3 if col == 0 else -2.3)
            s += text(lab, lx, y, 'F.SilkS', 0.8)
            s += text(lab, lx, y, 'B.SilkS', 0.8, mirror=True)
    return s + ')'


def niceview_fp():
    """Duas filas de 5 furos para o nice!view: a de cima para a face da frente, a de baixo
    (2,54 mm abaixo, ordem invertida) para o verso. O ecrã fica por cima do controlador."""
    s = '(footprint "corne:nice_view_reversible" (layer "F.Cu") (tedit 0) (tstamp X)\n  (at 0 0)\n  (attr through_hole)\n'
    s += text('DISP1', 0, 5, 'F.Fab', 1, kind='reference')
    s += '  (fp_rect (start -7 -34.4) (end 7 1.6) (layer "F.Fab") (width 0.1) (fill none) (tstamp X))\n'
    s += '  (fp_rect (start -7 -31.86) (end 7 4.14) (layer "B.Fab") (width 0.1) (fill none) (tstamp X))\n'
    s += text('nice!view', 0, -1.9, 'F.SilkS', 0.8)
    s += text('nice!view', 0, 4.45, 'B.SilkS', 0.8, mirror=True)
    for row, (y, nets) in enumerate(((0, NICE_VIEW), (2.54, NICE_VIEW[::-1]))):
        for i, n in enumerate(nets):
            s += (f'  (pad "{i + 1 + 5 * row}" thru_hole circle (at {fmt((i - 2) * 2.54)} {fmt(y)}) (size 1.7 1.7) '
                  f'(drill 1.0) (layers *.Cu *.Mask) (net 1 "{n}") (tstamp X))\n')
    return s + ')'


def templates(dust):
    def ref(fp):
        r = [c for c in find(fp, 'fp_text') if c[1] == 'reference']
        return r[0][2].strip('"') if r else ''

    fps = find(dust, 'footprint')
    by_ref = {(ref(f), find(f, 'layer')[0][1]): f for f in fps}
    return dict(
        switch=parse(SWITCH_FP),
        led=parse(LED_FP),
        mcu=parse(mcu_fp()),
        niceview=parse(niceview_fp()),
        # díodo do dust só com os pads SMD (frente e verso)
        diode=[c for c in by_ref[('D1', '"F.Cu"')]
               if not (isinstance(c, list) and c[0] == 'pad' and c[2] == 'thru_hole')],
        # interruptor de energia do dust, frente e verso
        power=[f for f in fps if ref(f) == 'T1'],
    )


def footprint_hull(fp):
    """Envolvente aproximada (pads + linhas) de um footprint, em coordenadas da placa."""
    at = find(fp, 'at')[0]
    x, y, a = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
    pts = []
    for c in fp:
        if not isinstance(c, list):
            continue
        if c[0] == 'pad':
            px, py = map(float, find(c, 'at')[0][1:3])
            sw, sh = map(float, find(c, 'size')[0][1:3])
            r = max(sw, sh) / 2
            pts += [(px - r, py - r), (px + r, py + r), (px - r, py + r), (px + r, py - r)]
        elif c[0] in ('fp_line',) and find(c, 'layer')[0][1] not in ('"Dwgs.User"', '"Cmts.User"'):
            for k in ('start', 'end'):
                pts.append(tuple(map(float, find(c, k)[0][1:3])))
    world = [(x + dx, y + dy) for dx, dy in (rot(px, py, a) for px, py in pts)]
    return MultiPoint(world).convex_hull


def cell(k, w=SX, h=SY):
    return affinity.translate(affinity.rotate(box(-w / 2, -h / 2, w / 2, h / 2), -k['a']), k['x'], k['y'])


# ---------------------------------------------------------------- main

def main(dust_path):
    dust = parse(open(dust_path, encoding='utf8').read())
    tpl = templates(dust)
    board = Board(dust)
    keys = layout()

    for i, k in enumerate(keys, 1):
        name = f"k_c{k['col']}_{k['row']}"
        k['net'] = name
        board.place(tpl['switch'], k['x'], k['y'], k['a'], f'S{i}',
                    lambda pad, old, k=k: f"c{k['col']}" if pad == '1' else k['net'])
        # o último polegar não tem nada à direita: o díodo fica entre ele e o anterior
        side = -1 if (k['col'], k['row']) == (5, 'r0') else 1
        dx, dy = rot(side * DIODE_DX, 0, k['a'])
        board.place(tpl['diode'], k['x'] + dx, k['y'] + dy, 90 + k['a'], f'D{i}',
                    lambda pad, old, k=k: k['row'] if pad == '1' else k['net'])

    # LEDs: DIN do anterior na cadeia, DOUT para o seguinte
    for n, (c, r) in enumerate(LED_ORDER):
        i, k = next((i, k) for i, k in enumerate(keys, 1) if k['col'] == c and k['row'] == r)
        dx, dy = rot(0, LED_DY, k['a'])
        pins = {'1': f'rgb{n + 1}', '2': 'GND', '3': f'rgb{n}', '4': 'VCC'}
        board.place(tpl['led'], k['x'] + dx, k['y'] + dy, k['a'], f'L{i}', lambda pad, old, p=pins: p[pad])

    # Bloco de eletrónica, à direita da coluna interna: controlador com o USB na borda de
    # cima, nice!view por cima dele (furos logo abaixo), interruptor na borda da direita
    inner_top = next(k for k in keys if k['col'] == 5 and k['row'] == 'r3')
    mx, my = inner_top['x'] + MCU_AT[0], inner_top['y'] + MCU_AT[1]
    board.place(tpl['mcu'], mx, my, 0, 'MCU1', lambda pad, old: old)
    board.place(tpl['niceview'], mx, my + 17.9, 0, 'DISP1', lambda pad, old: old)
    for f in tpl['power']:
        board.place(f, inner_top['x'] + PWR_AT[0], inner_top['y'] + PWR_AT[1], None, 'PWR1')
        if find(f, 'layer')[0][1] == '"B.Cu"':
            # as duas cópias do interruptor (frente/verso) partilham os furos: só a da frente os leva
            fp = board.footprints[-1]
            fp[:] = [c for c in fp if not (isinstance(c, list) and c[0] == 'pad' and c[2] == 'np_thru_hole')]
    cluster_area = box(inner_top['x'] + SX / 2, inner_top['y'] - 2.25,
                       inner_top['x'] + 35.0, inner_top['y'] + 40.2)

    # ---- contorno: união das células das teclas + bloco, fechada e com cantos arredondados
    # (o invólucro convexo bloco+último polegar evita um entalhe entre os dois)
    shape = unary_union([cell(k) for k in keys] + [cluster_area,
                                                   unary_union([cluster_area, cell(keys[-1])]).convex_hull])
    shape = shape.buffer(8, join_style='round').buffer(-8, join_style='round')
    shape = shape.buffer(-1.5, join_style='round').buffer(1.5, join_style='round').simplify(0.02)
    assert shape.geom_type == 'Polygon', shape.geom_type

    # ---- verificações
    problems = []
    caps = [cell(k, *CAP) for k in keys]
    for i in range(len(caps)):
        for j in range(i + 1, len(caps)):
            if caps[i].intersection(caps[j]).area > 0.01:
                problems.append(f'keycaps S{i + 1} e S{j + 1} sobrepõem-se')
    edge = shape.buffer(0.01)
    for fp in board.footprints:
        h = footprint_hull(fp)
        r = [c for c in find(fp, 'fp_text') if c[1] == 'reference'][0][2]
        # o USB-C do XIAO fica 0,37 mm fora da borda de propósito (como no dust)
        if not (shape.buffer(0.5) if r == '"XIAO1"' else edge).contains(h):
            problems.append(f'{r} sai fora do contorno ({h.difference(edge).area:.2f} mm²)')
        if not r.startswith(('"S', '"D', '"L')):
            for i, cap in enumerate(caps):
                if cap.intersection(h).area > 0.5:
                    problems.append(f'{r} fica debaixo do keycap S{i + 1}')

    # ---- escrever o .kicad_pcb
    gr = []
    ring = list(shape.exterior.coords)
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        gr.append(['gr_line', ['start', fmt(x1), fmt(y1)], ['end', fmt(x2), fmt(y2)],
                   ['layer', '"Edge.Cuts"'], ['width', '0.15'], ['tstamp', 'X']])
    tx, ty = inner_top["x"] + 18.5, inner_top["y"] + 38.75
    for layer, extra in (('"F.SilkS"', []), ('"B.SilkS"', [['justify', 'mirror']])):
        gr.append(['gr_text', '"corne-pg1316s"', ['at', fmt(tx), fmt(ty)], ['layer', layer], ['tstamp', 'X'],
                   ['effects', ['font', ["size", "1.2", "1.2"], ["thickness", "0.18"]]] + extra])

    setup = copy.deepcopy(find(dust, 'setup')[0])
    pp = find(setup, 'pcbplotparams')[0]
    pp[:] = [c for c in pp if not (isinstance(c, list) and c[0] == 'outputdirectory')]
    body = [
        ['general', ['thickness', '1.6']], ['paper', '"A3"'],
        ['title_block', ['title', '"corne-pg1316s"'], ['rev', '"v0.5"'], ['company', '"baseado no dust (Jason Hazel) e no mikefive (Mike Holscher)"']],
        find(dust, 'layers')[0], setup,
    ] + [['net', str(i), f'"{n}"'] for i, n in enumerate(board.nets)] + board.footprints + gr
    out = '(kicad_pcb (version 20211014) (generator pcbnew)\n'
    out += '\n'.join('  ' + dumps(b, 1) for b in body) + '\n)\n'
    out = re.sub(r'\(tstamp [^)\s]+\)', lambda m: f'(tstamp {uuid.uuid4()})', out)
    with open(os.path.join(HERE, 'corne-pg1316s.kicad_pcb'), 'w', encoding='utf8', newline='\n') as f:
        f.write(out)

    write_preview(shape, keys, board, caps)

    w, h = shape.bounds[2] - shape.bounds[0], shape.bounds[3] - shape.bounds[1]
    print(f'{len(keys)} teclas, {len(board.footprints)} footprints, {len(board.nets) - 1} nets, '
          f'placa {w:.1f} x {h:.1f} mm, {len(ring) - 1} segmentos de contorno')
    print('\n'.join(problems) or 'sem colisões; tudo dentro do contorno')
    return not problems


def write_preview(shape, keys, board, caps):
    minx, miny, maxx, maxy = shape.bounds
    m = 6
    vb = f'{minx - m:.2f} {miny - m:.2f} {maxx - minx + 2 * m:.2f} {maxy - miny + 2 * m:.2f}'
    pts = ' '.join(f'{x:.2f},{y:.2f}' for x, y in shape.exterior.coords)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{(maxx - minx + 2 * m) * 6:.0f}" '
         f'font-family="sans-serif">',
         f'<rect x="{minx - m}" y="{miny - m}" width="100%" height="100%" fill="#fff"/>',
         f'<polygon points="{pts}" fill="#4b2a7a" stroke="#c9b6ff" stroke-width="0.3"/>']
    for fp in board.footprints:
        r = [c for c in find(fp, 'fp_text') if c[1] == 'reference'][0][2].strip('"')
        if re.fullmatch(r'[SDL]\d+', r) or find(fp, 'layer')[0][1] != '"F.Cu"':
            continue
        h = footprint_hull(fp)
        hp = ' '.join(f'{x:.2f},{y:.2f}' for x, y in h.exterior.coords) if h.geom_type == 'Polygon' else ''
        cx, cy = h.centroid.x, h.centroid.y
        s.append(f'<polygon points="{hp}" fill="#2d6a4f" fill-opacity="0.8" stroke="#95d5b2" stroke-width="0.25"/>')
        s.append(f'<text x="{cx:.2f}" y="{cy:.2f}" font-size="2" fill="#fff" text-anchor="middle">{r or "BAT-"}</text>')
    for i, (k, cap) in enumerate(zip(keys, caps), 1):
        cp = ' '.join(f'{x:.2f},{y:.2f}' for x, y in cap.exterior.coords)
        s.append(f'<polygon points="{cp}" fill="#f4f1ea" stroke="#333" stroke-width="0.25" rx="1"/>')
        s.append(f'<text x="{k["x"]:.2f}" y="{k["y"] - 1:.2f}" font-size="2.6" text-anchor="middle" '
                 f'transform="rotate({-k["a"]} {k["x"]:.2f} {k["y"]:.2f})">S{i}</text>')
        s.append(f'<text x="{k["x"]:.2f}" y="{k["y"] + 3:.2f}" font-size="2" fill="#666" text-anchor="middle" '
                 f'transform="rotate({-k["a"]} {k["x"]:.2f} {k["y"]:.2f})">c{k["col"]} · {k["row"]}</text>')
    s.append('</svg>')
    with open(os.path.join(HERE, 'preview.svg'), 'w', encoding='utf8') as f:
        f.write('\n'.join(s))


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1]) else 1)

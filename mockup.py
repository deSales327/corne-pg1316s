"""Mockup do teclado montado (as duas metades, vista de cima), a partir de corne-pg1316s.kicad_pcb.

    python mockup.py   ->  mockup.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerar_pcb import HERE, find, layout, parse  # noqa: E402

GAP = 46.0  # distância entre as metades (mm)
LEGENDS = {
    'L': [['Tab', 'Q', 'W', 'E', 'R', 'T'], ['Ctrl', 'A', 'S', 'D', 'F', 'G'],
          ['Shift', 'Z', 'X', 'C', 'V', 'B'], ['', '', '', 'GUI', 'Lower', 'Space']],
    'R': [['Bksp', 'P', 'O', 'I', 'U', 'Y'], ["'", ';', 'L', 'K', 'J', 'H'],
          ['Esc', '/', '.', ',', 'M', 'N'], ['', '', '', 'Alt', 'Raise', 'Enter']],
}
ROW_INDEX = {'r3': 0, 'r2': 1, 'r1': 2, 'r0': 3}


def board_data():
    b = parse(open(os.path.join(HERE, 'corne-pg1316s.kicad_pcb'), encoding='utf8').read())
    # encadeia os segmentos do contorno (o KiCad pode guardá-los por outra ordem)
    nxt = {}
    for g in find(b, 'gr_line'):
        if find(g, 'layer')[0][1] == '"Edge.Cuts"':
            a, z = (tuple(round(float(v), 3) for v in find(g, k)[0][1:3]) for k in ('start', 'end'))
            nxt.setdefault(a, []).append(z)
            nxt.setdefault(z, []).append(a)
    ring, prev = [next(iter(nxt))], None
    while True:
        cur = ring[-1]
        step = next(p for p in nxt[cur] if p != prev)
        if step == ring[0]:
            break
        prev = cur
        ring.append(step)
    parts = {}
    for fp in find(b, 'footprint'):
        if find(fp, 'layer')[0][1] != '"F.Cu"':
            continue
        # KiCad 6 usa fp_text reference; o KiCad 9 usa property "Reference"
        ref = [c[2] for c in find(fp, 'fp_text') if c[1] == 'reference']
        ref += [c[2] for c in find(fp, 'property') if c[1] == '"Reference"']
        ref = ref[0].strip('"')
        at = find(fp, 'at')[0]
        parts[ref or 'BAT-'] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0)
    return ring, parts


def keycap(x, y, a, label, hue):
    """Keycap transparente (Kailh PG1316 "Clear") com o LED RGB aceso por baixo."""
    return f'''<g transform="translate({x:.3f} {y:.3f}) rotate({-a:.2f})">
  <rect x="-8" y="-8" width="16" height="16" rx="2" fill="#000" opacity=".3" filter="url(#soft)" transform="translate(.6 1.1)"/>
  <circle cx="0" cy="-2.5" r="7.5" fill="hsl({hue:.0f},100%,60%)" opacity=".85" filter="url(#glow)"/>
  <rect x="-8" y="-8" width="16" height="16" rx="2" fill="#ffffff" fill-opacity=".38" stroke="#ffffff99" stroke-width=".3"/>
  <rect x="-7.3" y="-7.3" width="14.6" height="13.6" rx="1.5" fill="#ffffff" opacity=".12"/>
  <circle cx="0" cy="-2.5" r="1.6" fill="hsl({hue:.0f},100%,85%)" opacity=".9" filter="url(#soft)"/>
  <text x="0" y="{(3.4 if len(label) <= 1 else 2.3) * .35 + 2:.2f}" font-size="{3.4 if len(label) <= 1 else 2.3}" fill="#1e1e1e" fill-opacity=".8" text-anchor="middle" font-weight="600">{label}</text>
</g>'''


def controller(x, y, header_dy):
    """nice!nano (por baixo, só se veem as filas de pinos e o USB) com o nice!view por cima."""
    pads = ''.join(f'<circle cx="{sx:.2f}" cy="{-13.97 + i * 2.54:.2f}" r=".75" fill="url(#gold)"/>'
                   for i in range(12) for sx in (-7.62, 7.62))
    top = header_dy - 34.4
    return f'''<g transform="translate({x:.3f} {y:.3f})">
  <rect x="-9" y="-16.5" width="18" height="33" rx=".8" fill="#000" opacity=".5" filter="url(#soft)" transform="translate(.5 1)"/>
  <rect x="-9" y="-16.5" width="18" height="33" rx=".8" fill="#14161a" stroke="#3a3d42" stroke-width=".2"/>
  <rect x="-4.5" y="-17.7" width="9" height="3.6" rx="1.2" fill="url(#steel)" stroke="#777" stroke-width=".15"/>
  {pads}
  <rect x="-7" y="{top:.2f}" width="14" height="36" rx="1" fill="#000" opacity=".5" filter="url(#soft)" transform="translate(.6 1.2)"/>
  <rect x="-7" y="{top:.2f}" width="14" height="36" rx="1" fill="#1b1b1d" stroke="#444" stroke-width=".2"/>
  <rect x="-6" y="{top + 4.2:.2f}" width="12" height="27.5" rx=".3" fill="#cfd3c8"/>
  <text x="0" y="{top + 9:.2f}" font-size="2.4" fill="#222" text-anchor="middle" font-weight="700">87%</text>
  <rect x="-3.2" y="{top + 10.2:.2f}" width="6.4" height="2.6" rx=".4" fill="none" stroke="#222" stroke-width=".35"/>
  <rect x="-2.8" y="{top + 10.6:.2f}" width="4.8" height="1.8" fill="#222"/>
  <text x="0" y="{top + 18:.2f}" font-size="2" fill="#222" text-anchor="middle" font-weight="700">BT 1</text>
  <circle cx="0" cy="{top + 22.5:.2f}" r="2" fill="#222"/><text x="0" y="{top + 23.2:.2f}" font-size="1.8" fill="#cfd3c8" text-anchor="middle" font-weight="700">1</text>
  <text x="0" y="{top + 29:.2f}" font-size="1.7" fill="#222" text-anchor="middle" font-weight="600">BASE</text>
  <text x="0" y="{top + 34.6:.2f}" font-size="1.1" fill="#999" text-anchor="middle">nice!view</text>
</g>'''


def hole(x, y):
    # furo não metalizado de 3,2 mm: vê-se a mesa através dele
    return (f'<circle cx="{x:.3f}" cy="{y:.3f}" r="1.6" fill="#a9a196" stroke="#2a1745" stroke-width=".35"/>'
            f'<circle cx="{x + .25:.3f}" cy="{y + .3:.3f}" r="1.2" fill="#8f877c"/>')


def slide_switch(x, y):
    return f'''<g transform="translate({x:.3f} {y:.3f})">
  <rect x="-2" y="-3.8" width="4" height="7.6" rx=".4" fill="url(#steel)" stroke="#666" stroke-width=".15"/>
  <rect x="1.4" y="-1.8" width="1.8" height="1.6" rx=".3" fill="#1a1a1a"/>
</g>'''


def xh(x, y, hx, hy, s):
    """JST-XH vertical rodado 90° com a ficha da bateria; (x, y) é o pino 1 (o pino 2 fica 2,5 mm
    acima), (hx, hy) o furo dos fios, s = 1 na metade esquerda e -1 na direita (espelhada)."""
    bx = x - 2.35 if s > 0 else x - 3.4
    return f'''<g>
  <rect x="{bx:.3f}" y="{y - 4.95:.3f}" width="5.75" height="7.4" rx=".4" fill="#000" opacity=".4" filter="url(#soft)" transform="translate(.4 .8)"/>
  <rect x="{bx:.3f}" y="{y - 4.95:.3f}" width="5.75" height="7.4" rx=".4" fill="#f3efe4" stroke="#b9b2a2" stroke-width=".15"/>
  <rect x="{bx + .85:.3f}" y="{y - 4.1:.3f}" width="3.6" height="5.7" rx=".3" fill="#e4ddcc"/>
  <path d="M{x:.3f} {y:.3f} C {x:.3f} {y + 3:.3f}, {hx:.3f} {hy - 3:.3f}, {hx - .4 * s:.3f} {hy:.3f}" stroke="#c62828" stroke-width=".7" fill="none" stroke-linecap="round"/>
  <path d="M{x + .8 * s:.3f} {y - 2.5:.3f} C {x + 2.5 * s:.3f} {y + 1:.3f}, {hx + 1 * s:.3f} {hy - 3:.3f}, {hx + .4 * s:.3f} {hy:.3f}" stroke="#1b1b1b" stroke-width=".7" fill="none" stroke-linecap="round"/>
  <circle cx="{x:.3f}" cy="{y:.3f}" r=".55" fill="url(#gold)"/><circle cx="{x:.3f}" cy="{y - 2.5:.3f}" r=".55" fill="url(#gold)"/>
</g>'''


def reset_button(x, y):
    return (f'<rect x="{x - 1.25:.3f}" y="{y - 1.5:.3f}" width="2.5" height="3" rx=".3" fill="url(#steel)" stroke="#666" stroke-width=".15"/>'
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r=".7" fill="#2a2a2a"/>')


def half(side, ring, parts, keys, mirror_x):
    def X(x):
        return mirror_x - x if side == 'R' else x

    def A(a):
        return -a if side == 'R' else a

    pts = ' '.join(f'{X(x):.3f},{y:.3f}' for x, y in ring)
    out = [f'<polygon points="{pts}" fill="#000" opacity=".55" filter="url(#shadow)" transform="translate(1.5 3)"/>',
           f'<polygon points="{pts}" fill="url(#pcb)" stroke="#c9a227" stroke-width=".35"/>',
           f'<polygon points="{pts}" fill="none" stroke="#ffffff22" stroke-width=".2" transform="translate(-.15 -.15)"/>']
    # silkscreen, controlador + nice!view, bateria, interruptor e reset
    mx, my, _ = parts['MCU1']
    out.append(f'<text x="{X(mx - .5):.2f}" y="{my + 24.4:.2f}" font-size="1.5" fill="#efe6ff" text-anchor="middle" '
               f'font-weight="700" letter-spacing=".2">corne-pg1316s</text>')
    _, dy, _ = parts['DISP1']
    out.append(controller(X(mx), my, dy - my + (2.54 if side == 'R' else 0)))
    jx, jy, _ = parts['J1']
    hx, hy, _ = parts['H1']
    out.append(hole(X(hx), hy))
    out.append(xh(X(jx), jy, X(hx), hy, 1 if side == 'L' else -1))
    sx, sy, _ = parts['PWR1']
    out.append(slide_switch(X(sx), sy) if side == 'L'
               else f'<g transform="translate({X(sx):.3f} 0) scale(-1 1)">{slide_switch(0, sy)}</g>')
    rx, ry, _ = parts['RST1']
    out.append(reset_button(X(rx), ry))
    x0, x1 = min(X(x) for x, _ in ring), max(X(x) for x, _ in ring)
    for k in keys:
        label = LEGENDS[side][ROW_INDEX[k['row']]][k['col']]
        hue = (X(k['x']) - x0) / (x1 - x0) * 150 + (0 if side == 'L' else 150)
        out.append(keycap(X(k['x']), k['y'], A(k['a']), label, hue))
    return '\n'.join(out)


def main():
    ring, parts = board_data()
    keys = layout()
    minx = min(x for x, _ in ring)
    maxx = max(x for x, _ in ring)
    miny = min(y for _, y in ring)
    maxy = max(y for _, y in ring)
    mirror = 2 * maxx + GAP  # a metade direita é a mesma PCB virada ao contrário
    left = half('L', ring, parts, keys, mirror)
    right = half('R', ring, parts, keys, mirror)
    w = (mirror - minx) - minx
    m = 14
    vx, vy, vw, vh = minx - m, miny - 22, w + 2 * m, (maxy - miny) + 22 + 20
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.2f} {vy:.2f} {vw:.2f} {vh:.2f}"
     width="{vw * 6.2:.0f}" height="{vh * 6.2:.0f}" font-family="Segoe UI, Helvetica, Arial, sans-serif">
<defs>
  <linearGradient id="desk" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9d4cc"/><stop offset="1" stop-color="#b9b2a7"/></linearGradient>
  <linearGradient id="pcb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5a2f91"/><stop offset="1" stop-color="#3d1d68"/></linearGradient>
  <linearGradient id="capA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbf8f1"/><stop offset="1" stop-color="#e3ddcf"/></linearGradient>
  <linearGradient id="capM" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b9bcc2"/><stop offset="1" stop-color="#9497a0"/></linearGradient>
  <linearGradient id="capT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8743b"/><stop offset="1" stop-color="#c4551f"/></linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f5d77a"/><stop offset="1" stop-color="#b8902c"/></linearGradient>
  <linearGradient id="steel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f2f2f2"/><stop offset=".5" stop-color="#b5b5b5"/><stop offset="1" stop-color="#8c8c8c"/></linearGradient>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation=".5"/></filter>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feGaussianBlur stdDeviation="1.6"/></filter>
</defs>
<rect x="{vx:.2f}" y="{vy:.2f}" width="{vw:.2f}" height="{vh:.2f}" fill="url(#desk)"/>
{left}
{right}
<text x="{vx + 8:.2f}" y="{vy + vh - 7:.2f}" font-size="4" fill="#3b3631" font-weight="700">corne-pg1316s</text>
<text x="{vx + 44:.2f}" y="{vy + vh - 7:.2f}" font-size="2.6" fill="#5b554d">42 teclas · Kailh PG1316S · LED RGB por tecla · keycaps Kailh transparentes · nice!nano + nice!view (BLE, sem fios) · bateria LiPo por baixo · PCB reversível · mockup ilustrativo</text>
</svg>'''
    with open(os.path.join(HERE, 'mockup.svg'), 'w', encoding='utf8') as f:
        f.write(svg)
    print('mockup.svg', f'{vw * 6.2:.0f}x{vh * 6.2:.0f}px')


if __name__ == '__main__':
    main()

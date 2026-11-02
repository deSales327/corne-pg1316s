# corne-pg1316s

PCB reversível e sem fios no formato **Corne** (3×6 + 3 polegares por metade, 42 teclas)
para os switches ultrafinos **Kailh PG1316S**, com keycaps impressas em 3D (do
[mikefive](https://github.com/mikeholscher/zmk-config-mikefive)). É a versão "irmã" do
[corne-x](https://github.com/deSales327/corne-x), que usa switches Kailh X (PG1425).

![mockup](mockup.png)

| Frente | Verso |
| :---: | :---: |
| ![frente](images/render-top.png) | ![verso](images/render-bottom.png) |

## Estado
- Roteada nas duas camadas, com plano de GND.
- **DRC do KiCad 10: 0 violações e 0 ligações em falta.**
- Gerbers e furação prontos em [`corne-pg1316s-gerbers.zip`](corne-pg1316s-gerbers.zip).
- **Ainda não foi fabricada nem testada.** As posições dos contactos do switch foram confirmadas com o footprint do [Delta Omega](https://github.com/unspecworks/delta-omega) (rev4, já fabricado) e com o do mikefive. Mesmo assim, confirma com um switch físico (por exemplo, numa impressão 1:1) antes de encomendar.
- **v0.2:** os contactos do switch passaram de x = ±2,5 mm para x = −0,5 e +1,7 mm (no verso ficam espelhados). Os gerbers da v0.1 **não servem**.

## Componentes (por metade)
| Qtd. | Peça |
|---|---|
| 21 | Kailh PG1316S (SMD) |
| 21 | Díodo 1N4148W, SOD-123 |
| 1 | Seeed XIAO nRF52840 (BLE) |
| 1 | Interruptor SPDT (o mesmo do dust) |
| 1 | Conector JST-XH 2,50 mm, vertical, 2 pinos |
| 1 | Bateria LiPo pequena com ficha JST-XH |
| 21 | Keycaps impressas, ver [`keycaps/`](keycaps/) |

## Diferenças para o corne-x
- **Espaçamento de 17 × 17 mm** para keycaps de 16,5 × 16,5 mm. Cada metade mede 125,6 × 83,9 mm.
- **Footprint PG1316S reversível**, desenhado em `gerar_pcb.py`:
  - O chassi e os furos seguem a ficha técnica `CPG1316S01D02`.
  - Os contactos seguem o footprint testado do Delta Omega.
  - Os terminais do switch não são simétricos, por isso os contactos têm pads próprios em cada face, espelhados no verso, e as pistas ligam-nos entre si.
  - Os pads do chassi têm um furo metalizado e servem as duas faces.
  - Há furos para os pinos de alinhamento das duas faces.
- **Díodos na cavidade debaixo do switch**, na mesma face que ele, como no mikefive. Os pads SMD existem nas duas faces.
- **Soldadura:** os switches são SMD. Numa metade ficam na frente e na outra no verso. Uma placa de aquecimento (hotplate) com pasta de solda é o mais prático; com ferro de soldar dá, mas custa mais.

## Bateria
- **J1**: JST-XH 2,50 mm vertical, de furos passantes. O pino 1 é o BAT+ e o pino 2 o BAT−.
- **H1**: furo de 3,2 mm para passar os fios da bateria, que fica por baixo da placa.
- **PWR1**: interruptor no BAT−.
- Atenção à altura: o JST-XH vertical tem cerca de 7 mm, muito mais do que o resto do teclado.

## Matriz e pinos do XIAO
| Pino | Função | Pino | Função |
|---|---|---|---|
| D0 | c5 (indicador interno) | D7 | r0 (polegares) |
| D1 | c4 (indicador) | D8 | r1 (fila de baixo) |
| D2 | c3 (médio) | D9 | r2 (fila home) |
| D3 | c2 (anelar) | D10 | r3 (fila de cima) |
| D4 | c1 (mindinho) | D6 | livre |
| D5 | c0 (mindinho externo) | | |

- O cátodo dos díodos (pad 1) fica na linha, por isso o sentido é COL2ROW (no ZMK, `diode-direction = "col2row"`).
- Os polegares usam as colunas c3, c4 e c5 da linha r0.

## Regenerar
```
python gerar_pcb.py caminho/para/dust/pcbs/dust.kicad_pcb
"%LOCALAPPDATA%\Programs\KiCad\10.0\bin\python.exe" finalizar_pcb.py caminho/para/freerouting-2.5.0.jar
python mockup.py
```
Precisas do `shapely` (pip), do KiCad 10, do Freerouting 2.5 e do Java 25.

## Créditos
- Díodo, XIAO e interruptor: [dust](https://github.com/hazels-garage/dust), de Jason Hazel (CC BY 4.0).
- Keycaps e referência do PG1316S: [mikefive](https://github.com/mikeholscher/zmk-config-mikefive), de Mike Holscher. Uso permitido com crédito ao autor.
- Footprint do switch: desenhado a partir da ficha técnica da Kailh (CPG1316S01D02). As posições dos contactos foram confirmadas com o [Delta Omega](https://github.com/unspecworks/delta-omega), de unspecworks (CERN-OHL-W-2.0).
- Lojas de PG1316S indicadas pelo Delta Omega (não verificadas): Modulo Industries (EUA), Holykeebs (EUA) e Keycapsss (UE).
- Layout: Corne (crkbd), de foostan (MIT).
- Este projeto: CC BY 4.0, exceto as keycaps, que seguem as condições do autor.

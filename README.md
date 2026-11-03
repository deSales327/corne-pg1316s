# corne-pg1316s

PCB reversível e sem fios no formato **Corne** (3×6 + 3 polegares por metade, 42 teclas)
para os switches ultrafinos **Kailh PG1316S**, com **um LED RGB por tecla** e keycaps impressas
em 3D (do [mikefive](https://github.com/mikeholscher/zmk-config-mikefive)) ou compradas. É a versão "irmã" do
[corne-x](https://github.com/deSales327/corne-x), que usa switches Kailh X (PG1425).

![mockup](mockup.png)

| Frente | Verso |
| :---: | :---: |
| ![frente](images/render-top.png) | ![verso](images/render-bottom.png) |

## Estado
- Roteada nas duas camadas, com plano de GND.
- **DRC do KiCad 10: 0 violações e 0 ligações em falta.**
- Gerbers e furação prontos em [`corne-pg1316s-gerbers.zip`](corne-pg1316s-gerbers.zip).
- **Ainda não foi fabricada nem testada.** Há footprints de PG1316S já fabricados com os contactos em sítios diferentes: x = ±2,5 mm (ficha técnica, [mikefive](https://github.com/mikeholscher/zmk-config-mikefive), [ULK](https://github.com/Goga64/ULK)) e x = −0,5 / +1,7 mm ([Delta Omega](https://github.com/unspecworks/delta-omega) rev4). Os terminais do switch são largos o suficiente para os dois. Mesmo assim, confirma com um switch físico (por exemplo, numa impressão 1:1) antes de encomendar.
- **v0.4:** um LED RGB WS2812B-2020 por tecla, na cavidade debaixo do switch, e um interruptor para lhes cortar a alimentação (RGB1). Os díodos passaram para o intervalo entre colunas, na face de baixo. Usa os gerbers da v0.4.
- **v0.3:** os pads de contacto são largos e cobrem as duas posições testadas: o pad 1 vai de −3,275 a −0,025 mm e o pad 2 de +0,925 a +3,275 mm, como no footprint reversível do mikefive. No verso ficam espelhados.

## Componentes (por metade)
| Qtd. | Peça |
|---|---|
| 21 | Kailh PG1316S (SMD) |
| 21 | LED RGB WS2812B-2020 (2 × 2 mm) |
| 21 | Díodo 1N4148W, SOD-123 |
| 1 | Seeed XIAO nRF52840 (BLE) |
| 2 | Interruptor SPDT (o mesmo do dust): energia e LEDs |
| 1 | Conector JST-XH 2,50 mm, vertical, 2 pinos |
| 1 | Bateria LiPo com ficha JST-XH (quanto maior, melhor, por causa dos LEDs) |
| 21 | Keycaps: Kailh PG1316 1U transparentes (16 × 16 mm, ex.: Modulo "Clear") para se ver a luz, ou as impressas de [`keycaps/`](keycaps/) |
| 4+ | Pés de borracha com 1,5 mm ou mais (os díodos ficam por baixo) |

## Diferenças para o corne-x
- **Espaçamento de 17 × 17 mm** para keycaps de 16,5 × 16,5 mm. Cada metade mede 125,6 × 83,9 mm.
- **Footprint PG1316S reversível**, desenhado em `gerar_pcb.py`:
  - O chassi e os furos seguem a ficha técnica `CPG1316S01D02`.
  - Os contactos são largos e cobrem as posições dos footprints testados do mikefive, do ULK e do Delta Omega.
  - Os terminais do switch não são simétricos, por isso os contactos têm pads próprios em cada face, espelhados no verso, e as pistas ligam-nos entre si.
  - Os pads do chassi têm um furo metalizado e servem as duas faces.
  - Há furos para os pinos de alinhamento das duas faces.
- **LED na cavidade debaixo do switch**, que é a janela de LED da ficha técnica. Os pads existem nas duas faces; o LED vai na mesma face que o switch.
- **Díodos entre colunas, na face oposta à do switch** (a de baixo). Os pads existem nas duas faces; na face do switch ficam vazios.
- **Soldadura**, por esta ordem, em cada metade:
  1. LEDs e switches na face de cima (numa metade é a frente, na outra o verso), com pasta de solda e placa de aquecimento (hotplate). Os LEDs de 2 × 2 mm são difíceis de soldar com ferro.
  2. Díodos na face de baixo, com ferro de soldar (não voltes a pôr a placa na hotplate com peças por baixo).
  3. XIAO, interruptores e conector.
  - Testa os LEDs antes de soldar os switches por cima: depois deixam de estar acessíveis.

## Bateria
- **J1**: JST-XH 2,50 mm vertical, de furos passantes. O pino 1 é o BAT+ e o pino 2 o BAT−.
- **H1**: furo de 3,2 mm para passar os fios da bateria, que fica por baixo da placa.
- **PWR1**: interruptor no BAT−.
- Atenção à altura: o JST-XH vertical tem cerca de 7 mm, muito mais do que o resto do teclado.

## LEDs RGB
- **L1–L21**: WS2812B-2020, um por tecla, em cadeia: D6 do XIAO → polegares (de dentro para fora) → colunas em serpentina, da interna (c5) para a externa (c0).
- **RGB1**: interruptor que liga o BAT+ ao VLED, a alimentação dos LEDs. Fica 9 mm acima do PWR1, na mesma borda.
  - Os LEDs gastam corrente mesmo apagados (cerca de 1 mA cada, 21 mA por metade). Com o RGB1 desligado não gastam nada; desliga-o quando não quiseres luz.
  - O retorno dos LEDs passa pelo PWR1, por isso com o PWR1 desligado os LEDs também ficam sem energia.
- Os LEDs são alimentados diretamente pela bateria (3,0–4,2 V); os dados vêm a 3,3 V do XIAO.
- **Limita o brilho no firmware.** Os 21 LEDs a branco no máximo podem gastar várias centenas de mA, mais do que uma bateria pequena aguenta bem.
- O XIAO não tem um pino livre para desligar os LEDs por software (os 11 pinos estão todos em uso), por isso o corte é feito pelo RGB1.

### ZMK
No `.overlay` de cada metade (o D6 do XIAO nRF52840 é o P1.11):

```dts
#include <dt-bindings/led/led.h>

&xiao_serial { status = "disabled"; };

&pinctrl {
    spi3_default: spi3_default {
        group1 { psels = <NRF_PSEL(SPIM_MOSI, 1, 11)>; };
    };
    spi3_sleep: spi3_sleep {
        group1 { psels = <NRF_PSEL(SPIM_MOSI, 1, 11)>; low-power-enable; };
    };
};

&spi3 {
    compatible = "nordic,nrf-spim";
    status = "okay";
    pinctrl-0 = <&spi3_default>;
    pinctrl-1 = <&spi3_sleep>;
    pinctrl-names = "default", "sleep";
    led_strip: ws2812@0 {
        compatible = "worldsemi,ws2812-spi";
        reg = <0>;
        spi-max-frequency = <4000000>;
        chain-length = <21>;
        spi-one-frame = <0x70>;
        spi-zero-frame = <0x40>;
        color-mapping = <LED_COLOR_ID_GREEN LED_COLOR_ID_RED LED_COLOR_ID_BLUE>;
    };
};

/ { chosen { zmk,underglow = &led_strip; }; };
```

No `.conf`:

```
CONFIG_ZMK_RGB_UNDERGLOW=y
CONFIG_WS2812_STRIP=y
CONFIG_ZMK_RGB_UNDERGLOW_EXT_POWER=n
CONFIG_ZMK_RGB_UNDERGLOW_BRT_MAX=40
CONFIG_ZMK_RGB_UNDERGLOW_AUTO_OFF_IDLE=y
```

## Matriz e pinos do XIAO
| Pino | Função | Pino | Função |
|---|---|---|---|
| D0 | c5 (indicador interno) | D7 | r0 (polegares) |
| D1 | c4 (indicador) | D8 | r1 (fila de baixo) |
| D2 | c3 (médio) | D9 | r2 (fila home) |
| D3 | c2 (anelar) | D10 | r3 (fila de cima) |
| D4 | c1 (mindinho) | D6 | dados dos LEDs RGB |
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
- Footprint do switch: desenhado a partir da ficha técnica da Kailh (CPG1316S01D02). As posições dos contactos foram comparadas com o [Delta Omega](https://github.com/unspecworks/delta-omega), de unspecworks (CERN-OHL-W-2.0), e com o [ULK](https://github.com/Goga64/ULK), de Georgii Miakishev (MIT), um Corne com PG1316S já construído.
- Lojas de PG1316S indicadas pelo Delta Omega (não verificadas): Modulo Industries (EUA), Holykeebs (EUA) e Keycapsss (UE).
- Layout: Corne (crkbd), de foostan (MIT).
- Este projeto: CC BY 4.0, exceto as keycaps, que seguem as condições do autor.

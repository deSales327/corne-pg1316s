# corne-pg1316s

PCB reversível e sem fios no formato **Corne** (3×6 + 3 polegares por metade, 42 teclas)
para os switches ultrafinos **Kailh PG1316S**, com **um LED RGB por tecla** e keycaps impressas
em 3D (do [mikefive](https://github.com/mikeholscher/zmk-config-mikefive)) ou compradas, e **nice!nano + nice!view**. É a versão "irmã" do
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
- **v0.5:** o XIAO deu lugar a um Pro Micro nRF52840 (nice!nano v2 ou clone) com a pinagem do Corne do ZMK, e há furos para um nice!view por cima dele. Os LEDs são desligados por software (VCC do nice!nano), por isso o interruptor RGB1 saiu. Foi acrescentado um botão de reset. Usa os gerbers da v0.5.
- **v0.4:** um LED RGB WS2812B-2020 por tecla, na cavidade debaixo do switch. Os díodos passaram para o intervalo entre colunas, na face de baixo.
- **v0.3:** os pads de contacto são largos e cobrem as duas posições testadas: o pad 1 vai de −3,275 a −0,025 mm e o pad 2 de +0,925 a +3,275 mm, como no footprint reversível do mikefive. No verso ficam espelhados.

## Componentes (por metade)
| Qtd. | Peça |
|---|---|
| 21 | Kailh PG1316S (SMD) |
| 21 | LED RGB WS2812B-2020 (2 × 2 mm) |
| 21 | Díodo 1N4148W, SOD-123 |
| 1 | Pro Micro nRF52840: nice!nano v2 ou clone compatível (ex.: SuperMini nRF52840) com corte de VCC no P0.13 |
| 1 | nice!view (ecrã de 1,08", 36 × 14 mm), com o conector e os pinos que trazem |
| 2 | Barras de 12 pinos fêmea + pinos macho baixos (para o controlador) |
| 1 | Interruptor SPDT (o mesmo do dust) |
| 1 | Botão Omron B3U-1000P (reset) |
| 1 | Conector JST-XH 2,50 mm, vertical, 2 pinos |
| 1 | Bateria LiPo com ficha JST-XH (quanto maior, melhor, por causa dos LEDs) |
| 21 | Keycaps: Kailh PG1316 1U transparentes (16 × 16 mm, ex.: Modulo "Clear") para se ver a luz, ou as impressas de [`keycaps/`](keycaps/) |
| 4+ | Pés de borracha com 1,5 mm ou mais (os díodos ficam por baixo) |

## Diferenças para o corne-x
- **Espaçamento de 17 × 17 mm** para keycaps de 16,5 × 16,5 mm. Cada metade mede 128,5 × 83,9 mm.
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
  3. Botão de reset na face de cima, também com ferro.
  4. Controlador, nice!view, interruptor e conector.
  - Testa os LEDs antes de soldar os switches por cima: depois deixam de estar acessíveis.

## Bateria
- **J1**: JST-XH 2,50 mm vertical, de furos passantes. O pino 1 é o BAT+ e o pino 2 o BAT−.
- **H1**: furo de 3,2 mm para passar os fios da bateria, que fica por baixo da placa.
- **PWR1**: interruptor no BAT−.
- O BAT+ liga ao pino RAW do nice!nano v2, que é a entrada da bateria (e passa pelo carregador dele).
- Atenção à altura: o JST-XH vertical tem cerca de 7 mm, muito mais do que o resto do teclado.

## Controlador e nice!view
- **MCU1**: Pro Micro reversível sem pontes de solda. Os furos são os mesmos nas duas faces:
  - na metade em que a placa tem a **frente para cima**, o controlador monta-se com os **componentes para cima**;
  - na metade em que a placa tem o **verso para cima**, monta-se com os **componentes para baixo** (como no Corne). Assim cada pino cai sempre no mesmo furo. Está escrito no silkscreen de cada face.
- **DISP1**: duas filas de 5 furos para o nice!view, logo abaixo do controlador. A fila de cima é para a metade com a frente para cima e a de baixo para a outra (a ordem dos pinos fica invertida quando a placa se vira). O ecrã fica por cima do controlador.
- **RST1**: botão de reset (duplo toque entra no bootloader). Há pads nas duas faces; solda-se só o da face de cima.
- Altura: com o nice!view por cima, o bloco do controlador fica bem mais alto do que as teclas (cerca de 7–10 mm, conforme os pinos e as barras que usares).

## Pinos do Pro Micro
Iguais aos do Corne do ZMK, por isso servem os shields `corne_left`/`corne_right` sem alterações.

| Pino | Função | Pino | Função |
|---|---|---|---|
| D1 (P0.06) | nice!view CS | RAW | BAT+ (via J1) |
| D0 (P0.08) | dados dos LEDs RGB | GND | GND |
| GND | GND | RST | botão de reset |
| GND | GND | VCC | 3,3 V comutado (LEDs e nice!view) |
| D2 (P0.17) | nice!view MOSI | D21 | c0 (mindinho externo) |
| D3 (P0.20) | nice!view SCK | D20 | c1 (mindinho) |
| D4 | r3 (fila de cima) | D19 | c2 (anelar) |
| D5 | r2 (fila home) | D18 | c3 (médio) |
| D6 | r1 (fila de baixo) | D15 | c4 (indicador) |
| D7 | r0 (polegares) | D14 | c5 (indicador interno) |
| D8 | livre | D16 | livre |
| D9 | livre | D10 | livre |

- O cátodo dos díodos (pad 1) fica na linha: COL2ROW, como no Corne.
- Os polegares usam as colunas c3, c4 e c5 da linha r0 (`RC(3,3)`, `RC(3,4)`, `RC(3,5)`).

## LEDs RGB
- **L1–L21**: WS2812B-2020, um por tecla, em cadeia: D0 → polegares (de dentro para fora) → colunas em serpentina, da interna (c5) para a externa (c0).
- Alimentados pelo **VCC do nice!nano** (3,3 V), que o ZMK corta quando os LEDs estão desligados ou o teclado em repouso (`ext-power`, P0.13). Os LEDs gastam corrente mesmo apagados, por isso este corte é importante.
- 3,3 V está abaixo dos 3,7 V da ficha técnica dos WS2812B-2020. É como muitos Corne sem fios com nice!nano funcionam, mas o azul e o branco podem ficar um pouco mais fracos.
- **Limita o brilho no firmware.** O VCC do nice!nano não aguenta os 21 LEDs a branco no máximo.

## ZMK
No `build.yaml` do teu zmk-config:

```yaml
include:
  - board: nice_nano_v2
    shield: corne_left nice_view_adapter nice_view
  - board: nice_nano_v2
    shield: corne_right nice_view_adapter nice_view
```

(Nas versões mais recentes do ZMK a placa chama-se `nice_nano` em vez de `nice_nano_v2`.)

Para os LEDs, num `corne.overlay` (ou `corne_left.overlay` e `corne_right.overlay`) na pasta `config`:

```dts
#include <dt-bindings/led/led.h>

&pinctrl {
    spi3_default: spi3_default {
        group1 { psels = <NRF_PSEL(SPIM_MOSI, 0, 8)>; };
    };
    spi3_sleep: spi3_sleep {
        group1 { psels = <NRF_PSEL(SPIM_MOSI, 0, 8)>; low-power-enable; };
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

No `corne.conf`:

```
CONFIG_ZMK_RGB_UNDERGLOW=y
CONFIG_WS2812_STRIP=y
CONFIG_ZMK_RGB_UNDERGLOW_EXT_POWER=y
CONFIG_ZMK_RGB_UNDERGLOW_BRT_MAX=40
CONFIG_ZMK_RGB_UNDERGLOW_AUTO_OFF_IDLE=y
```
## Regenerar
```
python gerar_pcb.py caminho/para/dust/pcbs/dust.kicad_pcb
"%LOCALAPPDATA%\Programs\KiCad\10.0\bin\python.exe" finalizar_pcb.py caminho/para/freerouting-2.5.0.jar
python mockup.py
```
Precisas do `shapely` (pip), do KiCad 10, do Freerouting 2.5 e do Java 25.

## Créditos
- Díodo e interruptor: [dust](https://github.com/hazels-garage/dust), de Jason Hazel (CC BY 4.0).
- Keycaps e referência do PG1316S: [mikefive](https://github.com/mikeholscher/zmk-config-mikefive), de Mike Holscher. Uso permitido com crédito ao autor.
- Footprint do switch: desenhado a partir da ficha técnica da Kailh (CPG1316S01D02). As posições dos contactos foram comparadas com o [Delta Omega](https://github.com/unspecworks/delta-omega), de unspecworks (CERN-OHL-W-2.0), e com o [ULK](https://github.com/Goga64/ULK), de Georgii Miakishev (MIT), um Corne com PG1316S já construído.
- Lojas de PG1316S indicadas pelo Delta Omega (não verificadas): Modulo Industries (EUA), Holykeebs (EUA) e Keycapsss (UE).
- Layout: Corne (crkbd), de foostan (MIT).
- Este projeto: CC BY 4.0, exceto as keycaps, que seguem as condições do autor.

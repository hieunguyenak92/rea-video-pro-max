# REA-Video-Pro-Max

## Entenda a edição. Crie algo novo com o mesmo estilo.

**Transforme um vídeo de referência em uma linha do tempo com evidências e um template de estilo reutilizável. Adicione outro roteiro e outras mídias para renderizar seu próprio vídeo.**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[Demonstração gravada](docs/index.html) · [Vídeo A](docs/media/reference.mp4) · [Vídeo B](docs/media/adapted.mp4) · [Verificação (English)](docs/VALIDATION.md)

Uma boa edição reúne decisões sobre cortes, grupos de palavras, destaque, movimento e som. O REA-Video-Pro-Max permite inspecionar e reutilizar as partes compatíveis desse sistema.

```text
Vídeo A → análise + linha do tempo inferida → template + conteúdo novo → projeto editável → vídeo B
```

A demonstração usa mídia sintética pertencente ao projeto. A e B têm textos e mídias diferentes. O site estático mostra um resultado gravado; não executa inferência ao vivo nem envia vídeos de visitantes.

## O que você pode pedir

- Analisar o vídeo inteiro em planos, legendas, estilo, movimento, eventos de áudio e uma linha do tempo com evidências temporais.
- Examinar tipografia, composição e cores de um frame. Uma imagem isolada não define tempos de animação ou som.
- Aplicar o estilo extraído a um roteiro, imagens ou filmagens novos para criar um vídeo diferente.
- Entregar apenas a linha do tempo e os arquivos de análise quando esse for o pedido.

```text
Use REA-Video-Pro-Max para analisar a linha do tempo e o estilo de reference.mp4. Com meu novo roteiro e meus arquivos, crie outro vídeo com legendas, movimento e ritmo semelhantes. Entregue template, projeto, vídeo e limitações não verificadas.
```

## Primeiro resultado

Você precisa de Python 3.11+, FFmpeg e FFprobe. O runtime Python usa Pillow, NumPy e PyAV. Tesseract é opcional para OCR; os dados de idioma instalados definem quais idiomas podem ser executados. Veja o [escopo testado (English)](docs/SUPPORT-MATRIX.md).

macOS é a plataforma de desenvolvimento medida. Linux é um destino previsto de CI; o renderizador nativo no Windows não é certificado. A verificação de criação exige o recibo exato do render e OCR independente, portanto o fluxo completo precisa do Tesseract com dados `eng`.

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

Os comandos usam a estrutura do checkout Git. No pacote de skill extraído, a entrada é `scripts/rea-video-pro-max.py`; mantenha `lib`, `assets` e `references` juntos. Use o Python em que as dependências foram instaladas, sem copiar só o script.

## Insira seu próprio conteúdo

`examples/content.json` é um exemplo sintético de content binding: cada nova cena tem `id`, `text`, `duration`, `background`, `accent` e `asset` opcional. `width`, `height` e `fps` definem a saída; `audio` e `font` são opcionais. Os caminhos são relativos ao arquivo de bindings. O projeto copia os arquivos e registra seus hashes, sem reutilizar silenciosamente a filmagem ou a música de A. Novas palavras exigem novos tempos; o método de estimativa é informado quando não há alinhamento exato.

O áudio do vídeo de cada cena fica mudo; forneça um novo vínculo `audio` para ter som. Clipes curtos mantêm o último quadro. O renderizador nativo exige mídia na orientação correta e com pixels quadrados. CSV exporta apenas linhas de planos. Confira os limites de composição e agrupamento para escritas complexas ou bidirecionais.

## Usar com Claude Code / Codex

Copie a pasta inteira `skills/rea-video-pro-max` para o diretório de skills do host ou peça ao agente para instalar a partir do checkout. Os locais de projeto comuns são `.claude/skills/rea-video-pro-max` e `.agents/skills/rea-video-pro-max`. Instalar a skill não instala FFmpeg, idiomas OCR nem pesos de modelos. Conta, permissões de execução e política de dados do host são independentes. A [skill](skills/rea-video-pro-max/SKILL.md) e as referências técnicas estão em English.

## Arquivos e exportação

- JSON nativo preserva análise, linha do tempo, dados de legenda/estilo/movimento/áudio, templates e projetos. CSV ajuda a revisar dados editoriais.
- SRT/WebVTT/ASS exportam texto e tempos conforme a capacidade de cada formato. SRT não preserva toda a tipografia ou o movimento.
- Use apenas os adaptadores de timeline declarados disponíveis pela versão instalada. O recibo informa subconjunto, aproximações e perdas; não garante qualquer efeito em qualquer editor.
- O renderizador por software compõe o conteúdo novo e codifica com FFmpeg. Não exige os filtros opcionais `drawtext`, `ass` ou `subtitles`.

## Limites importantes

Metadados medidos, OCR, ajuste de estilo e hipóteses de edição são evidências diferentes. Um vídeo achatado não determina de forma única os clipes originais, camadas ocultas, fonte, plugin, projeto do editor ou prompt de IA. O escopo inicial cobre tempos, legendas e primitivas 2D compatíveis. Não é um descompilador universal nem um produto comprovadamente líder. Oclusões complexas, reconstrução 3D, masterização HDR e round trips NLE arbitrários ficam fora do escopo verificado. Escritas complexas precisam de shaping e testes próprios; nove traduções não certificam nove idiomas de OCR ou renderização.

O vídeo B é verificado pelo conteúdo novo, pelo contrato de estilo e pela reprodução, sem exigir identidade de pixels com A. Verificação técnica e julgamento criativo humano são coisas diferentes. [Evidências e limites (English)](docs/VALIDATION.md).

## Execução local e créditos

O núcleo roda localmente, sem exigir API paga, enviar vídeo a inferência hospedada ou publicar mídia. Instalação de dependências e provedores opcionais podem usar a rede. O host Claude/Codex tem políticas próprias. [Privacy (English)](docs/PRIVACY.md). Inspirado em JuneYaooo/rea-video; produto independente, sem ser uma atualização oficial. Licenças de código, fontes, mídia, codecs e modelos são separadas.

Os relatórios locais copiam por padrão a mídia de referência e as evidências. `report --no-media` omite somente a cópia completa da mídia; mantém texto OCR, caminhos locais e recortes. Revise antes de compartilhar.

[Suporte (English)](SUPPORT.md) · [Manutenção (English)](docs/MAINTENANCE.md) · Não afirmamos revisão profissional das traduções por falantes nativos.

[Fala local e movimento avançado (referência técnica em inglês)](skills/rea-video-pro-max/references/speech-and-motion.md).

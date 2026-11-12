# REA-Video-Pro-Max

## Dê ao Claude e ao Codex o olhar de um editor.

**Desvende o ritmo, as legendas e os movimentos de um vídeo de referência. Transforme essas decisões em um estilo reutilizável. Renderize um novo vídeo com suas próprias palavras e mídias.**

Grandes edições têm uma linguagem própria. Traga essa linguagem para sua criação.

[**▶ Explore a demonstração ao vivo**](https://hieunguyenak92.github.io/rea-video-pro-max/) · [**Baixe a skill**](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) · [Versão v0.1.1](https://github.com/hieunguyenak92/rea-video-pro-max/releases/tag/v0.1.1)

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

**Skill para Claude Code / Codex · CLI + MCP opcional · Processamento local · Apache-2.0**

---

## De “Adorei essa edição” a “Aqui está a minha versão”.

Você encontra um vídeo com a energia certa: o ritmo dos cortes, a entrada das legendas, um destaque que percorre cada frase, um zoom que dá movimento a uma imagem parada.

O REA-Video-Pro-Max transforma as partes compatíveis desse estilo em algo que você pode inspecionar, ajustar e reutilizar. Traga um novo roteiro, imagens, vídeos ou narração. Ao final, você terá um projeto editável e um vídeo de fato renderizado.

| Referência A | Seu novo vídeo B |
| :---: | :---: |
| [![Quadro do vídeo de referência próprio](docs/media/readme-reference.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) | [![Quadro renderizado com novas palavras e mídias independentes](docs/media/readme-new-video.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) |
| Estude o ritmo dos planos e o tratamento das legendas. | Aplique o estilo reutilizável a outra história. |

*Quadros reais da demonstração própria incluída. B usa texto novo, mídias geradas de forma independente e nova temporização das legendas. O [guia interativo](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) permite percorrer os dois vídeos e inspecionar a timeline registrada, o template, o projeto e a verificação.*

```text
Reference video → editing evidence + timeline → reusable style
                                                   + your new content
                                                   → editable project + Video B
```

## Coloque uma referência para trabalhar

| O que você quer fazer | O que leva com você |
| --- | --- |
| Entender por que uma edição transmite aquela sensação | Intervalos dos planos, texto visível, aparência das legendas, movimento aparente e sinais de áudio, vinculados a timestamps e evidências. |
| Levar um tratamento de legendas para outra história | Tipografia, layout e paletas de destaque reutilizáveis, aplicados às novas palavras com sua própria temporização. |
| Criar um formato de vídeo repetível | Um template de estilo que você pode vincular a outro roteiro e a outro conjunto de recursos. |
| Dirigir o resultado | Uma timeline/projeto nativo em JSON, com recursos copiados e hashes, que você pode inspecionar, alterar e renderizar novamente. |
| Integrar a análise ao seu próprio fluxo | Arquivos estruturados, um inspetor offline, exportações de legendas e intercâmbio de timelines com limites definidos. |

Use para apresentar um produto, criar um vídeo educativo, desenvolver uma série de conteúdo, estudar uma edição ou construir uma ferramenta de vídeo personalizada. Quando você só precisa do detalhamento, a análise e a timeline já são entregas completas.

## Um prompt para começar

Instale a skill incluída, entregue ao agente a referência e seu conteúdo novo, e faça o pedido abaixo. Este prompt em inglês está pronto para usar:

```text
Use REA-Video-Pro-Max to break down reference.mp4: shot rhythm,
subtitle layout, highlight colors and supported motion.
Extract a reusable style, then use my new script and assets to make
an original video with a similar editing language.
Render the video, keep the editable project, verify the new content,
and show me any effects that need an approximation.
```

Você dirige a história. A skill entrega ao agente um fluxo concreto e ferramentas executáveis para analisar, compor, renderizar e verificar.

## O que torna esse fluxo útil

- **Uma edição que você pode inspecionar.** Timestamps de apresentação decodificados, evidências por quadro e cobertura tornam a timeline rastreável. Sinais medidos, resultados de modelos e decisões de edição inferidas mantêm suas próprias identificações.
- **Detalhes de legenda que chegam ao projeto.** Estime tamanho visível, posição, preenchimento e contorno; preserve as diferentes paletas de destaque e variantes de estilo observadas. Reorganize e temporize as novas palavras durante a composição.
- **Movimento que preserva a direção.** Ajuste modelos limitados de movimento de similaridade/afim e candidatos a curvas temporais. O renderizador nativo pode reutilizar o componente de zoom compatível com seu sinal, incluindo o afastamento.
- **Um projeto para continuar criando.** Novas imagens, vídeos, fontes e áudio opcional são copiados para um projeto portátil. Vínculos explícitos e hashes permitem inspecionar o conteúdo escolhido.
- **Voz quando o trabalho pede.** O ASR local opcional com faster-whisper fornece intervalos de palavras derivados do modelo. A correspondência estrita entre roteiro e áudio pode vinculá-los ao conteúdo novo; é necessário indicar explicitamente um modelo local.
- **Um resultado que você pode conferir.** Verifique a correspondência entre projeto e saída, decodifique o vídeo renderizado e confira o conteúdo das legendas por OCR independente. Guarde as evidências junto com o resultado.

O renderizador nativo oferece **legendas estáticas / fade / pop / slide**, **transições cut / dissolve / fade / wipe** e **fundos estáticos / panzoom com direção definida**. A análise pode preservar observações de movimento mais ricas do que o renderizador nativo consegue reproduzir. [Compatibilidade exata (inglês)](docs/SUPPORT-MATRIX.md).

## Obtenha seu primeiro resultado

### 1. Prepare o ambiente de execução

Use **Python 3.11+**, **FFmpeg + FFprobe** e uma compilação do FFmpeg com **libx264**. Instale **Tesseract com os dados do idioma `eng`** para executar o exemplo incluído de OCR e verificação de legendas. As dependências de Python são instaladas abaixo.

```sh
git clone https://github.com/hieunguyenak92/rea-video-pro-max.git
cd rea-video-pro-max
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
rea-video-pro-max doctor
```

Esses comandos de shell são para macOS/Linux. O CI da versão passou em Linux e macOS; a renderização nativa no Windows não está certificada. `doctor` informa as ferramentas realmente disponíveis na sua máquina.

### 2. Entregue a skill ao agente

Copie a pasta **inteira** `skills/rea-video-pro-max` para o diretório de skills do projeto:

| Ambiente | Destino dentro do projeto |
| --- | --- |
| Claude Code | `.claude/skills/rea-video-pro-max` |
| Codex | `.agents/skills/rea-video-pro-max` |

Você também pode extrair o [ZIP da skill](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) nesse local. Mantenha `lib`, `assets`, `scripts` e `references` juntos. Para instalar apenas a partir do ZIP, instale as dependências de Python com `python -m pip install -r /path/to/rea-video-pro-max/requirements.txt`; o ponto de entrada é `python /path/to/rea-video-pro-max/scripts/rea-video-pro-max.py`. Os comandos de console abaixo vêm da instalação do repositório descrita acima. Seu agente deve usar o interpretador que contém essas dependências.

### 3. Execute o exemplo A → B incluído

```sh
rea-video-pro-max analyze examples/reference.mp4 --out work/analysis --ocr required --ocr-lang eng
rea-video-pro-max template work/analysis/analysis.json --out work/style-template.json
rea-video-pro-max compose work/style-template.json --content examples/content.json --out work/project
rea-video-pro-max render work/project/project.json --out work/video-b.mp4
rea-video-pro-max verify work/project/project.json --mode style-transfer --render work/video-b.mp4 --ocr-lang eng
```

Abra `work/video-b.mp4`. O projeto portátil está em `work/project/`; a análise da referência está em `work/analysis/`. Use um diretório de saída novo para cada composição. Para gerar um inspetor de análise offline, execute:

```sh
rea-video-pro-max report work/analysis/analysis.json --out work/report
```

Depois, abra `work/report/timeline.html` localmente. A [CLI, a skill e o MCP opcional compartilham o mesmo núcleo (inglês)](skills/rea-video-pro-max/references/runtime-and-support.md).

<details>
<summary><strong>Faça do seu jeito: o que entra em uma vinculação de conteúdo?</strong></summary>

Uma vinculação de conteúdo é um arquivo JSON que define suas novas cenas, texto, mídias e áudio/fonte opcionais. Seu agente pode criá-lo a partir de um briefing comum. Comece por [examples/content.json](examples/content.json).

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 24,
  "scenes": [
    {
      "id": "intro",
      "text": "Your next story starts here",
      "duration": 3.0,
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

Adicione um caminho `asset` para uma imagem ou um vídeo, e `audio` para uma trilha ou narração explícita. Os caminhos das mídias são resolvidos em relação a esse arquivo JSON. O renderizador usa o conteúdo novo escolhido; reutilizar as mídias exatas da referência exige uma opção explícita.

Novas palavras recebem uma nova temporização. O tempo ponderado por caracteres é uma estimativa. Forneça novos intervalos de palavras ou use ASR local com correspondência estrita quando a sincronização da fala for importante. [Guia de voz e movimento (inglês)](skills/rea-video-pro-max/references/speech-and-motion.md).

</details>

## Veja o trabalho por trás da promessa

**A v0.1.1 passou em 176 testes locais**, incluindo o caso real de ASR local opcional. [O CI hospedado passou em três jobs de Linux/macOS](https://github.com/hieunguyenak92/rea-video-pro-max/actions/runs/43324016397). Os seis artefatos publicados da versão foram baixados e comparados com os bytes e checksums locais.

As evidências incluem uma reprodução completa própria de **A → análise → estilo → novo B**, uma tarefa independente em vietnamita com tipografia/contorno corrigidos e dois tratamentos de destaque, e uma tarefa de movimento que preserva a direção de aproximação/afastamento. São casos próprios delimitados: comprovam o fluxo demonstrado, sem estabelecer precisão ampla para todos os gêneros ou idiomas.

[Inspecione a análise](docs/evidence/reference-analysis.json) · [Leia o template](docs/evidence/style-template.json) · [Abra o projeto](docs/evidence/project.json) · [Confira a verificação](docs/evidence/verification.json) · [Detalhes de validação (inglês)](docs/VALIDATION.md)

## Fique com o resultado. Amplie o sistema.

| Formato | O que contém |
| --- | --- |
| JSON nativo | Análise, timelines, dados de legendas/estilo/movimento/áudio, templates e projetos nativos editáveis. |
| CSV | Linhas de planos para inspeção e processamento posterior. |
| SRT / WebVTT | Texto visível e intervalos das legendas. |
| ASS | Temporização de legendas com um estilo substituto explícito; a aparência observada e a incerteza permanecem nas evidências nativas. |
| OTIO / EDL | Trechos opcionais da referência em OTIO com anotações; EDL para cortes medidos com CFR inteiro. Os relatórios de exportação descrevem as perdas. |
| MP4 + HTML offline | O vídeo novo e um relatório de análise local que você pode inspecionar. |

O projeto nativo é JSON editável. Esta versão não exporta projetos nativos de Premiere, Resolve, After Effects ou CapCut, nem FCPXML. A importação dos arquivos de intercâmbio compatíveis em editores externos continua sem verificação. [Limites dos exportadores e do renderizador (inglês)](docs/SUPPORT-MATRIX.md).

## Conheça os limites criativos

A versão atual se concentra em evidências de edição observáveis e na reutilização de estilos **2D** compatíveis. As fontes originais exatas, camadas ocultas, plugins, recursos de origem e histórico do projeto podem continuar desconhecidos. O OCR e os ajustes de movimento podem errar; a cobertura amostrada e a incerteza permanecem visíveis.

Os vídeos vinculados devem estar na orientação correta e ter pixels quadrados. O áudio das cenas é silenciado; forneça o áudio explicitamente. Escritas complexas precisam de fontes e composição tipográfica adequadas; legendas bidirecionais são rejeitadas. As nove traduções do README descrevem o produto e não certificam nove idiomas de OCR/renderização. A avaliação do estilo criativo e do som continua precisando de revisão humana. [Matriz completa de compatibilidade (inglês)](docs/SUPPORT-MATRIX.md).

O processamento principal é local e não exige API paga de modelos nem envio de conteúdo. Dependências e preparação de modelos opcionais podem precisar de acesso à rede; o ambiente Claude/Codex tem suas próprias políticas de dados. Por padrão, os relatórios locais incluem mídias da referência e recortes. `report --no-media` omite a cópia completa da referência, mas mantém o texto e os recortes. [Privacidade (inglês)](docs/PRIVACY.md).

## Ajude a criar o próximo fluxo de edição

**Se você quer esse fluxo na sua caixa de ferramentas criativa, dê uma estrela ao projeto.** Isso ajuda outros criadores e desenvolvedores de IA a descobrir o trabalho.

**Faça um fork e construa seu próprio vocabulário de edição:** adicione um tratamento de legendas, desenvolva um adaptador de renderização, amplie uma exportação ou contribua com um exemplo próprio da referência ao resultado. Traga evidências reproduzíveis para que cada nova capacidade conquiste seu lugar.

[**⭐ Dê uma estrela no GitHub**](https://github.com/hieunguyenak92/rea-video-pro-max) · [**🍴 Faça um fork e crie**](https://github.com/hieunguyenak92/rea-video-pro-max/fork) · [Contribua (inglês)](CONTRIBUTING.md) · [Proponha uma tarefa](https://github.com/hieunguyenak92/rea-video-pro-max/issues)

Projeto independente, inspirado em [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video). [Apache-2.0](LICENSE); os termos específicos de fontes, codecs e modelos estão preservados em [NOTICE](NOTICE).

[Suporte (inglês)](SUPPORT.md) · [Manutenção (inglês)](docs/MAINTENANCE.md) · [Instruções da skill (inglês)](skills/rea-video-pro-max/SKILL.md)

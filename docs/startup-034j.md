# DSi RA Bridge — 0.3.4-J official BlocksDS ARM7 A/B

**Objetivo:** verificar se um núcleo ARM7 *pré-compilado e mantido pelo BlocksDS* com DSWiFi inicializa no DSi XL via Flipnote Lenny → HBMenu, em contraste com os experimentos ARM7 personalizados 034F/G/H que apresentaram telas brancas.

**Status:** o CI compila e valida estrutura do arquivo. Não confirma que vai rodar no DSi; isso depende do teste físico do usuário. Não executar jogo, não conectar internet, não desbloquear conquistas.

## O que está incluído

- `DSIRB_034J_BASE.nds`: ARM9 da UI já conhecida e **núcleo oficial `arm7_maxmod.elf`** (BlocksDS).
- `DSIRB_034J_WIFI_CORE.nds`: **mesmo código ARM9**, mas com núcleo oficial `arm7_dswifi_maxmod.elf` (BlocksDS). Esta é a **única variável importante** de compilação, além dos metadados do nome do arquivo.
- **Nenhum fonte ARM7 personalizado** incluído. O programa ARM9 NÃO faz `Wifi_InitDefault`, não solicita conexão, não abre rede, não lê/monta SD e não escreve arquivos. O núcleo oficial inclui tratamento de hardware/DSWiFi, mas não há solicitação ARM9 de conexão.

Fontes do próprio BlocksDS:
- https://blocksds.skylyrac.net/docs/guides/usage_notes/
- https://blocksds.skylyrac.net/tutorial/basic/first_program/

## Instalação física isolada

1. Desligar completamente o DSi XL. Conectar SD ao PC e **fazer backup do cartão** antes de copiar. Não tocar em NAND, Unlaunch, `boot.nds`, `private/`, `_nds/`, TWiLight++.
2. Baixar o pacote `DSi_RA_Bridge_034J_OFFICIAL_ARM7_SD_ONLY` na execução GitHub Actions deste branch. Extrair o ZIP interno. Copiar **somente** a pasta `nds/DSiRABridge_034J/` para o cartão (p.ex. `D:\nds\DSiRABridge_034J\`).
3. DSi XL, Flipnote Lenny → HBMenu: testar **J0 `DSIRB_034J_BASE.nds` primeiro**. Deve exibir `MAIN REACHED: YES` e, após cerca de 2 s, `LOOP ALIVE`. Pressionar START para sair. Se branco, parar (POWER) e **não testar J1**.
4. Somente se J0 PASS, iniciar **J1 `DSIRB_034J_WIFI_CORE.nds`**. Ver se exibe `MAIN REACHED: YES` e `LOOP ALIVE`; se branco, parar, POWER. **Não repetir automaticamente**.
5. Informar resultado de J0/J1, texto exibido e se o contador avança. Não enviar ROM, SAV, credenciais, dados da NAND.

## Interpretação

- J0 PASS + J1 PASS: núcleo oficial DSWiFi é inicializável nesse fluxo; investigar migrar o launcher à arquitetura padrão, **sem afirmar que Wi-Fi conectado, retail ou RA funcionam**.
- J0 PASS + J1 WHITE: falha correlacionada à inclusão do núcleo DSWiFi *mesmo que oficial*, reforçando hipótese loader/tamanho/layout/estado RAM antes do ARM9; investigar segmento e possível incompatibilidade com a entrada HBMenu, não adivinhar.
- J0 WHITE: nossa reprodução do controle básico divergiu de F1; revisar versão, pacote, processo e configuração antes de testar J1.
- Em qualquer caso, **retail e conquistas oficiais continuam bloqueados** até validação separada.

Compilar, ligar ARM7ELF e validar header são condições de construção, não provas de boot real. Proibido modificar NAND/desbloqueio, lançar jogos ou configurar Wi-Fi nesta fase.

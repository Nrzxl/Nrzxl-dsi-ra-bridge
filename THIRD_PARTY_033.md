# Licenças da fase 0.3.3
A licença MIT da raiz continua aplicável ao código original do projeto, exceto componentes explicitamente identificados.

- dsi/launcher-033-gpl é GPL-2.0-or-later, incluindo glue novo e arquivos nds_loader_arm9.c/.h copiados de devkitPro/nds-hb-menu em 3c1f64c12da157fdd14a2d594db139f50e283261. Cabeçalhos e COPYING preservados. Não se apresenta esse executável como MIT.
- nds-bootloader em a0f819008a63f28c4994e7cc8a8ace892450bbb5 é GPL-2.0-or-later. O script build-independent-033.sh remove explicitamente o reparo volátil de keyslot AES da NAND para este laboratório SD-only. Nenhuma escrita persistente NAND é adicionada. Fonte correspondente completa e alteração são distribuídas junto do executável.
- fixture, observer e ferramentas host originais são MIT. O monitor não liga código DScheevos GPL.
- SDK devkitPro/libnds/Calico/newlib e seus termos são preservados no inventário/licenses do artefato de build. Não remover avisos.
- rcheevos oficial, commit1433173220a7eaede6a9ed7a18e94117be1821e0, MIT. Windows inclui licença e engine real.
- melonDS GPL é ferramenta de teste construída de fonte fixada; não é integrado ao monitor MIT nem incluído no ZIP SD.
- DScheevos/nds-bootstrap são fontes de pesquisa GPL; uma futura derivação retail deverá ter seu próprio escopo GPL e fonte correspondente. Não há relicenciamento para MIT.

Não há ROM, BIOS, firmware ou NAND de usuário nos artefatos.

# Arquitetura escolhida
## Fase 0.1 implementada em fontes
A aplicação independente é também um homebrew cooperativo de teste:
atualiza quatro palavras próprias, faz cópia limitada, valida valores e
guarda registros DSRB. A leitura é bytewise volatile sobre um objeto
alocado pelo próprio programa. Guardas vizinhas detectam corrupção.
Não há aceitação de endereços arbitrários, varredura de RAM, patch de
jogo, acesso NAND ou stack de rádio.

A coleta é acionada por A; B pausa; X exporta após pausar; START encerra.
Cada registro tem CRC32 e limites fixos. O diretório de saída fica somente
em sd:/DSiRABridge_010, e os arquivos usam O_EXCL. FAT é inicializado
somente quando o usuário pede exportação. Sem sd:/, a operação falha
sem escolher outro volume. Um arquivo parcial não é apagado nem
sobrescrito; repetir X escolhe outro nome.

A frequência nominal de coleta acompanha o laço swiWaitForVBlank.
O contador frame é do laço, não um contador independente de interrupções:
este espécime não mede VBlanks perdidos. A medição por timers 0/1 é da
cópia de 16 bytes no aplicativo isolado, não do custo de um monitor em jogo.

## Windows
O mesmo módulo JavaScript valida pacotes no viewer e no cliente Node.
Node oferece simulate, replay, listen e send-sim. Python é replay alternativo.
O listener fica em loopback por padrão; --bind 0.0.0.0 é opção de laboratório.
Não abre firewall, não autentica um DSi e não acessa serviços RA.
O viewer abre sem servidor ou instalação e permite simulação/importação.
Seu funcionamento em navegador e Node no Windows ainda é NOT_RUN.

## Separação de origem
source=1 quer dizer “produzido pelo diagnóstico em um runtime DS/DSi”.
Não atesta que seja hardware físico: um emulador executa o mesmo .nds.
source=2 é simulado. Importações e UDP mantêm a origem não verificada.
CRC detecta corrupção acidental, não fraude. Todos os caminhos atuais
têm officialEligible=false e nenhuma implementação de submissão RA.

## Próxima arquitetura de monitor persistente
Um fork isolado de nds-bootstrap deve reservar imagem/stack/fila,
reduzir cache de ROM quando necessário e verificar limites em link map.
CE7 acompanha VBlank; ARM9 captura RAM/DTCM coerentes, preservando
registradores, CPSR, LR, pilhas, alinhamento e política de cache.
Não reutilizar timers/DMA/VRAM já pertencentes ao jogo.

A transmissão e acesso ao filesystem devem ocorrer fora de IRQ, em
pontos compatíveis com o loader. Se houver perda, overflow, mudança de
jogo ou leitura desconhecida, a avaliação deve parar ou invalidar o
intervalo. Não repetir artificialmente frames com valores antigos para
continuar uma sessão oficial.

Um experimento A/B precisa comparar frames, saves separados, áudio,
tempo de carga e input com o bootstrap original. DSi-enhanced em modo
DSi não tem a mesma reserva que um título NTR; o modo deve ser gate de
ativação, não ajuste cosmético. Hardware sem permissões requer recusa.

## Integração oficial planejada
No Windows: rc_hash → identificação, rc_client → login/token,
carregamento do conjunto, callback de memória e avaliação por frame.
HTTPS com validação de certificado e User-Agent próprio.
Senha apenas durante login; token protegido pelo Windows e omitido dos logs.
Web API key de perfil não substitui automaticamente o token do cliente.

Primeiro usar apenas testes locais/spectator; posteriormente sessão
softcore com captura real validada e protocolo fechado para replay.
Importações SD, simulação, memória editável e sessão com perdas não
podem entrar no caminho de envio. O demonstrador C usa rc_runtime,
sem rc_client e sem transporte HTTP, por isso é incapaz de fazer award.
Consultar RA sobre o desenho de cliente em hardware antes de tratar a
integração como suportada. Aprovação hardcore é outra etapa, não um flag.

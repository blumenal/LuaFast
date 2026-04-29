## Funcionalidade do LuaFast

### Instalação de jogos
Permite pesquisar por appId ou partes do nome dos jogos, faz o download de forma automática dos arquivos .lua e .manifest .

### Instalar DLS´s
Permite selecionar jogos que foram adicionados e instalar as DLC´s disponíveis para o jogo selecionado.

### Atualizar Keys Instaladas
Permite fazer uma busca online por novas versões de arquivos .manifest e quando os encontra faz o download e atualiza o arquivo .lua .

### Remover Jogos
Permite selecionar jogos instalados e removelos da conta Steam.

### Backup de Key
Permite fazer o Backup e Restauração de arquivos .lua e .manifest .

### Save Games 
Permite fazer o Backup dos saves (funcionalidade ainda em implementação, pode conter erros).

### Reiniciar Steam 
Sempre que for inserido algo novo, este botão fecha a Steam e Abre novamente.

### Configurções
Aqui é possíve definir o local da pasta Steam e também mudar o tema do LuaFast.

### Token Hucap
Aqui é possível adicionar o token do https://hubcapmanifest.com
Os tokens são utilizados para liberar o download dos arquivos quando utilizando o metodo 2.

## Observação
Obs. Para o LuaFast funcionar perfeitamente ele precisa do Git instalado em seu pc. segue o link: https://git-scm.com/install/
Sobre a instalacao do git, apenas va apertando no next ate o fim sem precisar configurar nada.


## Funcionalidade das DLLs

### Recursos Principais

Possibilita adicionar uma quantidade gigantesca de jogos que você não possui utilizando arquivos .lua e .manifast.

Desbloqueie todos os DLCs de jogos que você não possui.

Carregar automaticamente chaves de descriptografia de depots a partir da .lua e .manifast.

Não faz nenhum tipo de conexão externa, tudo funciona localmente, único momento que se faz necessário ter uma conexão é no momento de download dos jogos.

Suporte para download de jogos ou DLCs protegidos que exigem um token de acesso.

## Compartilhamento Familiar e Remote Play
Contorne as restrições do Compartilhamento Familiar da Steam, permitindo que jogos compartilhados sejam jogados sem limitações.

## Como gerar as DLL´s

### Requisitos
Windows 10/11
CMake 3.20+
Visual Studio 2022 com MSVC (2022 17.14.31 x64)

1- Execute build.bat a partir da raiz do projeto para compilar.

2 - Ao termino do processo as dll´s se encontra em \build\Release

Obs.: Ao usar o LuaFast ele já cria as DLL´s dentro da pasta da Steam! Mas para estudos e conhecimento aqui tem tudo o necessário para ser criado as dlls do zero.




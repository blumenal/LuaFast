import asyncio
import logging
import os
import platform
import shutil
import re
import aiohttp
import httpx
import time
import json
import io
from pathlib import Path
from tqdm import tqdm
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Credenciais do Google Drive embutidas no código
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": " ",
    "private_key_id": " ",
    "private_key": """ """,
    "client_email": " ",
    "client_id": " ",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/v1/certs",
    "client_x509_cert_url": " ",
    "universe_domain": "googleapis.com"
}
# ID da pasta no Google Drive onde ficam os backups
PASTA_BACKUPS_ID = ' '


# Configuração de log
logging.basicConfig(level=logging.INFO, format="%(message)s")
LOG = logging.getLogger("Banner")

# Caminhos
STPLUG_PATH = Path("C:/Program Files (x86)/Steam/config/stplug-in")
DEPOTCACHE_PATH = Path("C:/Program Files (x86)/Steam/depotcache")
BACKUP_ROOT = Path("logs/backup")

# Cores ANSI
PRETO = "\033[30m"
VERMELHO = "\033[91m"
VERDE = "\033[92m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
MAGENTA = "\033[95m"
CIANO = "\033[96m"
BRANCO = "\033[97m"

# Tons normais (não brilhantes)
VERMELHO_ESCURO = "\033[31m"
VERDE_ESCURO = "\033[32m"
AMARELO_ESCURO = "\033[33m"
AZUL_ESCURO = "\033[34m"

# Reset
RESET = "\033[0m"


def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def tela_inicial():
    limpar_tela()
    # Ajustar o tamanho da janela (Windows)
    if os.name == "nt":
        os.system("mode con: cols=120 lines=50")

    arte = r"""
 _        _   _     ___          _____     ___      ___    _____   
| |      | | | |   / _ \        |  ___|   / _ \    / __|  |_   _|  
| |      | | | |  / /_\ \       | |_     / /_\ \   \__ \    | |    
| |___   | | | |  |  _  |       |  _|    |  _  |   __/ /    | |    
|_____|   \___/   | | | |       | |      | | | |  |___/     |_|    
    """
    print(VERDE + arte.center(80) + RESET)
    print(VERDE + "\tBem-vindo ao Gerenciador de Games LuaFast STEAM!" + RESET)
    print(AMARELO_ESCURO + "\nEste programa permite adicionar e remover jogos a sua conta STEAM, \nalém de fazer backup e restauração dos arquivos de licença." + RESET)
    print("\nMas antes de usar, leia atentamente as " + VERMELHO_ESCURO + "OBSERVAÇÕES" + RESET + " descritas a seguir.")
    print("__________________________________________________________________________________")
    print(VERDE + "\nQUAIS JOGOS FUNCIONAM COM ESSE MÉTODO?" + RESET)
    print("\nTodos os jogos que têm apenas a proteção antipirataria " + AZUL + "STEAM DRM" + RESET)
    print()
    print("Para saber se o jogo tem " + AZUL + "STEAM DRM" + RESET + ", verifique a página do jogo, lá haverá algo como: " + AMARELO + "\n'Requer aceitação de contrato de terceiros...'" + RESET)
    print()
    print("Exemplos de jogos que usam STEAM DRM: " + VERDE + "FINAL FANTASY VII REBIRTH, THE LAST OF US, SPIDER MAN..." + RESET)
    print("----------------------------------------------------------------------------------")
    print(VERMELHO + "\nQUAIS JOGOS É CERTO QUE NÃO IRÃO FUNCIONAR DE FORMA ALGUMA?" + RESET)
    print()
    print("Jogos que em sua página de informação constem:")
    print("- " + VERMELHO + "DRM de TERCEIROS" + RESET)
    print("- " + VERMELHO + "EA online activation" + RESET)
    print("- " + VERMELHO + "Xbox Live activation" + RESET)
    print("- " + VERMELHO + "Activision Account" + RESET)
    print("- " + VERMELHO + "Ubisoft Account" + RESET)
    print("- " + VERMELHO + "Denuvo Anti-tamper" + RESET)
    print()

    # Pergunta ao usuário se ele entendeu
    while True:
        resposta = input(AMARELO + "\nVocê entendeu todas as informações? (s/n): " + RESET).strip().lower()
        if resposta == "s":
            break
        elif resposta == "n":
            print(VERMELHO + "\nVocê não confirmou a leitura das instruções." + RESET)
            print(VERMELHO + "O programa será fechado em 4 segundos..." + RESET)
            time.sleep(4)
            exit(0)
        else:
            print(VERMELHO + "Opção inválida! Digite apenas 's' para sim ou 'n' para não." + RESET)



def exibir_banner():
    limpar_tela()
    if not platform.system() == "Windows":
        LOG.error("Este script só pode ser executado no Windows.")
        exit(1)
    banner = r"""
 _        _   _     ___          _____    _____     ___    _____   
| |      | | | |   / _ \        |  ___|  | ____|   / __|  |_   _|  
| |      | | | |  / /_\ \       | |_     |  _|     \__ \    | |    
| |___   | | | |  |  _  |       |  _|    | |___    __/ /    | |    
|_____|   \___/   | | | |       | |      |_____|  |___/     |_|    
                  \_| |_/       |_|                                 
    """
    LOG.info(banner)
    print(f"{VERDE}Desenvolvedores: blumenal86 & Jeffersonsud | Versão: 3.0.3 {RESET}")
    LOG.warning(" ")
    print(f"{VERMELHO}Venda proibida, esse programa é totalmente Gratis e mantido pelos Desenvolvedores.{RESET}")
    LOG.warning("Aviso: Funciona apenas no Windows 10/11.")
    LOG.warning("Utilize o site " + AZUL + "https://steamdb.info/" + RESET + " para conseguir o ID do game desejado. \nPara acessar o link segure Ctrl e clique no link.")
    LOG.warning(" ")
    
def autenticar_drive():
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=scopes
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

def listar_backups_drive(service, pasta_id):
    resultados = service.files().list(
        q=f"'{pasta_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name)",
    ).execute()
    return resultados.get('files', [])

def baixar_pasta_backup(service, pasta_id, destino):
    resultados = service.files().list(
        q=f"'{pasta_id}' in parents and trashed = false",
        fields="files(id, name, size)",
    ).execute()
    arquivos = resultados.get('files', [])

    os.makedirs(destino, exist_ok=True)

    for arquivo in arquivos:
        request = service.files().get_media(fileId=arquivo['id'])
        file_path = os.path.join(destino, arquivo['name'])
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        print()  # Linha em branco
        with tqdm(
            total=100,
            unit="%",
            ncols=100,                      # Deixa a barra larga
            bar_format="{desc} |{bar}| {percentage:.1f}% | {n_fmt}/{total_fmt} | ETA: {remaining}s",
            dynamic_ncols=True
        ) as pbar:
            pbar.set_description_str(f"Baixando {arquivo['name']}")
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    pbar.n = progress
                    pbar.last_print_n = progress
                    pbar.refresh()
            pbar.n = 100
            pbar.last_print_n = 100
            pbar.refresh()

        print(f"\n✅ Arquivo {arquivo['name']} baixado com sucesso!\n")




def executar_add():
    try:
        import add
        asyncio.run(add.main_flow(input("Digite o ID do Game: ").strip()))
    except Exception as e:
        print(f"Erro ao executar add.py: {e}")
        input("\nPressione Enter para continuar...")
        
def executar_compat():
    try:
        import compat
        asyncio.run(compat.menu_principal())
    except Exception as e:
        print(f"Erro ao executar compat.py: {e}")
        input("\nPressione Enter para continuar...")

def remover_manifests_por_id(app_id: str):
    for arquivo in DEPOTCACHE_PATH.glob(f"{app_id}_*.manifest"):
        try:
            arquivo.unlink()
        except Exception as e:
            print(f"Erro ao remover manifest {arquivo.name}: {e}")

async def fetch_game_name(app_id: str) -> str:
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data[app_id]['data']['name'] if data[app_id]['success'] else "Desconhecido"
    except:
        return "Desconhecido"

async def remover_game():
    if not STPLUG_PATH.exists():
        print("Pasta stplug-in não encontrada.")
        return
    while True:
        arquivos = list(STPLUG_PATH.glob("*.lua"))
        limpar_tela()
        print("\n" + "=" * 45)
        print("[ Remover Games/App da Conta Steam ]".center(45))
        print("=" * 45 + "\n")

        if not arquivos:
            print("Nenhum Game/App foi localizado.\n")
            input("Pressione Enter para continuar...")
            return

        print("Jogos encontrados:")
        id_map = {}
        for idx, arq in enumerate(arquivos, 1):
            app_id = arq.stem
            nome = await fetch_game_name(app_id)
            id_map[str(idx)] = arq
            print(f"{idx}. {app_id} - {nome}")
        sair_opcao = str(len(arquivos) + 1)
        print("0. Remover TODOS os jogos")
        print(f"{sair_opcao}. Voltar ao menu")

        escolha = input("\nDigite o número do jogo que deseja remover: ").strip()

        if escolha == sair_opcao:
            break
        elif escolha == "0":
            confirm = input("Tem certeza que deseja remover TODOS os jogos? (s/n): ").strip().lower()
            if confirm == "s":
                for arq in arquivos:
                    app_id = arq.stem
                    arq.unlink()
                    remover_manifests_por_id(app_id)
                input("Todos os jogos foram removidos com sucesso. Pressione Enter para continuar...")
                return
        elif escolha in id_map:
            app_id = id_map[escolha].stem
            id_map[escolha].unlink()
            remover_manifests_por_id(app_id)
            input("Jogo removido com sucesso. Pressione Enter para continuar...")
        else:
            input("Opção inválida. Pressione Enter para tentar novamente...")

async def backup_games():
    if not STPLUG_PATH.exists() or not DEPOTCACHE_PATH.exists():
        print("Pastas necessárias não foram encontradas.")
        return
    while True:
        limpar_tela()
        print("\n" + "=" * 50)
        print("[ Backup dos Arquivos de licença ]".center(50))
        print("=" * 50 + "\n")
        print(VERDE + "EM ALGUNS CASOS SÓ É POSSÍVEL EFETUAR O BACKUP ANTES DE SER FEITA A INSTALAÇÃO DO JOGO \nPOIS AO SER INSTALADO O APLICATIVO DA STEAM APAGA O ARQUIVO DE INSTALAÇÃO DA LICENÇA. \nENTÃO ANTES DE INSTALAR JÁ FAÇA O BACKUP CASO QUEIRA GUARDAR OS ARQUIVOS." + RESET)
        print("\n")
        arquivos = list(STPLUG_PATH.glob("*.lua"))
        if not arquivos:
            print("Nenhum jogo (.lua) encontrado para backup.")
            input("\nPressione Enter para sair...")
            return

        id_map = {}
        nomes_map = {}
        for idx, arq in enumerate(arquivos, 1):
            app_id = arq.stem
            nome = await fetch_game_name(app_id)
            id_map[str(idx)] = arq.name
            nomes_map[app_id] = nome
            status = f"{VERDE}[Backup OK]{RESET}" if (BACKUP_ROOT / app_id).exists() else ""
            print(f"{idx}. {app_id} - {nome} {status}")

        opcao_backup_todos = str(len(arquivos) + 1)
        opcao_sair = str(len(arquivos) + 2)
        print(f"{opcao_backup_todos}. Fazer backup de TODOS os jogos")
        print(f"{opcao_sair}. Sair")

        escolha = input("\nEscolha um número: ").strip()

        async def copiar_backup(lua_filename):
            app_id = Path(lua_filename).stem
            destino = BACKUP_ROOT / app_id
            destino.mkdir(parents=True, exist_ok=True)
            lua_origem = STPLUG_PATH / lua_filename
            arquivos_salvos = []
            if lua_origem.exists():
                shutil.copy2(lua_origem, destino)
                arquivos_salvos.append(lua_origem.name)
                with open(lua_origem, "r", encoding="utf-8") as f:
                    appids = re.findall(r'addappid\((\d+)', f.read())
                for a_id in set(appids):
                    for manifest in DEPOTCACHE_PATH.glob(f"{a_id}_*.manifest"):
                        shutil.copy2(manifest, destino)
                        arquivos_salvos.append(manifest.name)
            nome_jogo = nomes_map.get(app_id, "Desconhecido")
            print(f"\nArquivos copiados para o backup de {app_id} - {nome_jogo}:")
            for arquivo in arquivos_salvos:
                print(f" - {arquivo} [OK]")

        if escolha == opcao_sair:
            break
        elif escolha == opcao_backup_todos:
            for arq in arquivos:
                await copiar_backup(arq.name)
            input("\nBackup de todos os jogos realizado com sucesso. Pressione Enter...")
        elif escolha in id_map:
            await copiar_backup(id_map[escolha])
            app_id_escolhido = Path(id_map[escolha]).stem
            nome_escolhido = nomes_map.get(app_id_escolhido, "Desconhecido")
            input(f"\nBackup do jogo {app_id_escolhido} - {nome_escolhido} concluído. Pressione Enter...")
        else:
            input("\nOpção inválida. Pressione Enter para tentar novamente...")


async def restaurar_backup():
    while True:
        limpar_tela()
        print("\n" + "=" * 50)
        print("[ Opções de Backup ]".center(50))
        print("=" * 50 + "\n")
        print(VERDE + "\nQuando você não localizar ou não conseguir instalar um jogo pela opção de instalação usando o ID, \nvenha aqui e verifique se existe backup aqui na opção Nuvem." + RESET)
        print("\n1. Restaurar backups")
        print("\n2. Baixar backups da Nuvem")
        print("\n0. Voltar")
        escolha = input("\nEscolha uma opção: ").strip()

        if escolha == "1":
            break  # Continua para restaurar backups locais
        elif escolha == "2":
            try:
                await baixar_backup_drive()
            except Exception as e:
                print(f"\nOcorreu um erro ao baixar o backup: {e}")
                input("\nPressione Enter para copiar o erro e voltar...")
        elif escolha == "0":
            return  # Voltar ao menu principal
        else:
            input("\nOpção inválida. Pressione Enter para tentar novamente...")

    # =============================
    # Daqui para baixo é a restauração LOCAL (o seu código original)

    if not BACKUP_ROOT.exists():
        print("A pasta de backups não foi encontrada.")
        input("\nPressione Enter para sair...")
        return

    backups = sorted([p for p in BACKUP_ROOT.iterdir() if p.is_dir()])
    if not backups:
        print("Nenhum backup disponível para restaurar.")
        input("\nPressione Enter para sair...")
        return

    while True:
        limpar_tela()
        print("\n" + "=" * 50)
        print("[ Restauração de Backups Steam ]".center(50))
        print("=" * 50 + "\n")

        id_map = {}
        for idx, pasta in enumerate(backups, 1):
            app_id = pasta.name
            nome = await fetch_game_name(app_id)
            id_map[str(idx)] = app_id
            print(f"{idx}. {app_id} - {nome}")

        sair_opcao = str(len(backups) + 1)
        print("0. Restaurar TODOS os backups")
        print(f"{sair_opcao}. Sair")
        escolha = input("\nEscolha uma opção: ").strip()

        def restaurar(app_id):
            origem = BACKUP_ROOT / app_id
            for arquivo in origem.glob("*"):
                try:
                    destino = STPLUG_PATH if arquivo.suffix == ".lua" else DEPOTCACHE_PATH
                    shutil.copy2(arquivo, destino)
                except Exception as e:
                    print(f"Erro ao restaurar {arquivo.name}: {e}")

        if escolha == sair_opcao:
            break
        elif escolha == "0":
            for app_id in id_map.values():
                restaurar(app_id)
            input("\nTodos os backups foram restaurados. Pressione Enter...")
        elif escolha in id_map:
            restaurar(id_map[escolha])
            input(f"\nBackup do jogo {id_map[escolha]} restaurado com sucesso. Pressione Enter...")
        else:
            input("\nOpção inválida. Pressione Enter para tentar novamente...")

            
async def baixar_backup_drive():
    service = autenticar_drive()
    backups = listar_backups_drive(service, PASTA_BACKUPS_ID)

    if not backups:
        print("Nenhum backup encontrado no Google Drive.")
        input("\nPressione Enter para voltar...")
        return

    while True:
        limpar_tela()
        print("\n" + "=" * 50)
        print("[ Baixar Backups do Google Drive ]".center(50))
        print("=" * 50 + "\n")

        id_map = {}
        for idx, backup in enumerate(backups, 1):
            appid = backup['name']
            nome_jogo = await fetch_game_name(appid)
            id_map[str(idx)] = backup
            print(f"{idx}. {appid} - {nome_jogo}")

        sair_opcao = str(len(backups) + 1)
        print(f"\n{sair_opcao}. Voltar")
        escolha = input("\nEscolha um backup para baixar: ").strip()

        if escolha == sair_opcao:
            break
        elif escolha in id_map:
            backup_escolhido = id_map[escolha]
            destino = BACKUP_ROOT / backup_escolhido['name']
            print(f"\nBaixando backup: {backup_escolhido['name']}")
            baixar_pasta_backup(service, backup_escolhido['id'], destino)
            print(f"\nBackup '{backup_escolhido['name']}' baixado com sucesso em '{destino}'!")

            # Perguntar se quer baixar outro
            outra = input("\nDeseja baixar outro backup? (S/N): ").strip().lower()
            if outra != 's':
                break  # se não quiser baixar outro, sai do loop

        else:
            print(f"\n{VERMELHO}Opção inválida.{RESET}")
            input("\nPressione Enter para tentar novamente...")




def encerrar_processos_steam():
    try:
        print("Encerrando todos os processos relacionados à Steam...")
        os.system("taskkill /F /IM Steam.exe >nul 2>&1")
        os.system("taskkill /F /IM steamwebhelper.exe >nul 2>&1")
        os.system("taskkill /F /IM GameOverlayUI.exe >nul 2>&1")
        while True:
            time.sleep(1)
            check = os.popen('tasklist | findstr /I "steam"').read()
            if check.strip() == "":
                break
        print("Todos os processos da Steam foram encerrados.\n")
        
        while True:
            resposta = input("Deseja reabrir a Steam agora? (s/n): ").strip().lower()
            if resposta == "s":
                abrir_steam()
                break
            elif resposta == "n":
                print("Ok, a Steam permanecerá fechada.")
                break
            else:
                print("Opção inválida! Digite 's' para sim ou 'n' para não.")
    except Exception as e:
        print(f"Erro ao encerrar processos da Steam: {e}")
        input("\nPressione Enter para continuar...")


def abrir_steam():
    try:
        tasks = os.popen('tasklist /FI "IMAGENAME eq Steam.exe"').read()
        if "Steam.exe" in tasks:
            print("A Steam já está em execução.")
        else:
            steam_path = '"C:\\Program Files (x86)\\Steam\\Steam.exe"'
            os.system(f'start "" {steam_path}')
            print("Steam foi iniciada.")
        input("\nPressione Enter para continuar...")
    except Exception as e:
        print(f"Erro ao abrir a Steam: {e}")
        input("\nPressione Enter para continuar...")

def menu():
    while True:
        exibir_banner()
        print("\nSelecione uma opção:")
        print("1. Compatibilidade dos jogos.")
        print("2. Adicionar Game/App à sua conta STEAM.")
        print("3. Remover Game/App da sua conta STEAM.")
        print("4. Fazer Backup dos Arquivos de ativação.")
        print("5. Restaurar Backup")
        print("6. Finalizar Steam")
        print("7. Inicializar Steam")
        print("0. Sair")
        escolha = input("\nDigite o número da opção desejada: ")
        print(" ")

        if escolha == "1":
            executar_compat()
        if escolha == "2":
            executar_add()
        elif escolha == "3":
            asyncio.run(remover_game())
        elif escolha == "4":
            asyncio.run(backup_games())
        elif escolha == "5":
            asyncio.run(restaurar_backup())
        elif escolha == "6":
            encerrar_processos_steam()
        elif escolha == "7":
            abrir_steam()
        elif escolha == "0":
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    tela_inicial()
    menu()

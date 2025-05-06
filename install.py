import os
import io
import sys
import time
import asyncio
import aiohttp
import aiofiles
import httpx
import vdf
import subprocess
import requests
import traceback
from bs4 import BeautifulSoup
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from typing import Any, Tuple, List, Dict
from common import log, variable
from common.variable import CLIENT, HEADER, STEAM_PATH, REPO_LIST

# Cores ANSI
PRETO = "\033[30m"
VERMELHO = "\033[91m"
VERDE = "\033[92m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
MAGENTA = "\033[95m"
CIANO = "\033[96m"
BRANCO = "\033[97m"
VERMELHO_ESCURO = "\033[31m"
VERDE_ESCURO = "\033[32m"
AMARELO_ESCURO = "\033[33m"
AZUL_ESCURO = "\033[34m"
RESET = "\033[0m"

def formatar_data_brasil(data_iso: str) -> str:
    """Converte data ISO (ex: '2024-05-20T14:30:00Z') para DD/MM/AAAA HH:MM."""
    from datetime import datetime
    try:
        data_obj = datetime.strptime(data_iso.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
        return data_obj.strftime("%d/%m/%Y %H:%M")  # Formato BR
    except:
        return data_iso  # Mantém o original se falhar

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# Credenciais do Google Drive embutidas no código
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": " ",
    "private_key_id": " ",
    "private_key": """-----BEGIN PRIVATE KEY-----

-----END PRIVATE KEY-----""",
    "client_email": " ",
    "client_id": " ",
    "auth_uri": " ",
    "token_uri": " ",
    "auth_provider_x509_cert_url": " ",
    "client_x509_cert_url": " ",
    "universe_domain": " "
}
# ID da pasta no Google Drive onde ficam os backups
PASTA_BACKUPS_ID = ' '

STPLUG_PATH = Path("C:/Program Files (x86)/Steam/config/stplug-in")
DEPOTCACHE_PATH = Path("C:/Program Files (x86)/Steam/depotcache")

# --- Funções auxiliares ---

def autenticar_drive():
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
    return build('drive', 'v3', credentials=credentials)

def buscar_backup_por_id(service, appid):
    query = f"'{PASTA_BACKUPS_ID}' in parents and name = '{appid}' and trashed = false"
    resultados = service.files().list(q=query, fields="files(id, name)").execute()
    arquivos = resultados.get('files', [])
    return arquivos[0]['id'] if arquivos else None

async def buscar_nome_jogo(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if data and str(appid) in data and data[str(appid)]['success']:
                return data[str(appid)]['data']['name']
            return None

def baixar_arquivos_backup(service, pasta_id):
    resultados = service.files().list(
        q=f"'{pasta_id}' in parents and trashed = false",
        fields="files(id, name, size)"
    ).execute()
    arquivos = resultados.get('files', [])
    total = len(arquivos)
    if total == 0:
        print("Nenhum arquivo encontrado para este backup.")
        return

    print(f"\n🔎 {total} arquivos encontrados no backup. Iniciando download...\n")
    barra_total = 30

    for idx, arquivo in enumerate(arquivos, 1):
        request = service.files().get_media(fileId=arquivo['id'])
        destino = STPLUG_PATH if arquivo['name'].endswith('.lua') else DEPOTCACHE_PATH
        os.makedirs(destino, exist_ok=True)
        file_path = destino / arquivo['name']
        try:
            with io.FileIO(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            sucesso = True
        except Exception:
            sucesso = False

        barra = int((idx / total) * barra_total)
        barra_visual = '[' + '=' * barra + ' ' * (barra_total - barra) + ']'
        status_text = "✅" if sucesso else "❌"
        print(f"{barra_visual} {idx}/{total} {status_text} {arquivo['name']}")

# --- Função desbloqueio (substitui GitHub) ---

async def desbloquear_jogo(app_id: str):
    LOG = log.log("LuaFast")

    def stack_error(exception: Exception) -> str:
        return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

    async def check_github_api_rate_limit(headers):
        url = "https://api.github.com/rate_limit"
        try:
            r = await CLIENT.get(url, headers=headers)
            if r.status_code == 200:
                r_json = r.json()
                remaining_requests = r_json.get("rate", {}).get("remaining", 0)
                LOG.info(f"Requisições restantes: {remaining_requests}")
        except Exception as e:
            LOG.error(f"Erro ao verificar limite da API do GitHub: {stack_error(e)}")

    async def get_latest_repo_info(repos: list, app_id: str, headers):
        data_mais_recente = None
        repo_selecionado = None
        for repo in repos:
            url = f"https://api.github.com/repos/{repo}/branches/{app_id}"
            r = await CLIENT.get(url, headers=headers)
            if "commit" in r.json():
                data = r.json()["commit"]["commit"]["author"]["date"]
                if (data_mais_recente is None) or (data > data_mais_recente):
                    data_mais_recente = str(data)
                    repo_selecionado = str(repo)
        return repo_selecionado, data_mais_recente

    async def fetch_from_cdn(sha: str, path: str, repo: str):
        url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
        for _ in range(3):
            try:
                r = await CLIENT.get(url, headers=HEADER, timeout=30)
                if r.status_code == 200:
                    return r.read()
            except Exception as e:
                LOG.warning(f"Erro ao baixar {path}: {e}")
        raise Exception(f"Falha ao baixar {path}")

    def parse_key_vdf(content: bytes) -> List[Tuple[str, str]]:
        try:
            depots = vdf.loads(content.decode("utf-8"))['depots']
            return [(d_id, d_info['DecryptionKey']) for d_id, d_info in depots.items()]
        except Exception as e:
            LOG.error(f"Erro parseando chave: {e}")
            return []

    async def handle_depot_files(repos: List, app_id: str, steam_path: Path, repo: str):
        coletados = []
        mapa_depot = {}
        url = f"https://api.github.com/repos/{repo}/branches/{app_id}"
        r = await CLIENT.get(url, headers=HEADER)
        tree_url = r.json()["commit"]["commit"]["tree"]["url"]
        tree_res = await CLIENT.get(tree_url)
        
        # Contar arquivos para barra de progresso
        arquivos = [item for item in tree_res.json()["tree"] if item["path"].endswith(".manifest") or "key.vdf" in item["path"].lower()]
        total = len(arquivos)
        barra_total = 30
        
        if total == 0:
            print("Nenhum arquivo encontrado para download.")
            return coletados, mapa_depot
            
        print(f"\n🔎 {total} arquivos encontrados. Iniciando download...\n")
        
        for idx, item in enumerate(arquivos, 1):
            path = item["path"]
            if path.endswith(".manifest"):
                caminho_salvar = steam_path / "depotcache" / path
                os.makedirs(caminho_salvar.parent, exist_ok=True)
                conteudo = await fetch_from_cdn(r.json()["commit"]["sha"], path, repo)
                async with aiofiles.open(caminho_salvar, "wb") as f:
                    await f.write(conteudo)
                sucesso = True
            elif "key.vdf" in path.lower():
                conteudo = await fetch_from_cdn(r.json()["commit"]["sha"], path, repo)
                coletados.extend(parse_key_vdf(conteudo))
                sucesso = True
            else:
                sucesso = False

            # Atualizar barra de progresso
            barra = int((idx / total) * barra_total)
            barra_visual = '[' + '=' * barra + ' ' * (barra_total - barra) + ']'
            status_text = "✅" if sucesso else "❌"
            print(f"{barra_visual} {idx}/{total} {status_text} {path}")
            
        return coletados, mapa_depot

    async def setup_steamtools(depot_data: List[Tuple[str, str]], app_id: str, depot_map: Dict):
        st_path = STEAM_PATH / "config" / "stplug-in"
        st_path.mkdir(exist_ok=True)
        bloquear = True
        conteudo = f'addappid({app_id}, 1, "None")\n'
        for d_id, d_key in depot_data:
            conteudo += f'addappid({d_id}, 1, "{d_key}")\n'
        async with aiofiles.open(st_path / f"{app_id}.lua", "w") as f:
            await f.write(conteudo)
        return True

    await check_github_api_rate_limit(HEADER)
    repo_usado, data_recente = await get_latest_repo_info(REPO_LIST, app_id, HEADER)
        
    if not repo_usado:
        #LOG.error("Nenhum repositório válido encontrado.")
        return None, None
    depot_data, depot_map = await handle_depot_files(REPO_LIST, app_id, STEAM_PATH, repo_usado)
    await setup_steamtools(depot_data, app_id, depot_map)
    return repo_usado, data_recente

def verificar_drm(appid):
    def buscar_drm_steam_store(appid):
        def extrair_drm(texto):
            texto = texto.lower()
            drm = set()
            if "denuvo" in texto:
                drm.add("Denuvo")
            if "steamworks" in texto or "requires steam" in texto or "necessita do steam" in texto:
                drm.add("Steamworks")
            if "third-party drm" in texto or "3rd-party drm" in texto or "drm de terceiros" in texto:
                drm.add("Third-party DRM")
            return drm

        try:
            drm_total = set()
            url_en = f"https://store.steampowered.com/app/{appid}/?cc=us&l=en"
            response_en = requests.get(url_en, headers=HEADERS)
            if response_en.status_code == 200:
                soup_en = BeautifulSoup(response_en.text, "html.parser")
                drm_total.update(extrair_drm(soup_en.get_text()))

            url_pt = f"https://store.steampowered.com/app/{appid}/"
            response_pt = requests.get(url_pt, headers=HEADERS)
            if response_pt.status_code == 200:
                soup_pt = BeautifulSoup(response_pt.text, "html.parser")
                drm_total.update(extrair_drm(soup_pt.get_text()))

            return ", ".join(sorted(drm_total)) if drm_total else "Não especificado"

        except Exception:
            return "Não especificado"

    def get_steam_game_info(appid):
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            return {"appid": appid, "error": "Erro ao acessar a Steam API."}

        data = response.json()
        game_data = data.get(str(appid), {}).get("data")
        if not game_data:
            return {"appid": appid, "error": "Jogo não encontrado."}

        name = game_data.get("name", "Desconhecido")
        about = game_data.get("about_the_game", "")
        detailed = game_data.get("detailed_description", "")
        drm = []

        about_lower = about.lower()
        detailed_lower = detailed.lower()

        if "denuvo" in about_lower or "denuvo" in detailed_lower:
            drm.append("Denuvo")
        if "third-party drm" in about_lower or "3rd-party drm" in about_lower:
            drm.append("Third-party DRM")
        if "steamworks" in about_lower or "requires steam" in about_lower:
            drm.append("Steamworks")

        drm_info = ", ".join(drm) if drm else buscar_drm_steam_store(appid)

        return {"appid": appid, "name": name, "drm": drm_info}

    info = get_steam_game_info(appid)
    if "error" in info:
        print(f"\n❌ [{appid}] ERRO: {info['error']}")
        return

    print(f"\n📌 AppID: {appid}")
    print(f"🎮 Nome : {info['name']}")
    print(f"🔐 DRM  : {info['drm']}")
    
    drm_text = info['drm'].lower()
    if "denuvo" in drm_text:
        print("🚫 Situação: ❌ O jogo não funciona atualmente (Denuvo), mas pode funcionar no futuro.\n")
    elif "steamworks" in drm_text and ("third-party" in drm_text or "," in drm_text):
        print("⚠️ Situação: ⚠️ O jogo talvez funcione (Steamworks + outro DRM).\n")
    elif "steamworks" in drm_text:
        print("✅ Situação: ✔️ O jogo deve funcionar normalmente.\n")
    elif drm_text in ["", "não especificado"]:
        print("✅ Situação: ✔️ O jogo deve funcionar (sem DRM detectado).\n")
    else:
        print("❓ Situação: ❓ DRM não identificado claramente. Talvez funcione.\n")
    return info['name']

def encerrar_e_reiniciar_steam():
    processos_steam = [
        "Steam.exe",  # Deve ser encerrado primeiro
        "steamwebhelper.exe",
        "GameOverlayUI.exe",
        "SteamService.exe",
        "steamerrorreporter.exe",
        "steamstart.exe",
        "steamguard.exe"
    ]

    print("[*] Encerrando processos da Steam...\n")
    for processo in processos_steam:
        try:
            print(f"[-] Encerrando {processo}...")
            subprocess.run(["taskkill", "/F", "/IM", processo], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Erro ao encerrar {processo}: {e}")

    time.sleep(2)

    print("\n[*] Verificando se ainda há processos ativos...")
    try:
        # encoding='mbcs' evita erros com nomes de processos em sistemas em pt-BR
        output = subprocess.check_output("tasklist", shell=True, encoding="mbcs").lower()
        processos_ativos = [p for p in processos_steam if p.lower() in output]

        if processos_ativos:
            print("[!] Ainda existem processos ativos:")
            for p in processos_ativos:
                print(f"    - {p}")
        else:
            print("[✓] Todos os processos da Steam foram encerrados.")
    except Exception as e:
        print(f"[!] Erro ao verificar processos: {e}")

    print("\n[*] Reiniciando a Steam...")
    caminho_steam = os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Steam", "Steam.exe")
    if os.path.exists(caminho_steam):
        try:
            subprocess.Popen([caminho_steam], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[✓] Steam reiniciada com sucesso.")
        except Exception as e:
            print(f"[!] Erro ao iniciar a Steam: {e}")
    else:
        print("[!] Caminho da Steam não encontrado.")

# --- Nova função para instalar múltiplos IDs ---
async def instalar_multiplos_ids():
    print(f"\n{AMARELO}🎮 Digite os IDs das DLCs que deseja instalar (separados por espaço):{RESET}\n")
    ids_input = input().strip()
    ids = ids_input.split()
    
    if not ids:
        print(f"{VERMELHO}❌ Nenhum ID fornecido.{RESET}")
        return
    
    for appid in ids:
        appid = appid.strip()
        if not appid.isdigit():
            print(f"{VERMELHO}❌ ID inválido: {appid}. Pulando...{RESET}")
            continue
            
        print(f"\n{AZUL}════════════════════════════════════════════════════════════{RESET}")
        print(f"{VERDE}🔍 Processando ID: {appid}{RESET}")
        
        nome = verificar_drm(appid)
        if not nome:
            print(f"{VERMELHO}⚠️ Nome do jogo não encontrado na Steam. Continuando assim mesmo.{RESET}")
            nome = appid
            
        try:
            repo_usado, data_recente = await desbloquear_jogo(appid)
            if repo_usado:
                data_br = formatar_data_brasil(data_recente)
                print(f"{VERDE}✅ {nome} instalado com sucesso!{RESET}")
                print(f"📦 Arquivos obtidos do repositório: {AMARELO}{repo_usado}{RESET}")
                print(f"📅 Data da atualização da Key: {VERDE}{data_br}{RESET}")
            else:
                print(f"{VERMELHO}❌ Não foi possível encontrar arquivos para {nome} em nenhum repositório.{RESET}")
        except Exception as e:
            print(f"{VERMELHO}❌ Erro ao instalar {nome}: {str(e)}{RESET}")
            continue

# --- Menu principal ---
async def main_flow():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Cabeçalho decorativo
        print(f"{AZUL}      \n        ╔════════════════════════════════════════════════════════════╗")
        print(f"        ║        {BRANCO}     🚀 INSTALADOR DE KEYS STEAM v3.7               {AZUL}║")
        print(f"        ╚════════════════════════════════════════════════════════════╝{RESET}\n")

        # Informações explicativas
        print(f"{VERDE}       📢 Escolha a biblioteca de onde será feito o download das keys:{RESET}\n")
        print(f"    🔓 A biblioteca compartilhada é pública e atualizada com frequência, contem uma vasta quantidade de games.")
        print(f"    🔒 A biblioteca restrita (LuaFast) oferece backups de que podem ainda não estar na Biblioteca Publica.")
        print(f"\n{AMARELO}    💡 Dica:{RESET} Caso o jogo não apareça após instalar por uma opção, tente a outra.")
        print(f"        As bibliotecas são atualizadas em momentos diferentes.\n")

        print(f"{AZUL}                ╔════════════════════════════════════════════╗")
        print(f"                ║  {AMARELO}[1]{RESET} Biblioteca compartilhada              {AZUL}║")
        print(f"                ║  {AMARELO}[2]{RESET} Biblioteca restrita (LuaFast)         {AZUL}║")
        print(f"                ║  {CIANO}[3]{RESET} Instalar DLCs (múltiplos IDs)         {AZUL}║")
        print(f"                ║  {VERMELHO}[0]{RESET} Sair do programa                      {AZUL}║")
        print(f"                ╚════════════════════════════════════════════╝{RESET}")

        escolha = input(f"\n{CIANO}👉 Digite sua escolha: {RESET}").strip().lower()
        if escolha == "0":
            print(f"\n{VERMELHO}❌ Encerrando o programa...{RESET}")
            time.sleep(1)
            sys.exit()
        if escolha not in ["1", "2", "3"]:
            print(f"\n{VERMELHO}❗ Escolha inválida. Tente novamente.{RESET}")
            time.sleep(2)
            continue

        if escolha == "3":
            await instalar_multiplos_ids()
        else:
            appid = input(f"\n{AMARELO}🎮 Digite o ID do jogo que deseja instalar:{RESET} ").strip()
            if appid == "0":
                continue

            nome = verificar_drm(appid)
            if nome:            
                if input("Deseja instalar este jogo? (S/N): ").strip().lower() != "s":
                    print("\nInstalação cancelada.\n")
                    time.sleep(2)
                    continue
            else:
                print("\nNome do jogo não encontrado na Steam. Continuando assim mesmo.")
                time.sleep(1)

            if escolha == "1":
                repo_usado, data_recente = await desbloquear_jogo(appid)
                if repo_usado:
                    print(f"\n✅ Instalação do jogo {nome if nome else appid} concluída com sucesso!\n")
                    data_br = formatar_data_brasil(data_recente)
                    print(f"📦 Arquivos obtidos do repositório: {AMARELO}{repo_usado}{RESET}")
                    print(f"📅 Data da atualização da Key: {VERDE}{data_br}{RESET}\n")
                else:
                    print(f"\n{VERMELHO}❌ Não foi possível encontrar arquivos para {nome if nome else appid} em nenhum repositório.{RESET}\n")
            else:
                repo_usado = None
                service = autenticar_drive()
                pasta_id = buscar_backup_por_id(service, appid)
                if not pasta_id:
                    print("\nBackup não encontrado para este ID.")
                    time.sleep(2)
                    continue
                baixar_arquivos_backup(service, pasta_id)
                print(f"\n✅ Instalação do jogo {nome if nome else appid} concluída com sucesso!\n")

        if input("\nDeseja instalar outro jogo? (S/N): ").strip().lower() != "s":
            if input("Deseja reiniciar a Steam agora? (S/N): ").strip().lower() == "s":
                encerrar_e_reiniciar_steam()
                print("Steam reiniciada com sucesso!")
            break

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main_flow())
            break  # Sai do loop se main_flow() terminar sem erros
        except Exception as e:
            print(f"\n{VERMELHO}⚠️ Ocorreu um erro inesperado:{RESET}")
            print(f"{VERMELHO}{traceback.format_exc()}{RESET}")
            print(f"\n{AMARELO}O programa será reiniciado automaticamente em 5 segundos...{RESET}")
            time.sleep(8)
            continue  # Reinicia o loop e o programa
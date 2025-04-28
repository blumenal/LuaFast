import os
import sys
import traceback
import asyncio
import aiofiles
import httpx
import vdf
import time
from typing import Any, Tuple, List, Dict
from pathlib import Path
from common import log, variable
from common.variable import (
    get_client,
    HEADER,
    STEAM_PATH,
    REPO_LIST,
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

LOCK = asyncio.Lock()
LOG = log.log("Onekey")
DEFAULT_REPO = REPO_LIST[0]

def init() -> None:
    pass

def stack_error(exception: Exception) -> str:
    stack_trace = traceback.format_exception(
        type(exception), exception, exception.__traceback__
    )
    return "".join(stack_trace)

async def checkcn(CLIENT) -> bool:
    try:
        req = await CLIENT.get("https://mips.kugou.com/check/iscn?&format=json")
        body = req.json()
        scn = bool(body["flag"])
        if not scn:
            LOG.info(f"Você está usando o projeto fora da China ({body['country']}), alternando automaticamente para a CDN oficial do GitHub")
            variable.IS_CN = False
            return False
        else:
            variable.IS_CN = True
            return True
    except KeyboardInterrupt:
        LOG.info("O programa foi encerrado")
        return True
    except httpx.ConnectError:
        variable.IS_CN = True
        LOG.warning("Falha ao verificar a localização do servidor, ignorado, considerado como China")
        return False

async def check_github_api_rate_limit(CLIENT, headers):
    url = "https://api.github.com/rate_limit"
    try:
        r = await CLIENT.get(url, headers=headers)
        r_json = r.json()
        if r.status_code == 200:
            rate_limit = r_json.get("rate", {})
            remaining_requests = rate_limit.get("remaining", 0)
            reset_time = rate_limit.get("reset", 0)
            reset_time_formatted = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(reset_time)
            )
            LOG.info(f"Restante de requisições: {remaining_requests}")
            if remaining_requests == 0:
                LOG.warning(
                    f"Limite de requisições da API do GitHub foi atingido, será resetado em {reset_time_formatted}. Recomenda-se gerar um Token e colocá-lo no arquivo de configuração."
                )
        else:
            LOG.error("Falha ao verificar as requisições do GitHub, erro de rede")
    except KeyboardInterrupt:
        LOG.info("O programa foi encerrado")
    except httpx.ConnectError as e:
        LOG.error(f"Falha ao verificar a API do GitHub, {stack_error(e)}")
    except httpx.ConnectTimeout as e:
        LOG.error(f"Timeout ao verificar API do GitHub: {stack_error(e)}")
    except Exception as e:
        LOG.error(f"Erro ocorreu: {stack_error(e)}")

async def get_latest_repo_info(CLIENT, repos: list, app_id: str, headers) -> Any | str | None:
    latest_date = None
    selected_repo = None
    for repo in repos:
        url = f"https://api.github.com/repos/{repo}/branches/{app_id}"
        r = await CLIENT.get(url, headers=headers)
        r_json = r.json()
        if r_json and "commit" in r_json:
            date = r_json["commit"]["commit"]["author"]["date"]
            if (latest_date is None) or (date > latest_date):
                latest_date = str(date)
                selected_repo = str(repo)
    return selected_repo, latest_date

async def handle_depot_files(CLIENT, repos: List, app_id: str, steam_path: Path) -> List[Tuple[str, str]]:
    collected = []
    depot_map = {}
    try:
        selected_repo, latest_date = await get_latest_repo_info(CLIENT, repos, app_id, headers=HEADER)
        if selected_repo:
            branch_url = f"https://api.github.com/repos/{selected_repo}/branches/{app_id}"
            branch_res = await CLIENT.get(branch_url, headers=HEADER)
            branch_res.raise_for_status()

            tree_url = branch_res.json()["commit"]["commit"]["tree"]["url"]
            tree_res = await CLIENT.get(tree_url)
            tree_res.raise_for_status()

            depot_cache = steam_path / "depotcache"
            depot_cache.mkdir(exist_ok=True)

            LOG.info(f"Repositório selecionado: https://github.com/{selected_repo}")
            LOG.info(f"Última atualização da branch: {latest_date}")

            for item in tree_res.json()["tree"]:
                file_path = str(item["path"])
                if file_path.endswith(".manifest"):
                    save_path = depot_cache / file_path
                    if save_path.exists():
                        LOG.warning(f"Manifesto já existe: {save_path}")
                        continue
                    content = await fetch_from_cdn(CLIENT, branch_res.json()["commit"]["sha"], file_path, selected_repo)
                    LOG.info(f"Manifesto baixado com sucesso: {file_path}")
                    async with aiofiles.open(save_path, "wb") as f:
                        await f.write(content)
                elif "key.vdf" in file_path.lower():
                    key_content = await fetch_from_cdn(CLIENT, branch_res.json()["commit"]["sha"], file_path, selected_repo)
                    collected.extend(parse_key_vdf(key_content))

            for item in tree_res.json()["tree"]:
                if not item["path"].endswith(".manifest"):
                    continue
                filename = Path(item["path"]).stem
                if "_" not in filename:
                    continue
                depot_id, manifest_id = filename.replace(".manifest", "").split("_", 1)
                if not (depot_id.isdigit() and manifest_id.isdigit()):
                    continue
                depot_map.setdefault(depot_id, []).append(manifest_id)

            for depot_id in depot_map:
                depot_map[depot_id].sort(key=lambda x: int(x), reverse=True)

    except httpx.HTTPStatusError as e:
        LOG.error(f"Erro HTTP: {e.response.status_code}")
    except Exception as e:
        LOG.error(f"Falha ao processar arquivos: {str(e)}")
    return collected, depot_map

async def fetch_from_cdn(CLIENT, sha: str, path: str, repo: str):
    if variable.IS_CN:
        url_list = [
            f"https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}",
            f"https://raw.gitmirror.com/{repo}/{sha}/{path}",
            f"https://raw.dgithub.xyz/{repo}/{sha}/{path}",
            f"https://gh.akass.cn/{repo}/{sha}/{path}",
        ]
    else:
        url_list = [f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"]

    retry = 3
    while retry > 0:
        for url in url_list:
            try:
                r = await CLIENT.get(url, headers=HEADER, timeout=30)
                if r.status_code == 200:
                    return r.read()
                else:
                    LOG.error(f"Falha ao obter: {path} - Código: {r.status_code}")
            except Exception as e:
                LOG.error(f"Erro ao tentar obter {path}: {str(e)}")
        retry -= 1
        LOG.warning(f"Tentativas restantes: {retry} - {path}")
    raise Exception(f"Não foi possível baixar: {path}")

def parse_key_vdf(content: bytes) -> List[Tuple[str, str]]:
    try:
        depots = vdf.loads(content.decode("utf-8"))["depots"]
        return [(d_id, d_info["DecryptionKey"]) for d_id, d_info in depots.items()]
    except Exception as e:
        LOG.error(f"Falha ao parsear chave: {str(e)}")
        return []

async def setup_unlock_tool(depot_data: List[Tuple[str, str]], app_id: str, tool_choice: int, depot_map: Dict) -> bool:
    return await setup_steamtools(depot_data, app_id, depot_map)

async def setup_steamtools(depot_data: List[Tuple[str, str]], app_id: str, depot_map: Dict) -> bool:
    st_path = STEAM_PATH / "config" / "stplug-in"
    st_path.mkdir(exist_ok=True)

    versionlock = True
    lua_content = f'addappid({app_id}, 1, "None")\n'
    for d_id, d_key in depot_data:
        if versionlock:
            for manifest_id in depot_map[d_id]:
                lua_content += f'addappid({d_id}, 1, "{d_key}")\nsetManifestid({d_id},"{manifest_id}")\n'
        else:
            lua_content += f'addappid({d_id}, 1, "{d_key}")\n'

    lua_file = st_path / f"{app_id}.lua"
    async with aiofiles.open(lua_file, "w") as f:
        await f.write(lua_content)
    return True

async def main_flow(app_id: str):
    CLIENT = get_client()
    app_id_list = list(filter(str.isdecimal, app_id.strip().split("-")))
    if not app_id_list:
        LOG.error(f"ID do Game inválido")
        return False

    app_id = app_id_list[0]
    try:
        await checkcn(CLIENT)
        await check_github_api_rate_limit(CLIENT, HEADER)
        depot_data, depot_map = await handle_depot_files(CLIENT, REPO_LIST, app_id, STEAM_PATH)

        if await setup_unlock_tool(depot_data, app_id, 1, depot_map):
            LOG.info("Configuração de desbloqueio concluída!")
            LOG.info("Reinicie o Steam para aplicar.")
        else:
            LOG.error("Falha na configuração")
        return True
    except Exception as e:
        LOG.error(f"Erro ao executar: {stack_error(e)}")
        os.system("pause")
        return False
    finally:
        await CLIENT.aclose()

if __name__ == "__main__":
    try:
        init()
        app_id = input("Digite o ID do Game: ").strip()
        asyncio.run(main_flow(app_id))
        input("Pressione Enter para reiniciar o programa...")

        steam_exe = r"C:\Program Files (x86)\Steam\Steam.exe"
        if os.path.exists(steam_exe):
            LOG.info("Abrindo o cliente Steam novamente...")
            os.startfile(steam_exe)
        else:
            LOG.warning("Steam.exe não encontrado no caminho padrão.")

        os.execl(sys.executable, sys.executable, *sys.argv)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    except Exception as e:
        LOG.error(f"Erro: {stack_error(e)}")
        os.system("pause")

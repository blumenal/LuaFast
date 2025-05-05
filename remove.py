import asyncio
import os
import re
import httpx
from pathlib import Path
from typing import List

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def mostrar_cabecalho():
    limpar_tela()
    print("╔" + "═" * 56 + "╗")
    print("║" + "🎮 REMOVER GAMES DA CONTA STEAM 🎮".center(54) + "║")
    print("╚" + "═" * 56 + "╝")

def remover_todos_arquivos():
    """Remove TODOS os arquivos das duas pastas (sem verificação de IDs)"""
    stplug_path = Path("C:/Program Files (x86)/Steam/config/stplug-in")
    depotcache_path = Path("C:/Program Files (x86)/Steam/depotcache")
    
    # Remove todos os .lua
    lua_removidos = 0
    if stplug_path.exists():
        for arquivo in stplug_path.glob("*.lua"):
            try:
                arquivo.unlink()
                lua_removidos += 1
            except Exception:
                pass
    
    # Remove todos os .manifest
    manifest_removidos = 0
    if depotcache_path.exists():
        for arquivo in depotcache_path.glob("*.manifest"):
            try:
                arquivo.unlink()
                manifest_removidos += 1
            except Exception:
                pass
    
    return lua_removidos, manifest_removidos

def extrair_appids_do_lua(lua_path: Path) -> List[str]:
    """Extrai IDs para remoção específica"""
    try:
        with open(lua_path, "r", encoding="utf-8", errors="replace") as f:
            conteudo = f.read()
        return list(set(re.findall(r'addappid\(\s*(\d+)\s*,', conteudo)))
    except Exception:
        return []

def remover_manifests_por_ids(ids_manifest: List[str]):
    """Remove apenas manifests com IDs específicos"""
    depotcache_path = Path("C:/Program Files (x86)/Steam/depotcache")
    if not depotcache_path.exists():
        return
    
    for app_id in ids_manifest:
        for manifest in depotcache_path.glob(f"{app_id}_*.manifest"):
            try:
                manifest.unlink()
            except Exception:
                pass

async def fetch_game_name(app_id: str) -> str:
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
            if data.get(app_id, {}).get("success"):
                return data[app_id]["data"]["name"]
            return "Nome não encontrado"
    except Exception:
        return "Erro ao buscar nome"

async def remove_game():
    stplug_path = Path("C:/Program Files (x86)/Steam/config/stplug-in")
    if not stplug_path.exists():
        print("Pasta stplug-in não encontrada.")
        input("Pressione Enter para continuar...")
        return

    while True:
        arquivos = list(stplug_path.glob("*.lua"))
        mostrar_cabecalho()

        if not arquivos:
            print("\nNenhum Game/App foi localizado.\n")
            input("Pressione Enter para continuar...")
            return

        print("Jogos encontrados:\n")
        id_map = {}
        for idx, arq in enumerate(arquivos, 1):
            app_id = arq.stem
            nome = await fetch_game_name(app_id)
            id_map[str(idx)] = arq
            print(f"{idx}. {app_id} - {nome}")
        print("\n00. Remover TODOS os jogos (limpeza completa)")
        print("0. Voltar / Sair")

        escolha = input("\nDigite o número do jogo que deseja remover: ").strip()

        if escolha == "0":
            return

        elif escolha == "00":
            confirm = input("Tem certeza que deseja remover TODOS os jogos e arquivos relacionados? (s/n): ").strip().lower()
            if confirm == "s":
                lua, manifest = remover_todos_arquivos()
                print(f"\nRemovidos: {lua} arquivos .lua e {manifest} arquivos .manifest")
                input("Pressione Enter para continuar...")
            continue

        elif escolha in id_map:
            arq = id_map[escolha]            
            ids_manifest = extrair_appids_do_lua(arq)
            
            if ids_manifest:
                remover_manifests_por_ids(ids_manifest)
            
            try:
                arq.unlink()
                print("\nJogo e arquivos relacionados removidos com sucesso.")
            except Exception:
                print("\nO jogo foi removido, mas alguns arquivos podem ter permanecido.")
            
            input("Pressione Enter para continuar...")

async def main():
    await remove_game()

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import os
from pathlib import Path
import aiohttp
from colorama import init, Fore, Style

init(autoreset=True)

STPLUG_PATH = Path("C:/Program Files (x86)/Steam/config/stplug-in")
DEPOTCACHE_PATH = Path("C:/Program Files (x86)/Steam/depotcache")

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def remover_manifests_por_id(app_id: str):
    for arquivo in DEPOTCACHE_PATH.glob(f"{app_id}_*.manifest"):
        try:
            arquivo.unlink()
        except Exception as e:
            print(Fore.RED + f"❌ Erro ao remover manifest {arquivo.name}: {e}")

async def fetch_game_name(app_id: str) -> str:
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data[app_id]['data']['name'] if data[app_id]['success'] else "Desconhecido"
    except:
        return "Desconhecido"

async def exibir_menu(arquivos):
    limpar_tela()
    print(Fore.LIGHTCYAN_EX + "↘" + "═" * 55 + "↙")
    print(Fore.LIGHTYELLOW_EX + "||" + Fore.WHITE + "        🧹 REMOVER GAMES DA CONTA STEAM        ".center(53) + Fore.LIGHTYELLOW_EX + "||")
    print(Fore.LIGHTCYAN_EX + "↗" + "═" * 55 + "↖")

    if not arquivos:
        print(Fore.LIGHTRED_EX + "❗ Nenhum Game/App foi localizado.\n")
        input("Pressione Enter para voltar...")
        return None

    print(Fore.LIGHTCYAN_EX + "                     🎮 Jogos encontrados:\n")
    print(Fore.LIGHTCYAN_EX + "Para remover mais de um Game de uma unica vez, digite os numeros com espços. Exemplo:1 5 8 \n\n")
    id_map = {}

    cores = [Fore.WHITE, Fore.LIGHTYELLOW_EX]  # Apenas branco e amarelo claro

    for idx, arq in enumerate(arquivos, 1):
        app_id = arq.stem
        nome = await fetch_game_name(app_id)
        cor = cores[(idx - 1) % len(cores)]
        id_map[str(idx)] = arq
        print(f"{cor}[{idx}] {app_id} - {nome}")

    sair_opcao = "0"
    print(Fore.LIGHTRED_EX + f"\n[00] Remover TODOS os jogos")
    print(Fore.LIGHTCYAN_EX + f"[0]  Voltar ao menu\n")
    return id_map, sair_opcao


async def remover_jogo_individual(id_map, escolha):
    app_id = id_map[escolha].stem
    print(Fore.YELLOW + f"\n🗑️ Removendo {app_id}...")
    id_map[escolha].unlink()
    remover_manifests_por_id(app_id)
    print(Fore.GREEN + "✅ Jogo removido com sucesso!\n")
    input("Pressione Enter para continuar...")

async def remover_todos(arquivos):
    confirm = input(Fore.YELLOW + "\n⚠️ Tem certeza que deseja remover TODOS os jogos? (s/n): ").strip().lower()
    if confirm == "s":
        print(Fore.YELLOW + "\n🗑️ Removendo todos os jogos...\n")
        for arq in arquivos:
            app_id = arq.stem
            arq.unlink()
            remover_manifests_por_id(app_id)
        print(Fore.GREEN + "✅ Todos os jogos foram removidos com sucesso!\n")
        input("Pressione Enter para continuar...")

async def main():
    if not STPLUG_PATH.exists():
        print(Fore.RED + "❌ Pasta stplug-in não encontrada.")
        return

    while True:
        arquivos = list(STPLUG_PATH.glob("*.lua"))
        resultado = await exibir_menu(arquivos)
        if resultado is None:
            return

        id_map, sair_opcao = resultado
        escolha = input(Fore.LIGHTCYAN_EX + "👉 Digite os números dos jogos que deseja remover (ex: 1 3): ").strip()

        if escolha == "0":
            break
        elif escolha == "00":
            await remover_todos(arquivos)
            return
        else:
            selecoes = escolha.split()
            jogos_validos = [s for s in selecoes if s in id_map]
            if not jogos_validos:
                print(Fore.LIGHTRED_EX + "\n❌ Nenhum número válido foi selecionado.")
                input(Fore.LIGHTCYAN_EX + "Pressione Enter para tentar novamente...")
                continue

            for s in jogos_validos:
                await remover_jogo_individual(id_map, s)
  

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
import csv
from datetime import datetime
from pathlib import Path

import aiohttp
import gspread
from google.oauth2 import service_account

# Caminhos
STPLUG_PATH = Path("C:/Program Files (x86)/Steam/config/stplug-in")
LOG_LOCAL = Path("envios_locais.csv")

# Cores
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
RESET = "\033[0m"
AZUL = "\033[94m"

# Credenciais embutidas
SERVICE_ACCOUNT_INFO = {
    "type": " ",
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

# ID da planilha
SPREADSHEET_ID = ' '

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

async def fetch_game_name(app_id: str) -> str:
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data[app_id]['data']['name'] if data[app_id]['success'] else "Desconhecido"
    except:
        return "Desconhecido"

def conectar_planilha():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def salvar_log_local(app_id, nome_jogo, status):
    try:
        novo = not LOG_LOCAL.exists()
        with open(LOG_LOCAL, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if novo:
                writer.writerow(["DataHora", "ID", "Nome", "Status"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app_id, nome_jogo, status])
        print(f"{VERDE}Registro local salvo!{RESET}")
    except Exception as e:
        print(f"{VERMELHO}Erro ao salvar log local: {e}{RESET}")
async def avaliar_jogo():
    limpar_tela()
    print("=" * 60)
    print(f"{VERDE}[ AVALIAR JOGOS ]{RESET}".center(60))
    print("=" * 60)
    print("\nEscolha como deseja avaliar:")
    print("1. Avaliar Jogos Instalados")
    print("2. Avaliar Jogo pelo ID")
    print("0. Voltar ao menu principal")
    escolha = input("\nDigite a opção desejada: ").strip()

    if escolha == "1":
        await avaliar_varios_jogos()
    elif escolha == "2":
        await avaliar_jogo_pelo_id()
    elif escolha == "0":
        return
    else:
        print(f"{VERMELHO}Opção inválida!{RESET}")
        input("\nPressione Enter para voltar...")

async def avaliar_varios_jogos():
    try:
        sheet = conectar_planilha()
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar na planilha:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return

    arquivos = list(STPLUG_PATH.glob("*.lua"))
    if not arquivos:
        print(f"{VERMELHO}Nenhum jogo encontrado.{RESET}")
        input("\nPressione Enter para sair...")
        return

    while True:
        limpar_tela()
        print("\nJogos encontrados:\n")
        id_map = {}
        for idx, arq in enumerate(arquivos, 1):
            app_id = arq.stem
            nome = await fetch_game_name(app_id)
            id_map[str(idx)] = (app_id, nome)
            print(f"{idx}. {app_id} - {nome}")

        escolha = input("\nDigite o número do jogo que deseja avaliar (ou 0 para voltar): ").strip()

        if escolha == "0":
            break

        if escolha not in id_map:
            print(f"{AMARELO}Número inválido.{RESET}")
            input("\nPressione Enter para tentar novamente...")
            continue

        app_id, nome_jogo = id_map[escolha]

        status_novo = escolher_status()
        if not status_novo:
            print(f"{VERMELHO}Nenhum status selecionado. Cancelando operação.{RESET}")
            input("\nPressione Enter para voltar...")
            return

        await enviar_para_google(sheet, app_id, nome_jogo, status_novo)

        continuar = input("\nDeseja avaliar outro jogo instalado? (S/N): ").strip().lower()
        if continuar != "s":
            break

        
async def avaliar_jogo_pelo_id():
    try:
        sheet = conectar_planilha()
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar na planilha:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return

    while True:
        limpar_tela()
        app_id = input("Digite o ID do jogo (ou 0 para voltar): ").strip()
        if app_id == "0":
            break

        nome_jogo = await fetch_game_name(app_id)

        print(f"\nID: {app_id}")
        print(f"Nome: {nome_jogo}")
        confirmar = input("\nÉ este jogo? (S/N): ").strip().lower()

        if confirmar == "s":
            status_novo = escolher_status()
            if not status_novo:
                print(f"{VERMELHO}Nenhum status selecionado. Cancelando operação.{RESET}")
                input("\nPressione Enter para voltar...")
                return

            await enviar_para_google(sheet, app_id, nome_jogo, status_novo)

            continuar = input("\nDeseja avaliar outro jogo por ID? (S/N): ").strip().lower()
            if continuar != "s":
                break
        else:
            print(f"{AMARELO}Vamos tentar novamente.{RESET}")
            input("\nPressione Enter para digitar outro ID...")

            
async def enviar_para_google(sheet, app_id, nome_jogo, status_novo):
    try:
        registros = sheet.get_all_records()
        linha_existente = None
        status_antigo = None
        for idx, registro in enumerate(registros, start=2):
            if str(registro.get('ID')) == app_id:
                linha_existente = idx
                status_antigo = registro.get('Status')
                break

        if linha_existente:
            if status_antigo == "Não Funciona" and status_novo == "Funciona":
                sheet.update(f"C{linha_existente}", [[status_novo]])
                print(f"{VERDE}Atualizado para FUNCIONA!{RESET}")
            elif status_antigo != "Funciona":
                sheet.update(f"C{linha_existente}", [[status_novo]])
                print(f"{AMARELO}Status atualizado para {status_novo}.{RESET}")
            else:
                print(f"{VERDE}Já está como FUNCIONA. Nenhuma alteração feita.{RESET}")
        else:
            sheet.append_row([app_id, nome_jogo, status_novo])
            print(f"{VERDE}Novo status enviado para a planilha!{RESET}")

        salvar_log_local(app_id, nome_jogo, status_novo)
        input("\nPressione Enter para continuar...")

    except Exception as e:
        print(f"{VERMELHO}Erro ao enviar para a planilha:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para continuar...")
def escolher_status():
    print("\nEscolha a situação:")
    print(f"1.{VERDE} Funciona{RESET}")
    print(f"2.{AMARELO} Funciona Parcialmente{RESET}")
    print(f"3.{VERMELHO} Não Funciona{RESET}")
    status_escolha = input("\nDigite o número correspondente: ").strip()

    status_map = {
        "1": "Funciona",
        "2": "Funciona Parcialmente",
        "3": "Não Funciona"
    }

    return status_map.get(status_escolha)

def visualizar_lista_compatibilidade():
    try:
        sheet = conectar_planilha()
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar na planilha:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return

    while True:
        limpar_tela()
        print("=" * 60)
        print(f"{VERDE}[ LISTA DE COMPATIBILIDADE DE JOGOS ]{RESET}".center(60))
        print("=" * 60)
        print("\nAqui você pode visualizar a lista de compatibilidade para saber quais jogos funcionam!\n")

        try:
            registros = sheet.get_all_records()
            if not registros:
                print(f"{AMARELO}Planilha vazia.{RESET}")
                input("\nPressione Enter para voltar...")
                return

            termo_pesquisa = input("Digite o " + AZUL + "ID" + RESET + ", parte do " + AZUL + "NOME " + RESET + "do jogo, ou apenas pressione " + AZUL + "[Enter] " + RESET + "para listar tudo. \n\nAguardando: ").strip().lower()

            limpar_tela()
            print("\n+--------------+----------------------------------------------------+------------------------+")
            print("| {:^12} | {:^50} | {:^22} |".format("ID", "Nome", "Status"))
            print("+--------------+----------------------------------------------------+------------------------+")

            encontrou = False

            for registro in registros:
                app_id = str(registro.get('ID', '')).strip()
                nome = str(registro.get('Nome', 'Sem nome')).strip()
                status = str(registro.get('Status', 'Desconhecido')).strip()

                if termo_pesquisa:
                    if termo_pesquisa not in app_id and termo_pesquisa not in nome.lower():
                        continue

                status_text = status.center(22)
                if status == "Funciona":
                    status_cor = VERDE + status_text + RESET
                elif status == "Funciona Parcialmente":
                    status_cor = AMARELO + status_text + RESET
                elif status == "Não Funciona":
                    status_cor = VERMELHO + status_text + RESET
                else:
                    status_cor = status_text

                nome_exibido = nome[:50] if len(nome) > 50 else nome

                print("| {:^12} | {:50} | {} |".format(app_id, nome_exibido, status_cor))
                encontrou = True

            if not encontrou:
                print(f"\n{AMARELO}Nenhum jogo encontrado com essa busca.{RESET}")

            print("+--------------+----------------------------------------------------+------------------------+")

            # Perguntar se quer fazer outra busca
            outra_busca = input("\nDeseja fazer outra busca? (S/N): ").strip().lower()
            if outra_busca != 's':
                break  # sai do loop e volta para o menu principal

        except Exception as e:
            print(f"{VERMELHO}Erro ao visualizar planilha:{RESET}")
            import traceback
            traceback.print_exc()
            input("\nPressione Enter para voltar...")
            break


            
def visualizar_planilha():
    try:
        sheet = conectar_planilha()
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar na planilha:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return

    limpar_tela()
    print(f"\n{VERDE}Visualizando a Planilha:{RESET}\n")

    try:
        registros = sheet.get_all_records()
        if not registros:
            print(f"{AMARELO}Planilha vazia.{RESET}")
            input("\nPressione Enter para voltar...")
            return

        termo_pesquisa = input("Digite uma palavra para filtrar (ou pressione Enter para ver tudo): ").strip().lower()

        # Novo cabeçalho
        print("\n+--------------+----------------------------------------------------+------------------------+")
        print("| {:^12} | {:^50} | {:^22} |".format("ID", "Nome", "Status"))
        print("+--------------+----------------------------------------------------+------------------------+")

        encontrou = False

        for registro in registros:
            app_id = str(registro.get('ID', ''))
            nome = registro.get('Nome', 'Sem nome')
            status = registro.get('Status', 'Desconhecido')

            if termo_pesquisa and termo_pesquisa not in nome.lower():
                continue  # pula se não encontrar o termo

            encontrou = True

            # Cores para Status
            if status == "Funciona":
                status_cor = VERDE + status + RESET
            elif status == "Funciona Parcialmente":
                status_cor = AMARELO + status + RESET
            elif status == "Não Funciona":
                status_cor = VERMELHO + status + RESET
            else:
                status_cor = status

            nome = str(nome)  # transforma em string
            nome_exibido = nome[:50] if len(nome) > 50 else nome


            print("| {:^12} | {:50} | {:^31} |".format(app_id, nome_exibido, status_cor))

        if not encontrou:
            print(f"\n{AMARELO}Nenhum jogo encontrado com esse termo.{RESET}")

        print("+--------------+----------------------------------------------------+------------------------+")

    except Exception as e:
        print(f"{VERMELHO}Erro ao visualizar planilha:{RESET}")
        import traceback
        traceback.print_exc()

    input("\nPressione Enter para voltar...")
    
def buscar_id_na_planilha():
    try:
        sheet = conectar_planilha()
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar na planilha:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return

    limpar_tela()
    print(f"\n{VERDE}Buscar informações de um jogo na planilha:{RESET}\n")
    app_id = input("Digite o ID do jogo (ex: 123456): ").strip()

    try:
        registros = sheet.get_all_records()
        encontrado = False
        for registro in registros:
            if str(registro.get('ID')) == app_id:
                nome = registro.get('Nome') or "Nome não encontrado"
                status = registro.get('Status') or "Status desconhecido"

                if status == "Funciona":
                    cor_status = VERDE + status + RESET
                elif status == "Funciona Parcialmente":
                    cor_status = AMARELO + status + RESET
                elif status == "Não Funciona":
                    cor_status = VERMELHO + status + RESET
                else:
                    cor_status = status

                print(f"\n{VERDE}Jogo encontrado:{RESET}")
                print(f"ID: {registro.get('ID')}")
                print(f"Nome: {nome}")
                print(f"Status: {cor_status}")
                encontrado = True
                break

        if not encontrado:
            print(f"{AMARELO}\nID {app_id} não encontrado na planilha.{RESET}")

    except Exception as e:
        print(f"{VERMELHO}Erro ao buscar informações:{RESET}")
        import traceback
        traceback.print_exc()

    input("\nPressione Enter para voltar...")
    
async def avaliar_jogo_pelo_id():
    try:
        sheet = conectar_planilha()
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar na planilha:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return

    while True:
        limpar_tela()
        app_id = input("Digite o ID do jogo (ou 0 para voltar): ").strip()
        if app_id == "0":
            break

        nome_jogo = await fetch_game_name(app_id)

        print(f"\nID: {app_id}")
        print(f"Nome: {nome_jogo}")
        confirmar = input("\nÉ este jogo? (S/N): ").strip().lower()

        if confirmar == "s":
            status_novo = escolher_status()
            if not status_novo:
                print(f"{VERMELHO}Nenhum status selecionado. Cancelando operação.{RESET}")
                input("\nPressione Enter para voltar...")
                return

            await enviar_para_google(sheet, app_id, nome_jogo, status_novo)
            break
        else:
            print(f"{AMARELO}Vamos tentar novamente.{RESET}")
            input("\nPressione Enter para digitar outro ID...")


async def menu_principal():
    while True:
        limpar_tela()
        print("╔" + "═" * 56 + "╗")
        print("║" + "COMPATIBILIDADE DE JOGOS - STEAM".center(56) + "║")
        print("╚" + "═" * 56 + "╝" + f"{RESET}")
        print("\n1. Visualizar lista de compatibilidade")
        print("\n2. Avaliar Jogos")
        print("\n3. Sair")
        escolha = input("\nEscolha uma opção: ").strip()

        if escolha == "1":
            visualizar_lista_compatibilidade()
        elif escolha == "2":
            await avaliar_jogo()
        elif escolha == "3":
            print(f"{AMARELO}Saindo...{RESET}")
            break
        else:
            print(f"{VERMELHO}Opção inválida.{RESET}")
            input("\nPressione Enter para tentar novamente...")

async def main_flow():
    await menu_principal()

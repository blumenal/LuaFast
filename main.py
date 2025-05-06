import asyncio
import os
import time
import platform
import json
import shutil
import sys  # Adicionado para suporte a _MEIPASS do PyInstaller

# Cores ANSI
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
VERMELHO_ESCURO = "\033[31m"
AMARELO_ESCURO = "\033[33m"
RESET = "\033[0m"

CAMINHO_LOG = "log/acordo.json"

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def verificar_acordo():
    if not os.path.exists("log"):
        os.makedirs("log")

    if not os.path.exists(CAMINHO_LOG):
        return None  # Arquivo não existe, precisa exibir tela de termos

    try:
        with open(CAMINHO_LOG, "r") as f:
            dados = json.load(f)
            return dados.get("acordo_aceito")
    except:
        return None  # Erro na leitura, exibe tela de termos novamente

# No seu main.py, modifique a função salvar_acordo:
def salvar_acordo(aceito: bool):
    with open(CAMINHO_LOG, "w") as f:
        json.dump({"acordo_aceito": aceito}, f)

def tela_inicial():
    limpar_tela()
    if os.name == "nt":
        os.system("mode con: cols=120 lines=50")
    print(VERDE + "\t           Bem-vindo ao Gerenciador de Games LuaFast STEAM!" + RESET)
    print(AMARELO_ESCURO + "\n                          Termos de Licença e Utilização" + RESET)
    print(f"\nEste projeto é distribuído sob a {AZUL}licença GPL-3.0{RESET}. As diretrizes a seguir são complementares à licença GPL-3.0; em caso de conflito, prevalecem sobre a mesma.")
    print(f"\nDurante o uso deste programa, podem ser gerados dados protegidos por direitos autorais. O usuário deverá excluir quaisquer dados protegidos no prazo máximo de 24 horas.")
    print(f"\nEste projeto é completamente {AZUL}gratuito e disponibilizado de forma aberta no GitHub{RESET}, com o propósito de promover o aprendizado.")
    print(f"\nO projeto não garante conformidade com legislações locais. O usuário assume responsabilidade por qualquer ato ilícito.")
    print("\nÉ proibido utilizar este projeto para fins comerciais.")
    print("Modificações no projeto só serão permitidas mediante a publicação conjunta do código-fonte correspondente.")
    print(f"{AMARELO}Ao utilizar este programa, você declara estar de acordo com todos os termos acima.{RESET}")

    while True:
        resposta = input(f"\n{VERMELHO}Você concorda com os termos de uso descritos acima? (s/n): {RESET}").strip().lower()
        if resposta == "s":
            salvar_acordo(True)
            return True
        elif resposta == "n":
            salvar_acordo(False)
            print(VERMELHO + "\nVocê não confirmou a leitura das instruções." + RESET)
            print(VERMELHO + "O programa será fechado em 4 segundos..." + RESET)
            time.sleep(4)
            exit(0)
        else:
            print(VERMELHO + "Opção inválida! Digite apenas 's' ou 'n'." + RESET)

def exibir_banner():
    limpar_tela()
    if not platform.system() == "Windows":
        print("Este script só pode ser executado no Windows.")
        exit(1)
    banner = r"""
 _        _   _     ___          _____    _____     ___    _____   
| |      | | | |   / _ \        |  ___|  | ____|   / __|  |_   _|  
| |      | | | |  / /_\ \       | |_     |  _|     \__ \    | |    
| |___   | | | |  |  _  |       |  _|    | |___    __/ /    | |    
|_____|   \___/   | | | |       | |      |_____|  |___/     |_|    
                  \_| |_/       |_|                                 
    """
    print(VERDE + banner + RESET)
    print(f"{VERDE} Ver: 3.7.3 |Desenvolvedores: blumenal86 | Colaborador: Jeffersonsud{RESET}")
    print("\n Use o site " + AZUL + "https://steamdb.info/" + RESET + " para obter o ID do game desejado.\n")

def exibir_menu():
    print("     ╔═════════════════════════════════════════════╗")
    print("     ║         🎮 GERENCIADOR DE JOGOS 🎮          ║")
    print("     ╠═════════════════════════════════════════════╣")
    print("     ║ [1] VERIFICAR COMPATIBILIDADE / DRM         ║")
    print("     ║ [2] ADICIONAR GAMES STEAM                   ║")
    print("     ║ [3] REMOVER GAMES STEAM                     ║")
    print("     ╠═════════════════════════════════════════════╣")
    print("     ║ [4] BACKUP & RESTAURAÇÃO                    ║")
    print("     ╠═════════════════════════════════════════════╣")
    print("     ║ [5] FINALIZAR STEAM / REINICIAR             ║")
    print("     ║ [6] TABELA DE TESTES E VALIDAÇÃO            ║")
    print("     ╠═════════════════════════════════════════════╣")
    print("     ║ [0] ❌ SAIR                                 ║")
    print("     ╚═════════════════════════════════════════════╝")

def menu():
    while True:
        exibir_banner()
        exibir_menu()
        escolha = input("\n        Digite o número da opção desejada: ").strip()
        print(" ")

        if escolha == "1":
            try:
                import drm
                drm.main()
            except Exception as e:
                print(f"Erro: {e}")
                input("Pressione Enter para continuar...")
        elif escolha == "2":
            try:
                import install
                asyncio.run(install.main_flow())
            except Exception as e:
                print(f"Erro: {e}")
                input("Pressione Enter para continuar...")
        elif escolha == "3":
            try:
                import remove
                asyncio.run(remove.main())
            except Exception as e:
                print(f"Erro: {e}")
                input("Pressione Enter para continuar...")
        elif escolha == "4":
            try:
                import backup
                asyncio.run(backup.menu_principal())
            except Exception as e:
                print(f"Erro: {e}")
                input("Pressione Enter para continuar...")
        elif escolha == "5":
            try:
                import fecharsteam
                fecharsteam.encerrar_steam_processos()
            except Exception as e:
                print(f"Erro: {e}")
                input("Pressione Enter para continuar...")
        elif escolha == "6":
            try:
                import compat
                asyncio.run(compat.main_flow())
            except Exception as e:
                print(f"Erro: {e}")
                input("Pressione Enter para continuar...")
        elif escolha == "0":
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida.")
            input("Pressione Enter para continuar...")

if __name__ == "__main__":
    acordo = verificar_acordo()
    if acordo is None or acordo is False:
        tela_inicial()
    menu()

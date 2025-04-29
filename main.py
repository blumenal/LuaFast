import asyncio
import os
import time
import platform

# Cores ANSI
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
VERMELHO_ESCURO = "\033[31m"
AMARELO_ESCURO = "\033[33m"
RESET = "\033[0m"

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def tela_inicial():
    limpar_tela()
    if os.name == "nt":
        os.system("mode con: cols=120 lines=50")
    arte = r"""
 _        _   _     ___          _____     ___      ___    _____   
| |      | | | |   / _ \        |  ___|   / _ \    / __|  |_   _|  
| |      | | | |  / /_\ \       | |_     / /_\ \   \__ \    | |    
| |___   | | | |  |  _  |       |  _|    |  _  |   __/ /    | |    
|_____|   \___/   |_| |_|       |_|      |_| |_|  |___/     |_|    
    """
    print(VERDE + arte.center(80) + RESET)
    print(VERDE + "\tBem-vindo ao Gerenciador de Games LuaFast STEAM!" + RESET)
    print(AMARELO_ESCURO + "\nEste programa permite adicionar e remover jogos a sua conta STEAM, \nalém de fazer backup e restauração dos arquivos de licença." + RESET)
    print("\nMas antes de usar, leia atentamente as " + VERMELHO_ESCURO + "OBSERVAÇÕES" + RESET + " descritas a seguir.")
    print("__________________________________________________________________________________")
    print(VERDE + "\nQUAIS JOGOS FUNCIONAM COM ESSE MÉTODO?" + RESET)
    print("\nTodos os jogos que têm apenas a proteção antipirataria " + AZUL + "STEAM DRM" + RESET)
    print()
    print("Para saber se o jogo tem " + AZUL + "STEAM DRM" + RESET + ", verifique a página do jogo.")
    print("Exemplos: " + VERDE + "FINAL FANTASY VII, THE LAST OF US, SPIDER MAN..." + RESET)
    print("----------------------------------------------------------------------------------")
    print(VERMELHO + "\nQUAIS JOGOS NÃO FUNCIONAM?" + RESET)
    print("- DRM de TERCEIROS")
    print("- EA/Xbox/Ubisoft/Activision Accounts")
    print("- Denuvo Anti-tamper")
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
    print(banner)
    print(VERMELHO + " Venda proibida, esse programa é totalmente grátis." + RESET)
    print(" Use o site " + AZUL + "https://steamdb.info/" + RESET + " para obter o ID do game.")

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
    print("     ║ [5] FINALIZAR STEAM                         ║")
    print("     ║ [6] TABELA DE TESTES E VALIDAÇÃO            ║")
    print("     ╠═════════════════════════════════════════════╣")
    print("     ║ [0] ❌ SAIR                                 ║")
    print("     ╚═════════════════════════════════════════════╝")
    print(f"     {VERDE}   Versão: 3.0.5 |{RESET}")
    print(f"     {VERDE}   Desenvolvedores: blumenal86 & Jeffersonsud{RESET}")


def menu():
    while True:
        exibir_banner()
        exibir_menu()
        escolha = input("\n        Digite o número da opção desejada: ").strip()
        print(" ")

        if escolha == "1":
            try:
                import drm
                asyncio.run(drm.main())
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
                import finalizar
                finalizar.main()
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
    tela_inicial()
    menu()

import os
import time

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

def main():
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

if __name__ == "__main__":
    main()
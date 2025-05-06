import subprocess
import time
import os

PROCESSOS_STEAM = [
    "Steam.exe",               # Fecha primeiro
    "steamwebhelper.exe",
    "GameOverlayUI.exe",
    "SteamService.exe",
    "steamerrorreporter.exe",
    "steamstart.exe",
    "steamguard.exe"
]

def encerrar_steam_processos():
    print("[*] Iniciando encerramento dos processos da Steam...\n")

    for nome_proc in PROCESSOS_STEAM:
        try:
            print(f"[-] Encerrando {nome_proc} ...")
            subprocess.run(["taskkill", "/F", "/IM", nome_proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Erro ao encerrar {nome_proc}: {e}")

    time.sleep(2)

    print("\n[*] Verificando se ainda há processos ativos...")
    try:
        # Corrigido para sistemas com idioma português no Windows
        output = subprocess.check_output("tasklist", shell=True, encoding="mbcs")
        output = output.lower()
        processos_ativos = [p for p in PROCESSOS_STEAM if p.lower() in output]

        if processos_ativos:
            print("[!] Ainda existem processos ativos:")
            for p in processos_ativos:
                print(f"   - {p}")
        else:
            print("[✓] Todos os processos da Steam foram encerrados com sucesso.")

    except Exception as e:
        print(f"[!] Erro ao verificar processos ativos: {e}")

    # Esta parte SEMPRE vai executar
    print("\n[?] Deseja abrir a Steam novamente? (s/n): ", end="")
    try:
        resp = input().strip().lower()
        if resp == 's':
            caminho_steam = os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Steam", "Steam.exe")
            if os.path.exists(caminho_steam):
                print("[*] Iniciando Steam...")
                subprocess.Popen([caminho_steam], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print("[!] Caminho da Steam não encontrado.")
        else:
            print("[✓] Steam não será reiniciada. Encerrando o programa.")
    except Exception as e:
        print(f"[!] Erro ao ler resposta: {e}")

if __name__ == "__main__":
    encerrar_steam_processos()

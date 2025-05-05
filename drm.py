import requests
from bs4 import BeautifulSoup
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def exibir_cabecalho():
    AZUL = "\033[94m"
    BRANCO = "\033[97m"
    RESET = "\033[0m"
    AMARELO = "\033[93m"

    print(f"{AZUL}      \n        ╔════════════════════════════════════════════════════════════╗")
    print(f"        ║        {BRANCO}     🔍 VERIFICADOR DE DRM STEAM LUAFAST         {AZUL}   ║")
    print(f"        ╚════════════════════════════════════════════════════════════╝{RESET}\n")
    print(f"{AZUL}      \n        ╔════════════════════════════════════════════════════════════╗")
    print(f"        ║{BRANCO}                                                            {AZUL}║")
    print(f"        ║{BRANCO} 🔎  Utilize AppIDs da Steam para verificar proteções DRM.  {AZUL}║")
    print(f"        ║{BRANCO}                                                            {AZUL}║")
    print(f"        ║{BRANCO} 🌐  Fontes utilizadas: Steam Store, SteamDB, PCGamingWiki. {AZUL}║")
    print(f"        ║{BRANCO}                                                            {AZUL}║")
    print(f"        ╚════════════════════════════════════════════════════════════╝{RESET}\n")
    
    print(f"\n🔎 Você pode pesquisar um ID por vez ou mais de um usando espaço entre eles. Exemplo: 1971870 2623190 ")
    print(f"\nℹ️ Para voltar a pagina anterior, deixe o campo ID vazio e precione ""[ENTER]""")

def buscar_drm_pcgw(nome_jogo):
    try:
        nome_url = nome_jogo.replace(" ", "_")
        url = f"https://www.pcgamingwiki.com/wiki/{nome_url}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        drm_section = soup.find("th", string="DRM")
        if drm_section:
            drm_value = drm_section.find_next_sibling("td")
            if drm_value:
                return drm_value.text.strip()
    except Exception as e:
        print(f"Erro ao buscar DRM na PCGamingWiki: {e}")
    return None

def buscar_drm_steamdb(appid):
    try:
        url = f"https://steamdb.info/app/{appid}/"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        drm_info = []

        text = soup.get_text().lower()
        if "denuvo" in text:
            drm_info.append("Denuvo")
        if "steamworks" in text or "requires steam" in text:
            drm_info.append("Steamworks")
        if "3rd-party" in text or "third-party drm" in text:
            drm_info.append("Third-party DRM")

        return ", ".join(set(drm_info)) if drm_info else None
    except Exception as e:
        print(f"Erro ao buscar DRM no SteamDB: {e}")
    return None

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

        return ", ".join(sorted(drm_total)) if drm_total else None

    except Exception as e:
        print(f"Erro ao buscar DRM na loja Steam: {e}")
        return None

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

    drm_info = ", ".join(drm) if drm else "Não especificado"

    if drm_info == "Não especificado":
        drm_info = buscar_drm_steam_store(appid) or drm_info
    if drm_info == "Não especificado":
        drm_info = buscar_drm_pcgw(name) or drm_info
    if drm_info == "Não especificado":
        drm_info = buscar_drm_steamdb(appid) or drm_info

    return {"appid": appid, "name": name, "drm": drm_info}

def main():
    while True:
        limpar_tela()
        exibir_cabecalho()

        while True:
            appids_input = input("\n\nDigite o(s) AppID(s) se deixar em : ").strip()
            if appids_input == "":
                while True:
                    sair = input("\n❓ Nenhum AppID digitado. Deseja sair? (s/n): ").lower()
                    if sair == "s":
                        print("\n👋 Obrigado por usar o verificador de DRM!\n")
                        return
                    elif sair == "n":
                        break
                    else:
                        print("\n⚠️ Por favor, digite apenas 's' para SAIR ou 'n' para permanecer e fazer uma busca.")
                continue
            else:
                break

        appids = [appid for appid in appids_input.split() if appid.isdigit()]
        resultados = []

        for appid in appids:
            info = get_steam_game_info(appid)
            if "error" in info:
                print(f"\n❌ [{appid}] ERRO: {info['error']}")
            else:
                print(f"\n📌 AppID: {appid}")
                print(f"🎮 Nome : \033[1;34m{info['name']}\033[0m")
                print(f"🔐 DRM  : \033[1;33m{info['drm']}\033[0m")

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

            resultados.append(info)

        repetir = input("🔁 Deseja fazer uma nova pesquisa? (s/n): ").lower()
        if repetir != "s":
            break

    print("\n👋 Obrigado por usar o verificador de DRM!\n")

if __name__ == "__main__":
    main()

#include "dllmain.h"
#include "HookManager.h"


// Load diversion.dll and prepare key runtime paths.
bool LoadDiversion()
{
	if (!GetCurrentDirectoryA(MAX_PATH, SteamInstallPath)) {
		return false;
	}
    sprintf_s(SteamclientPath, MAX_PATH, "%s\\steamclient64.dll", SteamInstallPath);
    sprintf_s(DiversionPath, MAX_PATH, "%s\\bin\\diversion.dll", SteamInstallPath);
    sprintf_s(LuaDir, MAX_PATH, "%s\\config\\lua", SteamInstallPath);
    // copy steamclient64.dll to diversion.dll
    CopyFileA(SteamclientPath, DiversionPath, FALSE);
	diversion_hMdoule = LoadLibraryA(DiversionPath);
	return diversion_hMdoule != nullptr;

}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD dwReason, PVOID pvReserved)
{
	if (dwReason == DLL_PROCESS_ATTACH)
	{
		DisableThreadLibraryCalls(hModule);
        if (LoadDiversion()) {
            LuaConfig::ParseDirectory(std::string(LuaDir));
            SteamUI::CoreHook();
            SteamClient::PatchBinary();
            SteamClient::CoreHook();
        }
    }
    else if (dwReason == DLL_PROCESS_DETACH)
    {
        SteamUI::CoreUnhook();
        SteamClient::CoreUnhook();
    }

    return true;
}

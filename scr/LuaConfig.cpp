#include "dllmain.h" 
#include "LuaConfig.h"
#include <lua.hpp>

extern "C" {
    struct lua_State;
}

namespace LuaConfig{
    static lua_State* g_lua_state = nullptr;
    std::unordered_map<AppId_t, std::string> DepotKeySet{};
    std::unordered_map<AppId_t, uint64_t> AccessTokenSet{};
    std::unordered_set<AppId_t> PinnedApps{};
    
    // Estrutura para armazenar informações de manifestos
    struct ManifestInfo {
        std::string manifestId;    // como string "3545882420322545098"
        uint64_t requestCode;      // código de requisição
    };
    static std::unordered_map<AppId_t, ManifestInfo> ManifestMap{};

    static int lua_addappid(lua_State* L) {
        // addappid(integer, integer, string)
        int argc = lua_gettop(L);
        // Validate argument count and required argument types.
        if (argc == 0) {
            return luaL_error(L, "addappid: missing arguments");
        }
        if (!lua_isinteger(L, 1)) {
            return luaL_error(L, "addappid: first argument must be integer");
        }

        // Read the first argument as app/depot id.
        lua_Integer value = lua_tointeger(L, 1);
        // Ensure the value fits into uint32_t range.
        if (value < 0 || value > UINT32_MAX)
            return luaL_error(L, "addappid: value out of range");
        AppId_t DepotId = (uint32_t)value;
        // Read the optional third argument as a key.
        std::string Key = "";
        if (argc > 2) {
            if (!lua_isstring(L, 3))
                return luaL_error(L, "addappid: third argument must be string");
            const char* key = lua_tostring(L, 3);
            // Keep only keys with exactly 64 characters.
            if (strlen(key) == 64) {
                Key = std::string(key);
            }
        }
        // Non-empty keys have priority over existing empty keys.
        if (!Key.empty() || !DepotKeySet.count(DepotId)) {
            DepotKeySet[DepotId] = Key;
        }

        return 0;
    }

    static int lua_addtoken(lua_State* L) {
        // addtoken(integer, string(uint64_t))
        int argc = lua_gettop(L);
        // Validate argument count and required argument types.
        if (argc == 0) {
            return luaL_error(L, "addtoken: missing arguments");
        }
        if (!lua_isinteger(L, 1)) {
            return luaL_error(L, "addtoken: first argument must be integer");
        }

        // Read the first argument as app/depot id.
        lua_Integer value = lua_tointeger(L, 1);
        // Ensure the value fits into uint32_t range.
        if (value < 0 || value > UINT32_MAX)
            return luaL_error(L, "addtoken: value out of range");
        AppId_t AppId = (uint32_t)value;
        // Read the second argument as a token.
        if (argc > 1) {
            if (!lua_isstring(L, 2))
                return luaL_error(L, "addtoken: second argument must be string");
            const char* token = lua_tostring(L, 2);
            // Convert the string token to a uint64_t value.
            if(!std::all_of(token, token + strlen(token), ::isdigit)) {
                return luaL_error(L, "addtoken: token must contain only digits");
            }
            AccessTokenSet[AppId] = std::stoull(token);
        }

        return 0;
    }

    static int lua_pinApp(lua_State* L) {
        // pinApp(integer)
        int argc = lua_gettop(L);
        // Validate argument count and required argument types.
        if (argc == 0) {
            return luaL_error(L, "pinApp: missing arguments");
        }
        if (!lua_isinteger(L, 1)) {
            return luaL_error(L, "pinApp: first argument must be integer");
        }

        // Read the first argument as appid.
        lua_Integer value = lua_tointeger(L, 1);
        // Ensure the value fits into uint32_t range.
        if (value < 0 || value > UINT32_MAX)
            return luaL_error(L, "pinApp: value out of range");
        AppId_t AppId = (uint32_t)value;
        
        PinnedApps.insert(AppId);

        return 0;
    }

    static int lua_setManifestid(lua_State* L) {
        // setManifestid(depotid, manifestId, requestCode)
        int argc = lua_gettop(L);
        
        if (argc < 3) {
            return luaL_error(L, "setManifestid requires 3 arguments: depotId, manifestId, requestCode");
        }
        if (!lua_isinteger(L, 1)) {
            return luaL_error(L, "setManifestid: first argument must be depotId (integer)");
        }
        if (!lua_isstring(L, 2)) {
            return luaL_error(L, "setManifestid: second argument must be manifestId (string)");
        }
        if (!lua_isinteger(L, 3)) {
            return luaL_error(L, "setManifestid: third argument must be requestCode (integer)");
        }
        
        AppId_t depotId = (AppId_t)lua_tointeger(L, 1);
        const char* manifestId = lua_tostring(L, 2);
        uint64_t requestCode = (uint64_t)lua_tointeger(L, 3);
        
        ManifestMap[depotId] = { std::string(manifestId), requestCode };
        
        return 0;
    }

    static bool Initialize() {
        if (g_lua_state)
            return true; 
        g_lua_state = luaL_newstate();
        if (!g_lua_state)
            return false;
        // Load standard Lua libraries.
        luaL_openlibs(g_lua_state);
        // Register custom helper functions for scripts.
        lua_register(g_lua_state, "addappid", lua_addappid);
        lua_register(g_lua_state, "addtoken", lua_addtoken);
        lua_register(g_lua_state, "pinApp", lua_pinApp);
        lua_register(g_lua_state, "setManifestid", lua_setManifestid);
        return true;
    }
    
    static void Cleanup() {
        if (g_lua_state) {
            lua_close(g_lua_state);
            g_lua_state = nullptr;
        }
    }

    bool HasDepot(AppId_t DepotId) {
        return DepotKeySet.count(DepotId);
    }

    std::vector<AppId_t> GetAllDepotIds() {
        std::vector<AppId_t> DepotIds;
        for (const auto& pair : DepotKeySet) {
            DepotIds.push_back(pair.first);
        }
        return DepotIds;
    }

    std::vector<uint8> GetDecryptionKey(AppId_t DepotId) {
        std::vector<uint8> keyBytes;
        if (DepotKeySet.count(DepotId)) {
            const std::string& keyStr = DepotKeySet[DepotId];
            // Convert hex string to byte vector.
            for (size_t i = 0; i < keyStr.length(); i += 2) {
                std::string byteString = keyStr.substr(i, 2);
                uint8 byte = (uint8)strtoul(byteString.c_str(), nullptr, 16);
                keyBytes.push_back(byte);
            }
        }
        return keyBytes;
    }

    uint64_t GetAccessToken(AppId_t AppId) {
        if (AccessTokenSet.count(AppId)) {
            return AccessTokenSet[AppId];
        }
        return 0;
    }
    
    bool pinApp(AppId_t AppId) {
        return PinnedApps.count(AppId);
    }

    void SetManifestId(AppId_t depotId, const std::string& manifestId, uint64_t requestCode) {
        ManifestMap[depotId] = { manifestId, requestCode };
    }

    uint64_t GetManifestRequestCode(AppId_t depotId, uint64_t manifestGid) {
        // Primeiro, tenta obter pelo script Lua
        if (ManifestMap.count(depotId)) {
            const auto& info = ManifestMap[depotId];
            
            // Converte manifestGid para string para comparar
            char expectedGidStr[32];
            sprintf_s(expectedGidStr, sizeof(expectedGidStr), "%llu", manifestGid);
            
            if (info.manifestId == expectedGidStr) {
                return info.requestCode;
            }
        }
        
        // Fallback: busca no arquivo .manifest dentro da pasta depotcache
        char manifestPath[MAX_PATH];
        
        // Obtém o diretório da DLL
        HMODULE hModule = GetModuleHandleA("OpenSteamTool.dll");
        if (!hModule) {
            hModule = GetModuleHandleA("dwmapi.dll");
        }
        
        if (hModule) {
            GetModuleFileNameA(hModule, manifestPath, MAX_PATH);
            char* lastSlash = strrchr(manifestPath, '\\');
            if (lastSlash) {
                *(lastSlash + 1) = '\0';
                strcat_s(manifestPath, "depotcache\\");
            }
        } else {
            // Fallback para o diretório atual
            GetCurrentDirectoryA(MAX_PATH, manifestPath);
            strcat_s(manifestPath, "\\depotcache\\");
        }
        
        char filename[256];
        sprintf_s(filename, sizeof(filename), "%u_%llu.manifest", depotId, manifestGid);
        strcat_s(manifestPath, filename);
        
        // Tenta abrir o arquivo
        HANDLE hFile = CreateFileA(manifestPath, GENERIC_READ, FILE_SHARE_READ, 
                                    NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        if (hFile != INVALID_HANDLE_VALUE) {
            // Lê o request code do arquivo (assumindo que está nos primeiros 8 bytes)
            uint64_t requestCode = 0;
            DWORD bytesRead = 0;
            ReadFile(hFile, &requestCode, sizeof(requestCode), &bytesRead, NULL);
            CloseHandle(hFile);
            
            if (bytesRead == sizeof(requestCode)) {
                return requestCode;
            }
        }
        
        return 0; // Não encontrado
    }

    void ParseDirectory(const std::string& directory) {
        if (!Initialize()) {
            return;
        }
        // catch error and create lua folder if its not there
        std::error_code ec;
        if (!std::filesystem::exists(directory, ec)) {
            std::filesystem::create_directories(directory, ec);
        }
        // check it exists and is a directory before iterating
        if (std::filesystem::exists(directory, ec) && std::filesystem::is_directory(directory, ec)) {
            // Iterate all files in the directory and execute .lua scripts.
            for (const auto& entry : std::filesystem::directory_iterator(directory, ec)) {
                if (ec) break;
                if (entry.is_regular_file()) {
                    const auto& path = entry.path();
                    if (path.extension() == ".lua") {
                        // Load and execute each Lua script.
                        if (luaL_dofile(g_lua_state, path.string().c_str()) != LUA_OK) {
                            // Clear Lua error object from the stack and continue.
                            lua_pop(g_lua_state, 1);
                        }
                    }
                }
            }
        }
        Cleanup();
    }
}
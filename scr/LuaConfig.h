#ifndef LUACONFIG_H
#define LUACONFIG_H

#include "dllmain.h"
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace LuaConfig{
    bool HasDepot(AppId_t appId);
    std::vector<AppId_t> GetAllDepotIds();
    std::vector<uint8> GetDecryptionKey(AppId_t appId);
    uint64_t GetAccessToken(AppId_t appId);
    bool pinApp(AppId_t appId); 
    void ParseDirectory(const std::string& directory);
    
    // Novas funções para suporte a manifestos locais
    void SetManifestId(AppId_t depotId, const std::string& manifestId, uint64_t requestCode);
    uint64_t GetManifestRequestCode(AppId_t depotId, uint64_t manifestGid);
}

#endif // LUACONFIG_H
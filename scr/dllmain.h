#ifndef DLLMAIN_H
#define DLLMAIN_H

#include <windows.h>
#include <string>
#include <fstream>
#include <filesystem>
#include <array>
#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <regex>
#include <memory>
#include <format>

#include "steam.h"
#include "LuaConfig.h"


inline HMODULE diversion_hMdoule = nullptr;
inline char SteamInstallPath[MAX_PATH] = {};
inline char SteamclientPath[MAX_PATH] = {};
inline char DiversionPath[MAX_PATH] = {};
inline char LuaDir[MAX_PATH] = {};


#endif // DLLMAIN_H

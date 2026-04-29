#ifndef BYTESEARCH_H
#define BYTESEARCH_H

#include "dllmain.h"

#define SEARCH_TYPE inline constexpr const char*

void* ByteSearch(const HMODULE& module, const char* pattern, const char* mask, int matchIndex = 1);
int __fastcall PatchMemoryBytes(void* pAddress, const void* pNewBytes, SIZE_T nSize);


/* -------------------------------------------------------------------------- */
/*                                   SteamUI                                  */
/* -------------------------------------------------------------------------- */
// 48 89 5C 24 18 48 89 6C 24 20 56 41 54 41 57 48 83 EC 40
SEARCH_TYPE LoadModuleWithPathPattern = "\x48\x89\x5C\x24\x18\x48\x89\x6C\x24\x20\x56\x41\x54\x41\x57\x48\x83\xEC\x40";
SEARCH_TYPE LoadModuleWithPathMask = "xxxxxxxxxxxxxxxxxxx";



/* -------------------------------------------------------------------------- */
/*									 SteamClient                              */
/* -------------------------------------------------------------------------- */

//48 89 5C 24 18 48 89 6C 24 20 56 57 41 54 41 55 41 57 48 81 EC 20 01
SEARCH_TYPE LoadPackagePattern = "\x48\x89\x5C\x24\x18\x48\x89\x6C\x24\x20\x56\x57\x41\x54\x41\x55\x41\x57\x48\x81\xEC\x20\x01";
SEARCH_TYPE LoadPackageMask = "xxxxxxxxxxxxxxxxxxxxxxx";

//48 8B C4 89 50 10 55 53 48 8D 68 D8
SEARCH_TYPE CheckAppOwnershipPattern = "\x48\x8B\xC4\x89\x50\x10\x55\x53\x48\x8D\x68\xD8";
SEARCH_TYPE CheckAppOwnershipMask = "xxxxxxxxxxxx";

// 48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 30(The Frist Search Result)
SEARCH_TYPE CUtlMemoryGrowPattern = "\x48\x89\x5C\x24\x08\x48\x89\x74\x24\x10\x57\x48\x83\xEC\x30";
SEARCH_TYPE CUtlMemoryGrowMask = "xxxxxxxxxxxxxxx";

//48 89 5C 24 08 48 89 6C 24 10 48 89 74 24 18 57 48 83 EC 30 48 63 FA 49 8B E9 8B D7 49 8B D8 48 8B F1
SEARCH_TYPE LoadDepotDecryptionKeyPattern = "\x48\x89\x5C\x24\x08\x48\x89\x6C\x24\x10\x48\x89\x74\x24\x18\x57\x48\x83\xEC\x30\x48\x63\xFA\x49\x8B\xE9\x8B\xD7\x49\x8B\xD8\x48\x8B\xF1";
SEARCH_TYPE LoadDepotDecryptionKeyMask = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";

// 48 89 5C 24 18 55 56 57 41 55 41 57 48 8D 6C 24 A0
SEARCH_TYPE GetManifestRequestCodePattern="\x48\x89\x5C\x24\x18\x55\x56\x57\x41\x55\x41\x57\x48\x8D\x6C\x24\xA0";
SEARCH_TYPE GetManifestRequestCodeMask="xxxxxxxxxxxxxxxxx";

// 0F 8E ?? ?? ?? ?? 48 89 BC 24 30 01 00 00
SEARCH_TYPE SharedLibraryStopPlayingPatchPattern = "\x0F\x8E\x00\x00\x00\x00\x48\x89\xBC\x24\x30\x01\x00\x00";
SEARCH_TYPE SharedLibraryStopPlayingPatchMask = "xx????xxxxxxxx";

// 0F 84 9C 01 00 00 4C 8D 35 ?? ?? ?? ?? 0F 1F 40 00
SEARCH_TYPE FamilyGroupRunningAppPatchPattern = "\x0F\x84\x9C\x01\x00\x00\x4C\x8D\x35\x00\x00\x00\x00\x0F\x1F\x40\x00";
SEARCH_TYPE FamilyGroupRunningAppPatchMask = "xxxxxxxxx????xxxx";

// 0F 84 ?? ?? ?? ?? 66 66 66 0F 1F 84 00 00 00 00 00 49 63 C6
SEARCH_TYPE FamilyGroupRunningApp2PatchPattern = "\x0F\x84\x00\x00\x00\x00\x66\x66\x66\x0F\x1F\x84\x00\x00\x00\x00\x00\x49\x63\xC6";
SEARCH_TYPE FamilyGroupRunningApp2PatchMask = "xx????xxxxxxxxxxxxxx";

// 48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 20 48 8B ?? ?? ?? ?? ?? 48 8B F1 8B FA
SEARCH_TYPE BCanRemotePlayTogetherPatchPattern = "\x48\x89\x5C\x24\x08\x48\x89\x74\x24\x10\x57\x48\x83\xEC\x20\x48\x8B\x00\x00\x00\x00\x00\x48\x8B\xF1\x8B\xFA";
SEARCH_TYPE BCanRemotePlayTogetherPatchMask = "xxxxxxxxxxxxxxxxx?????xxxxx";

//89 48 20 48 8B 4B 18 89 50 10 48 89 48 18
SEARCH_TYPE AddAccessTokenPattern = "\x89\x48\x20\x48\x8B\x4B\x18\x89\x50\x10\x48\x89\x48\x18";
SEARCH_TYPE AddAccessTokenMask = "xxxxxxxxxxxxxx";

//48 89 5C 24 10 48 89 6C 24 18 48 89 7C 24 20 41 56 48 81 EC 90 04 00 00
SEARCH_TYPE ModifyStateFlagsPattern = "\x48\x89\x5C\x24\x10\x48\x89\x6C\x24\x18\x48\x89\x7C\x24\x20\x41\x56\x48\x81\xEC\x90\x04\x00\x00";
SEARCH_TYPE ModifyStateFlagsMask = "xxxxxxxxxxxxxxxxxxxxxxx";

#endif // BYTESEARCH_H
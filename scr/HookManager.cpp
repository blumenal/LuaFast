#include "dllmain.h"
#include "HookManager.h"

#include <detours.h>
#include <charconv>

#pragma comment(lib, "winhttp.lib")


namespace SteamUI {
    using LoadModuleWithPath_t = HMODULE(*)(const char* inputPath, bool flags);
    static LoadModuleWithPath_t oLoadModuleWithPath = nullptr;

    HMODULE __fastcall hkLoadModuleWithPath(const char* inputPath, bool flags) {
        // Always call the original function first.
        HMODULE hModule = oLoadModuleWithPath(inputPath, flags);
        if (!strcmp(inputPath, "steamclient64.dll")) {
            // Replace the return module with our diversion module.
            hModule = diversion_hMdoule;
        }
        return hModule;
    }

    void CoreHook() {
        void* target = ByteSearch(GetModuleHandleA("steamui.dll"), LoadModuleWithPathPattern, LoadModuleWithPathMask);
        if (!target) {
            return;
        }
        oLoadModuleWithPath = reinterpret_cast<LoadModuleWithPath_t>(target);

        DetourTransactionBegin();
        DetourUpdateThread(GetCurrentThread());
        DetourAttach(reinterpret_cast<PVOID*>(&oLoadModuleWithPath),
                     reinterpret_cast<PVOID>(&hkLoadModuleWithPath));
        DetourTransactionCommit();
    }

    void CoreUnhook() {
        if (!oLoadModuleWithPath) {
            return;
        }
        DetourTransactionBegin();
        DetourUpdateThread(GetCurrentThread());
        DetourDetach(reinterpret_cast<PVOID*>(&oLoadModuleWithPath),
                     reinterpret_cast<PVOID>(&hkLoadModuleWithPath));
        DetourTransactionCommit();
        oLoadModuleWithPath = nullptr;
    }
}

namespace SteamClient {
    
    using CUtlMemoryGrow_t              =           void*(*)(CUtlVector<uint32>* pVec, int grow_size);
    using LoadPackage_t                 =           bool(*)(PackageInfo*, uint8*, int32, void*);
    using CheckAppOwnership_t           =           bool(*)(void*, AppId_t, AppOwnership*);
    using GetDecryptionKey_t            =           EResult(*)(void*,uint32,AppId_t,CUtlBuffer*);
    using LoadDepotDecryptionKey_t		=		    int32(*)(void*, uint32, char*, char*, uint32);
    using GetManifestRequestCode_t      =           EResult(*)(void*, AppId_t, AppId_t,uint64,const char*, uint64*);
    using ModifyStateFlags_t            =           bool(*)(CSteamApp*, int32, int32,int32);

    static CUtlMemoryGrow_t    oCUtlMemoryGrow    = nullptr;
    static LoadPackage_t       oLoadPackage       = nullptr;
    static CheckAppOwnership_t oCheckAppOwnership = nullptr;
    static GetDecryptionKey_t  oGetDecryptionKey  = nullptr;
    static LoadDepotDecryptionKey_t oLoadDepotDecryptionKey = nullptr;
    static GetManifestRequestCode_t oGetManifestRequestCode = nullptr;
    static ModifyStateFlags_t oModifyStateFlags = nullptr;
    static uint8_t* addAccessTokenTarget = nullptr;

    void PatchBinary() {
        // family sharing and remote play Patches
        static constexpr unsigned char kJmpPatchSharedLibraryStopPlaying[6] = { 0xE9, 0x31, 0x02, 0x00, 0x00, 0x90 };// jmp rel 0x00000231 + nop
        static constexpr unsigned char kJmpPatchFamilyGroupRunningApp[6] = { 0xE9, 0x9D, 0x01, 0x00, 0x00, 0x90 };// jmp rel 0x0000019D + nop
        static constexpr unsigned char kJmpPatchFamilyGroupRunningApp2[6] = { 0xE9, 0x31, 0x02, 0x00, 0x00, 0x90 };// jmp rel 0x00000231 + nop
        static constexpr unsigned char kPatchBCanRemotePlayTogether[5] = { 0xB0, 0x01, 0xC3, 0x90, 0x90 };// mov al, 1; ret; nop; nop

        if (!diversion_hMdoule) {
            return;
        }

        void* sharedLibraryStopPlayingTarget = ByteSearch(
            diversion_hMdoule,
            SharedLibraryStopPlayingPatchPattern,
            SharedLibraryStopPlayingPatchMask);
        if (sharedLibraryStopPlayingTarget) {
            PatchMemoryBytes(sharedLibraryStopPlayingTarget, kJmpPatchSharedLibraryStopPlaying, sizeof(kJmpPatchSharedLibraryStopPlaying));
        }

        void* familyGroupRunningAppTarget = ByteSearch(
            diversion_hMdoule,
            FamilyGroupRunningAppPatchPattern,
            FamilyGroupRunningAppPatchMask);
        if (familyGroupRunningAppTarget) {
            PatchMemoryBytes(familyGroupRunningAppTarget, kJmpPatchFamilyGroupRunningApp, sizeof(kJmpPatchFamilyGroupRunningApp));
        }

        void* familyGroupRunningApp2Target = ByteSearch(
            diversion_hMdoule,
            FamilyGroupRunningApp2PatchPattern,
            FamilyGroupRunningApp2PatchMask);
        if (familyGroupRunningApp2Target) {
            PatchMemoryBytes(familyGroupRunningApp2Target, kJmpPatchFamilyGroupRunningApp2, sizeof(kJmpPatchFamilyGroupRunningApp2));
        }

        void* bCanRemotePlayTogetherTarget = ByteSearch(
            diversion_hMdoule,
            BCanRemotePlayTogetherPatchPattern,
            BCanRemotePlayTogetherPatchMask);
        if (bCanRemotePlayTogetherTarget) {
            PatchMemoryBytes(bCanRemotePlayTogetherTarget, kPatchBCanRemotePlayTogether, sizeof(kPatchBCanRemotePlayTogether));
        }
    }

    bool __fastcall hkLoadPackage(PackageInfo* pPackageInfo, uint8* SHA_1_Hash, int32 ChangeNumber, void* p4) {
        bool result = oLoadPackage(pPackageInfo, SHA_1_Hash, ChangeNumber, p4);
        if (pPackageInfo->PackageId == 0) {
            // Insert Fake Game And Depot Into PackageInfo whose PackageId is 0
            std::vector<AppId_t> AddAppIdVector = LuaConfig::GetAllDepotIds();
            if (!AddAppIdVector.empty()) {
                uint32 oldSize = pPackageInfo->AppIdVec.m_Size;
                uint32 numToAdd = (uint32)AddAppIdVector.size();
                oCUtlMemoryGrow(&pPackageInfo->AppIdVec, numToAdd);
                for (uint32 i = 0; i < numToAdd; i++) {
                    pPackageInfo->AppIdVec.m_Memory.m_pMemory[oldSize + i] = AddAppIdVector[i];
                }
            }
        }
        return result;
    }

    bool __fastcall hkCheckAppOwnership(void* pObject, AppId_t AppId, AppOwnership* pOwnershipInfo) {
        bool result = oCheckAppOwnership(pObject, AppId, pOwnershipInfo);
        if (LuaConfig::HasDepot(AppId)) {
            pOwnershipInfo->PackageId = 0;
            pOwnershipInfo->ReleaseState = EAppReleaseState::Released;
            pOwnershipInfo->GameIDType = EGameIDType::k_EGameIDTypeApp;
            return true;
        }
        return result;
    }

    int32 __fastcall hkLoadDepotDecryptionKey(void* pObject, uint32 foo, char* KeyName, char* Key, uint32 KeySize)
    {
        std::string str_KeyName = std::string(KeyName);
        // Check if the KeyName contains the pattern "\DecryptionKey" and extract the DepotId.
        if (std::size_t last_slash = str_KeyName.find("\\DecryptionKey");last_slash != std::string::npos) {
            if (std::size_t start_pos = str_KeyName.find_last_of("\\", last_slash - 1);start_pos != std::string::npos) {
                // Extract DepotId
                AppId_t DepotId = std::stoul(str_KeyName.substr(start_pos + 1, last_slash - start_pos - 1));
                // Try to get the decryption key from LuaConfig using the extracted DepotId.
                if (const auto& DecryptionKey = LuaConfig::GetDecryptionKey(DepotId);!DecryptionKey.empty())
                {
                    // If a key is found, copy it to the provided buffer and return the key size.
                    if (KeySize >= DecryptionKey.size()) {
                        memcpy(Key, DecryptionKey.data(), DecryptionKey.size());
                        return DecryptionKey.size();
                    }
                    return 0;
                }
            }

        }
        return oLoadDepotDecryptionKey(pObject, foo, KeyName, Key, KeySize);
    }

    // FUNÇÃO LOCAL para buscar manifesto - SEM CONEXÃO EXTERNA
    static bool FetchManifestRequestCodeLocal(AppId_t DepotId, uint64_t manifest_gid, uint64_t* outRequestCode) {
        // Tenta obter do LuaConfig primeiro (script ou arquivo .manifest)
        uint64_t requestCode = LuaConfig::GetManifestRequestCode(DepotId, manifest_gid);
        if (requestCode != 0) {
            *outRequestCode = requestCode;
            return true;
        }
        
        // Se não encontrou, retorna false (sem fallback externo)
        return false;
    }

    // HOOK MODIFICADO - usa apenas fonte local, sem conexão externa
    EResult __fastcall hkGetManifestRequestCode(void* pObject, AppId_t AppId, AppId_t DepotId, 
                                                 uint64_t manifest_gid, const char* branch, 
                                                 uint64_t* outRequestCode) {
        if (LuaConfig::HasDepot(DepotId)) {
            // USA APENAS FONTE LOCAL
            if (FetchManifestRequestCodeLocal(DepotId, manifest_gid, outRequestCode)) {
                return k_EResultOK;
            }
            // Se não encontrar localmente, loga o erro mas não usa servidor externo
            char debugMsg[256];
            sprintf_s(debugMsg, sizeof(debugMsg), "[OpenSteamTool] Manifest not found locally for depot %u, manifest: %llu\n", DepotId, manifest_gid);
            OutputDebugStringA(debugMsg);
        }
        return oGetManifestRequestCode(pObject, AppId, DepotId, manifest_gid, branch, outRequestCode);
    }

    // this is a ligthweight hook that only modify the state flags to prevent steam from updating
    bool __fastcall hkModifyStateFlags(CSteamApp* pApp, int32 flagsToSet, int32 flagsToClear, int32 a4) {
        if (LuaConfig::pinApp(pApp->AppID)) {
            // only modify state flags for pinned and fully installed apps
            // however,it leads to some bad side effects like we can not verify instealled successfully if the app has a new version
            // TODO: we may need to hook the bind manifest function
            if(pApp->StateFlags & k_EAppStateFullyInstalled){
                flagsToSet &= ~(k_EAppStateUpdateRequired |
                                k_EAppStateUpdateQueued   |
                                k_EAppStateUpdateRunning  |
                                k_EAppStateUpdateStarted);

                flagsToClear |= (k_EAppStateUpdateRequired |
                                k_EAppStateUpdateQueued   |
                                k_EAppStateUpdateRunning  |
                                k_EAppStateUpdateStarted);
            
            }
            
        }
        return oModifyStateFlags(pApp, flagsToSet, flagsToClear, a4);
    }

    // VEH Handle For Software Breakpoint And Single Step to Add Access Token Support
    // TODO: maybe we should use inline hook this instruction instead of using a breakpoint, which is a bit hacky and may cause performance issues
    LONG CALLBACK VEH_Handler(PEXCEPTION_POINTERS pExInfo) {
      PCONTEXT ctx = pExInfo->ContextRecord;

      if (pExInfo->ExceptionRecord->ExceptionCode == EXCEPTION_BREAKPOINT
          && ctx->Rip == (uint64_t)addAccessTokenTarget) // address of add_access_token instruction
      {
        // original instruction: 48 89 48 18  mov [rax+18h], rcx 
        
        // read appid from [rax+20h]
        uint32_t appid = *(uint32_t*)(ctx->Rax + 0x20);

        // replace rcx with our access token if it not zero, otherwise keep the original value
        if(uint64_t access_token = LuaConfig::GetAccessToken(appid)) {
            ctx->Rcx = access_token;
        }

        // restore original first instruction byte 48 and set TF for single step to reapply the breakpoint after executing the original instruction
        *(uint8_t*)addAccessTokenTarget = 0x48;
        ctx->EFlags |= 0x100; // TF

        return EXCEPTION_CONTINUE_EXECUTION;
      }

      if (pExInfo->ExceptionRecord->ExceptionCode == EXCEPTION_SINGLE_STEP
          && ctx->Rip == (uint64_t)(addAccessTokenTarget + 4))  // address of the next instruction after add_access_token
      {
          // restore the breakpoint for the next time
          *(uint8_t*)addAccessTokenTarget = 0xCC;

          return EXCEPTION_CONTINUE_EXECUTION;
      }

      return EXCEPTION_CONTINUE_SEARCH;
  }

    void CoreHook() {
        // Resolve CUtlMemoryGrow (called directly, not hooked).
        oCUtlMemoryGrow = reinterpret_cast<CUtlMemoryGrow_t>(ByteSearch(diversion_hMdoule, CUtlMemoryGrowPattern, CUtlMemoryGrowMask));

        void* loadPackageTarget       = ByteSearch(diversion_hMdoule, LoadPackagePattern, LoadPackageMask);
        void* checkAppOwnershipTarget = ByteSearch(diversion_hMdoule, CheckAppOwnershipPattern, CheckAppOwnershipMask);
        void* loadDepotDecryptionKeyTarget  = ByteSearch(diversion_hMdoule, LoadDepotDecryptionKeyPattern, LoadDepotDecryptionKeyMask);
        void* getManifestRequestCodeTarget = ByteSearch(diversion_hMdoule, GetManifestRequestCodePattern, GetManifestRequestCodeMask);
        void* modifyStateFlagsTarget = ByteSearch(diversion_hMdoule, ModifyStateFlagsPattern, ModifyStateFlagsMask);

        oLoadPackage       = reinterpret_cast<LoadPackage_t>(loadPackageTarget);
        oCheckAppOwnership = reinterpret_cast<CheckAppOwnership_t>(checkAppOwnershipTarget);
        oLoadDepotDecryptionKey  = reinterpret_cast<LoadDepotDecryptionKey_t>(loadDepotDecryptionKeyTarget);
        oGetManifestRequestCode = reinterpret_cast<GetManifestRequestCode_t>(getManifestRequestCodeTarget);
        oModifyStateFlags = reinterpret_cast<ModifyStateFlags_t>(modifyStateFlagsTarget);

        DetourTransactionBegin();
        DetourUpdateThread(GetCurrentThread());
        if (loadPackageTarget) {
            DetourAttach(reinterpret_cast<PVOID*>(&oLoadPackage),
                         reinterpret_cast<PVOID>(&hkLoadPackage));
        }
        if (checkAppOwnershipTarget) {
            DetourAttach(reinterpret_cast<PVOID*>(&oCheckAppOwnership),
                         reinterpret_cast<PVOID>(&hkCheckAppOwnership));
        }
        if (loadDepotDecryptionKeyTarget) {
            DetourAttach(reinterpret_cast<PVOID*>(&oLoadDepotDecryptionKey),
                         reinterpret_cast<PVOID>(&hkLoadDepotDecryptionKey));
        }
        if (getManifestRequestCodeTarget) {
            DetourAttach(reinterpret_cast<PVOID*>(&oGetManifestRequestCode),
                        reinterpret_cast<PVOID>(&hkGetManifestRequestCode));
        }
        if (modifyStateFlagsTarget) {
            DetourAttach(reinterpret_cast<PVOID*>(&oModifyStateFlags),
                         reinterpret_cast<PVOID>(&hkModifyStateFlags));
        }
        DetourTransactionCommit();

        // Software breakpoint for add_access_token 
        addAccessTokenTarget = static_cast<uint8_t*>(ByteSearch(diversion_hMdoule, AddAccessTokenPattern, AddAccessTokenMask));
        if (addAccessTokenTarget) {
            addAccessTokenTarget += 10; // offset to the instruction we want to break on
            DWORD oldProtect;
            VirtualProtect(addAccessTokenTarget, 1, PAGE_EXECUTE_READWRITE, &oldProtect);
            *(uint8_t*)addAccessTokenTarget = 0xCC; // int3
            // we can not restore the original page protection here because we will continue to execute code at this address and we need to keep it writable for our VEH handler
            AddVectoredExceptionHandler(1, VEH_Handler);
        }
    }

    void CoreUnhook() {
        DetourTransactionBegin();
        DetourUpdateThread(GetCurrentThread());
        if (oLoadPackage) {
            DetourDetach(reinterpret_cast<PVOID*>(&oLoadPackage),
                         reinterpret_cast<PVOID>(&hkLoadPackage));
        }
        if (oCheckAppOwnership) {
            DetourDetach(reinterpret_cast<PVOID*>(&oCheckAppOwnership),
                         reinterpret_cast<PVOID>(&hkCheckAppOwnership));
        }
        if (oLoadDepotDecryptionKey) {
            DetourDetach(reinterpret_cast<PVOID*>(&oLoadDepotDecryptionKey),
                         reinterpret_cast<PVOID>(&hkLoadDepotDecryptionKey));
        }
        if (oGetManifestRequestCode) {
            DetourDetach(reinterpret_cast<PVOID*>(&oGetManifestRequestCode),
                        reinterpret_cast<PVOID>(&hkGetManifestRequestCode));
        }
        if (oModifyStateFlags) {
            DetourDetach(reinterpret_cast<PVOID*>(&oModifyStateFlags),
                         reinterpret_cast<PVOID>(&hkModifyStateFlags));
        }
        DetourTransactionCommit();

        oLoadPackage       = nullptr;
        oCheckAppOwnership = nullptr;
        oLoadDepotDecryptionKey  = nullptr;
        oGetManifestRequestCode = nullptr;
        oModifyStateFlags = nullptr;
    }
}
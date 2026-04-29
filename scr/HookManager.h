#ifndef HOOKMANAGER_H
#define HOOKMANAGER_H

#include "dllmain.h"
#include "ByteSearch.h"

namespace SteamUI {
    void CoreHook();
    void CoreUnhook();
}

namespace SteamClient {
    void PatchBinary();
    void CoreHook();
    void CoreUnhook();
}


#endif // HOOKMANAGER_H

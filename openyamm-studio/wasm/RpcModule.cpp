// The WebAssembly core as a module (S5_BROWSER_EDITOR.md 2.3): the typed request list behind one C function.
//   oymap_call(method, params JSON) -> {"result": ...} or {"error": ...}, a string the caller frees with oymap_free.
// The Node build (oymap_rpc) reads the host's file system through NODERAWFS; the browser worker build (oymap_worker,
// S5c's hosted page and walk mode) reads an in-memory file system the worker fills, with the asset root mounted by the
// worker's own read-only file system over the player's packages (web/src/hosted/packfs.ts).
//
// Besides the request list, two helpers for the hosted worker:
//   oymap_unzstd(source, size, target, capacity) -> bytes written, or 0: un-frames one zstd frame (a cooked texture's
//     blocks) with the core's own zstd, so the hosted page needs no JavaScript zstd (S5_BROWSER_EDITOR.md 2.11, 4.11);
//   oymap_heap(fields) fills four numbers: the heap's live bytes (malloc's in-use total), its arena (what malloc took
//     from the memory), the memory's size (it only grows) and malloc's largest footprint so far (S5c's budget). Only
//     this call walks the heap (mallinfo; with mimalloc its areas and the memory it took); the calls of the request
//     list pay nothing for it.
#include "cli/Rpc.h"

#include <emscripten/emscripten.h>
#include <emscripten/heap.h>
#include <malloc.h>
#include <zstd.h>

#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unistd.h>

#ifdef OYMAP_MIMALLOC
// Built with mimalloc (CMake OYMAP_WASM_MALLOC=mimalloc, S8f): its heap walk by areas, declared as Emscripten
// 4.0.10's system/lib/mimalloc/include/mimalloc.h has it.
extern "C"
{
typedef struct mi_heap_s mi_heap_t;
typedef struct mi_heap_area_s
{
    void *blocks;
    size_t reserved;
    size_t committed;
    size_t used;
    size_t block_size;
    size_t full_block_size;
} mi_heap_area_t;
typedef bool(mi_block_visit_fun)(const mi_heap_t *pHeap, const mi_heap_area_t *pArea, void *pBlock, size_t blockSize,
    void *pArg);
mi_heap_t *mi_heap_get_default(void);
bool mi_heap_visit_blocks(const mi_heap_t *pHeap, bool visitAllBlocks, mi_block_visit_fun *pVisitor, void *pArg);
// Where the linker put the heap's start (wasm-ld).
extern unsigned char __heap_base;
}

namespace
{
bool countArea(const mi_heap_t *, const mi_heap_area_t *pArea, void *, size_t, void *pArg)
{
    if (pArea != nullptr)
    {
        *static_cast<double *>(pArg) += static_cast<double>(pArea->used) * static_cast<double>(pArea->block_size);
    }

    return true;
}
}
#else
// dlmalloc's own count of the most it took from the memory (constant time).
extern "C" size_t malloc_max_footprint(void);
#endif

extern "C"
{
EMSCRIPTEN_KEEPALIVE char *oymap_call(const char *pMethod, const char *pParamsJson)
{
    const std::string answer = OpenYAMM::Studio::callRpcMethod(pMethod, std::string(pParamsJson ? pParamsJson : ""));
    char *pText = static_cast<char *>(std::malloc(answer.size() + 1));
    std::memcpy(pText, answer.c_str(), answer.size() + 1);
    return pText;
}

EMSCRIPTEN_KEEPALIVE void oymap_free(char *pText)
{
    std::free(pText);
}

EMSCRIPTEN_KEEPALIVE size_t oymap_unzstd(const uint8_t *pSource, size_t sourceBytes, uint8_t *pTarget, size_t capacity)
{
    const size_t written = ZSTD_decompress(pTarget, capacity, pSource, sourceBytes);
    return ZSTD_isError(written) ? 0 : written;
}

EMSCRIPTEN_KEEPALIVE void oymap_heap(double *pFields)
{
#ifdef OYMAP_MIMALLOC
    // mimalloc takes its segments from the memory by sbrk and keeps them: what it took is the arena now and its
    // largest so far (its own commit counts do not describe wasm memory).
    double live = 0.0;
    mi_heap_visit_blocks(mi_heap_get_default(), false, countArea, &live);
    const double taken = static_cast<double>(reinterpret_cast<uintptr_t>(sbrk(0))
        - reinterpret_cast<uintptr_t>(&__heap_base));
    pFields[0] = live;
    pFields[1] = taken;
    pFields[2] = static_cast<double>(emscripten_get_heap_size());
    pFields[3] = taken;
#else
    const struct mallinfo info = mallinfo();
    pFields[0] = static_cast<double>(info.uordblks);
    pFields[1] = static_cast<double>(info.arena);
    pFields[2] = static_cast<double>(emscripten_get_heap_size());
    pFields[3] = static_cast<double>(malloc_max_footprint());
#endif
}
}

// The runtime stays alive after main (EXIT_RUNTIME is off), so the module answers calls until it is dropped.
int main()
{
    return 0;
}

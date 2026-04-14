#pragma once

#include "editor/viewport/EditorOutdoorViewport.h"
#include "editor/document/EditorSession.h"
#include <bgfx/bgfx.h>
#include <cstdint>
#include <filesystem>
#include <limits>
#include <optional>
#include <string>
#include <unordered_map>

namespace OpenYAMM::Editor
{
class EditorMainWindow
{
public:
    void shutdown();
    void render(
        EditorSession &session,
        uint32_t frameNumber,
        float deltaSeconds,
        const std::string &rendererName);

    int viewportX() const;
    int viewportY() const;
    uint16_t viewportWidth() const;
    uint16_t viewportHeight() const;

private:
    enum class StatusMessageKind
    {
        Info,
        Success,
        Error
    };

    enum class ObjImportTarget
    {
        None,
        ReplaceSelectedBModel,
        ImportNewBModel
    };

    enum class MapPackageAction
    {
        None,
        SaveAs,
        Duplicate
    };

    struct FaceClipboard
    {
        bool valid = false;
        std::string textureName;
        std::vector<int16_t> textureUs;
        std::vector<int16_t> textureVs;
        int16_t textureDeltaU = 0;
        int16_t textureDeltaV = 0;
        bool hasSceneOverride = false;
        uint32_t sceneLegacyAttributes = 0;
        uint16_t sceneCogNumber = 0;
        uint16_t sceneCogTriggeredNumber = 0;
        uint16_t sceneCogTrigger = 0;
    };

    void ensureDefaultDockLayout();
    void renderMenuBar(EditorSession &session);
    void renderToolbar(EditorSession &session);
    void renderSceneOutliner(EditorSession &session);
    void renderInspector(EditorSession &session);
    void handleGlobalShortcuts(EditorSession &session);
    void renderLogPanel(
        const EditorSession &session,
        uint32_t frameNumber,
        float deltaSeconds,
        const std::string &rendererName);
    void renderViewportPanel(EditorSession &session, float deltaSeconds);
    void renderCreateButtons(EditorSession &session);
    void renderPlacementButtons(EditorSession &session);
    void renderToolModeButtons(EditorSession &session);
    void renderTransformToolbar();
    void renderTerrainToolbar(EditorSession &session);
    void renderViewToolbar();
    void renderToolbarStatus(const EditorSession &session);
    bool renderBitmapTextureSelector(
        EditorSession &session,
        const char *pLabel,
        std::string &value,
        std::optional<size_t> bmodelIndex = std::nullopt) const;
    std::optional<bgfx::TextureHandle> ensureBitmapPreviewTexture(
        const EditorSession &session,
        const std::string &textureName) const;
    std::optional<std::pair<int, int>> bitmapPreviewTextureSize(const std::string &textureName) const;
    void destroyBitmapPreviewTextures();
    void duplicateSelected(EditorSession &session);
    void deleteSelected(EditorSession &session);
    void renderDocumentSummary(const EditorSession &session) const;
    void renderEnvironmentInspector(EditorSession &session) const;
    void renderTerrainInspector(EditorSession &session) const;
    void renderBModelInspector(EditorSession &session, size_t bmodelIndex) const;
    void renderInteractiveFaceInspector(EditorSession &session) const;
    void renderEntityPlacementInspector(EditorSession &session) const;
    void renderEntityInspector(EditorSession &session, size_t entityIndex) const;
    void renderSpawnInspector(EditorSession &session, size_t spawnIndex) const;
    void renderActorInspector(EditorSession &session, size_t actorIndex) const;
    void renderSpriteObjectPlacementInspector(EditorSession &session) const;
    void renderSpriteObjectInspector(EditorSession &session, size_t spriteObjectIndex) const;
    void renderChestInspector(EditorSession &session, size_t chestIndex) const;
    void renderObjImportModal(EditorSession &session);
    void renderObjFileBrowserPopup(EditorSession &session);
    void renderNewOutdoorMapModal(EditorSession &session);
    void renderOpenOutdoorMapModal(EditorSession &session);
    void renderMapPackageActionModal(EditorSession &session);
    void renderDeleteCurrentMapModal(EditorSession &session);
    void ensureEditorStateLoaded(EditorSession &session);
    void persistEditorStateIfNeeded(const EditorSession &session);
    bool playtestCurrentMap(EditorSession &session, std::string &errorMessage) const;
    void setStatusMessage(StatusMessageKind kind, const std::string &message);
    void openObjFileBrowser(ObjImportTarget target, const char *pCurrentPath) const;
    void assignObjBrowserSelectionPath(const std::filesystem::path &path) const;
    void rememberObjImportDirectory(const char *pPath) const;
    void openNewOutdoorMapModal(EditorSession &session);
    void openOpenOutdoorMapModal() const;
    void openMapPackageActionModal(EditorSession &session, MapPackageAction action) const;
    void openDeleteCurrentMapModal() const;

    bool m_dockLayoutInitialized = false;
    int m_viewportX = 0;
    int m_viewportY = 0;
    uint16_t m_viewportWidth = 1;
    uint16_t m_viewportHeight = 1;
    mutable size_t m_bmodelTransformEditorIndex = std::numeric_limits<size_t>::max();
    mutable int m_bmodelMoveBy[3] = {0, 0, 0};
    mutable float m_bmodelRotateByDegrees[3] = {0.0f, 0.0f, 0.0f};
    mutable size_t m_bmodelBulkEditorIndex = std::numeric_limits<size_t>::max();
    mutable int m_bmodelBulkFaceScope = 0;
    mutable uint32_t m_bmodelBulkFaceAttributes = 0;
    mutable uint16_t m_bmodelBulkCogNumber = 0;
    mutable uint16_t m_bmodelBulkCogTriggeredNumber = 0;
    mutable uint16_t m_bmodelBulkCogTrigger = 0;
    mutable size_t m_bmodelImportEditorIndex = std::numeric_limits<size_t>::max();
    mutable char m_bmodelImportPath[512] = {};
    mutable float m_bmodelImportScale = 1.0f;
    mutable char m_bmodelImportDefaultTexture[64] = "grastyl";
    mutable char m_globalBModelImportPath[512] = {};
    mutable float m_globalBModelImportScale = 1.0f;
    mutable char m_globalBModelImportDefaultTexture[64] = "grastyl";
    mutable bool m_openNewOutdoorMapModal = false;
    mutable bool m_closeNewOutdoorMapModal = false;
    mutable char m_newOutdoorMapId[64] = {};
    mutable char m_newOutdoorDisplayName[128] = {};
    mutable int m_newOutdoorMapSizePreset = 0;
    mutable int m_newOutdoorTilesetPreset = 0;
    mutable bool m_openOpenOutdoorMapModal = false;
    mutable char m_openOutdoorMapFilter[128] = {};
    mutable char m_sceneFilter[128] = {};
    mutable bool m_openMapPackageActionModal = false;
    mutable MapPackageAction m_mapPackageAction = MapPackageAction::None;
    mutable char m_mapPackageActionMapId[64] = {};
    mutable char m_mapPackageActionDisplayName[128] = {};
    mutable bool m_openDeleteCurrentMapModal = false;
    mutable bool m_openImportNewBModelModal = false;
    mutable bool m_closeImportNewBModelModal = false;
    mutable bool m_openObjBrowserPopup = false;
    mutable ObjImportTarget m_objBrowserTarget = ObjImportTarget::None;
    mutable std::filesystem::path m_objBrowserDirectory;
    mutable char m_objBrowserFilter[128] = {};
    mutable std::unordered_map<std::string, bgfx::TextureHandle> m_bitmapPreviewTextures;
    mutable std::unordered_map<std::string, std::pair<int, int>> m_bitmapPreviewTextureSizes;
    mutable FaceClipboard m_faceClipboard;
    mutable bool m_editorStateLoaded = false;
    mutable std::string m_lastSavedEditorState;
    float m_toolsDockTargetHeight = 0.0f;
    std::string m_statusMessage;
    StatusMessageKind m_statusMessageKind = StatusMessageKind::Info;
    bool m_shutdownComplete = false;
    EditorOutdoorViewport m_viewport;
};
}

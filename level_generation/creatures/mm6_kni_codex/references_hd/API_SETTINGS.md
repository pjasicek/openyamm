# Meshy settings verified 2026-10-12

Official docs: https://docs.meshy.ai/en/api/image-to-3d ; https://docs.meshy.ai/en/api/pricing ; https://docs.meshy.ai/en/api/rigging ; https://docs.meshy.ai/en/api/retexture .

Smart Topology uses meshy-t2, target_polycount <=15000, no remesh necessary: 5 credits mesh only. Pose mode omitted because master is already in A-pose. Rigging is 5 credits, textured humanoid GLB facing glTF +Z. Use a neutral provisional texture for rig estimation; final retexture waits until deformation passes. Retexture 2K/4K is 10 credits; multi-view uses explicit meshy-7, front/left/back/right. No paid animations.

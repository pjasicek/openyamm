# Step 1B — one revised geometry candidate

Screenshot `test_img/2029.png` after Reuse prompt shows all four inputs with Multi-view ON and Image Enhancement OFF.
The missing upper-back plates and skull projection cannot be explained by an absent upload on this evidence.

Keep source master 01 unchanged. Make one revised candidate with:

| Control | Value |
| --- | --- |
| Model | Meshy 7.1 — Flagship / High Detail, unchanged |
| Images | Same front / left / back / right references, unchanged |
| Multi-view | ON |
| Resolution | Standard (change from Ultra 2K) |
| Pose | OFF (change from ON / A-Pose) |
| Image Enhancement | OFF |
| Texture | OFF |
| Split | OFF |

The references already contain the intended A-pose. Disabling the separate pose control requests reconstruction
without imposing another pose. This is a reasonable comparison, not a verified cure for the omitted geometry.
Standard follows the first-prototype detail policy and avoids using Ultra before it demonstrates a visual benefit.
Changing both controls means this is a candidate comparison, not an isolated experiment proving either caused an error.

Check the live credit quote and generate one candidate. Download its source GLB and return the path. Preserve the
first candidate; do not remesh, texture or rig either yet. Compare rear skull, upper-back plates, teeth, jewelry,
hand rest orientation and overall silhouette. If the structural omissions persist, stop these generation retries
and use the better body for targeted local repair before topology processing.

The default/reference versus custom-pose distinction is documented in
[Meshy Image to 3D](https://docs.meshy.ai/en/webapp/image-to-3d). There is no verified documentation establishing
that the Pose toggle caused this model's missing back plates or skull shape.

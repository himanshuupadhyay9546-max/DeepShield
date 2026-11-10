import os
import tempfile
import uuid
import torch
import cv2
import numpy as np


def _to_real_numpy(t: torch.Tensor) -> np.ndarray:
    """Convert tensor to float32 numpy, stripping imaginary part if complex."""
    if t.is_complex():
        t = t.real
    return t.float().cpu().numpy()


def generate_gradcam(model, tensor, orig_path):
    model.eval()
    inp = tensor.clone().detach().requires_grad_(True)

    features_holder = {}
    grads_holder = {}

    def fwd_hook(module, inp, out):
        features_holder['f'] = out
        out.register_hook(lambda g: grads_holder.update({'g': g}))

    handle = model.backbone._conv_head.register_forward_hook(fwd_hook)
    try:
        result = model(inp)
        result.backward()
    finally:
        handle.remove()

    feats = _to_real_numpy(features_holder['f'].detach())   # [1, C, H, W]
    if 'g' in grads_holder:
        grads = _to_real_numpy(grads_holder['g'].detach())
    else:
        grads = np.ones_like(feats)

    weights = grads.mean(axis=(2, 3), keepdims=True)        # [1, C, 1, 1]
    cam = np.maximum((weights * feats).sum(axis=1)[0], 0)   # [H, W]

    cam = cv2.resize(cam.astype(np.float32), (224, 224))
    if cam.max() > cam.min():
        cam = (cam - cam.min()) / (cam.max() - cam.min())

    heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)

    orig = cv2.imread(orig_path)
    if orig is not None:
        orig = cv2.resize(orig, (224, 224))
        overlay = cv2.addWeighted(orig, 0.6, heatmap, 0.4, 0)
    else:
        overlay = heatmap

    out_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_heatmap.jpg")
    cv2.imwrite(out_path, overlay)
    return out_path

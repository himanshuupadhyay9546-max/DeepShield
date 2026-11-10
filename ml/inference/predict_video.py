import cv2, torch, numpy as np
from models.deepshield import DeepShieldModel

def analyze_video(path, sample_rate=5):
    model = DeepShieldModel().eval()
    cap = cv2.VideoCapture(path)
    scores, frames = [], 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        if frames % sample_rate == 0:
            img = cv2.resize(frame, (224,224))
            x = torch.from_numpy(img).permute(2,0,1).float()/255
            with torch.no_grad():
                p = torch.sigmoid(model(x.unsqueeze(0))).item()
            scores.append(p)
        frames += 1
    cap.release()
    avg = float(np.mean(scores))
    return {
        "video_score": avg,
        "label": "FAKE" if avg>0.5 else "REAL",
        "frames_analyzed": len(scores),
        "temporal_variance": float(np.var(scores))
    }

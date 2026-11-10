from models.deepshield import DeepShieldModel
import torch, cv2

model = DeepShieldModel()
model.load_state_dict(torch.load("checkpoints/best.pth", map_location="cpu"))
model.eval()

def predict(path):
    img = cv2.imread(path); img = cv2.resize(img,(224,224))
    x = torch.from_numpy(img).permute(2,0,1).float()/255
    with torch.no_grad():
        p = torch.sigmoid(model(x.unsqueeze(0))).item()
    return {"fake_prob": p, "label": "FAKE" if p>0.5 else "REAL"}

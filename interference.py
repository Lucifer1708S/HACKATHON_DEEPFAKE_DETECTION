import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image, ImageOps
import cv2 
import numpy as np
import io

def get_model():
    model = models.efficientnet_b0(weights=None) 
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 2)
    return model


device = torch.device("cpu")
model = get_model()

try:
    checkpoint = torch.load("models/deepfake_model_epoch_5.pth", map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    print("✅ Model loaded on Cloud CPU")
except Exception as e:
    print(f"❌ Weight Error: {e}")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def predict_media(file_path):
    try:
        is_video = file_path.lower().endswith(('.mp4', '.avi', '.mov'))
        
        if is_video:
            cap = cv2.VideoCapture(file_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            success, frame = cap.read()
            cap.release()
            
            if not success: raise Exception("Video read failed")
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            img_raw = Image.open(file_path)
            img = ImageOps.exif_transpose(img_raw).convert('RGB')

        img_t = transform(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(img_t)
            prob = torch.nn.functional.softmax(outputs, dim=1)
            conf, pred = torch.max(prob, 1)
            
        return bool(pred.item() == 1), float(conf.item())
    except Exception as e:
        print(f"⚠️ Prediction error: {e}")
        return False, 0.0
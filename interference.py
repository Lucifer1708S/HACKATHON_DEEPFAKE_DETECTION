import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image, ImageOps
import cv2 
import numpy as np
import requests
import tempfile
import os

# Load Face Detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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
    print("✅ AI Model Loaded Successfully")
except Exception as e:
    print(f"❌ Weight Error: {e}")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def predict_media(file_path):
    temp_file_path = None
    try:
        is_url = file_path.startswith('http')
        is_video = file_path.lower().split('?')[0].endswith(('.mp4', '.avi', '.mov'))

        if is_url:
            response = requests.get(file_path, stream=True)
            suffix = ".mp4" if is_video else ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                temp_file_path = tmp.name
            use_path = temp_file_path
        else:
            use_path = file_path

        if is_video:
            cap = cv2.VideoCapture(use_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            success, frame = cap.read()
            cap.release()
            if not success: raise Exception("Video read failed")
        else:
            frame = cv2.imread(use_path)

        # --- FACE DETECTION ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_img = frame[y:y+h, x:x+w]
            img = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
            print("👤 Face detected: Cropping for focus.")
        else:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            print("⚠️ No face found: Analyzing full scene.")

        img_t = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = model(img_t)
            prob = torch.nn.functional.softmax(outputs, dim=1)
            conf, pred = torch.max(prob, 1)
            
        # prediction 0 = Authentic, 1 = Deepfake
        is_fake_detected = bool(pred.item() == 1)
        raw_confidence = float(conf.item())
        
        return is_fake_detected, raw_confidence

    except Exception as e:
        print(f"⚠️ Prediction error: {e}")
        return False, 0.0
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
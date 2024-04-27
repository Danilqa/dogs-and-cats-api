import torch
import torch.nn as nn
import os
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

MODEL_PATH = "./models/cats_dogs_trained_model.pt"
IMG_CLASSES = ["cat", "dog"]

def setup_model(model_path, cuda=False):
    device = torch.device("cuda" if cuda and torch.cuda.is_available() else "cpu")
    model = models.vgg16(pretrained=False)
    model.classifier = nn.Sequential(
        nn.Linear(25088, 4096),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(4096, 1000),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(1000, 100),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(100, 2),
    )
    model = model.to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    return model, device

def image_loader(img, model, device):
    scaler = transforms.Resize((224, 224))
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    to_tensor = transforms.ToTensor()
    image = normalize(to_tensor(scaler(img))).unsqueeze(0).to(device)
    output = model(image)
    _, pred = torch.max(output.data, 1)

    return pred.item()

def recognize(img_path):
    if os.path.exists(img_path):
        img = Image.open(img_path)
    else:
        print(f"Error: The file {img_path} does not exist.")
        raise Exception("File doesn't exist")

    model, device = setup_model(model_path=MODEL_PATH, cuda=False)
    prediction = image_loader(img, model, device)

    return IMG_CLASSES[prediction]

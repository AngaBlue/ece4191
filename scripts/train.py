from ultralytics import YOLO
import torch

def main():
  # Use CUDA
  USE_GPU = torch.cuda.is_available()

  # Load a model
  model = YOLO("yolo11n.pt")  # load a pretrained model (recommended for training)

  # Train the model
  model.train(data="data.yaml", epochs=100, imgsz=640, rect=True, batch=0.8, device= "0" if USE_GPU else "cpu")

if __name__ == '__main__':
    main()

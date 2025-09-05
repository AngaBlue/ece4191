from ultralytics import YOLO
import cv2
# Load the trained model
model = YOLO(r"C:\Users\jonat\ECE4191\ece4191\scripts\runs\detect\train17\weights\best.pt")  # path to your trained weights

# Path to your test image
img_path = r"C:\Users\jonat\ECE4191\ece4191\scripts\test6.jpg"

# Run detection
results = model.predict(img_path)  # or model(img_path)

# The first (and usually only) result in the batch
r = results[0]

# Bounding boxes: [x1, y1, x2, y2, confidence, class_id]
boxes = r.boxes.xyxy.cpu().numpy()      # coordinates
scores = r.boxes.conf.cpu().numpy()     # confidence
class_ids = r.boxes.cls.cpu().numpy()   # class indices

print("Boxes:", boxes)
print("Scores:", scores)
print("Class IDs:", class_ids)


# Load image
img = cv2.imread(img_path)

# Draw bounding boxes
for i, box in enumerate(boxes):
    x1, y1, x2, y2 = map(int, box[:4])
    conf = scores[i]
    cls_id = int(class_ids[i])
    class_names = ["kangaroo", "cockatoo", "tasmanian_devil", "frog", "platypus"]
    label = f"{class_names[cls_id]}: {conf:.2f}"
    
    # Draw rectangle and label
    cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
    cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

# Show image
cv2.imshow("YOLO Detection", img)
cv2.waitKey(0)
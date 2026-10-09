---
license: mit
library_name: ultralytics
pipeline_tag: image-segmentation
tags:
  - yolo
  - yolov11
  - ultralytics
  - instance-segmentation
  - object-detection
  - litter
  - waste
  - recycling
  - taco
metrics:
  - mAP
---

# YOLOv11 Litter Material Segmentation (TACO)

A YOLOv11-seg model that segments litter in images and labels each piece by material for a recycling/sorting use case:

Plastic · Metal · Glass · Paper · Other

Fine-tuned on the TACO dataset, whose 60 fine categories were grouped by material to reduce class imbalance.

## Results (validation)

| Metric | mAP50 | mAP50-95 |
| ------ | ----- | -------- |
| Mask   | 0.272 | 0.188    |
| Box    | 0.291 | 0.220    |

Per-material mask mAP50-95: Plastic 0.35, Metal 0.34, Paper 0.19, Other 0.04, Glass 0.02.

TACO is a small (~1,500 images), heavily imbalanced, real-world dataset, so absolute mAP is modest. Plastic and Metal (the best-represented materials) are the strongest; Glass is weak simply because very few glass instances exist in the data.

## Limitations & how it could be improved

The scores are modest because of the dataset, not the pipeline. On real photos the model still makes confident mistakes (for example reading crumpled plastic film as Glass) and misses small or occluded items. Ways to push accuracy up:

- More and better-balanced data: merge other litter datasets, oversample and copy-paste the rare classes (Glass, Other), train with a class-weighted loss.
- Stronger augmentation (mosaic, copy-paste, lighting/HSV jitter).
- Bigger backbone (yolo11s to m/l) and longer training, given enough GPU.
- Higher resolution or tiling so small litter survives downscaling.
- Per-class confidence tuning to cut confident-but-wrong calls.

## Usage

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

weights = hf_hub_download("CatSat/yolov11-litter-materials", "best.pt")
model = YOLO(weights)

results = model.predict("photo.jpg", conf=0.25)
results[0].show()
```

## Training

- Base model: yolo11s-seg
- Image size: 960 (small litter benefits from higher resolution)
- Epochs: 80 (early stopping), batch 16
- Labels: COCO segmentation polygons converted to YOLO-seg format

## Links

- Live demo: https://huggingface.co/spaces/CatSat/litter-detection-yolov11
- Code + training notebook: https://github.com/CatSatOK/litter-detection-yolov11

## License

MIT

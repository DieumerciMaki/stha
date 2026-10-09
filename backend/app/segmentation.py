"""Pixel masks from a pinned, documented YOLO segmentation checkpoint."""
import hashlib
import json
import time
import threading
import cv2
import numpy as np
from .config import ROOT, MODEL_MANIFEST

_model = None
_model_lock = threading.Lock()

def model_config():
    config = json.loads(MODEL_MANIFEST.read_text(encoding='utf-8'))
    path = (ROOT / config['weights']).resolve()
    if ROOT / 'models' not in path.parents or not path.is_file():
        raise ValueError('Poids du modèle introuvables.')
    return config, path

def model_status():
    try:
        config, path = model_config()
        evaluation_path = ROOT / 'models' / 'evaluation.json'
        if evaluation_path.exists():
            evaluation = json.loads(evaluation_path.read_text(encoding='utf-8'))
            if evaluation.get('model_sha256') == config['sha256']:
                config['local_evaluation'] = evaluation
        return {**config, 'configured': True, 'size_bytes': path.stat().st_size,
                'message': 'Modèle prêt. Vérifiez les résultats avant de les utiliser.'}
    except (OSError, ValueError, KeyError) as exc:
        return {'configured': False, 'name': None, 'message': 'Modèle indisponible : ' + str(exc)}

def load_model():
    global _model
    with _model_lock:
        if _model is None:
            from ultralytics import YOLO
            config, weights = model_config()
            if hashlib.sha256(weights.read_bytes()).hexdigest() != config['sha256']:
                raise ValueError('Le fichier du modèle ne correspond pas à son empreinte enregistrée.')
            model = YOLO(str(weights))
            if model.task != 'segment' or set(model.names.values()) != set(config['class_names']):
                raise ValueError('Architecture ou classes du modèle incompatibles.')
            _model = model
    return _model

def mask_union(masks, width, height):
    union = np.zeros((height, width), dtype=np.uint8)
    for mask in masks:
        binary = (np.asarray(mask) > .5).astype(np.uint8)
        if binary.shape != (height, width):
            binary = cv2.resize(binary, (width, height), interpolation=cv2.INTER_NEAREST)
        union[binary > 0] = 255
    return union

def predict(image_path, confidence, output_dir):
    import ultralytics
    config, _ = model_config()
    model = load_model()
    started = time.perf_counter()
    # imdecode supports Windows paths containing non-ASCII characters.
    image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Image illisible.')
    height, width = image.shape[:2]
    result = model.predict(image, conf=confidence, imgsz=960, device='cpu', retina_masks=True, verbose=False)[0]
    masks = result.masks.data.cpu().numpy() if result.masks is not None else []
    union = mask_union(masks, width, height)
    translations = {'Plastic': 'Plastique', 'Metal': 'Métal', 'Glass': 'Verre', 'Paper': 'Papier', 'Other': 'Autres'}
    colors = [(115, 181, 67), (203, 141, 62), (172, 110, 176), (69, 191, 208), (139, 158, 178)]
    overlay = image.copy()
    instances = []
    if result.masks is not None:
        for i, box in enumerate(result.boxes):
            class_id = int(box.cls.item())
            name = str(model.names[class_id])
            instance_mask = mask_union([masks[i]], width, height)
            selected = instance_mask > 0
            color = colors[class_id % len(colors)]
            overlay[selected] = (.60 * overlay[selected] + .40 * np.array(color)).astype(np.uint8)
            contours, _ = cv2.findContours(instance_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(overlay, contours, -1, color, 2)
            instances.append({'class_id': class_id, 'label': translations.get(name, name), 'label_original': name,
                              'confidence': round(float(box.conf.item()), 5), 'area_pixels': int(np.count_nonzero(selected)),
                              'box': box.xyxy[0].cpu().numpy().astype(float).tolist(),
                              'polygon': result.masks.xy[i].astype(float).tolist()})
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, array, extension in [('overlay.jpg', overlay, '.jpg'), ('mask.png', union, '.png')]:
        success, buffer = cv2.imencode(extension, array)
        if not success:
            raise OSError('Impossible de sauvegarder le résultat.')
        buffer.tofile(output_dir / filename)
    metadata = {'instances': instances, 'instance_count': len(instances),
                'coverage_percent': round(100 * np.count_nonzero(union) / (width * height), 3),
                'segmented_pixels': int(np.count_nonzero(union)), 'duration_seconds': round(time.perf_counter() - started, 3),
                'model': config['name'], 'model_sha256': config['sha256'], 'model_revision': config['revision'],
                'dataset': config['dataset'], 'ultralytics_version': ultralytics.__version__, 'device': 'cpu',
                'confidence_threshold': confidence, 'image_size': 960, 'width': width, 'height': height,
                'interpretation': 'Union des pixels reconnus comme déchets. Ni surface physique ni volume. Résultat à vérifier.'}
    (output_dir / 'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return metadata

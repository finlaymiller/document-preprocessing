import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

import cv2
import layoutparser as lp
import numpy as np
from PIL import ImageFont

from utils.files import ensure_dir

# monkey-patch for pillow 10.0.0+
# see: https://github.com/python-pillow/Pillow/issues/7322
if not hasattr(ImageFont.FreeTypeFont, "getsize"):

    def getsize(self, text, *args, **kwargs):
        bbox = self.getbbox(text, *args, **kwargs)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])

    ImageFont.FreeTypeFont.getsize = getsize

# global cache for the layout model to avoid reloading it for each image.
_model_cache: Optional[lp.Detectron2LayoutModel] = None


def _initialize_model(
    config: Dict[str, Any],
) -> lp.Detectron2LayoutModel:
    """
    Initialize the layoutparser model.

    Parameters
    ----------
    config : dict
        The configuration for the layout model.

    Returns
    -------
    lp.Detectron2LayoutModel
        The initialized layout model.
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    model_type = config.get(
        "type", "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config"
    )
    label_map = config.get(
        "label_map", {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
    )

    logging.info(f"initializing layout model: {model_type}")
    model = lp.Detectron2LayoutModel(
        config_path=model_type,
        label_map=label_map,
    )

    _model_cache = model
    return model


def _save_layout_data(
    layout: lp.Layout, output_path: str, label_map: Dict[int, str]
) -> None:
    """
    Save the detected layout data to a json file.

    Parameters
    ----------
    layout : lp.Layout
        The detected layout from layoutparser.
    output_path : str
        The path to save the json file.
    label_map : dict
        A mapping from model labels to human-readable names.
    """
    layout_data = []
    for block in layout:
        layout_data.append(
            {
                "box": [int(c) for c in block.coordinates],
                "type": block.type,
                "score": float(block.score),
            }
        )

    with open(output_path, "w") as f:
        json.dump(layout_data, f, indent=2)


def _save_visualization(image: np.ndarray, layout: lp.Layout, output_path: str) -> None:
    """
    Save a visualization of the detected layout.

    Parameters
    ----------
    image : np.ndarray
        The original image.
    layout : lp.Layout
        The detected layout.
    output_path : str
        The path to save the visualization image.
    """
    vis_image = lp.draw_box(image, layout, box_width=3, show_element_type=True)
    vis_image_bgr = cv2.cvtColor(np.array(vis_image), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, vis_image_bgr)


def process_image(
    image_path: str,
    config: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Process a single image to detect its layout.

    Parameters
    ----------
    image_path : str
        The path to the input image.
    config : dict
        The main configuration dictionary.

    Returns
    -------
    tuple[str, str]
        A tuple containing the path to the json data file and the visualization image file.
    """
    step_config = config["step_03_layout_analysis"]
    output_dir = step_config["output_dir"]
    model_config = step_config["model_config"]
    label_map = model_config["label_map"]

    json_output_dir = os.path.join(output_dir, "json")
    viz_output_dir = os.path.join(output_dir, "visualizations")
    ensure_dir(json_output_dir)
    ensure_dir(viz_output_dir)

    model = _initialize_model(
        model_config,
    )

    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"could not read image from path: {image_path}")

    # layoutparser expects bgr images, which is cv2's default.
    layout = model.detect(image)

    filename = os.path.basename(image_path)
    base_filename, _ = os.path.splitext(filename)

    json_path = os.path.join(json_output_dir, f"{base_filename}.json")
    viz_path = os.path.join(viz_output_dir, f"{base_filename}.png")

    _save_layout_data(layout, json_path, label_map)
    _save_visualization(image, layout, viz_path)

    logging.info(f"layout analysis complete for {filename}. results saved.")
    return json_path, viz_path

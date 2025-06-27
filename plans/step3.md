# Step 3: Layout Analysis - Implementation Plan

This plan details the implementation of the third step of the OCR pre-processing pipeline, "Layout Analysis." Following the pre-processing of images in Step 2, this step identifies the structural layout of each document page. The design uses a powerful machine learning model via the `layoutparser` library to detect regions such as text blocks, titles, tables, and figures, which is crucial for guiding the subsequent OCR process.

## 1. Goal

To analyze the preprocessed images and identify the physical layout of the content. For each image, this step will:
1.  Detect distinct content blocks (e.g., paragraphs, tables, images).
2.  Save the coordinates and type of each block to a structured JSON file.
3.  Create a visual representation of the detected layout by drawing bounding boxes on the original image for easy verification and debugging.

This structured data will enable more accurate, context-aware OCR in the next step.

## 2. Proposed Project Structure

This step introduces a new set of output directories to store the results of the layout analysis.

```
document-preprocessing/
├── config.yaml
├── input/
├── output/
│   ├── 01_normalized/
│   ├── 02_preprocessed/
│   └── 03_layout_analysis/       # Output of this step
│       ├── json/                 # Structured layout data (one JSON per image)
│       └── visualizations/       # Images with layout bounding boxes overlaid
├── requirements.txt
└── src/
    ├── pipeline_manager.py
    └── steps/
        ├── ...
        ├── step_02_preprocess_image.py
        └── step_03_layout_analysis.py # Logic for this step
    └── utils/
        ...
```

## 3. Configuration (`config.yaml`)

The `config.yaml` will be extended to manage the layout analysis step. This allows for easy configuration of the ML model and other parameters.

```yaml
# ... (previous settings) ...

# Step 3: Layout Analysis Configuration
step_03_layout_analysis:
  # The input directory for this step, typically the final output from step 2.
  input_dir: "output/02_preprocessed/final"
  # The root output directory for this step's results.
  output_dir: "output/03_layout_analysis"
  
  # Configuration for the layout detection model.
  model_config:
    # We will use a Detectron2-based model from the LayoutParser model catalog.
    # PubLayNet is a large dataset for document layout analysis.
    # Other models can be found here: https://layout-parser.readthedocs.io/en/latest/notes/model_zoo.html
    type: "lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config"
    
    # A mapping of model-specific labels to custom, human-readable names.
    # Labels for the PubLayNet model are: 'text', 'title', 'list', 'table', 'figure'.
    label_map:
      text: "Text"
      title: "Title"
      list: "List"
      table: "Table"
      figure: "Figure"
```

## 4. Core Components & Logic

### `src/steps/step_03_layout_analysis.py`
- **Purpose:** Contains all business logic for detecting and processing document layouts. It will be designed to be stateless and called by the pipeline manager for each image.
- **Key Functions:**
    - `process_image(image_path: str, config: dict) -> tuple[str, str]`:
        - The main entry point for processing a single image.
        - Loads the `step_03_layout_analysis` configuration.
        - Initializes the layout model using `_initialize_model`.
        - Loads the image from `image_path` using OpenCV.
        - Uses the model to detect the layout (`model.detect(image)`).
        - For each detected block, stores the coordinates, type (using the `label_map`), and confidence score.
        - Calls `_save_layout_data` to save the structured data as a JSON file in the `output/03_layout_analysis/json/` directory.
        - Calls `_save_visualization` to draw the detected blocks onto the image and save it to `output/03_layout_analysis/visualizations/`.
        - Returns a tuple containing the path to the JSON data file and the visualization image file.
    - **Private Helper Functions:**
        - `_initialize_model(config: dict) -> 'layoutparser.models.Detectron2LayoutModel'`:
            - Takes the `model_config` dictionary as input.
            - Creates and returns an instance of a `layoutparser` model. The example uses `lp.Detectron2LayoutModel`.
            - Caches the model in memory to avoid reloading it for every image.
        - `_save_layout_data(layout: 'layoutparser.Layout', output_path: str, label_map: dict)`:
            - Converts the `layout` object into a serializable list of dictionaries.
            - Each dictionary represents a block and contains `{'box': [x1, y1, x2, y2], 'type': 'TypeName', 'score': 0.99}`.
            - Writes the data to a JSON file at `output_path`.
        - `_save_visualization(image: np.ndarray, layout: 'layoutparser.Layout', output_path: str)`:
            - Uses `layoutparser.draw_box` to render the detected bounding boxes on the input image.
            - Saves the visualized image to `output_path` using OpenCV.

### `src/pipeline_manager.py`
- **Purpose:** Extend the orchestration logic to include Step 3.
- **Updated Logic:**
    1. After Step 2 completes, the manager holds a list of file paths to the preprocessed images.
    2. It reads the `step_03_layout_analysis` configuration.
    3. For each preprocessed image, it creates a Dask `delayed` object wrapping a call to `steps.step_03_layout_analysis.process_image`.
    4. It executes all layout analysis tasks in parallel using `dask.compute()`.
    5. The results (a list of (json_path, viz_path) tuples) will be collected and passed to the next pipeline step (Step 4/5: OCR).

## 5. Dependencies and Setup

### `requirements.txt`
The following dependencies are required for this step and should be added to `requirements.txt`.

```
# For ML-based layout detection
layoutparser

# Backend for LayoutParser. This will install PyTorch as a dependency.
# Note: Check for PyTorch installation instructions specific to your system (CPU/GPU).
layoutparser[detectron2]
```

### External Dependencies
- **PyTorch:** `layoutparser[detectron2]` depends on PyTorch. While `pip` will install a default version, for optimal performance (especially with a GPU), it's recommended to install it manually by following the instructions on the official [PyTorch website](https://pytorch.org/get-started/locally/).
- **Python Version Compatibility:**
  - The goal is to use Python 3.13. However, as of late 2023, major scientific computing libraries like `PyTorch` and `Detectron2` may not have stable releases for the newest Python versions.
  - **Action:** It is critical to verify the compatibility of `PyTorch` and `Detectron2` with Python 3.13 at the time of implementation. If they are not yet compatible, it will be necessary to use a supported Python version (e.g., 3.10 or 3.11) for the project until the dependencies are updated. This is a practical constraint of relying on a complex ML ecosystem.

This plan provides a robust framework for integrating sophisticated layout analysis into the document processing pipeline.

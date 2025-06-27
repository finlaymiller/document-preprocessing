# Step 4: Image Enhancement (Optional) - Implementation Plan

This plan details the implementation of the fourth step of the OCR pre-processing pipeline, "Image Enhancement." This is an optional step designed to recover quality from badly degraded documents, such as those with poor contrast, warping from camera captures, or low resolution. The design follows the established modular and configurable pipeline pattern.

## 1. Goal

To apply advanced, computationally-intensive enhancement techniques to pre-processed images. This step is designed to run after standard pre-processing (Step 2) and before layout analysis (Step 3), as a higher quality source image will improve the accuracy of all subsequent steps. The enhancements include contrast correction, document de-warping, and super-resolution.

## 2. Proposed Project Structure

This step adds a new module for its logic and a corresponding directory structure for its outputs.

```
document-preprocessing/
├── config.yaml
├── input/
├── output/
│   ├── 01_normalized/
│   ├── 02_preprocessed/
│   ├── 03_layout_analysis/
│   └── 04_enhanced/              # Output of this step
│       ├── final/                # Final enhanced images
│       ├── contrast/             # (optional) Contrast-enhanced outputs
│       ├── dewarped/             # (optional) De-warped outputs
│       └── super_resolution/     # (optional) Super-resolution outputs
├── requirements.txt
└── src/
    ├── pipeline_manager.py
    └── steps/
        ├── ...
        ├── step_03_layout_analysis.py
        └── step_04_enhance_image.py # Logic for this step
    └── utils/
        ...
```

## 3. Configuration (`config.yaml`)

The `config.yaml` file will be extended with a section to control this optional step. The step can be enabled or disabled entirely.

```yaml
# ... (previous settings) ...

# Step 4: Image Enhancement Configuration
step_04_enhance_image:
  # This entire step is optional. Set to 'false' to skip.
  enabled: false
  # The input directory for this step, typically the final output from step 2.
  input_dir: "output/02_preprocessed/final"
  # The main output directory for the final enhanced images.
  output_dir: "output/04_enhanced/final"
  # If true, saves the output of each sub-step into its own folder for debugging.
  save_intermediate_steps: true

  # A pipeline of enhancement techniques to apply in order.
  pipeline:
    - type: "contrast_enhancement"
      enabled: true
      # 'clahe' (Contrast Limited Adaptive Histogram Equalization) is often better than simple 'equalizehist'.
      method: "clahe"
      clip_limit: 2.0
      tile_grid_size: [8, 8]

    - type: "dewarp"
      enabled: false # Typically disabled due to computational cost
      # Path to a pre-trained DocUNet model.
      model_path: "models/docunet_model.pth"

    - type: "super_resolution"
      enabled: false # Typically disabled due to computational cost
      # Path to a pre-trained ESRGAN model.
      model_path: "models/esrgan_model.pth"
      # The scale factor to increase resolution by (e.g., 2 or 4).
      scale_factor: 2
```

## 4. Core Components & Logic

### `src/steps/step_04_enhance_image.py`
- **Purpose:** Contains all business logic for the advanced image enhancement operations.
- **Key Functions:**
    - `process_image(image_path: str, config: dict) -> str`:
        - The main entry point for processing a single image through the enhancement pipeline.
        - Reads the image from `image_path` using OpenCV.
        - Iterates through the `pipeline` specified in the config. For each enabled step, it calls the corresponding function (e.g., `_apply_contrast_enhancement`, `_apply_dewarp`).
        - Handles saving of intermediate and final images based on `save_intermediate_steps`.
        - Returns the file path of the final, enhanced image.
    - **Private Helper Functions:**
        - `_apply_contrast_enhancement(image: np.ndarray, params: dict) -> np.ndarray`:
            - Applies the specified contrast method. If `clahe`, uses `cv2.createCLAHE`. If `equalizehist`, uses `cv2.equalizeHist`.
        - `_apply_dewarp(image: np.ndarray, params: dict) -> np.ndarray`:
            - Initializes the de-warping model (e.g., DocUNet) on first run and caches it.
            - Pre-processes the image to fit the model's input requirements.
            - Runs inference to get the de-warped image.
            - Post-processes the output back to a standard image format.
        - `_apply_super_resolution(image: np.ndarray, params: dict) -> np.ndarray`:
            - Initializes the super-resolution model (e.g., ESRGAN) and caches it.
            - Runs inference to generate a high-resolution version of the image.

### `src/pipeline_manager.py`
- **Purpose:** To conditionally execute Step 4.
- **Updated Logic:**
    1. After Step 2 completes, the manager checks if `step_04_enhance_image.enabled` is `true` in the configuration.
    2. **If enabled:**
        - It uses the output from Step 2 as the input for Step 4.
        - It creates Dask `delayed` objects for `steps.step_04_enhance_image.process_image`.
        - It executes the enhancement tasks in parallel.
        - The output of this step (the list of enhanced image paths) becomes the input for Step 3 (Layout Analysis).
    3. **If disabled:**
        - It proceeds directly from Step 2 to Step 3, using the pre-processed images as input for layout analysis, thus skipping this step entirely.

## 5. Dependencies and Setup

### `requirements.txt`
The following dependencies would be required and should be added to `requirements.txt` if this step is used.

```
# For ML models (PyTorch backend)
# Installation should be done carefully, following official PyTorch instructions.
torch
torchvision

# A library or implementation for ESRGAN. Example placeholder:
# basicsr # A popular open-source image/video restoration toolbox

# A library or implementation for DocUNet (if available, otherwise via git submodule)
```

### External Dependencies & Models
- **Pre-trained Models:** This step requires pre-trained models (`.pth` files) for de-warping and super-resolution. A `models/` directory should be created in the project root to store them. The user will be responsible for obtaining these models. The `README.md` should link to download locations (e.g., from the official ESRGAN and DocUNet repositories).
- **ML Environment Complexity:** Similar to Step 3, using these models introduces significant complexity.
    - **GPU Support:** For acceptable performance, a CUDA-enabled GPU is strongly recommended. The PyTorch installation must be matched to the system's CUDA version.
    - **Python Version:** Compatibility between PyTorch and the target Python version (e.g., 3.13) must be verified. The project may need to lock to an older Python version (e.g., 3.10) if the ML libraries do not yet support the latest release.

This plan outlines a powerful but optional enhancement step that can be integrated into the pipeline to handle challenging documents, while allowing users to bypass it to avoid the heavy computational and setup costs.

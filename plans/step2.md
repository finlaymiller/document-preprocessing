# Step 2: Image Preprocessing - Implementation Plan

This plan details the implementation of the second step of the OCR pre-processing pipeline, "Image Preprocessing," as outlined in the master plan. This step is critical for enhancing image quality to maximize OCR accuracy. The design prioritizes configurability, allowing each preprocessing technique to be enabled, disabled, and tuned independently.

## 1. Goal

To apply a series of image enhancement techniques to the normalized images produced by Step 1. These techniques—grayscale conversion, denoising, thresholding, and deskewing—are designed to clean the images and make text features more prominent for the OCR engine. The step will be highly configurable and will optionally save intermediate outputs for debugging and quality assurance.

## 2. Proposed Project Structure

This step introduces a new module for its logic and a corresponding directory structure within `output/` to store its results, including intermediate files for verification.

```
document-preprocessing/
├── config.yaml
├── input/
├── output/
│   ├── 01_normalized/
│   └── 02_preprocessed/          # Output of this step
│       ├── final/                # Final processed images
│       ├── grayscale/            # (optional) Grayscale outputs
│       ├── denoised/             # (optional) Denoised outputs
│       ├── thresholded/          # (optional) Thresholded outputs
│       └── deskewed/             # (optional) Deskewed outputs
├── requirements.txt
└── src/
    ├── pipeline_manager.py
    └── steps/
        ├── __init__.py
        ├── step_01_normalize_input.py
        └── step_02_preprocess_image.py # Logic for this step
    └── utils/
        ...
```

## 3. Configuration (`config.yaml`)

The `config.yaml` file will be extended with a new section to control the behavior of this preprocessing step. This allows for fine-tuning without any code changes.

```yaml
# ... (previous settings for app, dask, step_01) ...

# Step 2: Image Preprocessing Configuration
step_02_preprocess_image:
  # The input directory for this step, typically the output from step 1.
  input_dir: "output/01_normalized"
  # The main output directory for the final preprocessed images.
  output_dir: "output/02_preprocessed/final"
  # If true, saves the output of each sub-step into its own folder for debugging.
  save_intermediate_steps: true

  # Each sub-step can be enabled and configured individually.
  # The pipeline will execute them in the order defined here.
  pipeline:
    - type: "grayscale"
      enabled: true

    - type: "denoise"
      enabled: true
      # Gaussian blur kernel size. Must be odd numbers.
      kernel_size: [5, 5]

    - type: "threshold"
      enabled: true
      # Method can be 'adaptive_gaussian', 'simple', or 'otsu'.
      method: "adaptive_gaussian"
      # Block size for adaptive thresholding.
      block_size: 11
      # Constant subtracted from the mean.
      c: 2

    - type: "deskew"
      enabled: true
```

## 4. Core Components & Logic

### `src/steps/step_02_preprocess_image.py`
- **Purpose:** This module will contain all the business logic for the image preprocessing operations. It will be designed to be stateless and easily callable by the pipeline manager.
- **Key Functions:**
    - `process_image(image_path: str, config: dict) -> str`:
        - This will be the main entry point for processing a single image through the entire preprocessing pipeline.
        - It reads the image from `image_path` using OpenCV.
        - It loads the `step_02_preprocess_image` configuration.
        - It iterates through the `pipeline` specified in the config. For each enabled step, it calls the corresponding function (e.g., `_apply_grayscale`, `_apply_denoise`).
        - If `save_intermediate_steps` is `true`, it saves the result of each operation to the appropriate subdirectory (e.g., `output/02_preprocessed/grayscale/`).
        - It saves the final processed image to the `output_dir`.
        - Returns the file path of the final, processed image.
    - **Private Helper Functions:**
        - `_apply_grayscale(image: np.ndarray) -> np.ndarray`: Converts a BGR image to grayscale.
        - `_apply_denoise(image: np.ndarray, params: dict) -> np.ndarray`: Applies Gaussian blur based on `kernel_size`.
        - `_apply_threshold(image: np.ndarray, params: dict) -> np.ndarray`: Applies the configured thresholding method.
        - `_apply_deskew(image: np.ndarray) -> np.ndarray`: Calculates the skew angle and rotates the image to correct it, as described in the master plan.

### `src/pipeline_manager.py`
- **Purpose:** To extend the orchestration logic to include Step 2.
- **Updated Logic:**
    1. After executing Step 1, the manager holds a list of file paths for the normalized images.
    2. It will then read the `step_02_preprocess_image` configuration.
    3. For each normalized image, it will create a Dask `delayed` object that wraps a call to `steps.step_02_preprocess_image.process_image`.
    4. It will use `dask.compute()` to execute all preprocessing tasks in parallel.
    5. The resulting list of preprocessed image paths will be collected to be passed to the next pipeline step (e.g., Layout Analysis).

## 5. Dependencies and Setup

### `requirements.txt`
The following dependencies are required for this step and should be added to `requirements.txt`.

```
# For image processing
opencv-python
numpy
scikit-image # For more advanced deskew or image analysis if needed later
```

### External Dependencies
This step relies on the Python packages above and does not introduce new system-level dependencies beyond what was needed for Step 1. The use of Python 3.13 will be ensured for development.

This plan provides a clear and robust foundation for implementing the image preprocessing stage, ensuring it is both powerful and flexible.

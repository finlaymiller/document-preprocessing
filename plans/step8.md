# Step 8: Quality Assurance (QA) & Retry Logic - Implementation Plan

This plan details the implementation of the eighth step, "Quality Assurance (QA) & Retry Logic." Unlike previous steps that follow a linear data flow, this step acts as a control system. It evaluates the quality of the OCR output and can trigger reprocessing of a document with alternative configurations to improve results. This makes the pipeline more robust and adaptive to varying document quality.

## 1. Goal

To automate the assessment of OCR output quality and orchestrate re-processing for low-quality results. The primary goals are:
1.  **Evaluate Quality:** Analyze the word-level confidence scores from Tesseract's TSV output (from Step 5) to calculate a quality score for each document page.
2.  **Make a Decision:** Based on a configurable threshold, decide if a page's quality is acceptable or if it needs to be re-processed.
3.  **Implement Retry Strategy:** If re-processing is needed, run a series of alternative processing configurations (e.g., different thresholding methods, different Tesseract PSM modes) in a predefined order.
4.  **Select Best Result:** After all attempts, select the version of the output with the highest quality score as the definitive result for that page to be passed to downstream steps (like Post-OCR Cleanup).

## 2. Proposed Project Structure & Data Flow

This step doesn't introduce a simple new directory in `output/`. Instead, it introduces a "feedback loop" into the pipeline orchestration. The `pipeline_manager` will be significantly updated to manage this loop.

```
document-preprocessing/
├── config.yaml
├── ...
├── output/
│   ├── ... (intermediate steps 01-07)
│   └── 08_qa_report/             # Output of this step
│       ├── summary.json          # A summary of QA results and retries for all docs
│       └── visualizations/       # (Optional) Bounding box visualizations for low-conf words
└── src/
    ├── pipeline_manager.py         # Will contain the core retry loop logic
    └── steps/
        ├── ...
        └── step_08_quality_assurance.py # Logic for evaluation and visualization
```

## 3. Configuration (`config.yaml`)

This step's configuration is crucial. It defines the "contract" for what is considered an acceptable output and what to do if it's not.

```yaml
# ... (previous settings) ...

# Step 8: Quality Assurance Configuration
step_08_quality_assurance:
  enabled: true

  # The primary quality metric.
  # 'average_confidence': The average word confidence score on the page.
  # 'low_confidence_word_ratio': The ratio of words with confidence below a threshold.
  metric: "average_confidence"
  
  # The threshold for the chosen metric. If a page's score is below this,
  # the retry strategies will be triggered.
  # For 'average_confidence', a value like 85 (out of 100) is a good start.
  quality_threshold: 85
  
  # The confidence level below which a single word is considered "low confidence".
  # Used for 'low_confidence_word_ratio' and for visualizations.
  low_confidence_threshold: 60

  # If true, generates images with low-confidence words highlighted with bounding boxes.
  generate_visualizations: true
  output_dir: "output/08_qa_report"

  # Retry Strategies: A list of configuration overrides to try in order.
  # The pipeline will re-run steps 2 through 5 with these new settings.
  # The name of each strategy should be descriptive.
  retry_strategies:
    - name: "aggressive_binarization"
      # This override will be temporarily applied to the main config for the retry attempt.
      # It modifies parameters from Step 2.
      step_02_preprocess_image:
        pipeline:
          - type: "grayscale"
            enabled: true
          - type: "denoise"
            enabled: false
          - type: "threshold"
            enabled: true
            method: "otsu" # Try Otsu's binarization instead of adaptive
    
    - name: "assume_sparse_text"
      # This override modifies parameters from Step 5 (OCR).
      step_05_ocr:
        tesseract_config:
          psm: 11 # Assume a single column of text of variable sizes.

    - name: "assume_single_block"
      # Another OCR strategy.
      step_05_ocr:
        tesseract_config:
          psm: 6 # Assume a single uniform block of text.

```

## 4. Core Components & Logic

### `src/steps/step_08_quality_assurance.py`
- **Purpose:** Contains the logic for evaluating a single document's OCR output.
- **Key Functions:**
    - `evaluate_ocr_quality(tsv_path: str, config: dict) -> dict`:
        - Reads the Tesseract `.tsv` file into a pandas DataFrame.
        - Cleans the data (e.g., removes rows that don't represent actual words).
        - Calculates the quality score based on the `metric` defined in the config (e.g., `df['conf'].mean()`).
        - Returns a dictionary containing the calculated score, the metric used, and other relevant stats (e.g., number of low-confidence words).
    - `generate_confidence_visualization(image_path: str, tsv_path: str, output_path: str, config: dict)`:
        - Loads the image.
        - Reads the `.tsv` file to get the bounding boxes (`left`, `top`, `width`, `height`) and confidence (`conf`) for each word.
        - Draws a red rectangle around words where `conf` is below `low_confidence_threshold`.
        - Saves the resulting image to the `visualizations` directory.

### `src/pipeline_manager.py` (Major Refactoring Required)
- **Purpose:** The `PipelineManager` will no longer execute a simple linear chain. It will be refactored to manage the QA and retry loop for each document.
- **New High-Level Logic per Document:**
    1.  **Initial Run:** Process a single document through the standard pipeline (Steps 1-7) as defined in the base `config.yaml`.
    2.  **Check QA:** After Step 5 (OCR), if QA is enabled, the manager pauses the main flow.
    3.  **Evaluate:** It calls `step_08_quality_assurance.evaluate_ocr_quality` on the resulting `.tsv` file.
    4.  **Decision:** It compares the result to the `quality_threshold`.
        - **If Acceptable:** The initial OCR output is considered "good." The manager stores its path and proceeds to Step 6/7.
        - **If Unacceptable:** The manager begins the retry loop.
    5.  **Retry Loop:**
        - For each strategy in `retry_strategies`:
            a. **Create Override Config:** Create a temporary, deep copy of the main configuration. Merge the strategy's overrides into it.
            b. **Re-run Sub-pipeline:** Re-execute the relevant parts of the pipeline (e.g., Steps 2-5) using the temporary config. This will produce a new set of OCR outputs (`.tsv`, `.txt`, `.hocr`).
            c. **Re-evaluate:** Evaluate the new `.tsv` file.
            d. **Store Result:** Store the new score and the paths to the new output files.
    6.  **Select Best:** After trying all strategies, compare the scores from all attempts (including the initial one). Select the set of OCR outputs that yielded the highest score.
    7.  **Proceed:** Use the "best" selected OCR outputs as the input for the subsequent pipeline steps (Step 6 Post-OCR Cleanup and Step 7 Output Formatting).
    8.  **Reporting:** Log the outcome (e.g., "Document X passed on initial run" or "Document Y passed after 'aggressive_binarization' strategy") and save any visualizations.

- **Dask Integration:** The entire process for a single document (initial run + potential retry loop) can be wrapped in a single Dask `delayed` task. This ensures that while each document might go through a complex, stateful process, multiple documents are still processed in parallel.

## 5. Dependencies

No major new dependencies are required if `pandas` is already included from a previous step.

```
# For reading and analyzing TSV data efficiently
pandas
```

This implementation transforms the pipeline from a static, one-shot process into a dynamic and adaptive system, significantly improving its real-world performance on diverse and challenging documents.

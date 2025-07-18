# Step 9: Parallelization with Dask - Implementation Plan

This plan details the implementation of the core pipeline orchestrator, `pipeline_manager.py`. This component is the brain of the system, responsible for running the entire sequence of processing steps (1-8) in parallel for a batch of documents. It leverages the Dask library to build and execute a dynamic task graph, handling conditional logic, complex inter-step dependencies, and the QA-driven retry loop.

## 1. Goal

To create a robust, scalable, and configurable pipeline manager that can:
1.  Read a central configuration file to control the behavior of the entire pipeline.
2.  Discover all input documents to be processed.
3.  For each document, dynamically execute the sequence of enabled steps, respecting their complex dependencies.
4.  Manage the state for each document, including the paths to all intermediate and final files.
5.  Implement the Quality Assurance feedback loop, re-processing documents with alternative configurations to improve results.
6.  Use Dask to execute the processing for all documents in parallel, maximizing the use of available CPU cores.
7.  Provide clear logging and a final summary of the batch processing run.

## 2. Proposed Project Structure

This plan focuses on the central `pipeline_manager.py` module, which orchestrates the calls to all `step_*.py` modules.

```
document-preprocessing/
├── config.yaml
├── ...
└── src/
    ├── __init__.py
    ├── main.py
    ├── pipeline_manager.py         # This is the core component described in this plan
    ├── steps/
    │   ├── step_01_normalize_input.py
    │   ├── step_02_preprocess_image.py
    │   ├── ...
    │   └── step_08_quality_assurance.py
    └── utils/
        ...
```

## 3. Configuration (`config.yaml`)

The `pipeline_manager.py` will be configured by the `dask` section of the `config.yaml`.

```yaml
# ... (all other step configurations) ...

# Dask configuration for parallel processing
dask:
  # The scheduler to use. 'threads' is good for I/O-bound tasks with GIL-releasing
  # libraries (like Pillow, NumPy). 'processes' is for CPU-bound tasks (heavy computation).
  # 'distributed' allows scaling across multiple machines.
  scheduler: "threads"
  # Number of parallel workers. Use "auto" to let Dask decide based on CPU cores.
  num_workers: "auto"
```

## 4. Core Components & Logic (`pipeline_manager.py`)

The manager will be implemented as a class that encapsulates the entire pipeline orchestration logic.

### `PipelineManager` Class

#### **`__init__(self, config_path: str)`**
-   Loads the `config.yaml` using `utils.config.load_config`.
-   Performs basic validation on the configuration.
-   Initializes the Dask configuration based on the `dask` section of the config. Sets the number of workers and the default scheduler.

#### **`run(self)`**
-   The main public method that executes the entire pipeline.
-   **1. Discover Files:** Uses `utils.files.find_files` to get a list of all documents in the `input_dir` specified in the Step 1 config.
-   **2. Build Dask Graph:**
    -   Creates an empty list, `tasks`.
    -   Iterates through each discovered `document_path`.
    -   For each document, it creates a Dask `delayed` object that wraps a call to the core processing method, `_process_document(document_path)`.
    -   Appends this `delayed` task to the `tasks` list.
-   **3. Execute Pipeline:**
    -   Calls `dask.compute(*tasks, scheduler=self.dask_scheduler)`. This triggers the parallel execution of the entire pipeline for all documents.
-   **4. Log Summary:** After computation is complete, it logs a summary of the results (e.g., number of documents processed, number of retries, final output locations).

### Core Processing Logic: `_process_document`

This is the most critical function. It defines the complete, stateful processing logic for a *single document*. It will be wrapped by `dask.delayed` so that it can run in parallel for many documents.

#### **`_process_document(self, doc_path: str) -> dict`**
1.  **State Management:**
    -   At the beginning of the function, a "state dictionary" or a `dataclass` is created for the document. This object will be populated with the file paths generated by each step.
    -   Example `doc_state = {'original_path': doc_path, 'results': {}}`.

2.  **Step-by-Step Execution:**
    -   The function calls the `run_step` (or `process_*`) function from each step's module in the correct order.
    -   After each call, it stores the returned file path(s) in the `doc_state` object.
    -   It uses the `doc_state` to fetch the correct inputs for the next step.

    ```python
    # Psuedocode for the flow inside _process_document
    
    # Step 1: Normalize
    normalized_paths = step_01.run(doc_path, self.config)
    doc_state['results']['step_01'] = normalized_paths
    
    # Process each page produced from the original document
    for page_path in normalized_paths:
        page_state = {'normalized_image': page_path}
        
        # Step 2: Preprocess
        preprocessed_image = step_02.run(page_state['normalized_image'], self.config)
        page_state['preprocessed_image'] = preprocessed_image

        # Step 4 (Conditional): Enhance
        image_for_layout = page_state['preprocessed_image']
        if self.config.step_04.enabled:
            enhanced_image = step_04.run(image_for_layout, self.config)
            image_for_layout = enhanced_image
        page_state['image_for_layout'] = image_for_layout
        
        # Step 3: Layout Analysis
        layout_json = step_03.run(page_state['image_for_layout'], self.config)
        page_state['layout_json'] = layout_json

        # --- QA & Retry Sub-Pipeline ---
        # This is the complex loop from step8.md
        best_ocr_outputs, best_score = self._run_qa_and_ocr_sub_pipeline(page_state)
        page_state['best_ocr_outputs'] = best_ocr_outputs # (path_to_txt, path_to_tsv, ...)
        
        # Step 6: Post-OCR Cleanup
        if self.config.step_06.enabled:
            structured_output = step_06.run(
                ocr_outputs=page_state['best_ocr_outputs'],
                layout_path=page_state['layout_json'],
                config=self.config
            )
            page_state['structured_output'] = structured_output

        # Step 7: Final Output Formatting
        if self.config.step_07.enabled:
            final_files = step_07.run(...)
            page_state['final_files'] = final_files

    return doc_state
    ```

### QA & Retry Sub-Pipeline: `_run_qa_and_ocr_sub_pipeline`

This private method encapsulates the logic from `step8.md`.

1.  **Initial Attempt:**
    -   Run Step 5 (OCR) using the standard configuration.
    -   Run Step 8's `evaluate_ocr_quality` function on the resulting `.tsv` file.
    -   Store this attempt's outputs and its quality score.

2.  **Decision & Retry Loop:**
    -   If the score is below `quality_threshold`, iterate through the `retry_strategies` from the config.
    -   For each strategy:
        -   Create a temporary, overridden configuration dictionary.
        -   **Re-run the sub-pipeline:** This is critical. A retry might need to re-run image preprocessing to test a different binarization method. The function must re-call `step_02`, `step_04` (if enabled), `step_03`, and finally `step_05` using the temporary config.
        -   Evaluate the quality of the new OCR output.
        -   Keep track of the attempt with the highest score.

3.  **Return Best:**
    -   After all attempts, return the file paths for the OCR outputs (`.txt`, `.tsv`, `.hocr`) that correspond to the highest-achieved quality score.

## 5. Summary

This implementation of the `PipelineManager` acts as the central nervous system of the entire application. By encapsulating the complex, conditional, and stateful logic for processing a single document within a function (`_process_document`) and then using Dask to apply that function across all documents in parallel, this design achieves all the project's goals. It is:
-   **Modular:** Each step's logic remains isolated in its own module.
-   **Configurable:** The entire flow is controlled by a single `config.yaml`.
-   **Robust:** The QA and retry loop makes it adaptive to input quality.
-   **Scalable:** Dask provides efficient, parallel execution on multi-core machines.

This architecture provides a powerful and flexible foundation for the document processing pipeline.

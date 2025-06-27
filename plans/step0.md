# Step 0: Project Professionalization and Automation Plan

This plan outlines the foundational steps required to turn the "Document Preprocessing Pipeline" into a professional, maintainable, and automated open-source project. It covers dependency management, code quality, continuous integration, documentation, and repository standards. This step should be implemented before or in parallel with the other pipeline steps.

## 1. Goal

To establish a robust, developer-friendly, and automated project environment that ensures code quality, simplifies setup, and encourages collaboration.

## 2. Comprehensive `README.md`

The `README.md` is the entry point for the project. It should be comprehensive and clear.

**Action:** Create/overwrite the main `README.md` with the following sections:
- **Project Title and Banner:** A clear title and a brief one-sentence description.
- **Overview:** A short paragraph explaining what the project does and its key features.
- **Pipeline Diagram:** A visual representation of the pipeline flow. A Mermaid diagram is recommended.
- **Features:** A bulleted list of key capabilities (e.g., PDF/Image support, configurable steps, parallel processing, QA loop).
- **Installation:**
    - **Prerequisites:** List all system-level dependencies (`poppler`, `tesseract-ocr`) with installation commands for macOS, Debian/Ubuntu, and Windows.
    - **Repository Setup:** `git clone`, `cd ...`.
    - **Python Environment:** Recommend using a virtual environment (`venv`).
    - **Python Dependencies:** `pip install -r requirements.txt`.
    - **ML Models:** Instructions on where to download the required models (`ESRGAN`, `DocUNet`, `SymSpell dictionary`) and where to place them (in a `models/` directory).
- **Configuration:** Explain the `config.yaml`, highlighting key parameters for each step. Provide a sample configuration.
- **Usage:**
    - How to place files in the `input/` directory.
    - How to run the pipeline: `python src/main.py`.
    - How to inspect outputs in the `output/` directory.
- **Project Structure:** A brief explanation of the key directories (`src`, `input`, `output`, `config.yaml`).
- **Contributing:** A link to `CONTRIBUTING.md`.
- **License:** A link to the `LICENSE` file.

### Pipeline Diagram (Mermaid Example)

```mermaid
graph TD
    A[Input Files <br/>(PDFs, Images)] --> B(Step 1: Normalize);
    B --> C(Step 2: Preprocess Image);
    C --> D{Optional: Enhance?};
    D -- Yes --> E[Step 4: Enhance Image];
    D -- No --> F[Step 3: Layout Analysis];
    E --> F;
    F --> G(Step 5: OCR);
    G --> H{QA Check};
    H -- Passes --> I[Step 6: Post-OCR Cleanup];
    H -- Fails --> J(Retry with new params);
    J --> C;
    I --> K[Step 7: Final Output];
    K --> L[Structured Data <br/>(JSON, Searchable PDF)];
```

## 3. Dependency Management

**Action:** Create two separate requirements files.

- **`requirements.txt`:** For core application dependencies. These should have pinned versions for reproducibility.
  ```
  # Base dependencies
  PyYAML==6.0.1
  rich==13.7.0
  # PDF/Image
  pdf2image==1.17.0
  Pillow==10.2.0
  # CV & ML
  opencv-python==4.9.0.80
  numpy==1.26.4
  scikit-image==0.22.0
  pytesseract==0.3.10
  # Layout Analysis (requires careful PyTorch installation)
  layoutparser==0.3.4
  # Recommend installing torch separately first, but include for completeness
  # torch==2.2.1 
  # torchvision==0.17.1
  # For layoutparser[detectron2], Detectron2 must be installed manually.
  # Post-processing & Output
  symspellpy-bp==6.7.7
  pandas==2.2.1
  markdown-it-py==3.0.0
  PyMuPDF==1.23.26
  # Parallelization
  dask[complete]==2024.2.0
  ```
- **`requirements-dev.txt`:** For development, testing, and code quality tools.
  ```
  -r requirements.txt
  # Code Quality
  pre-commit==3.6.2
  black==24.2.0
  ruff==0.2.2
  isort==5.13.2
  mypy==1.8.0
  # Testing
  pytest==8.0.2
  # Documentation
  Sphinx==7.2.6
  ```

## 4. Comprehensive `.gitignore`

**Action:** Create a `.gitignore` file to exclude common Python artifacts, environment files, OS files, and project-specific outputs.

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs / Editors
.idea/
.vscode/
*.swp

# OS-specific
.DS_Store
Thumbs.db

# Project-specific
/input/*
/output/*
/models/*
config.yaml
# Don't ignore the directories, but ignore their contents to keep them
!/input/.gitkeep
!/output/.gitkeep
!/models/.gitkeep
# Don't ignore the sample config
!config.sample.yaml
```

## 5. Pre-Commit Hooks

**Action:** Set up `pre-commit` to automate code formatting and linting.

1.  Create a `.pre-commit-config.yaml` file.
    ```yaml
    repos:
    -   repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.5.0
        hooks:
        -   id: check-yaml
        -   id: end-of-file-fixer
        -   id: trailing-whitespace
        -   id: check-added-large-files
            args: ['--maxkb=1024'] # 1 MB
    -   repo: https://github.com/psf/black
        rev: 24.2.0
        hooks:
        -   id: black
    -   repo: https://github.com/pycqa/isort
        rev: 5.13.2
        hooks:
        -   id: isort
    -   repo: https://github.com/charliermarsh/ruff-pre-commit
        rev: v0.2.2
        hooks:
        -   id: ruff
            args: [--fix, --exit-non-zero-on-fix]
    -   repo: https://github.com/pre-commit/mirrors-mypy
        rev: v1.8.0
        hooks:
        -   id: mypy
    ```
2.  Add instructions to the `README.md` on how to install and set it up: `pre-commit install`.

## 6. GitHub Actions for Continuous Integration (CI)

**Action:** Create a CI workflow file at `.github/workflows/ci.yml`.

-   **Triggers:** On push/pull_request to `main` branch.
-   **Jobs:**
    -   **Linting & Formatting:** A job to run all `pre-commit` checks. This is a fast way to fail if there are style issues.
    -   **Testing:** A job that runs the full test suite (`pytest`). This should run on a matrix of:
        -   `os`: `ubuntu-latest`, `macos-latest`, `windows-latest`
        -   `python-version`: `3.10`, `3.11` (given the ML library constraints mentioned in other plans).
-   **Workflow Steps:**
    1.  Checkout code.
    2.  Set up Python version.
    3.  Install system dependencies (Poppler, Tesseract).
    4.  Install Python dependencies (`pip install -r requirements-dev.txt`).
    5.  Run linter job / test job.

## 7. Testing Strategy

**Action:** Propose and create a testing infrastructure.

1.  Create a `tests/` directory at the project root.
2.  Inside `tests/`, mirror the `src/` structure: `tests/utils/`, `tests/steps/`.
3.  **Unit Tests:** Create `tests/utils/test_files.py` to test file utilities. Write tests for individual image processing functions in `tests/steps/`.
4.  **Integration Tests:** Create `tests/test_pipeline_manager.py` to test the orchestration of a simple, two-step pipeline. Use a small, sample set of input files and a minimal `config.yaml` for testing.
5.  Use `pytest` as the test runner.

## 8. Documentation Standards

**Action:** Enforce and standardize documentation.

1.  **Docstrings:** All modules, classes, and functions must have docstrings following the specified format (NumPy/SciPy style).
2.  **Code Comments:** Use inline comments only for non-obvious logic.
3.  **Type Hinting:** All function signatures and variables should have type hints. This is essential for `mypy`.
4.  **(Optional) Sphinx Docs:** Suggest setting up Sphinx in a `docs/` directory to auto-generate HTML documentation from docstrings.

## 9. License and Contribution Files

**Action:** Add standard open-source repository files.

1.  **`LICENSE`:** Add a `LICENSE` file. Recommend a permissive license like `MIT` or `Apache-2.0`.
2.  **`CONTRIBUTING.md`:** Add a file that explains:
    -   How to set up the development environment.
    -   The workflow for submitting a pull request (fork, branch, PR).
    -   Code style and testing expectations.

By implementing this plan, the project will have a professional foundation that makes it easier to develop, maintain, and contribute to.

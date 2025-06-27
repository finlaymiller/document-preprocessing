# Contributing to the Document Preprocessing Pipeline

First off, thank you for considering contributing! Your help is appreciated.

## Development Setup

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/document-preprocessing.git
    cd document-preprocessing
    ```
3.  **Set up a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```
4.  **Install dependencies**:
    ```bash
    pip install -r requirements-dev.txt
    ```
5.  **Install pre-commit hooks**:
    ```bash
    pre-commit install
    ```

## Contribution Workflow

1.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b your-feature-name
    ```
2.  **Make your changes**. Ensure you add or update tests as appropriate.
3.  **Commit your changes**. The pre-commit hooks will run automatically.
4.  **Push to your branch**:
    ```bash
    git push origin your-feature-name
    ```
5.  **Open a Pull Request** from your fork to the `main` branch of the original repository. Provide a clear description of your changes.

## Code Style and Quality

-   This project uses `black` for formatting, `isort` for import sorting, and `ruff` for linting. The pre-commit hooks handle this automatically.
-   All functions and classes should have type hints and NumPy-style docstrings.
-   All new features should have corresponding tests. 
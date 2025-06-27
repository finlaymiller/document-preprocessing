import logging
from typing import List

from dask import compute, delayed
from dask.distributed import Client, LocalCluster

from steps.step_01_normalize_input import normalize_file
from utils.config import load_config
from utils.files import find_files


class PipelineManager:
    """
    Orchestrates the document processing pipeline.
    """

    def __init__(self, config_path: str):
        """
        Initialize the PipelineManager.

        Parameters
        ----------
        config_path : str
            Path to the configuration file.
        """
        self.config = load_config(config_path)
        self.logger = logging.getLogger(self.config.get("app_name", "pipeline"))
        self._setup_dask()

    def _setup_dask(self) -> None:
        """
        Set up the Dask client.
        """
        dask_config = self.config.get("dask", {})
        num_workers = dask_config.get("num_workers", "auto")
        if num_workers == "auto":
            cluster = LocalCluster()
        else:
            cluster = LocalCluster(n_workers=int(num_workers))
        self.client = Client(cluster)
        self.logger.info(f"Dask client started: {self.client.dashboard_link}")

    def run(self) -> None:
        """
        Run the entire document processing pipeline.
        """
        self.logger.info("Starting pipeline...")
        normalized_files = self._run_step_01_normalize_input()
        self.logger.info(
            f"Step 1 (Normalize Input) completed. Produced {len(normalized_files)} files."
        )
        # Subsequent steps will be added here
        self.logger.info("Pipeline finished.")
        self.client.close()

    def _run_step_01_normalize_input(self) -> List[str]:
        """
        Run the input normalization step of the pipeline.

        Returns
        -------
        List[str]
            A list of paths to the normalized image files.
        """
        self.logger.info("Running Step 1: Normalize Input...")
        step_config = self.config["step_01_normalize_input"]
        input_dir = step_config["input_dir"]
        output_dir = step_config["output_dir"]
        pdf_dpi = step_config["pdf_dpi"]
        output_format = step_config["output_format"]

        # Supported extensions for this step, can be expanded in config later
        supported_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
        input_files = list(find_files(input_dir, supported_extensions))
        self.logger.info(f"Found {len(input_files)} files to process in '{input_dir}'.")

        tasks = [
            delayed(normalize_file)(
                file_path=f,
                output_dir=output_dir,
                pdf_dpi=pdf_dpi,
                output_format=output_format,
            )
            for f in input_files
        ]

        results = compute(*tasks)

        # Flatten the list of lists that may result from PDF processing
        processed_files = []
        for res in results:
            if isinstance(res, list):
                processed_files.extend(res)
            else:
                processed_files.append(res)

        return processed_files

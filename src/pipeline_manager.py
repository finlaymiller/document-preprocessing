import logging
from typing import List

from dask import compute, delayed
from dask.distributed import Client, LocalCluster

from steps.step_01_normalize_input import process_file as normalize_file
from steps.step_02_preprocess_image import process_image
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
        self.logger = logging.getLogger(__name__)
        self.dask_enabled = self.config.get("dask", {}).get("enabled", True)
        self.client = None

        if self.dask_enabled:
            self._setup_dask()

    def _setup_dask(self) -> None:
        """
        Set up the Dask client.
        """
        dask_config = self.config.get("dask", {})
        num_workers = dask_config.get("n_workers", -1)

        if num_workers == -1:
            cluster = LocalCluster()
        else:
            cluster = LocalCluster(n_workers=int(num_workers))

        self.client = Client(cluster)
        self.logger.info(f"Dask client started: {self.client.dashboard_link}")

    def run(self) -> None:
        """
        Run the entire document processing pipeline.
        """
        pipeline_steps = self.config.get("app", {}).get("pipeline", [])
        self.logger.info(f"Starting pipeline with steps: {pipeline_steps}")

        # this will hold the output file paths from the previous step
        step_input_files = None

        if "step_01_normalize_input" in pipeline_steps:
            step_input_files = self._run_step_01_normalize_input()
            self.logger.info(
                f"Step 1 (Normalize Input) completed. Produced {len(step_input_files)} files."
            )

        if "step_02_preprocess_image" in pipeline_steps:
            if not step_input_files:
                raise ValueError(
                    "Cannot run step_02_preprocess_image without output from the previous step."
                )
            step_input_files = self._run_step_02_preprocess_image(step_input_files)
            self.logger.info(
                f"Step 2 (Preprocess Image) completed. Produced {len(step_input_files)} files."
            )

        # Subsequent steps will be added here
        self.logger.info("Pipeline finished.")
        if self.client:
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

        # supported extensions can be configured or are hardcoded
        supported_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
        input_files = list(find_files(input_dir, supported_extensions))
        self.logger.info(f"Found {len(input_files)} files to process in '{input_dir}'.")

        tasks = [
            delayed(normalize_file)(file_path=f, config=self.config)
            for f in input_files
        ]

        if self.dask_enabled:
            results = compute(*tasks)
        else:
            results = [task.compute() for task in tasks]

        # flatten the list of lists that may result from pdf processing
        processed_files = []
        for res in results:
            if isinstance(res, list):
                processed_files.extend(res)
            else:
                processed_files.append(res)

        return processed_files

    def _run_step_02_preprocess_image(self, input_files: List[str]) -> List[str]:
        """
        Run the image preprocessing step of the pipeline.

        Parameters
        ----------
        input_files : List[str]
            A list of paths to the normalized image files from the previous step.

        Returns
        -------
        List[str]
            A list of paths to the preprocessed image files.
        """
        self.logger.info("Running Step 2: Preprocess Image...")

        tasks = [
            delayed(process_image)(image_path=f, config=self.config)
            for f in input_files
        ]

        if self.dask_enabled:
            results = compute(*tasks)
        else:
            results = [task.compute() for task in tasks]

        return list(results)

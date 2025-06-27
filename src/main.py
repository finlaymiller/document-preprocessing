import logging
import time

from rich.logging import RichHandler

from pipeline_manager import PipelineManager


def setup_logging(log_level: str) -> None:
    """
    Set up logging using rich for pretty console output.

    Parameters
    ----------
    log_level : str
        The logging level to use (e.g., 'INFO', 'DEBUG').
    """
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def main() -> None:
    """
    Main entry point for the document processing pipeline.
    """
    setup_logging("INFO")
    logger = logging.getLogger()

    start_time = time.time()
    logger.info("Starting the document processing pipeline...")

    try:
        manager = PipelineManager(config_path="config.yaml")
        manager.run()
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
    finally:
        end_time = time.time()
        logger.info(
            f"Pipeline execution finished in {end_time - start_time:.2f} seconds."
        )


if __name__ == "__main__":
    main()

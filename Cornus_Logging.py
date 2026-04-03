# -------------------- Imported Modules -------------------
import logging
import os


# -------------------- Logging Setup --------------------
def cornus_init_logging() -> logging.Logger:
    """
    Initialize and return the shared project logger for Cornus.

    This helper configures the named logger ``"Cornus"`` so that logging output is
    written both to a UTF-8-SIG encoded log file and to the console. The function is
    designed to be called once near the application entry point, after which other
    modules can retrieve the same configured logger by calling
    ``logging.getLogger("Cornus")``.

    The logging setup creates a dedicated ``Cornus_Logs`` directory beside the
    current module file if it does not already exist, builds a fixed log-file path,
    applies a consistent formatter, and avoids adding duplicate handlers when the
    function is called multiple times in the same process.

    Returns
    -------
    logging.Logger
        The configured shared ``Cornus`` logger instance.

    Behavior
    --------
    1. Resolve the current module directory as the local project root.
    2. Create the ``Cornus_Logs`` folder if it does not already exist.
    3. Build the log-file path ``Cornus_Logs/Cornus_Log.log``.
    4. Retrieve the named logger ``"Cornus"``.
    5. Set the logger level to ``logging.INFO``.
    6. Disable propagation so messages are not duplicated by ancestor loggers.
    7. Build a formatter using the pattern::

        %(asctime)s | %(levelname)s | %(name)s | %(message)s

    with date format::

        %Y-%m-%d %H:%M:%S

    8. Add a ``logging.FileHandler`` only if an equivalent file handler for the same
    log file is not already attached.
    9. Add a console ``logging.StreamHandler`` only if a non-file stream handler is
    not already attached.
    10. Write one startup log record indicating the active log-file path.
    11. Return the configured logger.

    Logging Outputs
    ---------------
    The configured logger writes to two destinations:

    - File output:
    ``Cornus_Logs/Cornus_Log.log``
    - Console output:
    standard stream output through ``logging.StreamHandler``

    Handler Deduplication
    ---------------------
    This function is safe to call more than once in the same runtime. Before adding
    handlers, it checks whether:

    - a file handler already points to the same ``log_file`` path
    - a console stream handler already exists and is not a file handler

    This prevents duplicated log lines caused by attaching the same handler multiple
    times.

    Side Effects
    ------------
    - Creates the ``Cornus_Logs`` directory when missing.
    - Creates or appends to the log file ``Cornus_Log.log``.
    - Modifies the shared named logger ``"Cornus"`` by setting level, propagation,
    and handlers.
    - Emits one INFO log message confirming initialization.

    Notes
    -----
    - The returned logger is intended to be reused across the whole project.
    - Other modules should normally use::

        logging.getLogger("Cornus")

    instead of rebuilding logging configuration independently.
    - ``logger.propagate = False`` is used to prevent duplicate messages when a root
    logger or parent logger is also configured elsewhere.
    - The file handler uses ``encoding="utf-8-sig"`` so that the log file is
    friendly to environments that expect UTF-8 with BOM.

    Examples
    --------
    Initialize logging in an entry-point script::

        logger = cornus_init_logging()
        logger.info("Cornus system started")

    Reuse the same logger in another module::

        import logging
        logger = logging.getLogger("Cornus")
        logger.info("Upload menu entered")
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    log_folder = os.path.join(project_root, "Cornus_Logs")
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, "Cornus_Log.log")

    logger = logging.getLogger("Cornus")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not any(
        isinstance(h, logging.FileHandler)
        and getattr(h, "baseFilename", "") == log_file
        for h in logger.handlers
    ):
        fh = logging.FileHandler(log_file, encoding="utf-8-sig")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in logger.handlers
    ):
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    logger.info("Logging initialized to: %s", log_file)
    return logger


# -------------------- Execute --------------------
if __name__ == "__main__":
    logger = cornus_init_logging()


# --------------------------------------------------------

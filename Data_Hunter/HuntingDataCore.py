# -------------------- Import Modules --------------------
import os

import pandas as pd

WORKSPACE_PATH = os.getcwd()
# -------------------- Hunting data core --------------------
class HuntingDataCore:
    """
    Hunting Data Core
    =================

    This module defines the `HuntingDataCore` class, a lightweight file-discovery
    and file-loading engine for local data exploration workflows.

    The class is designed to support an interactive or semi-interactive process in
    which the user:

    1. Scans the current working location for available folders.
    2. Selects a target folder.
    3. Scans that folder for available files.
    4. Selects a target file.
    5. Opens the selected file into a pandas-compatible in-memory structure.

    Primary Responsibilities
    ------------------------
    `HuntingDataCore` is responsible for:

    - locating folders in the current working directory
    - locating files inside a selected folder
    - recording selected folder / file metadata
    - building absolute paths for selected resources
    - opening supported file types into `self.target_data`
    - storing plain text content in tabular form for consistent downstream handling

    Supported File Types
    --------------------
    The `opener()` method currently supports:

    - `.csv`
    - `.xlsx`
    - `.xls`
    - `.xlsm`
    - `.json`
    - `.html`
    - `.sql`
    - `.txt`

    Loading Behavior by File Type
    -----------------------------
    - CSV / Excel:
    Loaded directly with pandas using optional `nrows`, `usecols`, and `index_col`.

    - JSON:
    Loaded with `pandas.read_json()`, then optionally filtered by selected columns,
    row count, and index assignment.

    - HTML:
    All tables are extracted with `pandas.read_html()`. A single table is selected
    using `html_table_index`, then optionally filtered by columns, row count, and
    index assignment.

    - SQL / TXT:
    Raw file content is read as text and wrapped into a one-row DataFrame so that
    later processing can still use a unified `DataFrame` interface.

    Design Notes
    ------------
    This class focuses on file hunting and file opening only. It does not perform
    data profiling, statistical inspection, visualization, or report generation.
    Those responsibilities are better handled in a separate browsing / inspection
    layer such as a `VisionCore`-style component.

    Attributes
    ----------
    target_data : pandas.DataFrame or None
        The currently opened data object. For structured files, this is the loaded
        table. For text-based files such as `.sql` and `.txt`, this is a one-row
        DataFrame containing the raw file content.

    selected_folder : str or None
        Name of the folder selected by the user from the working location.

    selected_file : str or None
        Name of the file selected inside `selected_folder`.

    current_text_content : str or None
        Reserved text buffer for future text-oriented workflows. Not actively used
        in the current implementation.

    current_working_place : list[str]
        List of folder names discovered in the current working directory.

    current_wp_dir : dict[int, str]
        Integer-indexed mapping of discovered folders, used for menu-style selection.

    files_from_selected_folder : list[str]
        List of file names found inside the selected folder.

    file_list : dict[int, str]
        Integer-indexed mapping of files discovered in the selected folder.

    current_folder_path : str or None
        Absolute path to the currently selected folder.

    current_file_path : str or None
        Absolute path to the currently selected file.

    target_data_report : dict or None
        Reserved storage for future profiling / summary metadata. Not actively used
        in the current implementation.

    Typical Workflow
    ----------------
    A typical usage pattern is:

    1. Instantiate `HuntingDataCore`.
    2. Call `working_place_searcher()` to discover folders.
    3. Call `files_searcher_from_folders()` with selected indices.
    4. Call `opener()` to load the selected file.
    5. Pass `target_data` into another component for inspection or analysis.

    Examples
    --------
    >>> hunter = HuntingDataCore()
    >>> hunter.working_place_searcher()
    >>> hunter.files_searcher_from_folders(selected_folder_num=1, selected_file_num=2)
    >>> df = hunter.opener()

    Notes
    -----
    - The class assumes local filesystem access.
    - The folder search is based on the current working directory.
    - File opening failures currently fall back to `None`.
    - Text-based files are normalized into DataFrames for interface consistency.
    - Success messages are printed only when the target file is loaded successfully.
    """

    # -------------------- Initialization --------------------
    def __init__(self):
        """
        Initialize the hunting engine state.

        This constructor prepares all working attributes used for folder discovery,
        file discovery, file selection, path tracking, and loaded data storage.

        Initialized State
        -----------------
        The constructor creates placeholders for:

        - loaded target data
        - selected folder and file names
        - current working-place folder listing
        - indexed folder and file dictionaries
        - absolute folder and file paths
        - optional future reporting metadata

        Attributes Initialized
        ----------------------
        target_data : pandas.DataFrame or None
            Storage for the currently opened file content.

        selected_folder : str or None
            Folder selected from the discovered working-place directories.

        selected_file : str or None
            File selected from within the chosen folder.

        current_text_content : str or None
            Reserved field for future direct text content handling.

        current_working_place : list[str]
            Cached list of folders discovered in the current working directory.

        current_wp_dir : dict[int, str]
            Indexed folder dictionary used for selection and display.

        files_from_selected_folder : list[str]
            Cached list of files discovered in the currently selected folder.

        file_list : dict[int, str]
            Indexed file dictionary used for selection and display.

        current_folder_path : str or None
            Absolute path of the selected folder.

        current_file_path : str or None
            Absolute path of the selected file.

        target_data_report : dict or None
            Reserved field for future data reporting output.

        Returns
        -------
        None

        Notes
        -----
        This method does not perform any file or folder scanning. It only prepares
        the object for later operations.
        """
        # ---------- Folder / File / Target data / Data content ----------
        self.target_data: pd.DataFrame = None
        self.selected_folder: str = None
        self.selected_file: str = None
        self.current_text_content: str = None

        # ---------- Record folders and files (working place) ----------
        self.current_working_place: list[str] = []
        self.current_wp_dir: dict[int, str] = {}
        self.files_from_selected_folder: list[str] = []
        self.file_list: dict[int, str] = {}

        # ---------- Record folder and file current path ----------
        self.current_folder_path: str = None
        self.current_file_path: str = None

        # ---------- Target data report ----------
        self.target_data_report: dict = None

    # -------------------- Hunting folders in working place --------------------
    def working_place_searcher(self):
        """
        Scan the current working directory for folders and build an indexed mapping.

        This method searches the current process working directory (`WORKSPACE_PATH`) and
        collects only directory entries. The discovered folder names are stored in
        `self.current_working_place`, and an integer-indexed lookup dictionary is
        built in `self.current_wp_dir` for menu-style selection.

        Workflow
        --------
        1. Read entries from the current working directory.
        2. Keep only those entries that are directories.
        3. Store the raw folder list in `self.current_working_place`.
        4. Build a 1-based indexed dictionary in `self.current_wp_dir`.

        Returns
        -------
        dict[int, str]
            A dictionary mapping 1-based numeric indices to folder names found in
            the current working directory.

        Side Effects
        ------------
        - Updates `self.current_working_place`
        - Updates `self.current_wp_dir`

        Examples
        --------
        >>> hunter = HuntingDataCore()
        >>> folders = hunter.working_place_searcher()
        >>> print(folders)
        {1: 'data', 2: 'reports', 3: 'archive'}

        Notes
        -----
        The method scans the current working directory of the running process,
        which may differ from `BASED_PATH` depending on how the program is launched.
        """
        # ---------- Get directories from working place ----------
        self.current_working_place = [
            item
            for item in os.listdir(WORKSPACE_PATH) # List the directories
            if os.path.isdir(os.path.join(WORKSPACE_PATH, item)) # Filtering only directories
        ]

        # ---------- Record directories as dictionary ----------
        self.current_wp_dir = {}
        for num, item in enumerate(self.current_working_place, 1):
            self.current_wp_dir[num] = item

        return self.current_wp_dir

    # -------------------- Hunting files in selected folders --------------------
    def files_searcher_from_folders(
        self,
        selected_folder_num: int,
        selected_file_num: int | None = None,
    ):
        """
        Discover files inside a selected folder and optionally record a selected file.

        Parameters
        ----------
        selected_folder_num : int
            1-based index of the folder to select.

        selected_file_num : int | None, default=None
            1-based index of the file to select.
            If None, only return the indexed file list from the selected folder.

        Returns
        -------
        dict[int, str] | str
            If selected_file_num is None:
                return indexed file dictionary.
            Otherwise:
                return absolute path to the selected file.
        """

        # ---------- Ensure folder list is ready ----------
        if not self.current_wp_dir: # No directories recorded currently
            self.working_place_searcher() # Back to working place searcher

        # ---------- Validate selected folder number ----------
        if selected_folder_num not in self.current_wp_dir:
            raise ValueError("⚠️ Invalid folder number selected ‼️")

        # ---------- Record selected folder ----------
        self.selected_folder = self.current_wp_dir[selected_folder_num]
        self.current_folder_path = os.path.join(WORKSPACE_PATH, self.selected_folder) # Join full path of selected folder

        # ---------- Record files from selected folder ----------
        self.files_from_selected_folder = [
            file
            for file in os.listdir(self.current_folder_path) # List selected folder
            if os.path.isfile(os.path.join(self.current_folder_path, file)) # Filtering only files
        ]

        # ---------- Build file index dictionary ----------
        self.file_list = {}
        for i, file in enumerate(self.files_from_selected_folder, 1):
            self.file_list[i] = file

        # ---------- Return file list ----------
        if selected_file_num is None:
            return self.file_list # No file selected

        # ---------- Validate selected file number ----------
        if selected_file_num not in self.file_list:
            raise ValueError("⚠️ Invalid file number selected ‼️")

        # ---------- Record selected file and its full path ----------
        self.selected_file = self.file_list[selected_file_num]
        self.current_file_path = os.path.join(
            self.current_folder_path, self.selected_file
        )

        return self.current_file_path # Full path of selected file

    # -------------------- Loading file to open target data --------------------
    def opener(
        self,
        nrows: int = None,
        usecols: list = None,
        index_col: int | str | list[int | str] = None,
        parse_dates: list[str] | bool | None = None,
        html_table_index: int = 0,
        encoding: str = "utf-8",
    ):
        """
        Open the currently selected file and load its content into `self.target_data`.

        This method reads the file pointed to by `self.current_file_path` and loads
        its content according to file extension. Structured tabular files are loaded
        directly into a pandas DataFrame, while plain-text files are wrapped into a
        one-row DataFrame for downstream consistency.

        Supported extensions include CSV, Excel, JSON, HTML, SQL, and TXT.

        Parameters
        ----------
        nrows : int, optional
            Number of rows to read for supported tabular file types. If None, all
            available rows are loaded.

        usecols : list, optional
            Column subset to load or retain. Behavior depends on file type:
            for CSV and Excel it is passed directly to pandas; for JSON and HTML
            it is applied after loading.

        index_col : int, str, or list[int | str], optional
            Column or columns to use as the index. For CSV and Excel it is passed
            directly to pandas; for JSON and HTML it is applied after loading.

        parse_dates : list or bool, optional
            Date parsing instruction passed directly to `pandas.read_csv()` and
            `pandas.read_excel()`.

            Typical usage includes:
            - `True`: attempt automatic date parsing when supported
            - `["date_col"]`: parse one or more named columns as datetime
            - `None`: do not apply explicit date parsing

            This parameter is currently used only for CSV and Excel loading.
            JSON and HTML branches do not apply `parse_dates` automatically.

        html_table_index : int, default=0
            Zero-based index of the table to extract when opening an HTML file that
            contains one or more tables.

        encoding : str, default="utf-8"
            Text encoding used when reading `.sql` and `.txt` files.

        Returns
        -------
        pandas.DataFrame or None
            The loaded DataFrame if reading succeeds, otherwise None.

        Loading Rules
        -------------
        CSV
            Loaded with `pandas.read_csv()`, with optional `nrows`, `usecols`,
            `index_col`, and `parse_dates`.

        Excel
            Loaded with `pandas.read_excel()` for `.xlsx`, `.xls`, and `.xlsm`,
            with optional `nrows`, `usecols`, `index_col`, and `parse_dates`.

        JSON
            Loaded with `pandas.read_json()`, then optionally filtered by columns,
            row count, and index assignment.

        HTML
            Loaded with `pandas.read_html()`. One table is selected using
            `html_table_index`, then optionally filtered by columns, row count,
            and index assignment.

        SQL
            Read as raw text and wrapped into a one-row DataFrame with column
            name `"sql_script"`.

        TXT
            Read as raw text and wrapped into a one-row DataFrame with column
            name `"text_content"`.

        Unsupported Types
            Unsupported file extensions result in a warning message and a `None`
            target.

        Side Effects
        ------------
        - Reads the file at `self.current_file_path`
        - Updates `self.target_data`
        - Prints a success message and timestamp when loading succeeds
        - Resets `self.target_data` to None if loading fails

        Raises
        ------
        ValueError
            If `html_table_index` is outside the range of available HTML tables.

        Notes
        -----
        - If `self.current_file_path` is not set, the method returns None immediately.
        - For HTML files, an empty table extraction result returns None.
        - `parse_dates` is currently supported only in the CSV and Excel branches.
        - All runtime exceptions are currently caught internally, and the method
        returns None instead of propagating the original exception.
        - Because exceptions are suppressed, debugging failed reads may require
        temporarily expanding the exception handling logic.

        Examples
        --------
        >>> hunter = HuntingDataCore()
        >>> hunter.files_searcher_from_folders(1, 1)
        >>> df = hunter.opener(
        ...     nrows=100,
        ...     usecols=["date", "price"],
        ...     parse_dates=["date"],
        ... )
        >>> print(df.dtypes)

        >>> hunter.files_searcher_from_folders(2, 3)
        >>> sql_df = hunter.opener(encoding="utf-8")
        >>> print(sql_df.iloc[0, 0][:100])
        """
        # ---------- Ensure selected file path is ready ----------
        if not self.current_file_path:
            self.target_data = None
            return None

        # ---------- Get file's extension ----------
        ext = os.path.splitext(self.current_file_path)[1].lower()

        try:
            # ---------- CSV ----------
            if ext == ".csv":
                self.target_data = pd.read_csv(
                    self.current_file_path,
                    nrows=nrows,
                    usecols=usecols,
                    index_col=index_col,
                    parse_dates=parse_dates,
                )

            # ---------- Excel ----------
            elif ext in [".xlsx", ".xls", ".xlsm"]:
                self.target_data = pd.read_excel(
                    self.current_file_path,
                    nrows=nrows,
                    usecols=usecols,
                    index_col=index_col,
                    parse_dates=parse_dates,
                )

            # ---------- JSON ----------
            elif ext == ".json":
                self.target_data = pd.read_json(self.current_file_path)

                if usecols is not None:
                    self.target_data = self.target_data[usecols]

                if nrows is not None:
                    self.target_data = self.target_data.head(nrows)

                if index_col is not None:
                    self.target_data = self.target_data.set_index(index_col)

            # ---------- HTML ----------
            elif ext == ".html":
                html_tables = pd.read_html(self.current_file_path)

                if not html_tables:
                    self.target_data = None
                    return None

                if html_table_index < 0 or html_table_index >= len(html_tables):
                    raise ValueError("⚠️ html_table_index is out of range ‼️")

                self.target_data = html_tables[html_table_index] # Using table index to select target data

                if usecols is not None:
                    self.target_data = self.target_data[usecols]

                if nrows is not None:
                    self.target_data = self.target_data.head(nrows)

                if index_col is not None:
                    self.target_data = self.target_data.set_index(index_col)

            # ---------- SQL ----------
            elif ext == ".sql":
                with open(self.current_file_path, "r", encoding=encoding) as f:
                    sql_text = f.read()

                self.target_data = pd.DataFrame({"sql_script": [sql_text]})

            # ---------- TXT ----------
            elif ext == ".txt":
                with open(self.current_file_path, "r", encoding=encoding) as f:
                    txt_text = f.read()

                self.target_data = pd.DataFrame({"text_content": [txt_text]})

            # ---------- Unsupported error ----------
            else:
                print(f"⚠️ Can't open selected file, unsupported file type: {ext} ‼️")
                self.target_data = None

            if self.target_data is not None:
                print(
                    f"\n🔥 {os.path.basename(self.current_file_path)} File opened successfully 🔥\n{'-'*100}"
                )

        except Exception:
            self.target_data = None

        return self.target_data


# =================================================

# -------------------- Import Modules --------------------
import io
import os

import pandas as pd

from Cornus.Data_Hunter.HuntingDataCore import HuntingDataCore

BASED_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_DIR = os.path.join(BASED_PATH, "Summary_Report")
TXT_DIR = os.path.join(BASED_PATH, "Full_data_Report")

os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)
# -------------------- Vision core --------------------
class VisionCore:
    """
    Dataset inspection core built on top of a `HuntingDataCore` object.

    `VisionCore` provides a compact inspection layer for already-loaded tabular
    data. It reads the target DataFrame from `HuntingDataCore`, validates that
    the data is usable, generates summary reports, inspects missing values,
    profiles selected subsets, and exports column-level metadata to CSV.

    Parameters
    ----------
    hunter_core : HuntingDataCore
        A data-loading core object that must already contain:
        - `target_data`: the loaded pandas DataFrame
        - `current_file_path`: the source file path of the loaded dataset

    Attributes
    ----------
    hunter_core : HuntingDataCore
        The upstream data-loading object used as the data provider.
    source_data : pandas.DataFrame or None
        The loaded dataset obtained from `hunter_core.target_data`.
    target_data_report : dict or None
        A container used to store generated reports from inspection methods.

    Intended Usage
    --------------
    This class is designed for exploratory inspection and reporting after a file
    has already been loaded through the companion data-loading layer.

    Typical workflow:
    1. Construct `VisionCore` with a valid `HuntingDataCore` instance.
    2. Run `data_content_info_core()` to inspect overall structure.
    3. Run `null_inspection_core()` to inspect missing values.
    4. Optionally run `data_inspection_by_column_index()` for a focused subset.
    5. Run `save_data_report_core()` to export a column profile summary.

    Notes
    -----
    - This class assumes pandas-based tabular data.
    - Most public methods print summaries and also save structured results into
      `self.target_data_report` for later reuse.
    """

    # -------------------- Initialization --------------------
    def __init__(self, hunter_core: HuntingDataCore):
        """
        Initialize the inspection core with a loaded data provider.

        This constructor receives a `HuntingDataCore` instance and extracts the
        currently loaded DataFrame from it. The loaded dataset becomes the working
        source for all inspection and reporting methods in this class.

        Parameters
        ----------
        hunter_core : HuntingDataCore
            A `HuntingDataCore` object that is expected to already hold:
            - `target_data`: the active pandas DataFrame to inspect
            - `current_file_path`: the path of the loaded source file

        Attributes Initialized
        ----------------------
        hunter_core : HuntingDataCore
            The upstream data-loading core.
        source_data : pandas.DataFrame or None
            The current dataset copied by reference from `hunter_core.target_data`.
        target_data_report : dict or None
            Storage for generated inspection results. Initially set to None.

        Notes
        -----
        This initializer does not validate the dataset immediately. Validation is
        performed by helper methods before each inspection routine runs.
        """
        # ---------- Receive target data from HuntingDataCore ----------
        self.hunter_core = hunter_core  # HuntingDataCore object
        self.source_data = hunter_core.target_data  # HuntingDataCore loaded target data
        self.target_data_report: dict = None  # Record data report

    # -------------------- Validation (helper) --------------------
    def _validation(self):
        """
        Validate whether the current source dataset is available and usable.

        This helper checks the minimum prerequisites required by downstream
        inspection methods:
        - source data exists
        - source data is a pandas DataFrame
        - source data is not empty
        - the upstream file path exists

        Returns
        -------
        bool
            True if the current dataset and file context are valid.
            False otherwise.

        Side Effects
        ------------
        Prints a warning message when validation fails.

        Validation Rules
        ----------------
        - `self.source_data` must not be None.
        - `self.source_data` must be a pandas DataFrame.
        - `self.source_data` must not be empty.
        - `self.hunter_core.current_file_path` must be available.

        Notes
        -----
        This method is intended for internal use before running report-generation
        methods. It prevents downstream operations from failing on missing or
        invalid input state.
        """
        if self.source_data is None:
            print("⚠️ No source data available ‼️")
            return False

        if not isinstance(self.source_data, pd.DataFrame):
            print("⚠️ Source data must be a pandas DataFrame ‼️")
            return False

        if self.source_data.empty:
            print("⚠️ Source data is empty ‼️")
            return False

        if not self.hunter_core.current_file_path:
            print("⚠️ No current file path available ‼️")
            return False

        return True

    # -------------------- Data content and informations --------------------
    def data_content_info_core(self):
        """
        Generate a broad structural and descriptive summary of the current dataset.

        This method inspects the full source DataFrame and builds a comprehensive
        report that includes shape, previews, sampled rows, `DataFrame.info()`
        output, memory usage, dtype counts, unique-value counts, and separate
        descriptive summaries for numeric and non-numeric columns.

        Returns
        -------
        dict or None
            A dictionary containing the generated dataset summary if validation
            succeeds; otherwise None.

            The returned dictionary contains:
            - ``shape`` : tuple
                DataFrame shape as `(n_rows, n_columns)`.
            - ``head_5`` : pandas.DataFrame
                First 5 rows of the dataset.
            - ``tail_5`` : pandas.DataFrame
                Last 5 rows of the dataset.
            - ``sampling_10_rows`` : pandas.DataFrame
                Random sample of up to 10 rows using a fixed random seed.
            - ``info`` : str
                Text output captured from `DataFrame.info()`.
            - ``memory_usage_byte`` : pandas.Series
                Per-column memory usage including deep object inspection.
            - ``dtype_amount`` : pandas.Series
                Count of each dtype in the dataset.
            - ``unique_values_per_column`` : pandas.Series
                Number of unique values per column, including NaN.
            - ``numeric_description`` : pandas.DataFrame or str
                Transposed descriptive statistics for numeric columns, or a message
                if no numeric columns are found.
            - ``non_numeric_description`` : pandas.DataFrame or str
                Transposed descriptive statistics for non-numeric columns, or a
                message if no non-numeric columns are found.

        Side Effects
        ------------
        - Prints a human-readable summary of the dataset.
        - Stores the generated report in `self.target_data_report`.

        Notes
        -----
        - Numeric and non-numeric columns are summarized separately to avoid mixed
        describe behavior.
        - The random sample uses `random_state=42` for reproducibility.
        - This method is useful as a first-pass overview before cleaning or
        modeling.
        """
        if not self._validation():
            return None

        # ---------- Get numeric and non-numeric columns ----------
        numeric_data = self.source_data.select_dtypes(include="number")
        non_numeric_data = self.source_data.select_dtypes(exclude="number")

        # ---------- Numeric columns descriptions ----------
        numeric_description = (
            numeric_data.describe().T
            if numeric_data.shape[1] > 0  # Check numeric type data existed
            else "🔥 No numeric columns found."
        )

        # ---------- Non-numeric columns descriptions ----------
        non_numeric_description = (
            non_numeric_data.describe().T
            if non_numeric_data.shape[1] > 0  # Check non-numeric type data existed
            else "🔔 No non-numeric columns found."
        )

        # ---------- Target data information ----------
        if self.source_data is not None:
            buffer = io.StringIO()
            self.source_data.info(buf=buffer)  # Information add to data report

            # ---------- Record target data report ----------
            data_report = {
                "shape": self.source_data.shape, # Data shape
                "head_5": self.source_data.head(), # First 5 rows of data
                "tail_5": self.source_data.tail(), # Last 5 rows of data
                "sampling_10_rows": self.source_data.sample( # Sampling 10 rows of data
                    n=min(10, len(self.source_data)), random_state=42
                ),
                "info": buffer.getvalue(), # Data info.
                "memory_usage_byte": self.source_data.memory_usage(deep=True), # Data memory usage
                "dtype_amount": self.source_data.dtypes.astype(str).value_counts(), # List each data type's amount
                "unique_values_per_column": self.source_data.nunique(dropna=False), # Unique amount
                "numeric_description": numeric_description,
                "non_numeric_description": non_numeric_description,
            }

            # ---------- Print target data report ----------
            print(f"📋 Shape of target: {data_report['shape']}\n{'-'*100}")
            print(
                f"📋 The content of data (first 5 rows)\n{data_report['head_5']}\n{'-'*100}"
            )
            print(
                f"📋 The content of data (last 5 rows)\n{data_report['tail_5']}\n{'-'*100}"
            )
            print(
                f"📋 The content of data (10 rows)\n{data_report['sampling_10_rows']}\n{'-'*100}"
            )
            print(f"📋 Target data information\n{data_report['info']}\n{'-'*100}")
            print(f"📋 Dtype amount\n{data_report['dtype_amount']}\n{'-'*100}")

            # ---------- Record target data report ----------
            self.target_data_report = data_report

        return self.target_data_report

    # -------------------- Null inspection --------------------
    def null_inspection_core(self):
        """
        Inspect missing-value patterns across the full dataset.

        This method computes overall and per-column null statistics, identifies
        columns containing missing values, counts rows affected by partial or full
        missingness, and highlights columns whose null ratio exceeds 50%.

        Returns
        -------
        dict or None
            The updated report dictionary if validation succeeds; otherwise None.

            The nested ``null_report`` entry contains:
            - ``total_null_count`` : int
                Total number of missing cells in the dataset.
            - ``null_count_per_column`` : pandas.Series
                Number of missing values in each column.
            - ``null_ratio_per_column`` : pandas.Series
                Percentage of missing values in each column.
            - ``columns_with_null`` : list[str]
                Column names that contain at least one missing value.
            - ``rows_with_any_null_count`` : int
                Number of rows with at least one missing value.
            - ``rows_all_null_count`` : int
                Number of rows where all values are missing.
            - ``overall_null_ratio_in_data`` : float
                Percentage of missing cells across the entire DataFrame.
            - ``high_null_ratio_columns_over_50pct`` : pandas.Series
                Columns whose null ratio is greater than 50%.

        Side Effects
        ------------
        - Prints a human-readable missing-value summary.
        - Initializes `self.target_data_report` if necessary.
        - Stores the null inspection result under
        `self.target_data_report["null_report"]`.

        Notes
        -----
        - Column null ratios are expressed as percentages.
        - The >50% threshold is intended as a quick alert for potentially
        problematic columns.
        - This method does not modify the source dataset.
        """
        if not self._validation():
            return None

        # ---------- Null situation ----------
        null_ratio_per_column = (
            (self.source_data.isna().sum() / len(self.source_data)) * 100
        ).round(2)
        overall_null_ratio_in_data = (
            self.source_data.isna().sum().sum() / self.source_data.size * 100
        ).round(2)

        # ---------- Missing value alert----------
        high_null_ratio_columns = null_ratio_per_column[null_ratio_per_column > 50]

        # ---------- Null report ----------
        null_report = {
            "total_null_count": self.source_data.isna().sum().sum(),
            "null_count_per_column": self.source_data.isna().sum(),
            "null_ratio_per_column": null_ratio_per_column,
            "columns_with_null": self.source_data.columns[
                self.source_data.isna().any()
            ].tolist(),
            "rows_with_any_null_count": self.source_data.isna().any(axis=1).sum(),
            "rows_all_null_count": self.source_data.isna().all(axis=1).sum(),
            "overall_null_ratio_in_data": overall_null_ratio_in_data,
            "high_null_ratio_columns_over_50pct": high_null_ratio_columns,
        }

        # ---------- Printout null report ----------
        print(f"📋 Total null count\n{null_report['total_null_count']}\n{'-'*100}")
        print(
            f"📋 Overall null ratio in data (%)\n{null_report['overall_null_ratio_in_data']}\n{'-'*100}"
        )
        print(f"📋 Columns with null\n{null_report['columns_with_null']}\n{'-'*100}")
        print(
            f"📋 Rows with any null count\n{null_report['rows_with_any_null_count']}\n{'-'*100}"
        )
        print(
            f"📋 Rows with all null count\n{null_report['rows_all_null_count']}\n{'-'*100}"
        )

        # ---------- High missing ratio for null ----------
        if not high_null_ratio_columns.empty:
            print(
                f"⚠️ High missing ratio columns (>50%)\n{null_report['high_null_ratio_columns_over_50pct']}\n{'-'*100}"
            )
        else:
            print(f"🔥 No 'High Missing Ratio' discovered for each column.\n{'-'*100}")

        # ---------- Record target data ----------
        if self.target_data_report is None:
            self.target_data_report = {}

        self.target_data_report["null_report"] = null_report

        return self.target_data_report

    # -------------------- Column / Index operations for viewing selected data properties --------------------
    def data_inspection_by_column_index(
        self,
        index: list = None,
        column: list[str] = None,
    ):
        """
        Inspect a selected subset of the dataset by row index and/or column names.

        This method starts from the full source DataFrame, optionally filters rows
        by index labels, optionally selects a subset of columns, then computes a
        focused structural report for the resulting subset.

        Parameters
        ----------
        index : list, optional
            Row index labels to select using `.loc`.
            If None, all rows are retained.
        column : list[str], optional
            Column names to select.
            If None, all columns are retained.

        Returns
        -------
        dict or None
            A dictionary describing the selected subset if validation and selection
            succeed; otherwise None.

            The returned dictionary contains:
            - ``selected_shape`` : tuple
                Shape of the selected subset.
            - ``selected_columns`` : list[str]
                Names of selected columns.
            - ``selected_head_5`` : pandas.DataFrame
                First 5 rows of the selected subset.
            - ``selected_dtypes`` : pandas.Series
                Dtypes of selected columns.
            - ``selected_non_null_count_per_column`` : pandas.Series
                Non-null counts for selected columns.
            - ``selected_null_count_per_column`` : pandas.Series
                Null counts for selected columns.
            - ``selected_null_ratio_per_column`` : pandas.Series
                Null ratios (%) for selected columns.
            - ``selected_unique_count_per_column`` : pandas.Series
                Unique counts per selected column, including NaN.
            - ``selected_memory_usage_byte`` : pandas.Series
                Per-column memory usage for the selected columns.
            - ``selected_duplicate_count`` : int
                Number of duplicated rows within the selected subset.
            - ``selected_duplicate_preview`` : pandas.DataFrame
                Preview of duplicated rows in the selected subset.
            - ``selected_index_name`` : str or None
                Name of the subset index.
            - ``selected_index_dtype`` : dtype
                Data type of the subset index.
            - ``selected_index_is_unique`` : bool
                Whether the subset index is unique.

        Side Effects
        ------------
        - Prints a concise summary of the selected subset.
        - Initializes `self.target_data_report` if needed.
        - Stores the result under
        `self.target_data_report["selected_data_report"]`.

        Raises / Failure Behavior
        -------------------------
        This method returns None and prints a warning if:
        - source data validation fails
        - any requested column names are not found

        Notes
        -----
        - Row filtering is performed before column filtering.
        - Duplicate detection is based on the already-selected subset, not the
        original full dataset.
        - If the selection yields a Series, it is converted back to a DataFrame so
        reporting remains structurally consistent.
        """
        if not self._validation():
            return None

        # ---------- Start from full source data ----------
        inspected_data = self.source_data.copy()

        # ---------- Select rows by index labels ----------
        if index is not None:
            inspected_data = inspected_data.loc[index] # Get data by selected index

        # ---------- Select columns ----------
        if column is not None:
            missing_cols = [col for col in column if col not in inspected_data.columns]
            if missing_cols:
                print(f"⚠️ Columns not found: {missing_cols} ‼️")
                return None

            inspected_data = inspected_data[column] # Get data by selected columns

        # ---------- Ensure selected data is DataFrame ----------
        if isinstance(inspected_data, pd.Series):
            inspected_data = inspected_data.to_frame() # Turn into DataFrame format to record as report

        # ---------- Selected data report ----------
        selected_data_report = {
            "selected_shape": inspected_data.shape,
            "selected_columns": inspected_data.columns.tolist(),
            "selected_head_5": inspected_data.head(),
            "selected_dtypes": inspected_data.dtypes,
            "selected_non_null_count_per_column": inspected_data.notna().sum(),
            "selected_null_count_per_column": inspected_data.isna().sum(),
            "selected_null_ratio_per_column": (
                inspected_data.isna().mean() * 100
            ).round(2),
            "selected_unique_count_per_column": inspected_data.nunique(dropna=False),
            "selected_memory_usage_byte": inspected_data.memory_usage(deep=True)[
                inspected_data.columns
            ],
            "selected_duplicate_count": inspected_data.duplicated().sum(),
            "selected_duplicate_preview": inspected_data[
                inspected_data.duplicated()
            ].head(),
            "selected_index_name": inspected_data.index.name,
            "selected_index_dtype": inspected_data.index.dtype,
            "selected_index_is_unique": inspected_data.index.is_unique,
        }

        # ---------- Print selected data summary ----------
        print(
            f"🔎 Selected data shape: {selected_data_report['selected_shape']}\n{'-'*100}"
        )
        print(
            f"🔎 Selected data preview\n{selected_data_report['selected_head_5']}\n{'-'*100}"
        )
        print(
            f"🔎 Selected null ratio per column (%)\n{selected_data_report['selected_null_ratio_per_column']}\n{'-'*100}"
        )
        print(
            f"🔎 Selected unique count per column\n{selected_data_report['selected_unique_count_per_column']}\n{'-'*100}"
        )

        if selected_data_report["selected_duplicate_count"] > 0:
            print(
                f"🔎 Duplicate data preview\n{inspected_data[inspected_data.duplicated()].head()}\n{'-'*100}"
            )
        print(
            f"🔎 Selected duplicate count: {selected_data_report['selected_duplicate_count']}"
        )

        print(f"🔎 Selected index name: {selected_data_report['selected_index_name']}")
        print(
            f"🔎 Selected index dtype: {selected_data_report['selected_index_dtype']}"
        )
        print(
            f"🔎 Selected index is unique: {selected_data_report['selected_index_is_unique']}\n{'-'*100}"
        )

        # ---------- Record selected data report ----------
        if self.target_data_report is None:
            self.target_data_report = {}

        self.target_data_report["selected_data_report"] = selected_data_report

        return selected_data_report

    # -------------------- Save data report as CSV file --------------------
    def save_data_report_core(self):
        """
        Build and save a column-level profile summary as a CSV report.

        This method generates a compact profile DataFrame containing core metadata
        for every column in the current dataset, then saves that summary to a CSV
        file in the configured `Summary_Report` directory.

        Returns
        -------
        str or None
            The full path to the saved CSV file if validation succeeds; otherwise
            None.

        Generated Report Columns
        ------------------------
        The exported profile includes:
        - ``column_name``
            Original column name.
        - ``dtype``
            Column dtype as string.
        - ``non_null_count``
            Count of non-missing values.
        - ``null_count``
            Count of missing values.
        - ``null_ratio_pct``
            Percentage of missing values.
        - ``unique_count``
            Number of unique values including NaN.
        - ``memory_usage_byte``
            Deep memory usage in bytes.

        Side Effects
        ------------
        - Saves a CSV file to disk using UTF-8-SIG encoding.
        - Initializes `self.target_data_report` if necessary.
        - Stores the generated profile DataFrame under
        `self.target_data_report["data_profile_report"]`.
        - Prints a preview and the saved file path.

        File Naming
        -----------
        The output file name is derived from the current source file name:
        ``<source_base_name>_profile_summary.csv``

        Notes
        -----
        - The base file name is extracted from
        `self.hunter_core.current_file_path`.
        - This method is intended for documentation, auditing, and quick profiling
        of raw or cleaned datasets.
        - The saved report is column-oriented and does not include row-level data.
        """
        if not self._validation():
            return None

        # ---------- Column profile summary ----------
        data_profile_df = pd.DataFrame(
            {
                "column_name": self.source_data.columns,
                "dtype": self.source_data.dtypes.astype(str).values,
                "non_null_count": self.source_data.notna().sum().values,
                "null_count": self.source_data.isna().sum().values,
                "null_ratio_pct": (self.source_data.isna().mean() * 100)
                .round(2)
                .values,
                "unique_count": self.source_data.nunique(dropna=False).values,
                "memory_usage_byte": self.source_data.memory_usage(deep=True)[
                    self.source_data.columns
                ].values,
            }
        )

        # ---------- Save CSV ----------
        base_name = os.path.splitext(
            os.path.basename(self.hunter_core.current_file_path)
        )[0]
        full_save_path = os.path.join(CSV_DIR, f"{base_name}_profile_summary.csv")
        data_profile_df.to_csv(full_save_path, index=False, encoding="utf-8-sig")

        # ---------- Record target data report ----------
        if self.target_data_report is None:
            self.target_data_report = {}

        self.target_data_report["data_profile_report"] = data_profile_df

        # ---------- Print summary ----------
        print(f"🔥 Column profile summary saved successfully 🔥")
        print(f"📋 Data profile summary\n{data_profile_df.head()}\n{'-'*100}")
        print(f"👣 Saved CSV file's path ---> {full_save_path}")

        return full_save_path

    # -------------------- Format helper (Helper) --------------------
    def _format_dataframe_for_txt(
        self,
        df: pd.DataFrame,
        max_rows: int | None = None,
        max_col_width: int = 50,
    ) -> str:
        """
        Format a DataFrame into row-wise text layout for TXT reports.
        """
        if df is None or df.empty:
            return "⚠️ No data available ‼️"

        if max_rows is not None:
            df = df.head(max_rows)

        lines = []

        for idx, row in df.iterrows():
            lines.append("-" * 80)
            lines.append(f"Row index: {idx}")
            lines.append("-" * 80)

            for col, value in row.items():
                value_str = str(value)

                if len(value_str) > max_col_width:
                    value_str = value_str[:max_col_width] + "..."

                lines.append(f"{str(col):<30} : {value_str}")

            lines.append("")

        return "\n".join(lines)

    # -------------------- Save full data report as TXT file --------------------
    def save_full_data_report_txt(self):
        """
        Save the current full in-memory inspection report as a formatted TXT file.

        This method exports `self.target_data_report` into a human-readable text
        report. Each top-level report section is written with a clear title and
        divider, and nested dictionary content is expanded into readable subsections
        instead of being written as a single raw dictionary string.

        Returns
        -------
        str or None
            Full path of the saved TXT file if saving succeeds.
            Returns None if no target data report is available.

        Side Effects
        ------------
        - Creates a TXT report file in the configured report directory.
        - Prints a success message and saved file path.
        - Does not modify `self.target_data_report`.

        Notes
        -----
        - DataFrame objects are formatted using `_format_dataframe_for_txt()`.
        - Series objects are written using `to_string()`.
        - Nested dictionaries are expanded section-by-section for readability.
        - This method saves the current report snapshot already stored in memory;
        it does not generate missing inspection content automatically.
        """
        if self.target_data_report is None:
            print(
                "⚠️ No target data report available to save. Please run a viewing action first ‼️"
            )
            return None

        base_name = os.path.splitext(
            os.path.basename(self.hunter_core.current_file_path)
        )[0]
        full_save_path = os.path.join(TXT_DIR, f"{base_name}_full_data_report.txt")

        def _write_value(f, value, indent: int = 0):
            prefix = " " * indent

            if isinstance(value, pd.DataFrame):
                text = self._format_dataframe_for_txt(value, max_col_width=50)
                for line in text.splitlines():
                    f.write(f"{prefix}{line}\n")
                f.write("\n")

            elif isinstance(value, pd.Series):
                f.write(value.to_string())
                f.write("\n")

            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    f.write(f"{prefix}{'-' * 60}\n")
                    f.write(f"{prefix}📌 {sub_key}\n")
                    f.write(f"{prefix}{'-' * 60}\n")

                    if isinstance(sub_value, pd.DataFrame):
                        text = self._format_dataframe_for_txt(
                            sub_value, max_col_width=50
                        )
                        for line in text.splitlines():
                            f.write(f"{prefix}{line}\n")

                    elif isinstance(sub_value, pd.Series):
                        text = sub_value.to_string()
                        for line in text.splitlines():
                            f.write(f"{prefix}{line}\n")

                    elif isinstance(sub_value, list):
                        if sub_value:
                            for item in sub_value:
                                f.write(f"{prefix}- {item}\n")
                        else:
                            f.write(f"{prefix}[]\n")
                    else:
                        f.write(f"{prefix}{sub_value}\n")

                    f.write("\n")

            elif isinstance(value, list):
                if value:
                    for item in value:
                        f.write(f"{prefix}- {item}\n")
                else:
                    f.write(f"{prefix}[]\n")

            else:
                f.write(f"{prefix}{value}\n")

        with open(full_save_path, "w", encoding="utf-8-sig") as f:
            f.write("🔥 CORNUS FULL DATA REPORT 🔥\n")
            f.write("=" * 80 + "\n\n")

            for key, value in self.target_data_report.items():
                f.write("=" * 80 + "\n")
                f.write(f"🔥 {key}\n")
                f.write("=" * 80 + "\n")

                _write_value(f, value)
                f.write("\n")

        print("🔥 Full data report TXT saved successfully 🔥")
        print(f"👣 Saved TXT file's path ---> {full_save_path}")

        return full_save_path


# =================================================

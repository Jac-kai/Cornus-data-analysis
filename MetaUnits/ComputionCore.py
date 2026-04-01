# -------------------- Import Modules --------------------
import os

import numpy as np
import pandas as pd

from Cornus.Data_Hunter.HuntingDataCore import HuntingDataCore
from Cornus.MetaUnits.ClarityCore import ClarityCore

BASED_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_DIR = os.path.join(BASED_PATH, "Compution_Record")
COMPUTED_DIR = os.path.join(BASED_PATH, "Compution_Report")

os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(COMPUTED_DIR, exist_ok=True)
# -------------------- ComputionCore --------------------
class ComputionCore:
    """
    Computation manager for cleaned tabular data.

    This class provides a structured interface for performing arithmetic,
    aggregation, and conditional transformations on a cleaned pandas DataFrame.
    It maintains an internal working dataset for computation workflows, records
    operation history, and supports exporting both computation records and selected
    result datasets to CSV files.

    Parameters
    ----------
    hunter_core : HuntingDataCore
        Core object that stores the originally loaded dataset and source file path.
    clarity_core : ClarityCore
        Core object that stores cleaned data and cleaning reports.

    Attributes
    ----------
    hunter_core : HuntingDataCore
        Reference to the upstream data-loading core.
    clarity_core : ClarityCore
        Reference to the upstream data-cleaning core.
    source_data : pandas.DataFrame or None
        Original dataset loaded by ``hunter_core``.
    cleaned_data : pandas.DataFrame or None
        Cleaned dataset produced by ``clarity_core``.
    computed_data : pandas.DataFrame or None
        Active working dataset used for computation operations.
        It is initialized as a copy of ``cleaned_data`` when available and is
        updated by operations that modify or extend the current computation result.
    cleaned_data_report : dict or None
        Cleaning report inherited from ``clarity_core``.
    compution_data_report : dict or None
        Latest computation summary report generated after a recorded operation.
    compution_history : list[dict]
        Sequential list of computation records describing all applied operations.

    Notes
    -----
    - This class assumes that cleaned data already exists in
    ``clarity_core.cleaned_data``.
    - Computation history is cumulative until the object is reinitialized.
    - Resetting computed data restores the working dataset from ``cleaned_data``,
    not from the original raw source.
    - Most column-based and conditional computation methods update
    ``self.computed_data`` directly.
    - Groupby aggregation behaves differently from column-update style operations:
    it returns a grouped summary result and may export that grouped result to CSV,
    but it does not overwrite ``self.computed_data`` by default.
    - CSV export responsibilities are intentionally separated:

    - ``_record_compution()`` exports computation history records
    - ``_save_computed_data_csv()`` exports the current full computed dataset
    - ``groupby_aggregation_calculation()`` may export grouped summary results
    """

    # -------------------- Initialization --------------------
    def __init__(self, hunter_core: HuntingDataCore, clarity_core: ClarityCore):
        """
        Initialize the computation core with upstream data and cleaning cores.

        Parameters
        ----------
        hunter_core : HuntingDataCore
            Object containing the source dataset and source file metadata.
        clarity_core : ClarityCore
            Object containing cleaned data and cleaning reports.

        Notes
        -----
        During initialization:

        - source data is read from ``hunter_core.target_data``
        - cleaned data is read from ``clarity_core.cleaned_data``
        - computed data is created as a copy of cleaned data when available
        - computation report is initialized to ``None``
        - computation history is initialized as an empty list
        """
        # ---------- Cores initialization / Data and records setup ----------
        self.hunter_core = hunter_core  # HuntingDataCore object
        self.clarity_core = clarity_core  # ClarityCore object

        self.source_data = hunter_core.target_data  # HuntingDataCore loaded target data
        self.cleaned_data = clarity_core.cleaned_data  # ClarityCore cleaned data
        self.computed_data = (
            self.cleaned_data.copy() if self.cleaned_data is not None else None
        )

        self.cleaned_data_report = (  # ClarityCore cleaned data report
            clarity_core.cleaned_data_report
        )
        self.compution_data_report: dict = None  # Record computed data report
        self.compution_history: list[dict] = []  # Record computed history

    # -------------------- Validation (helper) --------------------
    def _validation(self):
        """
        Validate the current computed dataset before running computation operations.

        Returns
        -------
        bool
            ``True`` if ``self.computed_data`` exists, is a pandas DataFrame,
            and is not empty; otherwise ``False``.

        Notes
        -----
        This helper checks three conditions:

        1. computed data is not ``None``
        2. computed data is a ``pandas.DataFrame``
        3. computed data is not empty

        If validation fails, a warning message is printed and the caller
        should stop the current operation.
        """
        if self.computed_data is None:
            print("⚠️ No computed data available ‼️")
            return False

        if not isinstance(self.computed_data, pd.DataFrame):
            print("⚠️ Computed data must be a pandas DataFrame ‼️")
            return False

        if self.computed_data.empty:
            print("⚠️ Computed data is empty ‼️")
            return False

        return True

    # -------------------- Column validation (helper) --------------------
    def _validate_columns(self, columns: list[str]):
        """
        Validate that the provided column list is usable and exists in computed data.

        Parameters
        ----------
        columns : list[str]
            Column names to validate against ``self.computed_data``.

        Returns
        -------
        bool
            ``True`` if ``columns`` is a non-empty list and every column exists
            in ``self.computed_data``; otherwise ``False``.

        Notes
        -----
        This helper is intended to guard computation methods before they attempt
        to access user-selected columns.
        """
        if columns is None or not isinstance(columns, list) or len(columns) == 0:
            print("⚠️ Columns must be a non-empty list ‼️")
            return False

        missing_cols = [col for col in columns if col not in self.computed_data.columns]
        if missing_cols:
            print(f"⚠️ Columns not found: {missing_cols} ‼️")
            return False

        return True

    # -------------------- Numeric columns validation (helper) --------------------
    def _validate_numeric_columns(self, columns: list[str]):
        """
        Validate that all specified columns are numeric.

        Parameters
        ----------
        columns : list[str]
            Column names that must have numeric dtype.

        Returns
        -------
        bool
            ``True`` if all selected columns are numeric; otherwise ``False``.

        Notes
        -----
        This helper uses ``pandas.api.types.is_numeric_dtype`` to verify that
        each selected column supports numeric computation.
        """
        non_numeric_cols = [
            col
            for col in columns
            if not pd.api.types.is_numeric_dtype(self.computed_data[col])
        ]

        if non_numeric_cols:
            print(f"⚠️ Columns must be numeric: {non_numeric_cols} ‼️")
            return False

        return True

    # -------------------- Compution history (helper) --------------------
    def _record_compution(
        self,
        action: str,
        before_shape: tuple,
        after_shape: tuple,
        details: dict = None,
        save_csv: bool = True,
    ):
        """
        Record a computation step and optionally export the computation history table.

        Parameters
        ----------
        action : str
            Name of the computation action that was executed.
        before_shape : tuple
            Shape of the DataFrame before the operation, typically ``(rows, columns)``.
        after_shape : tuple
            Shape of the DataFrame after the operation, typically ``(rows, columns)``.
        details : dict, optional
            Additional metadata describing the operation. Default is ``None``.
        save_csv : bool, default=True
            Whether to export the accumulated computation history table to a CSV file.

        Returns
        -------
        dict
            A record dictionary describing the latest computation step.

        Side Effects
        ------------
        - Appends a new record to ``self.compution_history``.
        - Updates ``self.compution_data_report``.
        - Optionally writes the full computation history table to CSV.

        Notes
        -----
        This helper is responsible only for recording computation metadata and
        optionally exporting the history table.

        It does not export the full current ``self.computed_data`` dataset.
        Full result-dataset export is handled separately by
        ``_save_computed_data_csv()``.

        The generated record typically contains:

        - step number
        - action name
        - before/after row count
        - before/after column count
        - additional operation-specific details

        If ``save_csv=True`` but no source file path is available from
        ``hunter_core.current_file_path``, a warning message is printed and the
        history CSV is not saved.
        """
        details = details or {}

        record = {
            "step": len(self.compution_history) + 1,
            "action": action,
            "before_rows": before_shape[0] if before_shape else None,
            "before_cols": before_shape[1] if before_shape else None,
            "after_rows": after_shape[0] if after_shape else None,
            "after_cols": after_shape[1] if after_shape else None,
            **details,
        }

        self.compution_history.append(record)

        self.compution_data_report = {
            "current_shape": self.computed_data.shape,
            "row_count": self.computed_data.shape[0],
            "column_count": self.computed_data.shape[1],
            "last_action": action,
            "last_details": details,
            "history_count": len(self.compution_history),
        }

        current_file_path = getattr(self.hunter_core, "current_file_path", None)

        if save_csv and current_file_path:
            history_df = pd.DataFrame(self.compution_history)
            base_name = os.path.splitext(os.path.basename(current_file_path))[0]
            save_path = os.path.join(CSV_DIR, f"{base_name}_Compution_Record.csv")
            history_df.to_csv(save_path, index=False, encoding="utf-8-sig")
        elif save_csv:
            print("⚠️ No current file path available, CSV record was not saved ‼️")

        return record

    # -------------------- Computing menu (helper) --------------------
    def _computing_menu(self):
        """
        Return the supported computation menu configuration.

        Returns
        -------
        dict
            A nested dictionary containing supported single-column and
            multi-column computation menu definitions.

        Notes
        -----
        The returned structure is intended for menu-driven interfaces and
        maps menu keys to internal operation names and human-readable descriptions.
        """
        return {
            # ---------- Single computing menu ----------
            "single_column": {
                "1": ("add", "Add constant to selected column"),
                "2": ("sub", "Subtract constant from selected column"),
                "3": ("mul", "Multiply selected column by constant"),
                "4": ("div", "Divide selected column by constant"),
                "5": ("abs", "Absolute value"),
                "6": ("round", "Round values"),
                "7": ("sqrt", "Square root"),
                "8": ("log", "Natural logarithm"),
            },
            # ---------- Multiple computing menu ----------
            "multi_column": {
                "1": ("sum", "Sum selected columns"),
                "2": ("mean", "Mean selected columns"),
                "3": ("max", "Maximum of selected columns"),
                "4": ("min", "Minimum of selected columns"),
                "5": ("product", "Multiply selected columns"),
                "6": ("sub", "Column A - Column B"),
                "7": ("div", "Column A / Column B"),
            },
        }

    # -------------------- Single column operations (helper) --------------------
    def _single_column_operations(self):
        """
        Return the mapping of supported single-column operations.

        Returns
        -------
        dict
            Dictionary mapping operation names to callable transformation functions.

        Notes
        -----
        Supported operations include:

        - ``add`` : add a constant
        - ``sub`` : subtract a constant
        - ``mul`` : multiply by a constant
        - ``div`` : divide by a constant
        - ``abs`` : absolute value
        - ``round`` : round values
        - ``sqrt`` : square root
        - ``log`` : natural logarithm
        """
        return {
            "add": lambda s, value: s + value,
            "sub": lambda s, value: s - value,
            "mul": lambda s, value: s * value,
            "div": lambda s, value: s / value,
            "abs": lambda s, value=None: s.abs(),
            "round": lambda s, value=None: s.round(2 if value is None else value),
            "sqrt": lambda s, value=None: np.sqrt(s),
            "log": lambda s, value=None: np.log(s),
        }

    # -------------------- Multi-column operations (helper) --------------------
    def _multi_column_operations(self):
        """
        Return the mapping of supported multi-column operations.

        Returns
        -------
        dict
            Dictionary mapping operation names to callable row-wise functions.

        Notes
        -----
        Supported operations include:

        - ``sum`` : row-wise sum across selected columns
        - ``mean`` : row-wise mean across selected columns
        - ``max`` : row-wise maximum across selected columns
        - ``min`` : row-wise minimum across selected columns
        - ``product`` : row-wise product across selected columns
        - ``sub`` : first column minus second column
        - ``div`` : first column divided by second column
        """
        return {
            "sum": lambda df, cols: df[cols].sum(axis=1),
            "mean": lambda df, cols: df[cols].mean(axis=1),
            "max": lambda df, cols: df[cols].max(axis=1),
            "min": lambda df, cols: df[cols].min(axis=1),
            "product": lambda df, cols: df[cols].prod(axis=1),
            "sub": lambda df, cols: df[cols[0]] - df[cols[1]],
            "div": lambda df, cols: df[cols[0]] / df[cols[1]],
        }

    # -------------------- Save computed data CSV (helper) --------------------
    def _save_computed_data_csv(self, action: str):
        """
        Save the current computed dataset to a CSV file.

        This helper exports the full current ``self.computed_data`` table after a
        successful computation workflow when the caller requests result saving.

        Parameters
        ----------
        action : str
            Name of the computation action used to build the output filename.

        Returns
        -------
        str | None
            Absolute save path of the exported CSV file if saving succeeds;
            otherwise ``None``.

        Side Effects
        ------------
        - Writes the current ``self.computed_data`` to a CSV file under ``CSV_DIR``.
        - Prints success or failure messages to the console.

        Notes
        -----
        - This helper saves the full current computed working dataset, not merely
        a computation history record.
        - If ``hunter_core.current_file_path`` is available, its base filename is used
        as the prefix of the exported CSV file.
        - If no current source-file path is available, the fallback base name
        ``"computed_data"`` is used.
        - The generated filename pattern is::

            {base_name}_{action}_Result.csv

        - This helper is intended for column-update style or reset workflows where the
        current ``self.computed_data`` represents the latest full computation result.
        - Groupby aggregation summary export is handled separately inside
        ``groupby_aggregation_calculation()``.
        """
        if self.computed_data is None or not isinstance(
            self.computed_data, pd.DataFrame
        ):
            print("⚠️ No computed data available to save ‼️")
            return None

        # -------------------- Get data name as file's name --------------------
        current_file_path = getattr(self.hunter_core, "current_file_path", None)

        if current_file_path:
            base_name = os.path.splitext(os.path.basename(current_file_path))[0]
        else:
            base_name = "computed_data"

        save_path = os.path.join(COMPUTED_DIR, f"{base_name}_{action}_Result.csv")

        try:
            self.computed_data.to_csv(save_path, index=False, encoding="utf-8-sig")
            print("🔥 Computed data CSV saved successfully 🔥")
            print(f"👣 Saved CSV file's path ---> {save_path}")
            return save_path
        except Exception as e:
            print(f"⚠️ Failed to save computed data CSV: {e} ‼️")
            return None

    # -------------------- Single column calculation --------------------
    def single_column_calculation(
        self,
        column: str,  # Only one column
        operation: str,
        value=None,
        new_column: str = None,
        inplace: bool = False,
        save_csv: bool = False,
    ):
        """
        Perform a numeric transformation on a single column.

        Parameters
        ----------
        column : str
            Source column to transform.
        operation : str
            Name of the single-column operation to apply.
        value : Any, optional
            Optional scalar used by operations that require an external value,
            such as add, subtract, multiply, divide, or custom rounding precision.
        new_column : str, optional
            Name of the output column when ``inplace=False``.
            If omitted, a default name of ``"{column}_{operation}"`` is used.
        inplace : bool, default=False
            Whether to overwrite the source column instead of creating a new column.
        save_csv : bool, default=False
            Whether to export computation records and the full current computed dataset
            to CSV after a successful operation.

        Returns
        -------
        pandas.DataFrame or None
            Updated computed DataFrame if successful; otherwise ``None``.

        Raises
        ------
        No exception is raised directly to the caller.
        Internal exceptions are caught and converted into warning messages.

        Notes
        -----
        Workflow
        ~~~~~~~~
        1. validate computed data
        2. validate source column existence
        3. validate operation support
        4. validate source column numeric type
        5. apply the transformation
        6. store the result in ``self.computed_data``
        7. record the operation in computation history
        8. optionally export the full current computed dataset to CSV
        9. return the updated DataFrame

        Examples of supported operations include:

        - add a constant
        - subtract a constant
        - multiply by a constant
        - divide by a constant
        - absolute value
        - rounding
        - square root
        - natural logarithm

        CSV behavior
        ~~~~~~~~~~~~
        If ``save_csv=True``, this method may produce two kinds of CSV output:

        - computation-history CSV through ``_record_compution()``
        - full current computed-data CSV through ``_save_computed_data_csv()``
        """
        if not self._validation():
            return None

        if not self._validate_columns([column]):
            return None

        # ---------- Single computing operations ----------
        operations = self._single_column_operations()
        if operation not in operations:
            print(f"⚠️ Unsupported single column operation: {operation} ‼️")
            return None

        if not self._validate_numeric_columns([column]):
            return None

        before_shape = self.computed_data.shape
        target_column = column if inplace else (new_column or f"{column}_{operation}")

        # ---------- Single computing process ----------
        try:
            result = operations[operation](self.computed_data[column], value)
            self.computed_data[target_column] = result
        except Exception as e:
            print(f"⚠️ Single column calculation failed: {e} ‼️")
            return None

        after_shape = self.computed_data.shape

        # ---------- Single computing history and records ----------
        details = {
            "column": column,
            "operation": operation,
            "value": value,
            "new_column": target_column,
            "inplace": inplace,
        }

        record = self._record_compution(
            action="single_column_calculation",
            before_shape=before_shape,
            after_shape=after_shape,
            details=details,
            save_csv=save_csv,
        )

        if save_csv:
            self._save_computed_data_csv("single_column_calculation")

        print(f"🔥 Single column calculation completed: {target_column}")
        print(f"🧾 Current history record: {record}")
        return self.computed_data

    # -------------------- Multiple columns calculation --------------------
    def multiple_columns_calculation(
        self,
        columns: list[str],
        operation: str,
        new_column: str = None,
        save_csv: bool = False,
    ):
        """
        Perform a row-wise calculation across multiple numeric columns.

        This method applies a supported multi-column operation to the selected columns
        in ``self.computed_data`` and stores the result in a target output column.
        When ``new_column`` is not provided, a default output column name is generated
        automatically from the selected source columns and the operation name.

        Parameters
        ----------
        columns : list[str]
            Source column names used in the calculation.

            All specified columns must:

            - exist in ``self.computed_data``
            - be numeric
            - form a non-empty list

        operation : str
            Name of the multi-column operation to apply.

            Supported operations are:

            - ``"sum"``
            - ``"mean"``
            - ``"max"``
            - ``"min"``
            - ``"product"``
            - ``"sub"``
            - ``"div"``

        new_column : str, optional
            Name of the output column used to store the calculation result.

            If omitted or ``None``, a default column name is generated as::

                "{col1}_{col2}_..._{operation}"

        save_csv : bool, default=False
            Whether to export computation records and the full current computed dataset
            to CSV after a successful operation.

        Returns
        -------
        pandas.DataFrame or None
            Updated computed DataFrame if the operation succeeds; otherwise ``None``.

        Notes
        -----
        Supported row-wise behaviors
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        The method supports the following row-wise calculations:

        - ``sum`` : sum across selected columns
        - ``mean`` : mean across selected columns
        - ``max`` : maximum across selected columns
        - ``min`` : minimum across selected columns
        - ``product`` : product across selected columns
        - ``sub`` : first selected column minus second selected column
        - ``div`` : first selected column divided by second selected column

        Validation rules
        ~~~~~~~~~~~~~~~~
        Before performing the calculation, this method validates that:

        1. ``self.computed_data`` is available and usable
        2. all selected columns exist
        3. all selected columns are numeric
        4. the requested operation is supported
        5. ``sub`` and ``div`` receive exactly two columns

        Execution flow
        ~~~~~~~~~~~~~~
        This method performs the following steps:

        1. validate computation state
        2. validate selected columns
        3. validate operation name
        4. validate numeric dtypes
        5. determine the final output column name
        6. execute the row-wise operation
        7. store the result in ``self.computed_data``
        8. record the operation through ``self._record_compution()``
        9. optionally export the full current computed dataset through
        ``self._save_computed_data_csv()``
        10. print completion and history information
        11. return the updated DataFrame

        CSV behavior
        ~~~~~~~~~~~~
        If ``save_csv=True``, this method may produce:

        - computation-history CSV
        - full current computed-data CSV
        """
        if not self._validation():
            return None

        if not self._validate_columns(columns):
            return None

        # ---------- Multiple computing operations ----------
        operations = self._multi_column_operations()
        if operation not in operations:
            print(f"⚠️ Unsupported multi-column operation: {operation} ‼️")
            return None

        if operation in ["sub", "div"] and len(columns) != 2:
            print(f"⚠️ Operation '{operation}' requires exactly 2 columns ‼️")
            return None

        if not self._validate_numeric_columns(columns):
            return None

        before_shape = self.computed_data.shape

        target_column = new_column or f"{'_'.join(columns)}_{operation}"

        # ---------- Multiple computing process ----------
        try:
            result = operations[operation](self.computed_data, columns)
            self.computed_data[target_column] = result
        except Exception as e:
            print(f"⚠️ Multiple columns calculation failed: {e} ‼️")
            return None

        after_shape = self.computed_data.shape

        # ---------- Multiple computing history and records ----------
        details = {
            "columns": columns,
            "operation": operation,
            "new_column": target_column,
        }

        record = self._record_compution(
            action="multiple_columns_calculation",
            before_shape=before_shape,
            after_shape=after_shape,
            details=details,
            save_csv=save_csv,
        )

        if save_csv:
            self._save_computed_data_csv("multiple_columns_calculation")

        print(f"🔥 Multiple columns calculation completed: {target_column}")
        print(f"🧾 Current history record: {record}")
        return self.computed_data

    # -------------------- Groupby aggregation calculation --------------------
    def groupby_aggregation_calculation(
        self,
        groupby_columns: list[str],
        target_columns: list[str],
        agg_method: str | list[str],
        save_csv: bool = True,
    ):
        """
        Perform grouped aggregation on selected numeric columns from ``computed_data``.

        Parameters
        ----------
        groupby_columns : list[str]
            Column names used as grouping keys.

            Each element must be a string and must exist in ``self.computed_data``.
            These columns define how rows are partitioned before aggregation is applied.

        target_columns : list[str]
            Numeric column names to aggregate within each group.

            Each element must be a string, must exist in ``self.computed_data``, and
            must be validated as numeric before aggregation is performed.

        agg_method : str | list[str]
            Aggregation method name, or a non-empty list of aggregation method names,
            applied to ``target_columns``.

            Supported aggregation methods are:

            - ``"sum"``
            - ``"mean"``
            - ``"max"``
            - ``"min"``
            - ``"count"``
            - ``"median"``
            - ``"std"``

        save_csv : bool, default=True
            Whether to export the grouped aggregation summary result to CSV and whether
            the computation-history helper should also export its related record table.

        Returns
        -------
        pandas.DataFrame | None
            A grouped and aggregated DataFrame if the operation succeeds; otherwise
            ``None``.

        Notes
        -----
        This method differs from column-update style computation methods.

        - It uses ``self.computed_data`` as the input dataset.
        - It returns a grouped summary DataFrame named conceptually as ``grouped_df``.
        - It may export that grouped summary result to CSV.
        - It does not overwrite ``self.computed_data`` by default.

        CSV behavior
        ~~~~~~~~~~~~
        If ``save_csv=True``, this method may produce:

        - computation-history CSV through ``_record_compution()``
        - grouped aggregation summary CSV through the method's own export logic

        It does not export the full current ``self.computed_data`` through
        ``_save_computed_data_csv()`` because the grouped result is treated as a
        summary output rather than as the default replacement working dataset.
        """
        if not self._validation():
            return None

        if not self._validate_columns(groupby_columns):
            return None

        if not self._validate_columns(target_columns):
            return None

        if not self._validate_numeric_columns(target_columns):
            return None

        supported_agg_methods = ["sum", "mean", "max", "min", "count", "median", "std"]

        if isinstance(agg_method, str):
            agg_methods = [agg_method]
        elif isinstance(agg_method, list) and agg_method:
            agg_methods = agg_method
        else:
            print("⚠️ agg_method must be a string or non-empty list of strings ‼️")
            return None

        invalid_methods = [m for m in agg_methods if m not in supported_agg_methods]
        if invalid_methods:
            print(f"⚠️ Unsupported aggregation methods: {invalid_methods} ‼️")
            return None

        before_shape = self.computed_data.shape

        agg_input = agg_methods[0] if len(agg_methods) == 1 else agg_methods
        try:
            grouped_df = (
                self.computed_data.groupby(groupby_columns)[target_columns]
                .agg(agg_input)
                .reset_index()
            )
        except Exception as e:
            print(f"⚠️ Groupby aggregation calculation failed: {e} ‼️")
            return None

        after_shape = grouped_df.shape

        # ---------- Flatten MultiIndex columns if needed ----------
        if isinstance(grouped_df.columns, pd.MultiIndex):
            grouped_df.columns = [
                "_".join([str(level) for level in col if str(level) != ""])
                for col in grouped_df.columns.to_flat_index()
            ]

        details = {
            "groupby_columns": groupby_columns,
            "target_columns": target_columns,
            "agg_method": agg_method,
            "result_rows": grouped_df.shape[0],
            "result_cols": grouped_df.shape[1],
        }

        record = self._record_compution(
            action="groupby_aggregation_calculation",
            before_shape=before_shape,
            after_shape=after_shape,
            details=details,
            save_csv=save_csv,
        )

        if save_csv:
            current_file_path = getattr(self.hunter_core, "current_file_path", None)
            if current_file_path:
                base_name = os.path.splitext(os.path.basename(current_file_path))[0]
            else:
                base_name = "computed_data"

            agg_name = "_".join(agg_methods)
            save_path = os.path.join(
                CSV_DIR, f"{base_name}_Groupby_{agg_name}_Summary.csv"
            )
            grouped_df.to_csv(save_path, index=False, encoding="utf-8-sig")

        print("🔥 Groupby aggregation calculation completed")
        print(f"🧾 Current history record: {record}")
        return grouped_df

    # -------------------- Reset computed data --------------------
    def reset_computed_data(
        self,
        save_csv: bool = True,
    ):
        """
        Reset the working computed dataset back to the cleaned-data baseline.

        Parameters
        ----------
        save_csv : bool, default=True
            Whether to record the reset operation and optionally export the full reset
            computed dataset to CSV.

        Returns
        -------
        pandas.DataFrame or None
            Reset computed DataFrame if successful; otherwise ``None``.

        Notes
        -----
        This method does not restore from raw source data.
        Instead, it restores ``self.computed_data`` from ``self.cleaned_data``.

        The reset operation is appended to computation history so that the reset event
        becomes part of the operation audit trail.

        CSV behavior
        ~~~~~~~~~~~~
        If ``save_csv=True``, this method may produce:

        - computation-history CSV through ``_record_compution()``
        - full current computed-data CSV through ``_save_computed_data_csv()``

        This exported result reflects the reset state after ``self.computed_data`` has
        been rebuilt from ``self.cleaned_data``.
        """
        if not self._validation():
            return None

        before_shape = (
            self.computed_data.shape
            if isinstance(self.computed_data, pd.DataFrame)
            else None
        )

        self.cleaned_data = self.clarity_core.cleaned_data
        self.computed_data = self.cleaned_data.copy()

        after_shape = self.computed_data.shape

        details = {
            "reset_from": "cleaned_data",
            "row_count": self.computed_data.shape[0],
            "column_count": self.computed_data.shape[1],
        }

        record = self._record_compution(
            action="reset_computed_data",
            before_shape=before_shape,
            after_shape=after_shape,
            details=details,
            save_csv=save_csv,
        )

        print("🔥 Computed data has been reset from cleaned data")
        print(f"🧾 Current history record: {record}")
        return self.computed_data

    # -------------------- Conditional calculation --------------------
    def conditional_calculation(
        self,
        source_column: str,
        operator: str,
        threshold,
        true_value,
        false_value,
        new_column: str = None,
        save_csv: bool = True,
    ):
        """
        Create a derived column based on a conditional rule.

        This method evaluates one source column against a threshold by using a selected
        comparison operator and creates a new output column from the resulting Boolean
        condition. Values meeting the condition receive ``true_value``; all other rows
        receive ``false_value``.

        When ``new_column`` is not provided, a default output column name is generated
        automatically as ``"{source_column}_flag"``.

        Parameters
        ----------
        source_column : str
            Column whose values are evaluated against the condition.

            This column must exist in ``self.computed_data``.

        operator : str
            Comparison operator used to build the condition.

            Supported operators are:

            - ``">"``
            - ``">="``
            - ``"<"``
            - ``"<="``
            - ``"=="``
            - ``"!="``

        threshold : Any
            Threshold or comparison value used with ``source_column``.

        true_value : Any
            Value assigned to the output column where the condition evaluates to
            ``True``.

        false_value : Any
            Value assigned to the output column where the condition evaluates to
            ``False``.

        new_column : str, optional
            Name of the output column to create.

            If omitted or ``None``, a default output column name is generated as::

                "{source_column}_flag"

        save_csv : bool, default=True
            Whether to record the operation and optionally export the full current
            computed dataset to CSV after success.

        Returns
        -------
        pandas.DataFrame or None
            Updated computed DataFrame if the operation succeeds; otherwise ``None``.

        Notes
        -----
        Purpose
        ~~~~~~~
        This method is useful for building rule-based engineered features such as:

        - pass/fail labels
        - threshold-based categories
        - binary indicator columns
        - condition flags used for downstream machine-learning workflows

        Execution method
        ~~~~~~~~~~~~~~~~
        The output column is created by using ``numpy.where`` on the generated Boolean
        condition.

        Validation rules
        ~~~~~~~~~~~~~~~~
        Before performing the calculation, this method validates that:

        1. ``self.computed_data`` is available and usable
        2. ``source_column`` exists
        3. ``operator`` is one of the supported comparison operators

        Execution flow
        ~~~~~~~~~~~~~~
        This method performs the following steps:

        1. validate computation state
        2. validate source column existence
        3. validate comparison operator
        4. determine the final output column name
        5. build the Boolean condition
        6. create the output column with ``numpy.where``
        7. record the operation through ``self._record_compution()``
        8. optionally export the full current computed dataset through
        ``self._save_computed_data_csv()``
        9. print completion and history information
        10. return the updated DataFrame

        CSV behavior
        ~~~~~~~~~~~~
        If ``save_csv=True``, this method may produce:

        - computation-history CSV
        - full current computed-data CSV
        """
        if not self._validation():
            return None

        if not self._validate_columns([source_column]):
            return None

        supported_operators = [">", ">=", "<", "<=", "==", "!="]
        if operator not in supported_operators:
            print(f"⚠️ Unsupported operator: {operator} ‼️")
            return None

        before_shape = self.computed_data.shape

        target_column = new_column or f"{source_column}_flag"

        try:
            if operator == ">":
                condition = self.computed_data[source_column] > threshold
            elif operator == ">=":
                condition = self.computed_data[source_column] >= threshold
            elif operator == "<":
                condition = self.computed_data[source_column] < threshold
            elif operator == "<=":
                condition = self.computed_data[source_column] <= threshold
            elif operator == "==":
                condition = self.computed_data[source_column] == threshold
            elif operator == "!=":
                condition = self.computed_data[source_column] != threshold

            self.computed_data[target_column] = np.where(
                condition,
                true_value,
                false_value,
            )

        except Exception as e:
            print(f"⚠️ Conditional calculation failed: {e} ‼️")
            return None

        after_shape = self.computed_data.shape

        details = {
            "source_column": source_column,
            "operator": operator,
            "threshold": threshold,
            "true_value": true_value,
            "false_value": false_value,
            "new_column": target_column,
        }

        record = self._record_compution(
            action="conditional_calculation",
            before_shape=before_shape,
            after_shape=after_shape,
            details=details,
            save_csv=save_csv,
        )

        if save_csv:
            self._save_computed_data_csv("conditional_calculation")

        print(f"🔥 Conditional calculation completed: {target_column}")
        print(f"🧾 Current history record: {record}")
        return self.computed_data


# =================================================

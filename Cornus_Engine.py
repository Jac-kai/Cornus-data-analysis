# -------------------- Import Modules --------------------
import logging

from Cornus.Data_Hunter.HuntingDataCore import HuntingDataCore
from Cornus.MetaUnits.ClarityCore import ClarityCore
from Cornus.MetaUnits.ComputionCore import ComputionCore
from Cornus.MetaUnits.TransViewCore import TransViewCore
from Cornus.MetaUnits.TrendencyCore import TrendencyCore
from Cornus.MetaUnits.VisionCore import VisionCore

logger = logging.getLogger("Cornus")


# -------------------- Cornus engine --------------------
class CornusEngine:
    """
    Top-level orchestration engine for the Cornus data workflow.

    `CornusEngine` serves as the central controller that coordinates data loading,
    inspection, cleaning, calculation, reshaping, and visualization across the
    Cornus project. It provides a unified interface for interacting with all major
    pipeline cores so that external menus, scripts, or workflow controllers do not
    need to call each core directly.

    The engine is responsible for:

    - creating the source-data loading core,
    - building downstream processing cores after data is loaded,
    - refreshing dependent cores when the cleaned dataset changes,
    - exposing high-level dispatcher methods for each functional module.

    Pipeline Components
    -------------------
    The engine manages the following cores:

    - `HuntingDataCore`
    Handles folder search, file discovery, and source-data loading.
    - `VisionCore`
    Handles data-content inspection, null summaries, and report generation.
    - `ClarityCore`
    Handles cleaning and preprocessing operations.
    - `ComputionCore`
    Handles derived columns, arithmetic operations, grouped summaries, and
    conditional calculations.
    - `TransViewCore`
    Handles reshape and structure-transform operations such as stack, unstack,
    melt, pivot, and pivot table.
    - `TrendencyCore`
    Handles visualization and plot-based trend inspection.

    Data Flow
    ---------
    A typical workflow through the engine is:

    1. Load source data through `HuntingDataCore`.
    2. Build all downstream cores using `build_cores()`.
    3. Inspect raw data through `VisionCore`.
    4. Clean data through `ClarityCore`.
    5. Refresh downstream cores if cleaned data changes inplace.
    6. Perform calculations, reshaping, or plotting through the corresponding
    dispatcher methods.

    Attributes
    ----------
    hunter_core : HuntingDataCore
        Source-data loading core. Created immediately during engine initialization.
    vision_core : VisionCore or None
        Inspection/reporting core. Built after source data is loaded.
    clarity_core : ClarityCore or None
        Cleaning/preprocessing core. Built after source data is loaded.
    compution_core : ComputionCore or None
        Calculation/feature-engineering core. Built after source data is loaded.
    transview_core : TransViewCore or None
        Reshape/transformation-view core. Built after source data is loaded.
    trendency_core : TrendencyCore or None
        Visualization/trend-inspection core. Built after source data is loaded.

    Notes
    -----
    - The engine is intentionally designed as a dispatcher/controller layer rather
    than a place for direct data-processing logic.
    - Downstream cores depend on the currently loaded source data and cleaned data,
    so refresh behavior is important when inplace cleaning modifies the working
    dataset.
    - This class is intended to be the main access point used by menu systems and
    command-style workflows.
    """

    # -------------------- Initialization --------------------
    def __init__(self):
        """
        Initialize the Cornus engine and prepare all pipeline-core references.

        This constructor creates the source-data loading core immediately and sets all
        other downstream cores to `None`. The remaining cores are built later only
        after a dataset has been successfully loaded.

        Attributes Initialized
        ----------------------
        hunter_core : HuntingDataCore
            Newly created source-data loader.
        vision_core : None
            Placeholder for the inspection/reporting core.
        clarity_core : None
            Placeholder for the cleaning/preprocessing core.
        compution_core : None
            Placeholder for the calculation core.
        transview_core : None
            Placeholder for the reshape/transformation core.
        trendency_core : None
            Placeholder for the visualization core.

        Notes
        -----
        This delayed initialization keeps the pipeline safe by ensuring that dependent
        cores are only constructed when valid source data exists.
        """
        # -------------------- Pipeline each metaUnits --------------------
        self.hunter_core = HuntingDataCore()
        self.vision_core = None
        self.clarity_core = None
        self.compution_core = None
        self.transview_core = None
        self.trendency_core = None
        logger.info("CornusEngine initialized")

    # -------------------- Source data property --------------------
    @property
    def source_data(self):
        """
        Return the currently loaded raw source dataset.

        This property exposes the dataset stored in `self.hunter_core.target_data`,
        which represents the original loaded data before cleaning, transformation, or
        feature engineering.

        Returns
        -------
        pandas.DataFrame or None
            The currently loaded raw dataset, or `None` if no dataset has been loaded.

        Notes
        -----
        This is the upstream dataset used to build all downstream pipeline cores.
        """
        return self.hunter_core.target_data

    # -------------------- Cleaned data property --------------------
    @property
    def cleaned_data(self):
        """
        Return the current cleaned dataset managed by `ClarityCore`.

        This property provides access to the cleaned working dataset after cleaning or
        preprocessing operations have been applied.

        Returns
        -------
        pandas.DataFrame or None
            The cleaned dataset from `self.clarity_core.cleaned_data`, or `None` if the
            cleaning core has not been initialized.

        Notes
        -----
        This dataset is commonly used as the source for downstream computation,
        transformation-view, and plotting operations.
        """
        if self.clarity_core is None:
            return None
        return self.clarity_core.cleaned_data  # From raw data (HunteringData)

    # -------------------- Computed data property --------------------
    @property
    def computed_data(self):
        """
        Return the current computed dataset managed by `ComputionCore`.

        This property exposes the working dataset maintained by the computation core,
        which may contain derived columns, grouped summaries, conditional results, or
        other calculated outputs.

        Returns
        -------
        pandas.DataFrame or None
            The computed dataset from `self.compution_core.computed_data`, or `None` if
            the computation core has not been initialized.

        Notes
        -----
        The exact contents depend on the most recent computation actions performed.
        """
        if self.compution_core is None:
            return None
        return self.compution_core.computed_data  # From cleaned_data (ClarityCore)

    # -------------------- Transview data property --------------------
    @property
    def transview_data(self):
        """
        Return the most recent transformation-view result managed by `TransViewCore`.

        This property exposes the latest reshaped or structure-transformed dataset
        stored by `TransViewCore`, such as the result of stack, unstack, melt,
        pivot, or pivot-table operations when those methods were executed with
        `inplace=True`.

        Returns
        -------
        pandas.DataFrame or None
            The most recent transformation result from
            `self.transview_core.transview_data`, or `None` if the transview core
            has not been initialized or no transformation result has been stored yet.

        Notes
        -----
        This property does not represent the default baseline dataset used by
        transformation methods. In the current design, `TransViewCore` uses
        cleaned data as the baseline input for each transformation method, while
        `transview_data` stores only the most recent saved transformation result.
        """
        if self.transview_core is None:
            return None
        return self.transview_core.transview_data  # Most recent saved transview result

    # -------------------- Build pipeline cores --------------------
    def build_cores(self):
        """
        Build all downstream cores after source data has been loaded.

        This method initializes the inspection, cleaning, computation,
        transformation-view, and visualization cores using the current source dataset.
        It should be called only after valid source data has been loaded into
        `self.hunter_core.target_data`.

        Raises
        ------
        ValueError
            If no source dataset is available.

        Side Effects
        ------------
        Creates or replaces the following engine attributes:

        - `self.vision_core`
        - `self.clarity_core`
        - `self.compution_core`
        - `self.transview_core`
        - `self.trendency_core`

        Notes
        -----
        - `VisionCore` depends on `HuntingDataCore`.
        - `ClarityCore` depends on `HuntingDataCore` and `VisionCore`.
        - `ComputionCore`, `TransViewCore`, and `TrendencyCore` depend on the cleaned
        dataset managed by `ClarityCore`.
        - This method is typically called immediately after successful data upload.
        """
        if self.source_data is None:
            logger.error("build_cores() called without source data")
            raise ValueError("⚠️ No source data available. Please load data first ‼️")

        logger.info("Building downstream cores")
        self.vision_core = VisionCore(self.hunter_core)
        self.clarity_core = ClarityCore(self.hunter_core, self.vision_core)
        self.compution_core = ComputionCore(self.hunter_core, self.clarity_core)
        self.transview_core = TransViewCore(self.hunter_core, self.clarity_core)
        self.trendency_core = TrendencyCore(self.hunter_core, self.clarity_core)
        logger.info("Building downstream cores")

    # -------------------- Refresh all pipeline cores (Changing another dataset) --------------------
    def refresh_cores(self):
        """
        Rebuild the full downstream pipeline from the current source dataset.

        This method refreshes all downstream cores by calling `build_cores()`. It is
        typically used when the user switches to a different source dataset and the
        entire processing pipeline must be reconstructed.

        Returns
        -------
        None

        Notes
        -----
        Use this method when the raw dataset itself has changed, not merely when the
        cleaned dataset has been updated inplace.
        """
        self.build_cores()
        logger.info("Refreshing all downstream cores")

    # -------------------- Refresh downstream cores (Update same dataset) --------------------
    def refresh_downstream_cores(self):
        """
        Refresh downstream cores that depend on the current cleaned dataset.

        This method rebuilds the computation, transformation-view, and visualization
        cores using the current `hunter_core` and `clarity_core`. It is intended for
        cases where the raw source dataset stays the same but the cleaned dataset has
        been modified inplace.

        Returns
        -------
        None

        Side Effects
        ------------
        Replaces the following attributes with newly initialized core instances:

        - `self.compution_core`
        - `self.transview_core`
        - `self.trendency_core`

        Notes
        -----
        - This method does not rebuild `VisionCore` or `ClarityCore`.
        - If `self.clarity_core` is not initialized, the refresh is skipped and a
        warning message is printed.
        - This method is commonly triggered after successful cleaning operations with
        `inplace=True`.
        """
        if self.clarity_core is None:
            logger.warning(
                "refresh_downstream_cores() skipped because clarity_core is not initialized"
            )
            print(
                "⚠️ Clarity core is not initialized. Cannot refresh downstream cores ‼️"
            )
            return

        logger.info(
            "Refreshing computation/transview/trendency cores from current cleaned data"
        )
        self.compution_core = ComputionCore(self.hunter_core, self.clarity_core)
        self.transview_core = TransViewCore(self.hunter_core, self.clarity_core)
        self.trendency_core = TrendencyCore(self.hunter_core, self.clarity_core)
        logger.info(
            "Refreshing computation/transview/trendency cores from current cleaned data"
        )

    # -------------------- Huntering data --------------------
    def upload_data(
        self,
        selected_folder_num: int,
        selected_file_num: int,
        opener_param_dict: dict | None = None,
    ):
        """
        Load source data through ``HuntingDataCore`` and initialize all downstream cores.

        This method performs the full source-data loading workflow, including working
        directory search, file selection, file opening, and downstream pipeline-core
        construction. When data loading succeeds, all dependent cores are initialized
        automatically so the loaded dataset can be inspected, cleaned, computed,
        transformed, and visualized in later steps.

        Parameters
        ----------
        selected_folder_num : int
            Menu number identifying the folder that contains the target file.
        selected_file_num : int
            Menu number identifying the target file within the selected folder.
        opener_param_dict : dict | None, optional
            Optional dictionary of keyword arguments forwarded to
            ``self.hunter_core.opener(...)``. If ``None``, an empty dictionary is used.

        Returns
        -------
        pandas.DataFrame or None
            The dataset returned by ``self.hunter_core.opener(...)``, or ``None`` if
            loading fails.

        Workflow
        --------
        1. Search available working folders.
        2. Search files inside the selected folder.
        3. Open the selected file.
        4. If loading succeeds, build all downstream cores automatically.

        Notes
        -----
        - This method is the main entry point for loading a new dataset into the engine.
        - Successful loading initializes the full downstream pipeline.
        - If loading fails, downstream cores are not rebuilt.
        """
        logger.info(
            "upload_data() called with selected_folder_num=%s, selected_file_num=%s",
            selected_folder_num,
            selected_file_num,
        )

        # ---------- Searching folder and file ----------
        self.hunter_core.working_place_searcher()
        self.hunter_core.files_searcher_from_folders(
            selected_folder_num=selected_folder_num,
            selected_file_num=selected_file_num,
        )

        # ---------- Opening target data ----------
        opener_param_dict = opener_param_dict or {}
        upload_data = self.hunter_core.opener(**opener_param_dict)

        if upload_data is not None:
            logger.info(
                "Source data uploaded successfully with shape=%s",
                getattr(upload_data, "shape", None),
            )
        else:
            logger.warning("upload_data() returned None")

        if (
            upload_data is not None
        ):  # Initialize other cores after uploading target data
            self.build_cores()
            logger.info("Pipeline cores initialized after upload")

        return upload_data

    # ---------- Viewing data ----------
    def viewing_data(
        self,
        action: str,
        index: list | None = None,
        column: list[str] | None = None,
    ):
        """
        Dispatch data-inspection and reporting actions to ``VisionCore``.

        This method provides a unified engine-level interface for dataset inspection
        services such as content summary, null inspection, subset viewing, and report
        generation. It validates that the vision core is available and forwards the
        requested viewing action to the corresponding ``VisionCore`` method.

        Parameters
        ----------
        action : str
            Viewing action name. Supported actions include:

            - ``"data_content"``
            - ``"null_summary"``
            - ``"selected_column_or_index"``
            - ``"save_data_report"``
            - ``"full_data_report"``
        index : list | None, optional
            Optional index labels used for row-level subset inspection.
        column : list[str] | None, optional
            Optional column names used for column-level subset inspection.

        Returns
        -------
        Any
            The result returned by the selected ``VisionCore`` method, or ``None`` if
            the vision core is unavailable or the action is unsupported.

        Supported Actions
        -----------------
        ``"data_content"``
            Return general information about the current dataset.
        ``"null_summary"``
            Return null-value inspection results.
        ``"selected_column_or_index"``
            Return a selected subset of the dataset using row and/or column filters.
        ``"save_data_report"``
            Save a report for the current dataset.
        ``"full_data_report"``
            Save a more complete text-based data report.

        Notes
        -----
        - If ``self.vision_core`` is not initialized, the method prints a warning and
        returns ``None``.
        - This method acts only as a dispatcher; detailed inspection logic remains in
        ``VisionCore``.
        """
        if self.vision_core is None:
            logger.warning("viewing_data() called before vision_core initialization")
            print("⚠️ Vision core is not initialized. Please upload data first ‼️")
            return None

        # ---------- Data content ----------
        logger.info("viewing_data() action=%s", action)
        if action == "data_content":
            return self.vision_core.data_content_info_core()

        # ---------- Null inspections ----------
        elif action == "null_summary":
            return self.vision_core.null_inspection_core()

        # ---------- Data viewing by selected columns and index ----------
        elif action == "selected_column_or_index":
            return self.vision_core.data_inspection_by_column_index(
                index=index,
                column=column,
            )

        # ---------- Save data information ----------
        elif action == "save_data_report":
            return self.vision_core.save_data_report_core()

        elif action == "full_data_report":
            return self.vision_core.save_full_data_report_txt()

        else:
            logger.warning("Unsupported viewing action: %s", action)
            print(f"⚠️ Unsupported viewing action: {action} ‼️")
            return None

    # -------------------- View pre-cleaning report --------------------
    def view_data_before_cleaning(self):
        """
        Return the pre-cleaning data view managed by `ClarityCore`.

        This method exposes the cleaning core's internal snapshot or report of the data
        before cleaning operations were applied.

        Returns
        -------
        Any
            The value returned by `self.clarity_core._view_data_before_cleaning()`, or
            `None` if the cleaning core is not initialized.

        Notes
        -----
        - This method is useful when comparing the original and cleaned states of the
        dataset.
        - The underlying core method is internal, as indicated by the leading
        underscore in its name.
        """
        if self.clarity_core is None:
            logger.warning(
                "view_data_before_cleaning() called before clarity_core initialization"
            )
            print("⚠️ Clarity core is not initialized. Please upload data first ‼️")
            return None

        logger.info("view_data_before_cleaning() called")
        return self.clarity_core._view_data_before_cleaning()

    # -------------------- Clarity data --------------------
    def clarity_data(self, action: str, **kwargs):
        """
        Dispatch cleaning and preprocessing actions to `ClarityCore`.

        This method acts as the engine-level interface for cleaning operations. It
        validates that the cleaning core is available, forwards the requested action
        and parameters to the matching `ClarityCore` method, and refreshes downstream
        cores when an inplace update succeeds.

        Parameters
        ----------
        action : str
            Cleaning action name. Supported actions include:

            - ``"drop_rows"``
            - ``"drop_columns"``
            - ``"drop_rows_by_value"``
            - ``"drop_columns_by_value"``
            - ``"drop_missing_values"``
            - ``"drop_duplicates"``
            - ``"fill_values"``
            - ``"strip_string_values"``
            - ``"replace_values"``
        **kwargs
            Additional keyword arguments forwarded to the selected cleaning method.

        Returns
        -------
        Any
            Result returned by the corresponding `ClarityCore` method, or `None` if the
            cleaning core is unavailable or the action is unsupported.

        Side Effects
        ------------
        If the cleaning action succeeds and ``inplace=True`` is specified, dependent
        downstream cores are refreshed through `self.refresh_downstream_cores()`.

        Supported Actions
        -----------------
        ``"drop_rows"``
            Drop rows by target index labels.
        ``"drop_columns"``
            Drop selected columns by name.
        ``"drop_rows_by_value"``
            Drop rows based on matching values in selected columns.
        ``"drop_columns_by_value"``
            Drop columns based on matching values.
        ``"drop_missing_values"``
            Remove missing values according to the chosen policy.
        ``"drop_duplicates"``
            Remove duplicated rows.
        ``"fill_values"``
            Fill missing values in selected columns.
        ``"strip_string_values"``
            Strip leading and trailing whitespace from string columns.
        ``"replace_values"``
            Replace values within selected columns.

        Notes
        -----
        - This method centralizes cleaning access for terminal menus or higher-level
        workflow controllers.
        - Refreshing downstream cores is necessary because computation,
        transformation-view, and plotting services depend on the latest cleaned data.
        """
        if self.clarity_core is None:
            logger.warning("clarity_data() called before clarity_core initialization")
            print("⚠️ Clarity core is not initialized. Please upload data first ‼️")
            return None

        result = None
        inplace = kwargs.get("inplace", False)
        logger.info("clarity_data() action=%s, inplace=%s", action, inplace)

        # ---------- Drop rows by index ----------
        if action == "drop_rows":
            result = self.clarity_core.drop_rows_core(
                target_index=kwargs.get("target_index"),
                inplace=inplace,
            )

        # ---------- Drop columns by name ----------
        elif action == "drop_columns":
            result = self.clarity_core.drop_columns_core(
                target_columns=kwargs.get("target_columns"),
                inplace=inplace,
            )

        # ---------- Drop rows by specific values ----------
        elif action == "drop_rows_by_value":
            result = self.clarity_core.drop_rows_by_value_core(
                target_columns=kwargs.get("target_columns"),
                drop_values=kwargs.get("drop_values"),
                inplace=inplace,
            )

        # ---------- Drop columns by specific values ----------
        elif action == "drop_columns_by_value":
            result = self.clarity_core.drop_columns_by_value_core(
                target_columns=kwargs.get("target_columns"),
                drop_values=kwargs.get("drop_values"),
                inplace=inplace,
            )

        # ---------- Drop missing values ----------
        elif action == "drop_missing_values":
            result = self.clarity_core.drop_missing_values(
                target_columns=kwargs.get("target_columns"),
                how=kwargs.get("how", "any"),
                inplace=inplace,
            )

        # ---------- Drop duplicates ----------
        elif action == "drop_duplicates":
            result = self.clarity_core.drop_duplicates(
                subset=kwargs.get("subset"),
                keep=kwargs.get("keep", "first"),
                inplace=inplace,
            )

        # ---------- Fill missing values ----------
        elif action == "fill_values":
            result = self.clarity_core.fill_values_in_data(
                fill_value=kwargs.get("fill_value"),
                target_columns=kwargs.get("target_columns"),
                inplace=inplace,
            )

        # ---------- Strip whitespace ----------
        elif action == "strip_string_values":
            result = self.clarity_core.strip_string_values(
                target_columns=kwargs.get("target_columns"),
                inplace=inplace,
            )

        # ---------- Replace values ----------
        elif action == "replace_values":
            result = self.clarity_core.replace_values_core(
                to_replace=kwargs.get("to_replace"),
                value=kwargs.get("value"),
                target_columns=kwargs.get("target_columns"),
                inplace=inplace,
            )

        else:
            logger.warning("Unsupported clarity action: %s", action)
            print(f"⚠️ Unsupported clarity action: {action} ‼️")
            return None

        # ---------- Refresh downstream cores after inplace update ----------
        if result is not None and inplace:
            logger.info(
                "Refreshing downstream cores after successful inplace clarity action: %s",
                action,
            )
            self.refresh_downstream_cores()

        logger.info("clarity_data() completed for action=%s", action)
        return result

    # -------------------- Computing data --------------------
    def compution_data(self, action: str, **kwargs):
        """
        Dispatch calculation and feature-engineering actions to ``ComputionCore``.

        This method provides a unified engine-level interface for column calculations,
        conditional feature generation, grouped aggregation, and computation reset
        workflows. It validates that the computation core is available and forwards
        the requested action and related parameters to the matching ``ComputionCore``
        method.

        Parameters
        ----------
        action : str
            Computation action name. Supported actions include:

            - ``"single_column_calculation"``
            - ``"multiple_columns_calculation"``
            - ``"groupby_aggregation_calculation"``
            - ``"reset_computed_data"``
            - ``"conditional_calculation"``
        **kwargs
            Additional keyword arguments forwarded to the selected computation method.

            Common forwarded arguments may include:

            - source/target column names
            - operation names
            - scalar values
            - output column names
            - ``inplace`` flags
            - ``save_csv`` flags

        Returns
        -------
        Any
            Result returned by the corresponding ``ComputionCore`` method, or ``None``
            if the computation core is unavailable or the action is unsupported.

        Supported Actions
        -----------------
        ``"single_column_calculation"``
            Apply a supported calculation to one selected column.

        ``"multiple_columns_calculation"``
            Perform a supported row-wise calculation involving multiple columns.

        ``"groupby_aggregation_calculation"``
            Perform grouped aggregation using selected grouping columns, target columns,
            and aggregation methods.

        ``"reset_computed_data"``
            Reset the current computation working dataset back to the cleaned-data
            baseline.

        ``"conditional_calculation"``
            Create a derived feature column from a condition rule applied to one source
            column.

        Notes
        -----
        - This method is a dispatcher only; detailed calculation logic remains
        implemented inside ``ComputionCore``.
        - Some actions support ``save_csv`` to export either the full current computed
        dataset, grouped summary output, and/or related computation-history records,
        depending on the downstream computation method.
        - Unsupported action names are reported explicitly.
        """
        if self.compution_core is None:
            logger.warning(
                "compution_data() called before compution_core initialization"
            )
            print("⚠️ Compution core is not initialized. Please upload data first ‼️")
            return None

        # ---------- Single column calculation ----------
        logger.info("compution_data() action=%s", action)
        if action == "single_column_calculation":
            return self.compution_core.single_column_calculation(
                column=kwargs.get("column"),
                operation=kwargs.get("operation"),
                value=kwargs.get("value"),
                new_column=kwargs.get("new_column"),
                inplace=kwargs.get("inplace", False),
                save_csv=kwargs.get("save_csv", False),
            )

        # ---------- Multiple columns calculation ----------
        elif action == "multiple_columns_calculation":
            return self.compution_core.multiple_columns_calculation(
                columns=kwargs.get("columns"),
                operation=kwargs.get("operation"),
                new_column=kwargs.get("new_column"),
                save_csv=kwargs.get("save_csv", False),
            )

        # ---------- Groupby aggregation calculation ----------
        elif action == "groupby_aggregation_calculation":
            return self.compution_core.groupby_aggregation_calculation(
                groupby_columns=kwargs.get("groupby_columns"),
                target_columns=kwargs.get("target_columns"),
                agg_method=kwargs.get("agg_method"),
                save_csv=kwargs.get("save_csv", True),
            )

        # ---------- Reset computed data ----------
        elif action == "reset_computed_data":
            return self.compution_core.reset_computed_data(
                save_csv=kwargs.get("save_csv", True),
            )

        # ---------- Conditional calculation ----------
        elif action == "conditional_calculation":
            return self.compution_core.conditional_calculation(
                source_column=kwargs.get("source_column"),
                operator=kwargs.get("operator"),
                threshold=kwargs.get("threshold"),
                true_value=kwargs.get("true_value"),
                false_value=kwargs.get("false_value"),
                new_column=kwargs.get("new_column"),
                save_csv=kwargs.get("save_csv", True),
            )

        else:
            logger.warning("Unsupported compution action: %s", action)
            print(f"⚠️ Unsupported compution action: {action} ‼️")
            return None

    # -------------------- Trans-viewing data --------------------
    def transviewing_data(self, action: str, **kwargs):
        """
        Dispatch reshape and structure-transformation actions to `TransViewCore`.

        This method acts as the engine-level interface for transformation-view
        operations such as stack, unstack, melt, pivot, and pivot table. It validates
        that the transview core is available and forwards the request to the
        corresponding `TransViewCore` method.

        Parameters
        ----------
        action : str
            Transformation action name. Supported actions include:

            - ``"stack"``
            - ``"unstack"``
            - ``"melt"``
            - ``"pivot"``
            - ``"pivot_table"``
        **kwargs
            Additional keyword arguments forwarded to the selected transformation
            method.

        Returns
        -------
        Any
            Result returned by the corresponding `TransViewCore` method, or `None` if
            the transview core is unavailable or the action is unsupported.

        Supported Actions
        -----------------
        ``"stack"``
            Stack selected columns into a longer row-oriented structure.
        ``"unstack"``
            Expand one index level back into columns.
        ``"melt"``
            Convert data from wide format to long format.
        ``"pivot"``
            Reshape data into wide format without aggregation.
        ``"pivot_table"``
            Reshape data into wide format with aggregation.

        Notes
        -----
        - This method is intended to keep menu code and external controllers simple by
        centralizing all transview dispatch logic in one place.
        - Detailed parameter validation and reshape behavior are handled inside
        `TransViewCore`.
        """
        if self.transview_core is None:
            logger.warning(
                "transviewing_data() called before transview_core initialization"
            )
            print("⚠️ TransView core is not initialized. Please upload data first ‼️")
            return None

        # ---------- Stack ----------
        logger.info("transviewing_data() action=%s", action)
        if action == "stack":
            return self.transview_core.stack_core(
                selected_columns=kwargs.get("selected_columns"),
                set_index=kwargs.get("set_index"),
                dropna=kwargs.get("dropna", True),
                reset_index=kwargs.get("reset_index", False),
                inplace=kwargs.get("inplace", False),
            )

        # ---------- Unstack ----------
        elif action == "unstack":
            return self.transview_core.unstack_core(
                set_index=kwargs.get("set_index"),
                selected_columns=kwargs.get("selected_columns"),
                level=kwargs.get("level", -1),
                fill_value=kwargs.get("fill_value"),
                reset_index=kwargs.get("reset_index", False),
                inplace=kwargs.get("inplace", False),
            )

        # ---------- Melt ----------
        elif action == "melt":
            return self.transview_core.melt_core(
                id_vars=kwargs.get("id_vars"),
                value_vars=kwargs.get("value_vars"),
                var_name=kwargs.get("var_name", "variable"),
                value_name=kwargs.get("value_name", "value"),
                ignore_index=kwargs.get("ignore_index", True),
                inplace=kwargs.get("inplace", False),
            )

        # ---------- Pivot ----------
        elif action == "pivot":
            return self.transview_core.pivot_core(
                index=kwargs.get("index"),
                columns=kwargs.get("columns"),
                values=kwargs.get("values"),
                reset_index=kwargs.get("reset_index", False),
                inplace=kwargs.get("inplace", False),
            )

        # ---------- Pivot table ----------
        elif action == "pivot_table":
            return self.transview_core.pivot_table_core(
                index=kwargs.get("index"),
                columns=kwargs.get("columns"),
                values=kwargs.get("values"),
                aggfunc=kwargs.get("aggfunc", "mean"),
                fill_value=kwargs.get("fill_value"),
                margins=kwargs.get("margins", False),
                dropna=kwargs.get("dropna", True),
                reset_index=kwargs.get("reset_index", False),
                inplace=kwargs.get("inplace", False),
            )

        else:
            logger.warning("Unsupported transview action: %s", action)
            print(f"⚠️ Unsupported transview action: {action} ‼️")
            return None

    # -------------------- Trendency data --------------------
    def trendency_data(self, action: str, **kwargs):
        """
        Dispatch plotting and trend-inspection actions to `TrendencyCore`.

        This method provides a unified engine-level interface for visualization
        services such as line plots, scatter plots, pair plots, histograms, box plots,
        and correlation heatmaps. It validates that the trendency core is available
        and forwards the request to the corresponding plotting method.

        Parameters
        ----------
        action : str
            Plotting action name. Supported actions include:

            - ``"line_plot"``
            - ``"scatter_plot"``
            - ``"pair_plot"``
            - ``"histogram_plot"``
            - ``"box_plot"``
            - ``"heatmap_plot"``
        **kwargs
            Additional keyword arguments forwarded to the selected plotting method.

        Returns
        -------
        Any
            Result returned by the corresponding `TrendencyCore` plotting method, or
            `None` if the trendency core is unavailable or the action is unsupported.

        Supported Actions
        -----------------
        ``"line_plot"``
            Plot one or more numeric y-series against a selected x-axis column.
        ``"scatter_plot"``
            Plot a scatter chart for two columns, optionally grouped by hue.
        ``"pair_plot"``
            Plot pairwise relationships among selected numeric columns.
        ``"histogram_plot"``
            Plot distributions for one or more numeric columns.
        ``"box_plot"``
            Plot box plots for selected numeric columns, optionally grouped by another
            column.
        ``"heatmap_plot"``
            Plot a correlation heatmap for selected numeric columns.

        Notes
        -----
        - This method centralizes plotting access for interactive menus and higher-
        level workflow controllers.
        - Column validation, numeric-type checks, figure rendering, and file-saving
        logic remain implemented inside `TrendencyCore`.
        """
        if self.trendency_core is None:
            logger.warning(
                "trendency_data() called before trendency_core initialization"
            )
            print("⚠️ Trendency core is not initialized. Please upload data first ‼️")
            return None

        # ---------- Line plot ----------
        logger.info("trendency_data() action=%s", action)
        if action == "line_plot":
            return self.trendency_core.line_plot(
                x=kwargs.get("x"),
                y=kwargs.get("y"),
                title=kwargs.get("title"),
                figsize=kwargs.get("figsize", (10, 6)),
                marker=kwargs.get("marker", "o"),
                save_fig=kwargs.get("save_fig", False),
                show_fig=kwargs.get("show_fig", True),
            )

        # ---------- Scatter plot ----------
        elif action == "scatter_plot":
            return self.trendency_core.scatter_plot(
                x=kwargs.get("x"),
                y=kwargs.get("y"),
                hue=kwargs.get("hue"),
                title=kwargs.get("title"),
                figsize=kwargs.get("figsize", (8, 6)),
                alpha=kwargs.get("alpha", 0.7),
                save_fig=kwargs.get("save_fig", False),
                show_fig=kwargs.get("show_fig", True),
            )

        # ---------- Pair plot ----------
        elif action == "pair_plot":
            return self.trendency_core.pair_plot(
                columns=kwargs.get("columns"),
                hue=kwargs.get("hue"),
                diag_kind=kwargs.get("diag_kind", "hist"),
                save_fig=kwargs.get("save_fig", False),
                show_fig=kwargs.get("show_fig", True),
            )

        # ---------- Histogram plot ----------
        elif action == "histogram_plot":
            return self.trendency_core.histogram_plot(
                columns=kwargs.get("columns"),
                bins=kwargs.get("bins", 30),
                kde=kwargs.get("kde", False),
                figsize=kwargs.get("figsize", (10, 6)),
                save_fig=kwargs.get("save_fig", False),
                show_fig=kwargs.get("show_fig", True),
            )

        # ---------- Box plot ----------
        elif action == "box_plot":
            return self.trendency_core.box_plot(
                y=kwargs.get("y"),
                x=kwargs.get("x"),
                figsize=kwargs.get("figsize", (10, 6)),
                rotate_xticks=kwargs.get("rotate_xticks", 0),
                save_fig=kwargs.get("save_fig", False),
                show_fig=kwargs.get("show_fig", True),
            )

        # ---------- Heatmap plot ----------
        elif action == "heatmap_plot":
            return self.trendency_core.heatmap_plot(
                columns=kwargs.get("columns"),
                method=kwargs.get("method", "pearson"),
                annot=kwargs.get("annot", True),
                figsize=kwargs.get("figsize", (10, 8)),
                save_fig=kwargs.get("save_fig", False),
                show_fig=kwargs.get("show_fig", True),
            )

        else:
            logger.warning("Unsupported trendency action: %s", action)
            print(f"⚠️ Unsupported trendency action: {action} ‼️")
            return None


# =================================================

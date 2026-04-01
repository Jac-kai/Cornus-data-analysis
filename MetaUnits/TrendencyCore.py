# -------------------- Import Modules --------------------
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from Cornus.Data_Hunter.HuntingDataCore import HuntingDataCore
from Cornus.MetaUnits.ClarityCore import ClarityCore

BASED_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLOT_DIR = os.path.join(BASED_PATH, "Features_Plot")
os.makedirs(PLOT_DIR, exist_ok=True)


# -------------------- TrendencyCore --------------------
class TrendencyCore:
    """
    Visualization and trend-inspection core for exploratory data analysis workflows.

    `TrendencyCore` provides a centralized plotting layer for the Cornus project.
    It receives the original dataset from `HuntingDataCore` and the cleaned dataset
    from `ClarityCore`, then builds a working plotting copy in `self.trendency_data`
    for visual inspection.

    The class is designed to support common exploratory plotting tasks before
    feature engineering or machine-learning modeling, including line plots,
    scatter plots, pair plots, histograms, box plots, and correlation heatmaps.

    Purpose
    -------
    This class helps users inspect cleaned tabular data through visual summaries.
    It is mainly intended for:

    - reviewing numeric distributions
    - checking feature-to-feature relationships
    - detecting possible outliers
    - inspecting grouped spread and dispersion
    - previewing simple trends
    - examining correlation structure

    Data Flow
    ---------
    - `source_data` stores the original dataset loaded by `HuntingDataCore`
    - `cleaned_data` stores the cleaned dataset provided by `ClarityCore`
    - `trendency_data` stores the current working dataset used for plotting

    Attributes
    ----------
    hunter_core : HuntingDataCore
        Data-loading core that provides the originally loaded dataset and, when
        available, the current input file path used for exported plot naming.
    clarity_core : ClarityCore
        Cleaning core that provides the cleaned dataset used as the plotting source.
    source_data : pandas.DataFrame or None
        Original dataset loaded from `HuntingDataCore`.
    cleaned_data : pandas.DataFrame or None
        Cleaned dataset obtained from `ClarityCore`.
    trendency_data : pandas.DataFrame or None
        Current working plotting dataset. This is initialized as a copy of
        `cleaned_data` when available.

    Notes
    -----
    - This class focuses on visualization only.
    - It does not perform data cleaning, reshaping, encoding, scaling, or model fitting.
    - Saved plot filenames are built from the currently loaded source filename when
    available; otherwise a default base name is used.
    - Tick labels in plotting methods are formatted for readability, and the current
    implementation applies a fixed 45-degree rotation to x-axis and y-axis tick labels
    in supported plots.
    """

    # -------------------- Initialization --------------------
    def __init__(self, hunter_core: HuntingDataCore, clarity_core: ClarityCore):
        """
        Initialize the plotting core with source and cleaned data dependencies.

        Parameters
        ----------
        hunter_core : HuntingDataCore
            A `HuntingDataCore` instance that stores the originally loaded dataset and
            may also provide the current input file path used for exported plot naming.
        clarity_core : ClarityCore
            A `ClarityCore` instance that stores the cleaned dataset used as the
            plotting source.

        Attributes Initialized
        ----------------------
        hunter_core : HuntingDataCore
            Stored reference to the incoming data-loading core.
        clarity_core : ClarityCore
            Stored reference to the incoming cleaning core.
        source_data : pandas.DataFrame or None
            Raw loaded dataset from `hunter_core.target_data`.
        cleaned_data : pandas.DataFrame or None
            Cleaned dataset from `clarity_core.cleaned_data`.
        trendency_data : pandas.DataFrame or None
            Working plotting copy initialized from `cleaned_data`. If no cleaned data
            is available, this attribute is set to `None`.

        Notes
        -----
        The plotting workflow is designed to operate on cleaned data rather than raw
        source data. For this reason, `trendency_data` is initialized from
        `clarity_core.cleaned_data` instead of directly from `source_data`.
        """
        # ---------- Cores initialization / Data and records setup ----------
        self.hunter_core = hunter_core
        self.clarity_core = clarity_core

        self.source_data = hunter_core.target_data
        self.cleaned_data = clarity_core.cleaned_data

        # ---------- TrendencyCore data ----------
        self.trendency_data = (
            self.cleaned_data.copy() if self.cleaned_data is not None else None
        )

    # -------------------- Validation (helper) --------------------
    def _validation(self):
        """
        Validate whether the current plotting dataset is available and usable.

        This helper checks whether `self.trendency_data` exists, is a pandas DataFrame,
        and is not empty before any plotting operation is attempted.

        Returns
        -------
        bool
            `True` if `self.trendency_data` is available, is a pandas DataFrame, and
            contains at least one row; otherwise `False`.

        Side Effects
        ------------
        Prints warning messages to the console when validation fails.

        Notes
        -----
        This validation is intended to prevent plotting methods from failing later due
        to missing data, wrong object type, or an empty working dataset.
        """
        if self.trendency_data is None:
            print("⚠️ No trendency data available ‼️")
            return False

        if not isinstance(self.trendency_data, pd.DataFrame):
            print("⚠️ Trendency data must be a pandas DataFrame ‼️")
            return False

        if self.trendency_data.empty:
            print("⚠️ Trendency data is empty ‼️")
            return False

        return True

    # -------------------- Column validation (helper) --------------------
    def _validate_columns(self, columns: list[str]):
        """
        Validate whether the requested columns exist in the current plotting dataset.

        Parameters
        ----------
        columns : list[str]
            Column names that must be present in `self.trendency_data.columns`.

        Returns
        -------
        bool
            `True` if `columns` is a non-empty list and every requested column exists
            in the current working dataset; otherwise `False`.

        Side Effects
        ------------
        Prints warning messages to the console when validation fails.

        Notes
        -----
        This helper checks only column existence. It does not verify whether the columns
        are numeric, categorical, unique, or otherwise suitable for a particular plot.
        """
        if columns is None or not isinstance(columns, list) or len(columns) == 0:
            print("⚠️ Columns must be a non-empty list ‼️")
            return False

        missing_cols = [
            col for col in columns if col not in self.trendency_data.columns
        ]
        if missing_cols:
            print(f"⚠️ Columns not found: {missing_cols} ‼️")
            return False

        return True

    # -------------------- Numeric column validation (helper) --------------------
    def _validate_numeric_columns(self, columns: list[str]):
        """
        Validate whether the requested columns exist and are numeric.

        Parameters
        ----------
        columns : list[str]
            Column names expected to exist in the current plotting dataset and to have
            numeric dtype.

        Returns
        -------
        bool
            `True` if all requested columns exist and are numeric; otherwise `False`.

        Side Effects
        ------------
        Prints warning messages to the console when validation fails.

        Notes
        -----
        This helper first checks column existence through `_validate_columns(columns)`.
        Only after the existence check passes does it verify numeric dtype.
        """
        if not self._validate_columns(columns):
            return False

        non_numeric_cols = [
            col
            for col in columns
            if not pd.api.types.is_numeric_dtype(self.trendency_data[col])
        ]
        if non_numeric_cols:
            print(f"⚠️ Columns must be numeric: {non_numeric_cols} ‼️")
            return False

        return True

    # -------------------- Build plot save path (helper) --------------------
    def _build_plot_path(self, plot_name: str):
        """
        Build the output file path for a saved plot image.

        Parameters
        ----------
        plot_name : str
            Plot label or plot type used as the filename suffix.

        Returns
        -------
        str
            Full output file path under `PLOT_DIR`.

        Behavior
        --------
        - If `hunter_core.current_file_path` is available, the saved plot filename uses
        the source file's base name.
        - If no current input file path is available, the default base name
        `"plot_data"` is used.

        Examples
        --------
        A source file such as `aapl_stock.csv` and a plot name of `"line_plot"` may
        produce an output filename similar to:

        `aapl_stock_line_plot.png`
        """
        # ---------- Get data name as file's name ----------
        current_file_path = getattr(self.hunter_core, "current_file_path", None)
        if current_file_path:
            base_name = os.path.splitext(os.path.basename(current_file_path))[0]
        else:
            base_name = "plot_data"  # Default for no data name from data path

        return os.path.join(PLOT_DIR, f"{base_name}_{plot_name}.png")

    # -------------------- Finalize plot (helper) --------------------
    def _finalize_plot(
        self,
        fig,
        plot_name: str,
        save_fig: bool = False,
        show_fig: bool = True,
    ):
        """
        Save and/or display a matplotlib figure.

        This helper centralizes the final plot-handling workflow after plotting logic
        has finished. It can save the figure to disk, display it on screen, or close it
        without display depending on the provided flags.

        Parameters
        ----------
        fig : matplotlib.figure.Figure
            Figure object to save or display.
        plot_name : str
            Plot label or plot type used in the output filename.
        save_fig : bool, default=False
            Whether to save the figure to disk.
        show_fig : bool, default=True
            Whether to display the figure interactively.

        Returns
        -------
        str or None
            Saved file path if `save_fig=True`; otherwise `None`.

        Side Effects
        ------------
        - May save an image file to `PLOT_DIR`.
        - May display the figure through `plt.show()`.
        - May close the figure through `plt.close(fig)` when `show_fig=False`.

        Notes
        -----
        When saving is enabled, the figure is exported with `dpi=300` and
        `bbox_inches="tight"` for clearer output and tighter layout.
        """
        save_path = None
        if save_fig:
            save_path = self._build_plot_path(plot_name)
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"📦 Plot saved: {save_path}")

        if show_fig:
            plt.show()
        else:
            plt.close(fig)

        return save_path

    # -------------------- Line plot --------------------
    def line_plot(
        self,
        x: str,
        y: list[str],
        title: str = None,
        figsize: tuple = (10, 6),
        marker: str = "o",
        save_fig: bool = False,
        show_fig: bool = True,
    ):
        """
        Plot one or more numeric line series against a selected x-axis column.

        This method draws a line chart using one column as the x-axis and one or more
        numeric columns as y-axis series. Each requested y column is drawn as a separate
        line on the same axes.

        Parameters
        ----------
        x : str
            Column name used as the x-axis.
        y : list[str]
            Numeric column names plotted as y-axis series.
        title : str, optional
            Custom plot title. If `None`, a default title is generated from `x` and `y`.
        figsize : tuple, default=(10, 6)
            Figure size passed to `matplotlib`.
        marker : str, default="o"
            Marker style used for line points.
        save_fig : bool, default=False
            Whether to save the plot image to disk.
        show_fig : bool, default=True
            Whether to display the plot interactively.

        Returns
        -------
        None

        Validation
        ----------
        - Requires `self.trendency_data` to be available and valid.
        - Requires `x` to exist in the current plotting dataset.
        - Requires every column in `y` to exist and be numeric.

        Behavior
        --------
        - The x-axis label is set to `x`.
        - The y-axis label is set to `"Value"`.
        - A legend is created for all selected y-axis series.
        - X-axis and y-axis tick labels are rotated by 45 degrees for readability.

        Notes
        -----
        This method assumes the x-axis column is already in a meaningful display order.
        It does not automatically sort values or parse date strings into datetime unless
        that has been handled earlier in the data workflow.
        """
        if not self._validation():
            return None

        if not self._validate_columns([x]):
            return None

        if not self._validate_numeric_columns(y):
            return None

        # ---------- Figure settings ----------
        fig, ax = plt.subplots(figsize=figsize)

        for col in y:
            ax.plot(
                self.trendency_data[x],
                self.trendency_data[col],
                marker=marker,
                label=col,
            )

        # ---------- Line plot settings ----------
        ax.set_xlabel(x)
        ax.set_ylabel("Value")
        ax.set_title(title or f"Line Plot: {x} vs {', '.join(y)}")
        ax.legend()
        ax.tick_params(axis="x", labelrotation=45)
        ax.tick_params(axis="y", labelrotation=45)
        plt.tight_layout()

        self._finalize_plot(
            fig=fig,
            plot_name="line_plot",
            save_fig=save_fig,
            show_fig=show_fig,
        )

    # -------------------- Scatter plot --------------------
    def scatter_plot(
        self,
        x: str,
        y: str,
        hue: str = None,
        title: str = None,
        figsize: tuple = (8, 6),
        alpha: float = 0.7,
        save_fig: bool = False,
        show_fig: bool = True,
    ):
        """
        Plot a scatter chart for two numeric columns, optionally grouped by color.

        This method creates a scatter plot using one numeric column on the x-axis and
        another numeric column on the y-axis. An optional `hue` column can be supplied
        to color points by group.

        Parameters
        ----------
        x : str
            Numeric column used as the x-axis.
        y : str
            Numeric column used as the y-axis.
        hue : str, optional
            Column used to group points by color.
        title : str, optional
            Custom plot title. If `None`, a default title is generated from `x` and `y`.
        figsize : tuple, default=(8, 6)
            Figure size passed to `matplotlib`.
        alpha : float, default=0.7
            Transparency level for plotted points.
        save_fig : bool, default=False
            Whether to save the plot image to disk.
        show_fig : bool, default=True
            Whether to display the plot interactively.

        Returns
        -------
        None

        Validation
        ----------
        - Requires `self.trendency_data` to be available and valid.
        - Requires both `x` and `y` to exist and be numeric.
        - If `hue` is provided, it must exist in the current plotting dataset.

        Behavior
        --------
        - The plot is drawn through `seaborn.scatterplot`.
        - A color grouping is applied when `hue` is provided.
        - X-axis and y-axis tick labels are rotated by 45 degrees for readability.

        Notes
        -----
        This method uses the `"viridis"` palette when a hue grouping is present.
        """
        if not self._validation():
            return None

        if not self._validate_numeric_columns([x, y]):
            return None

        if hue is not None and not self._validate_columns([hue]):
            return None

        # ---------- Figure plot settings ----------
        fig, ax = plt.subplots(figsize=figsize)

        sns.scatterplot(
            data=self.trendency_data,
            x=x,
            y=y,
            hue=hue,
            alpha=alpha,
            ax=ax,
            palette="viridis",
        )

        # ---------- Scatter plot settings ----------
        ax.set_title(title or f"Scatter Plot: {x} vs {y}")
        ax.tick_params(axis="x", labelrotation=45)
        ax.tick_params(axis="y", labelrotation=45)
        plt.tight_layout()

        self._finalize_plot(
            fig=fig,
            plot_name="scatter_plot",
            save_fig=save_fig,
            show_fig=show_fig,
        )

    # -------------------- Pair plot --------------------
    def pair_plot(
        self,
        columns: list[str] = None,
        hue: str = None,
        diag_kind: str = "hist",
        save_fig: bool = False,
        show_fig: bool = True,
    ):
        """
        Plot pairwise relationships among selected numeric columns.

        This method builds a seaborn pair plot for selected numeric columns, allowing
        the user to inspect pairwise relationships, univariate distributions, and
        optional group separation through color.

        Parameters
        ----------
        columns : list[str], optional
            Numeric column names to include in the pair plot. If `None`, all numeric
            columns from the current plotting dataset are used.
        hue : str, optional
            Column used to color observations by group.
        diag_kind : str, default="hist"
            Plot type used on the diagonal of the pair plot, such as `"hist"` or
            another diagonal option supported by seaborn pairplot.
        save_fig : bool, default=False
            Whether to save the plot image to disk.
        show_fig : bool, default=True
            Whether to display the plot interactively.

        Returns
        -------
        None

        Validation
        ----------
        - Requires `self.trendency_data` to be available and valid.
        - If `columns` is provided, all requested columns must exist and be numeric.
        - If `columns` is `None`, at least one numeric column must exist in the dataset.
        - If `hue` is provided, it must exist in the current plotting dataset.

        Behavior
        --------
        - If `columns` is omitted, all numeric columns are used automatically.
        - If `hue` is provided and is not already in `columns`, it is appended to the
        plotting subset so seaborn can color observations correctly.
        - Scatter panels use semi-transparent points and a reduced marker size.
        - X-axis and y-axis tick labels across all subplots are rotated by 45 degrees.
        - A global title `"Pair Plot"` is added above the grid.

        Notes
        -----
        Pair plots can become slow or visually crowded when many columns or many rows
        are included. In practice, this method is most useful with a moderate number
        of numeric features.
        """
        if not self._validation():
            return None

        if (
            columns is None
        ):  # If no input numeric-type columns, it automatically select all numeric-type columns
            columns = self.trendency_data.select_dtypes(
                include=np.number
            ).columns.tolist()
            if not columns:
                print("⚠️ No numeric columns available for pair plot ‼️")
                return None

        if not self._validate_numeric_columns(columns):
            return None

        if hue is not None and not self._validate_columns([hue]):
            return None

        # ---------- Pair plot hue settings ----------
        plot_cols = columns.copy()
        if (
            hue is not None and hue not in plot_cols
        ):  # Due to hue element needed to be existed in column for plotting
            plot_cols.append(hue)

        pair_grid = sns.pairplot(
            self.trendency_data[plot_cols],
            hue=hue,
            diag_kind=diag_kind,
            plot_kws={
                "alpha": 0.6,
                "s": 30,
            },
        )

        # ---------- Pair plot settings ----------
        pair_grid.figure.suptitle("Pair Plot", y=1.02)
        for ax in pair_grid.axes.flatten():
            if ax is not None:
                ax.tick_params(axis="x", labelrotation=45)
                ax.tick_params(axis="y", labelrotation=45)

        # ---------- Pair plot saving ----------
        save_path = None
        if save_fig:
            save_path = self._build_plot_path("pair_plot")
            pair_grid.figure.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"📦 Plot saved ---> {save_path}")

        if show_fig:
            plt.show()
        else:
            plt.close(pair_grid.figure)

    # -------------------- Histogram plot --------------------
    def histogram_plot(
        self,
        columns: list[str] = None,
        bins: int = 30,
        kde: bool = False,
        figsize: tuple = (10, 6),
        save_fig: bool = False,
        show_fig: bool = True,
    ):
        """
        Plot histograms for one or more numeric columns.

        This method creates a separate histogram for each selected numeric column in the
        current plotting dataset. An optional KDE curve can be added to each histogram.

        Parameters
        ----------
        columns : list[str], optional
            Numeric column names to plot. If `None`, all numeric columns from the
            current plotting dataset are used.
        bins : int, default=30
            Number of histogram bins.
        kde : bool, default=False
            Whether to overlay a KDE curve on each histogram.
        figsize : tuple, default=(10, 6)
            Figure size used for each histogram.
        save_fig : bool, default=False
            Whether to save each generated histogram image to disk.
        show_fig : bool, default=True
            Whether to display each histogram interactively.

        Returns
        -------
        None

        Validation
        ----------
        - Requires `self.trendency_data` to be available and valid.
        - If `columns` is provided, all requested columns must exist and be numeric.
        - If `columns` is `None`, at least one numeric column must exist in the dataset.

        Behavior
        --------
        - A separate figure is created for each selected column.
        - Each plot title is set to `"Histogram: <column_name>"`.
        - X-axis and y-axis tick labels are rotated by 45 degrees for readability.
        - When `save_fig=True`, each histogram is saved with a filename that includes
        the corresponding column name.

        Notes
        -----
        This method uses `seaborn.histplot` and is intended for univariate numeric
        distribution inspection.
        """
        if not self._validation():
            return None

        if columns is None:
            columns = self.trendency_data.select_dtypes(
                include=np.number
            ).columns.tolist()
            if not columns:
                print("⚠️ No numeric columns available for histogram plot ‼️")
                return None

        if not self._validate_numeric_columns(columns):
            return None

        # ---------- Histogram plot setting for each X variable ----------
        for col in columns:
            fig, ax = plt.subplots(figsize=figsize)

            sns.histplot(
                data=self.trendency_data,
                x=col,
                bins=bins,
                kde=kde,
                ax=ax,
            )

            ax.set_title(f"Histogram: {col}")
            ax.tick_params(axis="x", labelrotation=45)
            ax.tick_params(axis="y", labelrotation=45)
            plt.tight_layout()

            self._finalize_plot(
                fig=fig,
                plot_name=f"histogram_{col}",
                save_fig=save_fig,
                show_fig=show_fig,
            )

    # -------------------- Box plot --------------------
    def box_plot(
        self,
        y: list[str],
        x: str = None,
        figsize: tuple = (10, 6),
        rotate_xticks: int = 0,
        save_fig: bool = False,
        show_fig: bool = True,
    ):
        """
        Plot box plots for one or more numeric columns, optionally grouped by a column.

        This method creates a separate box plot for each numeric column in `y`. When
        `x` is omitted, each selected numeric column is plotted alone as a single box
        plot. When `x` is provided, each numeric column is plotted against the grouping
        column on the x-axis.

        Parameters
        ----------
        y : list[str]
            Numeric column names to plot.
        x : str, optional
            Grouping column used on the x-axis. If `None`, each numeric column is plotted
            alone without group separation.
        figsize : tuple, default=(10, 6)
            Figure size used for each box plot.
        rotate_xticks : int, default=0
            Rotation angle argument accepted by the current method implementation during
            grouped plotting. However, the final displayed x-axis tick labels are
            currently standardized to a fixed 45-degree rotation by subsequent axis-level
            formatting.
        save_fig : bool, default=False
            Whether to save each generated box plot image to disk.
        show_fig : bool, default=True
            Whether to display each box plot interactively.

        Returns
        -------
        None

        Validation
        ----------
        - Requires `self.trendency_data` to be available and valid.
        - Requires every column in `y` to exist and be numeric.
        - If `x` is provided, it must exist in the current plotting dataset.

        Behavior
        --------
        - A separate figure is created for each selected y column.
        - If `x` is `None`, the method draws a single-variable box plot for that column.
        - If `x` is provided, the method draws grouped box plots using `x` on the x-axis.
        - X-axis and y-axis tick labels are rotated by 45 degrees for readability.

        Notes
        -----
        The current implementation keeps `rotate_xticks` in the method signature, but
        the final tick-label presentation is standardized through `ax.tick_params(...)`
        with fixed 45-degree rotation.
        """
        if not self._validation():
            return None

        if not self._validate_numeric_columns(y):
            return None

        if x is not None and not self._validate_columns([x]):
            return None

        # ---------- Box plot setting for each Y variable ----------
        for col in y:
            fig, ax = plt.subplots(figsize=figsize)

            if x is None:
                sns.boxplot(y=self.trendency_data[col], ax=ax)
                ax.set_title(f"Box Plot: {col}")
                ax.set_ylabel(col)
            else:
                sns.boxplot(data=self.trendency_data, x=x, y=col, ax=ax)
                ax.set_title(f"Box Plot: {col} by {x}")
                plt.xticks(rotation=rotate_xticks)

            ax.tick_params(axis="x", labelrotation=45)
            ax.tick_params(axis="y", labelrotation=45)
            plt.tight_layout()

            self._finalize_plot(
                fig=fig,
                plot_name=f"box_plot_{col}",
                save_fig=save_fig,
                show_fig=show_fig,
            )

    # -------------------- Heatmap plot --------------------
    def heatmap_plot(
        self,
        columns: list[str] = None,
        method: str = "pearson",
        annot: bool = True,
        figsize: tuple = (10, 8),
        save_fig: bool = False,
        show_fig: bool = True,
    ):
        """
        Plot a correlation heatmap for selected numeric columns.

        This method computes a correlation matrix from selected numeric columns in the
        current plotting dataset and visualizes it as a heatmap.

        Parameters
        ----------
        columns : list[str], optional
            Numeric column names used to compute the correlation matrix. If `None`, all
            numeric columns from the current plotting dataset are used.
        method : str, default="pearson"
            Correlation method passed to `DataFrame.corr()`, such as `"pearson"`,
            `"spearman"`, or `"kendall"`.
        annot : bool, default=True
            Whether to annotate heatmap cells with formatted correlation values.
        figsize : tuple, default=(10, 8)
            Figure size passed to `matplotlib`.
        save_fig : bool, default=False
            Whether to save the heatmap image to disk.
        show_fig : bool, default=True
            Whether to display the heatmap interactively.

        Returns
        -------
        None

        Validation
        ----------
        - Requires `self.trendency_data` to be available and valid.
        - If `columns` is provided, all requested columns must exist and be numeric.
        - If `columns` is `None`, at least one numeric column must exist in the dataset.

        Behavior
        --------
        - A correlation matrix is computed from the selected numeric columns.
        - The heatmap is drawn with the `"coolwarm"` colormap.
        - Cell values are formatted with two decimal places.
        - X-axis and y-axis tick labels are rotated by 45 degrees for readability.

        Notes
        -----
        This method is intended for numeric feature relationship inspection rather than
        for causal interpretation.
        """
        if not self._validation():
            return None

        if columns is None:
            columns = self.trendency_data.select_dtypes(
                include=np.number
            ).columns.tolist()
            if not columns:
                print("⚠️ No numeric columns available for heatmap plot ‼️")
                return None

        if not self._validate_numeric_columns(columns):
            return None

        # ---------- Correlation data ----------
        corr_df = self.trendency_data[columns].corr(
            method=method
        )  # Metohd will be options (Pearson / Spearman / Kendall )

        # ---------- Heatmap settings ----------
        fig, ax = plt.subplots(figsize=figsize)

        sns.heatmap(
            corr_df,
            annot=annot,
            cmap="coolwarm",
            fmt=".2f",
            linewidths=0.5,
            ax=ax,
        )

        ax.set_title(f"Correlation Heatmap ({method})")
        ax.tick_params(axis="x", labelrotation=45)
        ax.tick_params(axis="y", labelrotation=45)
        plt.tight_layout()

        self._finalize_plot(
            fig=fig,
            plot_name="heatmap_plot",
            save_fig=save_fig,
            show_fig=show_fig,
        )


# =================================================

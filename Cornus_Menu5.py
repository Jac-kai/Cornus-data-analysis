# -------------------- Import Modules --------------------
import logging

from Cornus.Cornus_Engine import CornusEngine
from Cornus.Menu_Helper_Decorator import (
    column_list,
    input_int,
    input_list,
    input_yesno,
    menu_wrapper,
)

logger = logging.getLogger("Cornus")


# Trendency data section
# -------------------- Helper: select one column --------------------
def _select_one_column(data, prompt: str) -> str | None:
    """
    Interactively select a single column from a dataset by displayed menu number.

    This helper builds a numbered column mapping from the provided dataset by using
    ``column_list(data)`` and then reads one integer choice from the user. If the
    selection is valid, the corresponding real column name is returned.

    This function is mainly intended for menu-driven workflows where exactly one
    column is required, such as selecting the x-axis, y-axis, or hue column for a
    plot.

    Parameters
    ----------
    data : pandas.DataFrame
        Dataset whose columns are displayed and made selectable.
    prompt : str
        Prompt text displayed before reading the user's menu-number selection.

    Returns
    -------
    str | None
        - ``str``
        The selected real column name corresponding to the chosen menu number.
        - ``None``
        Returned when no selectable columns are available, when the user skips
        input, chooses back, or enters an invalid menu number.

    Side Effects
    ------------
    Prints warning messages when the selected menu number is invalid.

    Notes
    -----
    - This helper resolves only one column at a time.
    - The function does not modify the dataset.
    - A return value of ``None`` should be treated by the caller as cancel, skip,
    or invalid selection.

    Examples
    --------
    If the displayed column mapping is::

        1 -> Date
        2 -> Sales
        3 -> Region

    and the user enters ``2``, the function returns::

        "Sales"
    """
    logger.info("_select_one_column() started with prompt=%s", prompt)
    col_map = column_list(data)

    if not col_map:
        logger.warning("No column mapping available for single-column selection")
        return None

    selected_num = input_int(prompt)

    if selected_num in (None, 0):
        logger.info("_select_one_column() returned back or skipped")
        return None

    if selected_num not in col_map:
        logger.warning("Invalid trendency column number: %s", selected_num)
        print("⚠️ Invalid column number ‼️")
        return None

    logger.info("Selected trendency column: %s", col_map[selected_num])
    return col_map[selected_num]


# -------------------- Helper: select multiple columns --------------------
def _select_multiple_columns(data, prompt: str) -> list[str] | None:
    """
    Interactively select multiple columns from a dataset by displayed menu numbers.

    This helper builds a numbered column mapping from the provided dataset by using
    ``column_list(data)`` and then reads a comma-separated list of menu numbers
    from the user. Each valid selection is converted into its corresponding real
    column name and collected into a list.

    This function is intended for menu-based workflows that require one or more
    columns, such as selecting multiple y-axis columns, histogram columns, or
    heatmap columns.

    Parameters
    ----------
    data : pandas.DataFrame
        Dataset whose columns are displayed and made selectable.
    prompt : str
        Prompt text displayed before reading the user's selection.

    Returns
    -------
    list[str] | None
        - ``list[str]``
        List of selected real column names corresponding to valid menu numbers.
        - ``None``
        Returned when no selectable columns are available, when the user skips
        input, chooses back, or an invalid selection causes the current attempt
        to be rejected.

    Side Effects
    ------------
    Prints warning messages when an invalid menu number is encountered.

    Notes
    -----
    - Unlike some other selection helpers, this function returns ``None`` for both
    back/cancel and invalid selection cases.
    - This helper does not modify the dataset.
    - The caller is responsible for deciding whether to retry the selection.

    Examples
    --------
    If the displayed column mapping is::

        1 -> Open
        2 -> High
        3 -> Low
        4 -> Close

    and the user enters ``1,4``, the function returns::

        ["Open", "Close"]
    """
    logger.info("_select_multiple_columns() started with prompt=%s", prompt)
    col_map = column_list(data)

    if not col_map:
        logger.warning("No column mapping available for multi-column selection")
        return None

    selected_nums = input_list(prompt)

    if selected_nums in (None, "__BACK__"):
        logger.info("_select_multiple_columns() returned back or skipped")
        return None

    selected_columns = []
    for item in selected_nums:
        if str(item).isdigit() and int(item) in col_map:
            selected_columns.append(col_map[int(item)])
        else:
            logger.warning("Invalid trendency column number: %s", item)
            print(f"⚠️ Invalid column number: {item} ‼️")
            return None

    logger.info("Selected trendency columns: %s", selected_columns)
    return selected_columns if selected_columns else None


# -------------------- Helper: select plot action --------------------
def _select_trendency_action() -> str | None:
    """
    Interactively select one plotting action for trend inspection.

    This helper displays the available trendency plotting menu and converts the
    user's menu-number choice into the corresponding action string used by
    ``engine.trendency_data(...)``.

    Supported plot actions include line plot, scatter plot, pair plot, histogram
    plot, box plot, and heatmap plot.

    Returns
    -------
    str | None
        - ``str``
        Action string corresponding to the selected plotting service.
        - ``None``
        Returned when the user skips input, chooses back, or enters an invalid
        menu number.

    Side Effects
    ------------
    - Prints the trendency plot menu to the console.
    - Prints a warning message when the selection is invalid.

    Notes
    -----
    - This helper is responsible only for action selection.
    - Plot parameters such as columns, bins, hue, or correlation method are
    collected later by the main menu controller.
    - The returned action string is intended to be passed directly to
    ``engine.trendency_data(action=...)``.

    Supported Actions
    -----------------
    ``"line_plot"``
        Plot one or more numeric series against a selected x column.
    ``"scatter_plot"``
        Plot a scatter chart for two columns, optionally grouped by hue.
    ``"pair_plot"``
        Plot pairwise relationships among selected numeric columns.
    ``"histogram_plot"``
        Plot distributions for one or more numeric columns.
    ``"box_plot"``
        Plot box plots for one or more numeric columns.
    ``"heatmap_plot"``
        Plot a correlation heatmap for selected numeric columns.
    """
    logger.info("_select_trendency_action() started")
    trendency_menu = {
        1: "line_plot",
        2: "scatter_plot",
        3: "pair_plot",
        4: "histogram_plot",
        5: "box_plot",
        6: "heatmap_plot",
    }

    print("\n---------- 📈 Trendency Plot Menu 📈 ----------")
    for i, item in trendency_menu.items():
        print(f"🍁 {i}. {item}")

    selected = input_int("🔎 Enter plot function number")

    if selected in (None, 0):
        logger.info("_select_trendency_action() returned back or skipped")
        return None

    if selected not in trendency_menu:
        logger.warning("Invalid trendency menu number: %s", selected)
        print("⚠️ Invalid trendency menu number ‼️")
        return None

    logger.info("Selected trendency action: %s", trendency_menu[selected])
    return trendency_menu[selected]


# -------------------- Data trendency menu --------------------
@menu_wrapper("Data trendency menu")
def data_trendency_menu(engine: CornusEngine):
    """
    Run the interactive terminal menu for trend inspection and plotting.

    This menu acts as the user-facing controller for visualization services exposed
    through ``CornusEngine.trendency_data(...)``. It provides a menu-driven
    workflow that lets the user select a plotting action, configure plot-specific
    parameters, and execute the plotting request through the engine.

    The function is designed for interactive console use and focuses on input
    collection, basic menu control, and action dispatch rather than implementing
    plotting logic itself.

    Parameters
    ----------
    engine : CornusEngine
        Main engine instance used to execute plotting and trend-inspection actions
        through ``engine.trendency_data(...)``. The engine is expected to already
        contain a valid initialized ``trendency_core``.

    Returns
    -------
    None
        This function is an interactive menu controller. It does not directly
        return plotting results. Plot rendering, saving, and validation are handled
        by downstream engine and core methods.

    Workflow
    --------
    1. Check whether ``engine.trendency_core`` is initialized.
    2. Retrieve the current plotting working dataset from
    ``engine.trendency_core.trendency_data``.
    3. Display the trendency plot menu and read the user's selected action.
    4. Ask for shared plotting options such as whether to save or show the figure.
    5. Collect action-specific parameters such as columns, plot style options, or
    correlation settings.
    6. Dispatch the final request through ``engine.trendency_data(...)``.
    7. Ask whether the user wants to continue using the trendency menu.

    Supported Plot Workflows
    ------------------------
    ``"line_plot"``
        Prompts for one x column, one or more y columns, and
        marker style.

    ``"scatter_plot"``
        Prompts for x and y columns and optionally a hue column.

    ``"pair_plot"``
        Optionally lets the user select columns, optionally choose a hue column,
        and select the diagonal plot type.

    ``"histogram_plot"``
        Optionally lets the user select columns, then prompts for bin count and
        whether to add a KDE curve.

    ``"box_plot"``
        Prompts for one or more y columns, optionally a grouping x column, and
        x-tick rotation.

    ``"heatmap_plot"``
        Optionally lets the user select columns, then prompts for correlation
        method and whether to annotate values on the heatmap.

    Side Effects
    ------------
    - Prints menus, prompts, warnings, and navigation messages to the console.
    - May trigger figure display and/or figure saving depending on user choice and
    downstream plot-core behavior.

    Notes
    -----
    - This function assumes that source data has already been uploaded and that
    ``engine.build_cores()`` has already initialized ``trendency_core``.
    - Plot-specific validation such as checking whether columns exist or are
    numeric is handled inside ``TrendencyCore`` rather than this menu function.
    - The decorator ``@menu_wrapper("Data trendency menu")`` provides a consistent
    terminal-style wrapper around execution.

    Examples
    --------
    Typical usage::

        engine = CornusEngine()
        engine.upload_data(...)
        data_trendency_menu(engine)
    """
    logger.info("Entered data_trendency_menu")
    if engine.trendency_core is None:
        logger.warning("Trendency core is not initialized")
        print("⚠️ Trendency core is not initialized. Please upload data first ‼️")
        return None

    data = engine.trendency_core.trendency_data
    if data is None or data.empty:
        logger.warning("No trendency data available")
        print("⚠️ No trendency data available ‼️")
        return None

    while True:
        action = _select_trendency_action()
        logger.info("Trendency menu action selected: %s", action)

        if action is None:
            logger.info("Leaving trendency menu to previous menu")
            print("↩️ Back to previous menu.")
            return None

        # ---------- Shared options ----------
        save_fig = input_yesno("💾 Save figure")
        show_fig = input_yesno("🖥️ Show figure")
        logger.info(
            "Shared plot options selected: save_fig=%s, show_fig=%s", save_fig, show_fig
        )

        # ---------- Line plot ----------
        if action == "line_plot":
            x = _select_one_column(data, "🕯️ Enter x column number")
            if x is None:
                continue

            y = _select_multiple_columns(data, "🕯️ Enter y column numbers")
            if not y:
                continue

            marker_map = {
                1: "o",
                2: "s",
                3: "^",
                4: "x",
                5: "*",
            }

            print("\n----------🐝 Marker Menu 🐝----------")
            for i, item in marker_map.items():
                print(f"🔸 {i}. {item}")

            marker_num = input_int("🕯️ Enter marker number", default=1)
            marker = marker_map.get(marker_num, "o")

            logger.info(
                "Dispatching trendency_data: action=%s, x=%s, y=%s, marker=%s, save_fig=%s, show_fig=%s",
                action,
                x,
                y,
                marker,
                save_fig,
                show_fig,
            )
            engine.trendency_data(
                action="line_plot",
                x=x,
                y=y,
                marker=marker,
                save_fig=save_fig,
                show_fig=show_fig,
            )

        # ---------- Scatter plot ----------
        elif action == "scatter_plot":
            x = _select_one_column(data, "🕯️ Enter x column number")
            if x is None:
                continue

            y = _select_one_column(data, "🕯️ Enter y column number")
            if y is None:
                continue

            use_hue = input_yesno("🎨 Use hue column")
            hue = None
            if use_hue:
                hue = _select_one_column(data, "🕯️ Enter hue column number")
                if hue is None:
                    continue

            logger.info(
                "Dispatching trendency_data: action=%s, x=%s, y=%s, hue=%s, save_fig=%s, show_fig=%s",
                action,
                x,
                y,
                hue,
                save_fig,
                show_fig,
            )
            engine.trendency_data(
                action="scatter_plot",
                x=x,
                y=y,
                hue=hue,
                save_fig=save_fig,
                show_fig=show_fig,
            )

        # ---------- Pair plot ----------
        elif action == "pair_plot":
            use_custom_cols = input_yesno("🕯️ Select specific columns")
            columns = None
            if use_custom_cols:
                columns = _select_multiple_columns(
                    data,
                    "🕯️ Enter pair plot column numbers",
                )
                if not columns:
                    continue

            use_hue = input_yesno("🎨 Use hue column?")
            hue = None
            if use_hue:
                hue = _select_one_column(data, "🕯️ Enter hue column number")
                if hue is None:
                    continue

            diag_kind_menu = {
                1: "hist",
                2: "kde",
            }

            print("\n----------🐝 Diagonal Plot Menu 🐝----------")
            for i, item in diag_kind_menu.items():
                print(f"🔹 {i}. {item}")

            diag_num = input_int("🕯️ Enter diagonal plot type", default=1)
            diag_kind = diag_kind_menu.get(diag_num, "hist")

            logger.info(
                "Dispatching trendency_data: action=%s, columns=%s, hue=%s, diag_kind=%s, save_fig=%s, show_fig=%s",
                action,
                columns,
                hue,
                diag_kind,
                save_fig,
                show_fig,
            )
            engine.trendency_data(
                action="pair_plot",
                columns=columns,
                hue=hue,
                diag_kind=diag_kind,
                save_fig=save_fig,
                show_fig=show_fig,
            )

        # ---------- Histogram plot ----------
        elif action == "histogram_plot":
            use_custom_cols = input_yesno("🕯️ Select specific columns")
            columns = None
            if use_custom_cols:
                columns = _select_multiple_columns(
                    data,
                    "🕯️ Enter histogram column numbers",
                )
                if not columns:
                    continue

            bins = input_int("🕯️ Enter number of bins", default=30)
            kde = input_yesno("🪄 Add KDE curve")

            logger.info(
                "Dispatching trendency_data: action=%s, columns=%s, bins=%s, kde=%s, save_fig=%s, show_fig=%s",
                action,
                columns,
                bins if bins is not None else 30,
                kde,
                save_fig,
                show_fig,
            )
            engine.trendency_data(
                action="histogram_plot",
                columns=columns,
                bins=bins if bins is not None else 30,
                kde=kde,
                save_fig=save_fig,
                show_fig=show_fig,
            )

        # ---------- Box plot ----------
        elif action == "box_plot":
            y = _select_multiple_columns(data, "🕯️ Enter y column numbers")
            if not y:
                continue

            use_x = input_yesno("🪄 Use grouping x column")
            x = None
            if use_x:
                x = _select_one_column(data, "🕯️ Enter x column number")
                if x is None:
                    continue

            rotate_xticks = input_int("🕯️ Rotate x-ticks angle", default=0)

            logger.info(
                "Dispatching trendency_data: action=%s, y=%s, x=%s, rotate_xticks=%s, save_fig=%s, show_fig=%s",
                action,
                y,
                x,
                rotate_xticks if rotate_xticks is not None else 0,
                save_fig,
                show_fig,
            )
            engine.trendency_data(
                action="box_plot",
                y=y,
                x=x,
                rotate_xticks=rotate_xticks if rotate_xticks is not None else 0,
                save_fig=save_fig,
                show_fig=show_fig,
            )

        # ---------- Heatmap plot ----------
        elif action == "heatmap_plot":
            use_custom_cols = input_yesno("🪄 Select specific columns")
            columns = None
            if use_custom_cols:
                columns = _select_multiple_columns(
                    data,
                    "🔎 Enter heatmap column numbers",
                )
                if not columns:
                    continue

            method_menu = {
                1: "pearson",
                2: "spearman",
                3: "kendall",
            }

            print("\n----------🐝 Correlation Method Menu 🐝----------")
            for i, item in method_menu.items():
                print(f"🧮  {i}. {item}")

            method_num = input_int("🕯️ Enter correlation method", default=1)
            method = method_menu.get(method_num, "pearson")

            annot = input_yesno("🪄 Show correlation values on heatmap")

            logger.info(
                "Dispatching trendency_data: action=%s, columns=%s, method=%s, annot=%s, save_fig=%s, show_fig=%s",
                action,
                columns,
                method,
                annot,
                save_fig,
                show_fig,
            )
            engine.trendency_data(
                action="heatmap_plot",
                columns=columns,
                method=method,
                annot=annot,
                save_fig=save_fig,
                show_fig=show_fig,
            )

        # ---------- Continue ----------
        again = input_yesno("🕯️  Continue trendency menu")
        logger.info("Continue trendency menu choice: %s", again)
        if not again:
            logger.info("Leaving trendency menu")
            print("👣👣 Leaving trendency menu.")
            break


# =================================================

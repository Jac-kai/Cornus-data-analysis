# -------------------- Import Modules --------------------
import logging

from Cornus.Cornus_Engine import CornusEngine
from Cornus.Menu_Helper_Decorator import (
    column_list,
    input_int,
    input_list,
    input_text_value,
    input_yesno,
    menu_wrapper,
    select_inplace,
)

logger = logging.getLogger("Cornus")


# Transviewing data section
# -------------------- Helper: select target columns --------------------
def _select_target_columns(
    data,
    prompt: str = "🔎 Enter column numbers",
) -> list[str] | str | None:
    """
    Interactively select one or more columns from a dataset by displayed menu number.

    This helper builds a numbered column mapping from the provided dataset using
    ``column_list(data)`` and then reads a comma-separated selection from the user.
    Each valid numeric selection is converted into its corresponding real column
    name and returned as a list.

    The helper is intended for terminal-based menu workflows where the user chooses
    target columns for reshape or transformation operations such as stack, unstack,
    melt, pivot, and pivot table.

    Parameters
    ----------
    data : pandas.DataFrame
        Dataset whose columns are displayed and made selectable.
    prompt : str, default="🔎 Enter column numbers"
        Prompt text shown before reading the user's selection.

    Returns
    -------
    list[str] | str | None
        - ``list[str]``
        List of selected real column names corresponding to valid menu numbers.
        - ``"__BACK__"``
        Returned when the user explicitly chooses to go back.
        - ``None``
        Returned when no selectable columns are available, when the user skips
        input, or when no valid selections remain after validation.

    Side Effects
    ------------
    Prints warning messages for invalid menu-number selections.

    Notes
    -----
    - Invalid selections are ignored individually rather than terminating the
    whole selection process.
    - The helper only resolves menu numbers into actual column names.
    - This function does not modify the input dataset.

    Examples
    --------
    If the displayed column mapping is::

        1 -> Age
        2 -> Salary
        3 -> Department

    and the user enters ``1,3``, the function returns::

        ["Age", "Department"]
    """
    logger.info("_select_target_columns() started with prompt=%s", prompt)
    col_map = column_list(data)

    if not col_map:
        logger.warning("No column mapping available for transview column selection")
        return None

    selected_col_num = input_list(prompt)

    if selected_col_num == "__BACK__":
        logger.info("_select_target_columns() returned back")
        return "__BACK__"

    if not selected_col_num:
        logger.info("_select_target_columns() skipped by user")
        return None

    target_columns = []
    for item in selected_col_num:
        if str(item).isdigit() and int(item) in col_map:
            target_columns.append(col_map[int(item)])
        else:
            logger.warning("Invalid transview column number: %s", item)
            print(f"⚠️ Invalid column number: {item} ‼️")

    logger.info("Selected transview target columns: %s", target_columns)
    return target_columns if target_columns else None


# -------------------- Helper: input fill value --------------------
def _input_fill_value(prompt: str) -> int | float | str | None:
    """
    Read one fill value from user input with simple numeric parsing.

    This helper is designed for transformation workflows that accept an optional
    ``fill_value`` argument, such as unstack or pivot-table operations. It reads
    one manual input value and attempts lightweight numeric parsing.

    Input handling rules
    --------------------
    - Enter ``"b"`` to go back to the previous menu step.
    - Press ENTER to keep ``fill_value=None`` and continue the workflow.
    - Enter an integer-like value to return ``int``.
    - Enter a decimal-like value to return ``float``.
    - Enter any other non-empty text to return ``str``.

    Parameters
    ----------
    prompt : str
        Prompt text displayed before reading the fill value.

    Returns
    -------
    int | float | str | None
        - ``int``
        Returned when the entered value is parsed as an integer.
        - ``float``
        Returned when the entered value is parsed as a floating-point number.
        - ``str``
        Returned when the entered value is non-numeric text, including the
        internal sentinel ``"__EMPTY__"`` used to represent ENTER/keep-None.
        - ``None``
        Returned when the user enters ``"b"`` to go back.

    Notes
    -----
    - Numeric parsing is intentionally simple and is based on whether ``"."``
    appears in the input text.
    - ENTER does not mean back; it means keep ``fill_value=None`` and continue.
    - Because ENTER is represented internally by ``"__EMPTY__"``, the caller is
    expected to convert that sentinel back to ``None`` before dispatching the
    final transformation call.
    """
    logger.info("_input_fill_value() started with prompt=%s", prompt)

    while True:
        value = input(
            f"{prompt} (typing manually | ENTER keeps None | b to ↩️ BACK) ⚡ "
        ).strip()

        if value.lower() == "b":
            logger.info("_input_fill_value() returned back")
            return None

        if value == "":
            logger.info("_input_fill_value() kept fill_value=None")
            return "__EMPTY__"

        try:
            if "." in value:
                logger.info("Parsed fill_value as float: %s", value)
                return float(value)
            logger.info("Parsed fill_value as int: %s", value)
            return int(value)
        except ValueError:
            logger.info("Parsed fill_value as str: %s", value)
            return value


# -------------------- Helper: select reset_index option --------------------
def _select_reset_index() -> bool | None:
    """
    Ask whether the transformation result should reset its index.

    This helper provides a standardized yes/no prompt for transformation workflows
    that support a ``reset_index`` option after reshaping.

    Returns
    -------
    bool | None
        - ``True``
        Reset the index after transformation.
        - ``False``
        Keep the transformed result's current index structure.
        - ``None``
        Returned when the user cancels or goes back.

    Notes
    -----
    This helper delegates input handling to ``input_yesno(...)`` and exists mainly
    to keep menu code readable and consistent across transformation operations.
    """
    logger.info("_select_reset_index() started")
    return input_yesno("🕯️ Reset index after transform", default=False)


# -------------------- Helper: select dropna option --------------------
def _select_dropna() -> bool | None:
    """
    Ask whether missing values should be dropped during a transformation step.

    This helper provides a consistent yes/no prompt for transformation operations
    that expose a ``dropna`` argument, such as stack or pivot-table style logic.

    Returns
    -------
    bool | None
        - ``True``
        Drop missing values during the operation.
        - ``False``
        Keep missing values.
        - ``None``
        Returned when the user cancels or chooses to go back.

    Notes
    -----
    This helper wraps ``input_yesno(...)`` so that repeated menu logic remains
    compact and semantically clear.
    """
    logger.info("_select_dropna() started")
    return input_yesno("🕯️ Drop missing values", default=True)


# -------------------- Helper: select ignore_index option --------------------
def _select_ignore_index() -> bool | None:
    """
    Ask whether the original index should be ignored in the transformation result.

    This helper is mainly used for reshape operations such as melt, where the user
    may choose whether to preserve the original index or replace it with a default
    range index.

    Returns
    -------
    bool | None
        - ``True``
        Ignore the original index.
        - ``False``
        Preserve the original index.
        - ``None``
        Returned when the user cancels or goes back.

    Notes
    -----
    This helper standardizes handling of the ``ignore_index`` option in menu-based
    reshape workflows.
    """
    logger.info("_select_ignore_index() started")
    return input_yesno("🕯️ Ignore original index", default=True)


# -------------------- Helper: select margins option --------------------
def _select_margins() -> bool | None:
    """
    Ask whether pivot table margins should be included.

    This helper provides a standardized yes/no prompt for pivot-table workflows
    that support the ``margins`` argument.

    Returns
    -------
    bool | None
        - ``True``
        Add margins such as row/column totals.
        - ``False``
        Do not add margins.
        - ``None``
        Returned when the user cancels or goes back.

    Notes
    -----
    This helper is intended only for user input collection and does not build or
    modify the pivot table itself.
    """
    logger.info("_select_margins() started")
    return input_yesno("🕯️ Add margins", default=False)


# -------------------- Helper: select aggregation function --------------------
def _select_aggfunc() -> str | list[str] | None:
    """
    Interactively select one or more aggregation functions for pivot-table generation.

    This helper displays a numbered aggregation menu and lets the user choose one
    or multiple aggregation functions through comma-separated menu numbers. Valid
    selections are converted into pandas-compatible aggregation names.

    Supported aggregation functions include common statistical reductions such as
    sum, mean, max, min, count, median, and standard deviation.

    Returns
    -------
    str | list[str] | None
        - ``str``
        Returned when exactly one aggregation function is selected.
        - ``list[str]``
        Returned when multiple aggregation functions are selected.
        - ``"__BACK__"``
        Returned when the user explicitly chooses to go back.
        - ``None``
        Returned when the user skips input or when no valid selections remain
        after validation.

    Side Effects
    ------------
    Prints the aggregation menu and warning messages for invalid selections.

    Notes
    -----
    - Invalid selections are ignored individually rather than terminating the
    whole selection process.
    - The return type matches common pandas usage, where ``aggfunc`` may be either
    a single function name or a list of function names.
    - This helper does not apply aggregation itself; it only gathers user choice.

    Examples
    --------
    If the user selects ``1``, the function returns::

        "sum"

    If the user selects ``1,2,5``, the function returns::

        ["sum", "mean", "count"]

    If the user enters ``0``, the function returns::

        "__BACK__"
    """
    logger.info("_select_aggfunc() started")
    agg_menu = {
        1: "sum",
        2: "mean",
        3: "max",
        4: "min",
        5: "count",
        6: "median",
        7: "std",
    }

    for i, agg in agg_menu.items():
        print(f"🍁 {i}. {agg}")

    selected_agg_num = input_list("🕯️ Select aggregation function numbers")

    if selected_agg_num == "__BACK__":
        logger.info("_select_aggfunc() returned back")
        return "__BACK__"

    if not selected_agg_num:
        logger.info("_select_aggfunc() skipped by user")
        return None

    aggfuncs = []
    for item in selected_agg_num:
        if str(item).isdigit() and int(item) in agg_menu:
            aggfuncs.append(agg_menu[int(item)])
        else:
            logger.warning("Invalid transview aggregation number: %s", item)
            print(f"⚠️ Invalid aggregation number: {item} ‼️")

    if not aggfuncs:
        return None

    if len(aggfuncs) == 1:
        return aggfuncs[0]

    logger.info("Selected aggregation functions: %s", aggfuncs)
    return aggfuncs


# -------------------- Helper: select unstack level --------------------
def _input_unstack_level() -> int | str | None:
    """
    Read one unstack level from user input.

    This helper accepts either a numeric level or a named level for unstack-like
    operations. If the user presses ENTER without typing anything, the default level
    ``-1`` is returned.

    Returns
    -------
    int | str | None
        - ``int``
        Returned when the entered value is a valid integer level such as ``0``,
        ``1``, or ``-1``.
        - ``str``
        Returned when the entered value is treated as a named level.
        - ``None``
        Returned when the user enters ``"0"`` to cancel or go back.

    Notes
    -----
    - Empty input defaults to ``-1``.
    - Negative integer strings are supported.
    - This helper performs only light parsing and does not validate whether the
    specified level actually exists in the target dataset.
    """
    logger.info("_input_unstack_level() started")
    value = input("🕯️ Enter unstack level (default=-1 | 0 to ↩️ BACK) ⚡ ").strip()

    if value == "0":
        logger.info("_input_unstack_level() returned back")
        return None

    if value == "":
        logger.info("_input_unstack_level() used default level=-1 (skip)")
        return -1

    if value.lstrip("-").isdigit():
        logger.info("Parsed unstack level as int: %s", value)
        return int(value)

    logger.info("Parsed unstack level as str: %s", value)
    return value


# -------------------- Trans-viewing data menu --------------------
@menu_wrapper("Trans-viewing Data Menu")
def transviewing_data_menu(cornus: CornusEngine):
    """
    Run the interactive terminal menu for transformation-view operations.

    This menu acts as the user-facing controller for reshape and structure-changing
    operations exposed through ``CornusEngine.transviewing_data(...)``. It provides
    a menu-driven workflow that lets the user select one transformation action,
    configure operation-specific parameters, and execute the transformation through
    the engine.

    The function is designed for interactive console use and focuses on collecting
    validated user input rather than implementing the underlying reshape logic
    itself.

    Menu Options
    ------------
    1. ``stack``
        Stack one or more selected columns into a longer row-based structure.
    2. ``unstack``
        Expand one index level back into columns.
    3. ``melt``
        Reshape the dataset from wide format into long format.
    4. ``pivot``
        Reshape the dataset into wide format without aggregation.
    5. ``pivot_table``
        Reshape the dataset into wide format using one or more aggregation
        functions.
    0. ``Back to Main Menu``
        Exit this menu and return to the caller.

    Parameters
    ----------
    cornus : CornusEngine
        Main engine instance used to dispatch transformation-view actions through
        ``cornus.transviewing_data(...)``. The engine is expected to already hold
        a valid ``cleaned_data`` dataset through ``ClarityCore`` so that
        transformation options can be configured from the common baseline dataset.

    Returns
    -------
    None
        This function is a menu controller. It does not directly return transformed
        data. Transformation results are handled by the underlying engine and core
        methods.

    Workflow
    --------
    1. Display the transformation-view operation menu.
    2. Read the user's menu selection.
    3. Gather action-specific parameters using helper functions.
    4. Call ``cornus.transviewing_data(...)`` with the collected arguments.
    5. Continue looping until the user chooses to exit.

    Action Details
    --------------
    ``stack``
        Optionally selects index columns, optionally selects columns to stack,
        then asks whether to drop missing values, reset index, and apply the
        operation inplace.

    ``unstack``
        Optionally selects index columns and retained columns, then asks for the
        unstack level, optional fill value, reset-index behavior, and inplace mode.

    ``melt``
        Optionally selects ``id_vars`` and ``value_vars``, then asks for optional
        ``var_name`` and ``value_name`` custom labels, ignore-index behavior, and
        inplace mode.

    ``pivot``
        Requires user selection of ``index``, ``columns``, and ``values``, then
        asks whether to reset index and whether to update inplace.

    ``pivot_table``
        Optionally selects ``index``, ``columns``, and ``values``, then asks for
        aggregation function(s), optional fill value, margins, dropna behavior,
        reset-index behavior, and inplace mode.

    Error Handling
    --------------
    - Invalid menu numbers are rejected and the menu loop continues.
    - Unsupported actions are reported explicitly.
    - Any exception raised during downstream execution is caught and printed so that
    the interactive menu remains active.

    Side Effects
    ------------
    - Prints menu options, prompts, warnings, and execution errors to the console.
    - May trigger transformation operations that store the latest transformation
    result in the engine's transview state when ``inplace=True`` is selected.

    Notes
    -----
    - This function assumes that ``cornus.cleaned_data`` is already initialized
    and available for selection-based workflows.
    - The decorator ``@menu_wrapper("Trans-viewing Data Menu")`` provides a styled
    wrapper around the terminal menu execution.
    - User input collection and downstream transformation execution are intentionally
    separated so that the engine remains the single execution entry point.
    """
    logger.info("Entered transviewing_data_menu")
    while True:
        transview_op = {
            1: "stack",
            2: "unstack",
            3: "melt",
            4: "pivot",
            5: "pivot_table",
            0: "↩️ Back to Main Menu",
        }

        for i, operation in transview_op.items():
            print(f"🍁 {i}. {operation}")

        choice = input_int("🕯️ Please enter trans-view services", default=None)
        logger.info("Transview menu choice=%s", choice)

        if choice is None or choice == 0:
            logger.info("Leaving transviewing_data_menu")
            print("↩️ Back to Main Menu.")
            return

        if choice not in transview_op:
            logger.warning("Invalid transview menu choice: %s", choice)
            print("⚠️ Invalid choice ‼️")
            continue

        action = transview_op[choice]
        logger.info("Transview menu action selected: %s", action)

        try:
            # ---------- Stack ----------
            if action == "stack":
                set_index = None
                selected_columns = None

                select_index = input_yesno(
                    "🕯️ Set index columns before stacking", default=False
                )
                if select_index is None:
                    continue

                if select_index:
                    set_index = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter index column numbers",
                    )
                    if set_index == "__BACK__":
                        continue

                select_columns = input_yesno(
                    "🕯️ Select specific columns to stack", default=False
                )
                if select_columns is None:
                    continue

                if select_columns:
                    selected_columns = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter stack target column numbers",
                    )
                    if selected_columns == "__BACK__":
                        continue

                dropna = _select_dropna()
                if dropna is None:
                    continue

                reset_index = _select_reset_index()
                if reset_index is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching transviewing_data: action=%s, selected_columns=%s, set_index=%s, dropna=%s, reset_index=%s, inplace=%s",
                    action,
                    selected_columns,
                    set_index,
                    dropna,
                    reset_index,
                    inplace,
                )
                cornus.transviewing_data(
                    action=action,
                    selected_columns=selected_columns,
                    set_index=set_index,
                    dropna=dropna,
                    reset_index=reset_index,
                    inplace=inplace,
                )

            # ---------- Unstack ----------
            elif action == "unstack":
                set_index = None
                selected_columns = None

                select_index = input_yesno(
                    "🕯️ Set index columns before unstacking", default=True
                )
                if select_index is None:
                    continue

                if select_index:
                    set_index = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter index column numbers",
                    )
                    if set_index == "__BACK__":
                        continue

                select_columns = input_yesno(
                    "🕯️ Select specific columns before unstack", default=False
                )
                if select_columns is None:
                    continue

                if select_columns:
                    selected_columns = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter retained column numbers",
                    )
                    if selected_columns == "__BACK__":
                        continue

                level = _input_unstack_level()
                if level is None:
                    continue

                use_fill_value = input_yesno("🕯️ Set fill_value", default=False)
                if use_fill_value is None:
                    continue

                fill_value = None
                if use_fill_value:
                    fill_value = _input_fill_value("🕯️ Enter fill_value")
                    if fill_value is None:
                        continue

                reset_index = _select_reset_index()
                if reset_index is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching transviewing_data: action=%s, set_index=%s, selected_columns=%s, level=%s, fill_value=%s, reset_index=%s, inplace=%s",
                    action,
                    set_index,
                    selected_columns,
                    level,
                    fill_value,
                    reset_index,
                    inplace,
                )
                cornus.transviewing_data(
                    action=action,
                    set_index=set_index,
                    selected_columns=selected_columns,
                    level=level,
                    fill_value=fill_value,
                    reset_index=reset_index,
                    inplace=inplace,
                )

            # ---------- Melt ----------
            elif action == "melt":
                id_vars = None
                value_vars = None

                select_id_vars = input_yesno("🕯️ Select id_vars", default=False)
                if select_id_vars is None:
                    continue

                if select_id_vars:
                    id_vars = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter id_vars column numbers",
                    )
                    if id_vars == "__BACK__":
                        continue

                select_value_vars = input_yesno("🕯️ Select value_vars", default=False)
                if select_value_vars is None:
                    continue

                if select_value_vars:
                    value_vars = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter value_vars column numbers",
                    )
                    if value_vars == "__BACK__":
                        continue

                var_name = input_text_value("🕯️ Enter var_name (ENTER keeps default)")
                if var_name is None:
                    continue
                if var_name == "":
                    var_name = None

                value_name = input_text_value(
                    "🕯️ Enter value_name (ENTER keeps default)"
                )
                if value_name is None:
                    continue
                if value_name == "":
                    value_name = None

                ignore_index = _select_ignore_index()
                if ignore_index is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching transviewing_data: action=%s, id_vars=%s, value_vars=%s, var_name=%s, value_name=%s, ignore_index=%s, inplace=%s",
                    action,
                    id_vars,
                    value_vars,
                    var_name or "variable",
                    value_name or "value",
                    ignore_index,
                    inplace,
                )
                cornus.transviewing_data(
                    action=action,
                    id_vars=id_vars,
                    value_vars=value_vars,
                    var_name=var_name or "variable",
                    value_name=value_name or "value",
                    ignore_index=ignore_index,
                    inplace=inplace,
                )

            # ---------- Pivot ----------
            elif action == "pivot":
                index = None
                columns = None
                values = None

                index = _select_target_columns(
                    cornus.cleaned_data,
                    prompt="🔎 Enter pivot index column numbers",
                )
                if index == "__BACK__" or index is None:
                    continue

                columns = _select_target_columns(
                    cornus.cleaned_data,
                    prompt="🔎 Enter pivot columns numbers",
                )
                if columns == "__BACK__" or columns is None:
                    continue

                values = _select_target_columns(
                    cornus.cleaned_data,
                    prompt="🔎 Enter pivot values column numbers",
                )
                if values == "__BACK__" or values is None:
                    continue

                reset_index = _select_reset_index()
                if reset_index is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching transviewing_data: action=%s, index=%s, columns=%s, values=%s, reset_index=%s, inplace=%s",
                    action,
                    index,
                    columns,
                    values,
                    reset_index,
                    inplace,
                )
                cornus.transviewing_data(
                    action=action,
                    index=index,
                    columns=columns,
                    values=values,
                    reset_index=reset_index,
                    inplace=inplace,
                )

            # ---------- Pivot table ----------
            elif action == "pivot_table":
                index = None
                columns = None
                values = None

                select_index = input_yesno("🕯️ Select pivot_table index", default=False)
                if select_index is None:
                    continue

                if select_index:
                    index = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter pivot_table index column numbers",
                    )
                    if index == "__BACK__":
                        continue

                select_columns = input_yesno(
                    "🕯️ Select pivot_table columns", default=False
                )
                if select_columns is None:
                    continue

                if select_columns:
                    columns = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter pivot_table columns numbers",
                    )
                    if columns == "__BACK__":
                        continue

                select_values = input_yesno(
                    "🕯️ Select pivot_table values", default=False
                )
                if select_values is None:
                    continue

                if select_values:
                    values = _select_target_columns(
                        cornus.cleaned_data,
                        prompt="🔎 Enter pivot_table values column numbers",
                    )
                    if values == "__BACK__":
                        continue

                aggfunc = _select_aggfunc()
                if aggfunc == "__BACK__":
                    continue
                if aggfunc is None:
                    continue

                use_fill_value = input_yesno("🕯️ Set fill_value", default=False)
                if use_fill_value is None:
                    continue

                fill_value = None
                if use_fill_value:
                    fill_value = _input_fill_value("🕯️ Enter fill_value")
                    if fill_value is None:
                        continue
                    if fill_value == "__EMPTY__":
                        fill_value = None

                margins = _select_margins()
                if margins is None:
                    continue

                dropna = _select_dropna()
                if dropna is None:
                    continue

                reset_index = _select_reset_index()
                if reset_index is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching transviewing_data: action=%s, index=%s, columns=%s, values=%s, aggfunc=%s, fill_value=%s, margins=%s, dropna=%s, reset_index=%s, inplace=%s",
                    action,
                    index,
                    columns,
                    values,
                    aggfunc,
                    fill_value,
                    margins,
                    dropna,
                    reset_index,
                    inplace,
                )
                cornus.transviewing_data(
                    action=action,
                    index=index,
                    columns=columns,
                    values=values,
                    aggfunc=aggfunc,
                    fill_value=fill_value,
                    margins=margins,
                    dropna=dropna,
                    reset_index=reset_index,
                    inplace=inplace,
                )

            else:
                logger.warning("Unsupported transview action: %s", action)
                print(f"⚠️ Unsupported transview action: {action} ‼️")

        except Exception as e:
            logger.exception("transviewing_data_menu failed unexpectedly")
            print(f"⚠️ Trans-viewing data failed: {e} ‼️")


# =================================================

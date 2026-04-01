# -------------------- Import Modules --------------------
import logging

from Cornus.Cornus_Engine import CornusEngine
from Cornus.Menu_Helper_Decorator import (
    column_list,
    input_int,
    input_list,
    input_new_column_name,
    input_numeric_value,
    input_text_value,
    menu_wrapper,
    select_inplace,
    select_save_csv,
)

logger = logging.getLogger("Cornus")


# Compution data section
# -------------------- Helper: select one column --------------------
def _select_one_column(data) -> str | None:
    """
    Interactively select exactly one column from a dataset by menu number.

    This helper builds a menu-number-to-column-name mapping from the provided
    dataset, prompts the user to choose one column by entering its menu number,
    validates that exactly one valid choice was supplied, and returns the
    corresponding real column name.

    Parameters
    ----------
    data : pandas.DataFrame
        Dataset whose columns will be displayed for interactive selection.

    Returns
    -------
    str | None
        - ``str``
        The selected real column name.
        - ``None``
        Returned when no selectable columns are available, when the user chooses
        to go back, when the user skips input, when more than one column is
        entered, or when the entered menu number is invalid.

    Behavior
    --------
    - Calls ``column_list(data)`` to generate the menu-number-to-column-name
    mapping.
    - Prompts the user through ``input_list()`` to enter one column number.
    - Validates that exactly one menu number was entered.
    - Converts the selected menu number into the corresponding real column name.
    - Prints a warning if the input is invalid.

    Notes
    -----
    - This helper is intended for menu-driven workflows that require exactly one
    source column.
    - The function performs only selection and validation logic; it does not modify
    the dataset.
    """
    logger.info("_select_one_column() started")
    col_map = column_list(data)

    if not col_map:
        logger.warning("No column mapping available for single-column selection")
        return None

    selected_col_num = input_list("🔎 Enter one column number")

    if selected_col_num == "__BACK__":
        logger.info("_select_one_column() returned back")
        return None

    if not selected_col_num or len(selected_col_num) != 1:
        logger.info("_select_one_column() skipped or invalid count")
        print("⚠️ Please select exactly one column ‼️")
        return None

    item = selected_col_num[0]

    if not str(item).isdigit() or int(item) not in col_map:
        logger.warning("Invalid single column number: %s", item)
        print(f"⚠️ Invalid column number: {item} ‼️")
        return None

    logger.info("Selected single column: %s", col_map[int(item)])
    return col_map[int(item)]


# -------------------- Helper: select multiple columns --------------------
def _select_target_columns(
    data, prompt: str = "🔎 Enter column numbers"
) -> list[str] | None:
    """
    Interactively select one or more columns from a dataset by menu number.

    This helper builds a menu-number-to-column-name mapping from the provided
    dataset, prompts the user to choose one or more columns by entering menu
    numbers, converts valid selections into the corresponding real column names,
    and returns them as a list.

    Parameters
    ----------
    data : pandas.DataFrame
        Dataset whose columns will be displayed for interactive selection.
    prompt : str, default="🔎 Enter column numbers"
        Prompt text shown to the user before reading the menu-number input.

    Returns
    -------
    list[str] | None
        - ``list[str]``
        A list of selected real column names.
        - ``None``
        Returned when no selectable columns are available, when the user chooses
        to go back, when the user skips input, or when no valid menu numbers are
        successfully converted.

    Behavior
    --------
    - Calls ``column_list(data)`` to generate the menu-number-to-column-name
    mapping.
    - Prompts the user through ``input_list()`` using the supplied ``prompt``.
    - Converts each valid numeric menu choice into the corresponding real column
    name.
    - Prints a warning for any invalid menu number entered.
    - Returns only the successfully validated selections.

    Notes
    -----
    - Invalid selections are ignored individually rather than terminating the whole
    selection process.
    - This helper performs only selection and validation logic; it does not modify
    the dataset.
    """
    logger.info("_select_target_columns() started with prompt=%s", prompt)
    col_map = column_list(data)

    if not col_map:
        logger.warning("No column mapping available for target-column selection")
        return None

    selected_col_num = input_list(prompt)

    if selected_col_num == "__BACK__":
        logger.info("_select_target_columns() returned back")
        return None

    if not selected_col_num:
        logger.info("_select_target_columns() skipped by user")
        return None

    target_columns = []
    for item in selected_col_num:
        if str(item).isdigit() and int(item) in col_map:
            target_columns.append(col_map[int(item)])
        else:
            logger.warning("Invalid target column number: %s", item)
            print(f"⚠️ Invalid column number: {item} ‼️")

    logger.info("Selected target columns: %s", target_columns)
    return target_columns if target_columns else None


# -------------------- Helper: select single-column operation --------------------
def _select_single_column_operation() -> str | None:
    """
    Interactively select a supported single-column computation operation.

    This helper displays a fixed menu of supported single-column operations and
    returns the operation name corresponding to the user's menu choice.

    Returns
    -------
    str | None
        - ``str``
        The selected operation name.
        - ``None``
        Returned when the user cancels the prompt, goes back, or enters an
        invalid menu choice.

    Behavior
    --------
    - Displays the supported single-column operations as a numbered menu.
    - Uses ``input_int()`` to collect the user's choice.
    - Converts the selected menu number into the corresponding internal operation
    name.
    - Prints a warning when the entered choice is invalid.

    Supported Operations
    --------------------
    - ``add``
    - ``sub``
    - ``mul``
    - ``div``
    - ``abs``
    - ``round``
    - ``sqrt``
    - ``log``

    Notes
    -----
    - This helper is intended for interactive menu-driven computation workflows.
    - The returned value is designed to be passed into
    ``cornus.compution_data(action="single_column_calculation", ...)``.
    """
    logger.info("_select_single_column_operation() started")
    single_op_menu = {
        1: "add",
        2: "sub",
        3: "mul",
        4: "div",
        5: "abs",
        6: "round",
        7: "sqrt",
        8: "log",
    }

    for i, op in single_op_menu.items():
        print(f"🍁 {i}. {op}")

    op_choice = input_int("🕯️ Select single-column operation", default=None)

    if op_choice is None:
        logger.info("_select_single_column_operation() cancelled")
        return None

    operation = single_op_menu.get(op_choice)
    if operation is None:
        logger.warning("Invalid single-column operation choice: %s", op_choice)
        print("⚠️ Invalid operation choice ‼️")
        return None

    logger.info("Selected single-column operation: %s", operation)
    return operation


# -------------------- Helper: select multi-column operation --------------------
def _select_multi_column_operation() -> str | None:
    """
    Interactively select a supported multi-column computation operation.

    This helper displays a fixed menu of supported multi-column operations and
    returns the operation name corresponding to the user's menu choice.

    Returns
    -------
    str | None
        - ``str``
        The selected operation name.
        - ``None``
        Returned when the user cancels the prompt, goes back, or enters an
        invalid menu choice.

    Behavior
    --------
    - Displays the supported multi-column operations as a numbered menu.
    - Uses ``input_int()`` to collect the user's choice.
    - Converts the selected menu number into the corresponding internal operation
    name.
    - Prints a warning when the entered choice is invalid.

    Supported Operations
    --------------------
    - ``sum``
    - ``mean``
    - ``max``
    - ``min``
    - ``product``
    - ``sub``
    - ``div``

    Notes
    -----
    - The operations ``sub`` and ``div`` typically require exactly two source
    columns; that validation is handled later by the menu/controller logic.
    - This helper is intended for interactive menu-driven computation workflows.
    """
    logger.info("_select_multi_column_operation() started")
    multi_op_menu = {
        1: "sum",
        2: "mean",
        3: "max",
        4: "min",
        5: "product",
        6: "sub",
        7: "div",
    }

    for i, op in multi_op_menu.items():
        print(f"🍁 {i}. {op}")

    op_choice = input_int("🕯️ Select multi-column operation", default=None)

    if op_choice is None:
        logger.info("_select_multi_column_operation() cancelled")
        return None

    operation = multi_op_menu.get(op_choice)
    if operation is None:
        logger.warning("Invalid multi-column operation choice: %s", op_choice)
        print("⚠️ Invalid operation choice ‼️")
        return None

    logger.info("Selected multi-column operation: %s", operation)
    return operation


# -------------------- Helper: select aggregation method --------------------
def _select_agg_method() -> str | list[str] | None:
    """
    Interactively select one or more aggregation methods for grouped aggregation.

    This helper displays a numbered menu of supported aggregation methods, accepts
    one or more menu-number selections, converts valid selections into real
    aggregation names, and returns either a single method name or a list of method
    names depending on how many valid choices were made.

    Returns
    -------
    str | list[str] | None
        - ``str``
        Returned when exactly one valid aggregation method is selected.
        - ``list[str]``
        Returned when multiple valid aggregation methods are selected.
        - ``None``
        Returned when the user chooses to go back, skips input, or no valid
        aggregation selections are made.

    Behavior
    --------
    - Displays the supported aggregation methods as a numbered menu.
    - Uses ``input_list()`` to collect one or more menu-number selections.
    - Converts each valid numeric selection into the corresponding aggregation
    method name.
    - Prints a warning for any invalid menu number entered.
    - Returns a single string when one method is selected, otherwise a list.

    Supported Aggregation Methods
    -----------------------------
    - ``sum``
    - ``mean``
    - ``max``
    - ``min``
    - ``count``
    - ``median``
    - ``std``

    Notes
    -----
    - This helper is intended for use with groupby aggregation workflows such as
    ``cornus.compution_data(action="groupby_aggregation_calculation", ...)``.
    - Invalid selections are ignored individually rather than aborting the entire
    input step.
    """
    logger.info("_select_agg_method() started")
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

    selected_agg_num = input_list("🕯️ Select aggregation method numbers")

    if selected_agg_num == "__BACK__":
        logger.info("_select_agg_method() returned back")
        return None

    if not selected_agg_num:
        logger.info("_select_agg_method() skipped by user")
        return None

    agg_methods = []
    for item in selected_agg_num:
        if str(item).isdigit() and int(item) in agg_menu:
            agg_methods.append(agg_menu[int(item)])
        else:
            logger.warning("Invalid aggregation number: %s", item)
            print(f"⚠️ Invalid aggregation number: {item} ‼️")

    if not agg_methods:
        return None

    if len(agg_methods) == 1:
        logger.info("Selected aggregation method: %s", agg_methods[0])
        return agg_methods[0]

    logger.info("Selected aggregation methods: %s", agg_methods)
    logger.warning("_select_target_columns() finished with no valid target columns")
    return agg_methods


# -------------------- Helper: select conditional operator --------------------
def _select_operator() -> str | None:
    """
    Interactively select a supported comparison operator.

    This helper displays a fixed menu of supported comparison operators and returns
    the operator string corresponding to the user's menu choice.

    Returns
    -------
    str | None
        - ``str``
        The selected comparison operator.
        - ``None``
        Returned when the user cancels the prompt, goes back, or enters an
        invalid menu choice.

    Behavior
    --------
    - Displays the supported operators as a numbered menu.
    - Uses ``input_int()`` to collect the user's choice.
    - Converts the selected menu number into the corresponding operator string.
    - Prints a warning when the entered choice is invalid.

    Supported Operators
    -------------------
    - ``>``
    - ``>=``
    - ``<``
    - ``<=``
    - ``==``
    - ``!=``

    Notes
    -----
    - This helper is intended for conditional feature-generation workflows.
    - The returned operator is typically passed into
    ``cornus.compution_data(action="conditional_calculation", ...)``.
    """
    logger.info("_select_operator() started")
    operator_menu = {
        1: ">",
        2: ">=",
        3: "<",
        4: "<=",
        5: "==",
        6: "!=",
    }

    for i, op in operator_menu.items():
        print(f"🍁 {i}. {op}")

    op_choice = input_int("🕯️ Select operator", default=None)

    if op_choice is None:
        logger.info("_select_operator() cancelled")
        return None

    operator = operator_menu.get(op_choice)
    if operator is None:
        logger.warning("Invalid operator choice: %s", op_choice)
        print("⚠️ Invalid operator choice ‼️")
        return None

    logger.info("Selected operator: %s", operator)
    return operator


# -------------------- Computing data menu --------------------
@menu_wrapper("Computing Data Menu")
def compution_data_menu(cornus: CornusEngine):
    """
    Interactive menu controller for computation-related data operations.

    This menu provides a terminal-based interface for executing the main
    calculation and feature-engineering services exposed through ``CornusEngine``.
    Through an interactive workflow, the user can choose a computation action,
    select one or more source columns, configure action-specific parameters such as
    operations, thresholds, aggregation methods, output column names, and save
    preferences, and then trigger the corresponding computation method on the
    current computed dataset.

    Menu Options
    ------------
    1. ``single_column_calculation``
        Apply a supported numeric transformation to one selected source column.
    2. ``multiple_columns_calculation``
        Apply a supported row-wise operation across multiple selected columns and
        store the result in a new or default-named output column.
    3. ``groupby_aggregation_calculation``
        Group the current computed dataset by one or more columns and apply one or
        more aggregation methods to selected target columns.
    4. ``conditional_calculation``
        Create a new derived column based on a comparison rule applied to one
        source column.
    5. ``reset_computed_data``
        Reset the current computed working dataset back to the cleaned-data
        baseline.
    0. ``Back to Main Menu``
        Exit the computation menu and return to the main menu.

    Parameters
    ----------
    cornus : CornusEngine
        Main engine instance used to access computation-related features through
        ``cornus.compution_data(...)`` and the current computed working dataset
        through ``cornus.computed_data``.

    Returns
    -------
    None
        This function acts as an interactive menu loop and does not directly return
        the computed DataFrame. All previews, results, summaries, and saved outputs
        are handled by the downstream engine/core methods invoked by the selected
        menu branch.

    Workflow
    --------
    1. Display the available computation operations.
    2. Read and validate the user's menu choice.
    3. Resolve the selected action name from the menu mapping.
    4. Collect any required parameters through helper functions such as:

    - ``_select_one_column()``
    - ``_select_target_columns()``
    - ``_select_single_column_operation()``
    - ``_select_multi_column_operation()``
    - ``_select_agg_method()``
    - ``_select_operator()``
    - ``input_text_value()``
    - ``input_numeric_value()``
    - ``input_new_column_name()``
    - ``select_save_csv()``
    - ``select_inplace()``

    5. Call ``cornus.compution_data(...)`` with the collected arguments.
    6. Continue looping until the user chooses to return to the main menu.

    Behavior by Action
    ------------------
    - ``single_column_calculation``
    Requests exactly one source column, one supported single-column operation,
    optionally a numeric scalar for operations that require it, an optional
    output column name, and an inplace choice. If the output column name is
    skipped and ``inplace=False``, the downstream computation method may use a
    default generated column name.

    - ``multiple_columns_calculation``
    Requests multiple source columns, one supported multi-column operation, and
    an optional output column name. For ``"sub"`` and ``"div"``, exactly two
    source columns are required. If the output column name is skipped, the
    downstream computation method may generate a default column name.

    - ``groupby_aggregation_calculation``
    Requests groupby columns, target columns, one or more aggregation methods,
    and a save-to-CSV choice.

    - ``conditional_calculation``
    Requests one source column, one comparison operator, a threshold value, a
    true-case output value, a false-case output value, an optional output column
    name, and a save-to-CSV choice. If the output column name is skipped, the
    downstream computation method may generate a default column name.

    - ``reset_computed_data``
    Requests only whether the reset-related report/history should be saved.

    Error Handling
    --------------
    - Invalid menu choices are rejected and the menu is shown again.
    - Invalid or incomplete helper selections cause the current branch to be
    skipped and the menu loop to continue.
    - Unsupported action names are reported explicitly.
    - Any exception raised during computation execution is caught and printed
    without terminating the overall menu loop.

    Notes
    -----
    - This menu assumes that ``cornus.computed_data`` is already available, which
    normally requires prior data upload and pipeline initialization.
    - The current data source used for column selection in this menu is
    ``cornus.computed_data``, not ``cornus.cleaned_data``.
    - The decorator ``@menu_wrapper("Computing Data Menu")`` is used to provide a
    consistent menu-style user interface.
    - This function is intended for interactive terminal workflows and therefore
    prioritizes guided input collection over direct parameter passing.
    """
    logger.info("Entered compution_data_menu")
    while True:
        compution_op = {
            1: "single_column_calculation",
            2: "multiple_columns_calculation",
            3: "groupby_aggregation_calculation",
            4: "conditional_calculation",
            5: "reset_computed_data",
            0: "↩️ Back to Main Menu",
        }

        for i, operation in compution_op.items():
            print(f"🍁 {i}. {operation}")

        choice = input_int("🕯️ Please enter your choice", default=None)
        logger.info("Compution menu choice=%s", choice)

        if choice is None or choice == 0:
            logger.info("Leaving compution_data_menu")
            print("↩️ Back to Main Menu.")
            return

        if choice not in compution_op:
            logger.warning("Invalid compution menu choice: %s", choice)
            print("⚠️ Invalid choice ‼️")
            continue

        action = compution_op[choice]
        logger.info("Compution menu action selected: %s", action)

        try:
            # ---------- Single column calculation ----------
            if action == "single_column_calculation":
                column = _select_one_column(cornus.computed_data)
                if column is None:
                    continue

                operation = _select_single_column_operation()
                if operation is None:
                    continue

                value = None
                if operation in ["add", "sub", "mul", "div", "round"]:
                    value = input_numeric_value("🕯️ Enter numeric value")
                    if value is None:
                        continue

                new_column = input_new_column_name(allow_empty_default=True)
                if operation in [
                    "add",
                    "sub",
                    "mul",
                    "div",
                    "abs",
                    "round",
                    "sqrt",
                    "log",
                ]:
                    # allow_empty_default=True means None is valid as "use default"
                    pass

                inplace = select_inplace()
                if inplace is None:
                    continue

                save_csv = select_save_csv()
                if save_csv is None:
                    continue

                logger.info(
                    "Dispatching compution_data: action=%s, column=%s, operation=%s, value=%s, new_column=%s, inplace=%s, save_csv=%s",
                    action,
                    column,
                    operation,
                    value,
                    new_column,
                    inplace,
                    save_csv,
                )
                cornus.compution_data(
                    action=action,
                    column=column,
                    operation=operation,
                    value=value,
                    new_column=new_column,
                    inplace=inplace,
                    save_csv=save_csv,
                )

            # ---------- Multiple columns calculation ----------
            elif action == "multiple_columns_calculation":
                columns = _select_target_columns(
                    cornus.computed_data,
                    prompt="🔎 Enter column numbers",
                )
                if columns is None:
                    continue

                operation = _select_multi_column_operation()
                if operation is None:
                    continue

                if operation in ["sub", "div"] and len(columns) != 2:
                    logger.warning(
                        "Operation '%s' requires exactly 2 columns, got %s",
                        operation,
                        len(columns),
                    )
                    print("⚠️ Operation 'sub' or 'div' requires exactly 2 columns ‼️")
                    continue

                new_column = input_new_column_name(allow_empty_default=True)

                save_csv = select_save_csv()
                if save_csv is None:
                    continue

                logger.info(
                    "Dispatching compution_data: action=%s, columns=%s, operation=%s, new_column=%s, save_csv=%s",
                    action,
                    columns,
                    operation,
                    new_column,
                    save_csv,
                )
                cornus.compution_data(
                    action=action,
                    columns=columns,
                    operation=operation,
                    new_column=new_column,
                    save_csv=save_csv,
                )

            # ---------- Groupby aggregation calculation ----------
            elif action == "groupby_aggregation_calculation":
                groupby_columns = _select_target_columns(
                    cornus.computed_data,
                    prompt="🔎 Enter groupby column numbers",
                )
                if groupby_columns is None:
                    continue

                target_columns = _select_target_columns(
                    cornus.computed_data,
                    prompt="🔎 Enter target column numbers",
                )
                if target_columns is None:
                    continue

                agg_method = _select_agg_method()
                if agg_method is None:
                    continue

                save_csv = select_save_csv()
                if save_csv is None:
                    continue

                logger.info(
                    "Dispatching compution_data: action=%s, groupby_columns=%s, target_columns=%s, agg_method=%s, save_csv=%s",
                    action,
                    groupby_columns,
                    target_columns,
                    agg_method,
                    save_csv,
                )
                cornus.compution_data(
                    action=action,
                    groupby_columns=groupby_columns,
                    target_columns=target_columns,
                    agg_method=agg_method,
                    save_csv=save_csv,
                )

            # ---------- Conditional calculation ----------
            elif action == "conditional_calculation":
                source_column = _select_one_column(cornus.computed_data)
                if source_column is None:
                    continue

                operator = _select_operator()
                if operator is None:
                    continue

                threshold = input_text_value("🕯️ Enter threshold")
                if threshold is None:
                    continue

                true_value = input_text_value("🕯️ Enter true_value")
                if true_value is None:
                    continue

                false_value = input_text_value("🕯️ Enter false_value")
                if false_value is None:
                    continue

                new_column = input_new_column_name(allow_empty_default=True)

                save_csv = select_save_csv()
                if save_csv is None:
                    continue

                logger.info(
                    "Dispatching compution_data: action=%s, source_column=%s, operator=%s, threshold=%s, true_value=%s, false_value=%s, new_column=%s, save_csv=%s",
                    action,
                    source_column,
                    operator,
                    threshold,
                    true_value,
                    false_value,
                    new_column,
                    save_csv,
                )
                cornus.compution_data(
                    action=action,
                    source_column=source_column,
                    operator=operator,
                    threshold=threshold,
                    true_value=true_value,
                    false_value=false_value,
                    new_column=new_column,
                    save_csv=save_csv,
                )

            # ---------- Reset computed data ----------
            elif action == "reset_computed_data":
                save_csv = select_save_csv()
                if save_csv is None:
                    continue

                logger.info(
                    "Dispatching compution_data: action=%s, save_csv=%s",
                    action,
                    save_csv,
                )
                cornus.compution_data(
                    action=action,
                    save_csv=save_csv,
                )

            else:
                logger.warning("Unsupported compution action: %s", action)
                print(f"⚠️ Unsupported compution action: {action} ‼️")

        except Exception as e:
            logger.exception("compution_data_menu failed unexpectedly")
            print(f"⚠️ Compution data failed: {e} ‼️")


# =================================================

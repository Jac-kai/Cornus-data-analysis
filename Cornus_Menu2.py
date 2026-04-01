# -------------------- Import Modules --------------------
import logging

from Cornus.Cornus_Engine import CornusEngine
from Cornus.Menu_Helper_Decorator import (
    column_list,
    index_list,
    input_int,
    input_list,
    input_text_value,
    input_yesno,
    menu_wrapper,
    select_inplace,
)

logger = logging.getLogger("Cornus")


# Clarity data section
# -------------------- Helper: select target index --------------------
def _select_target_index(data) -> list | str | None:
    """
    Interactively select target index labels from a dataset by menu number.

    This helper function builds an index-number mapping from the provided dataset
    and lets the user choose one or more index labels by entering menu numbers.
    The selected menu numbers are converted into the corresponding real index
    labels and returned as a list.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataset whose index mapping will be displayed for selection.

    Returns
    -------
    list | str | None
        - ``list``
        A list of selected real index labels.
        - ``"__BACK__"``
        Returned when the user chooses to go back.
        - ``None``
        Returned when the user skips selection or when no index mapping is
        available.

    Behavior
    --------
    - Calls ``index_list(data)`` to generate the menu-number-to-index-label mapping.
    - Prompts the user to enter index numbers through ``input_list()``.
    - Converts valid numeric menu choices into the real index labels.
    - Prints a warning for any invalid menu number entered.

    Notes
    -----
    - Invalid selections are ignored individually rather than terminating the
    whole selection process.
    - If no index mapping is available, the function returns ``None`` immediately.
    - This function only handles selection logic and does not modify the dataset.
    """
    logger.info("_select_target_index() started")
    idx_map = index_list(data)

    if not idx_map:
        logger.warning("No index mapping available for selection")
        return None

    selected_index_num = input_list("🔎 Enter index numbers")

    if selected_index_num == "__BACK__":
        logger.info("_select_target_index() returned back")
        return "__BACK__"

    if not selected_index_num:
        logger.info("_select_target_index() skipped by user")
        return None

    selected_index = []
    for item in selected_index_num:
        if str(item).isdigit() and int(item) in idx_map:
            selected_index.append(idx_map[int(item)])
        else:
            print(f"⚠️ Invalid index number: {item} ‼️")

    logger.info("Selected target indexes: %s", selected_index)
    return selected_index


# -------------------- Helper: select target columns --------------------
def _select_target_columns(data) -> list[str] | str | None:
    """
    Interactively select target columns from a dataset by menu number.

    This helper function builds a column-number mapping from the provided dataset
    and lets the user choose one or more columns by entering menu numbers.
    The selected menu numbers are converted into the corresponding real column
    names and returned as a list.

    Parameters
    ----------
    data : pandas.DataFrame
        The dataset whose column mapping will be displayed for selection.

    Returns
    -------
    list[str] | str | None
        - ``list[str]``
        A list of selected real column names.
        - ``"__BACK__"``
        Returned when the user chooses to go back.
        - ``None``
        Returned when the user skips selection or when no column mapping is
        available.

    Behavior
    --------
    - Calls ``column_list(data)`` to generate the menu-number-to-column-name
    mapping.
    - Prompts the user to enter column numbers through ``input_list()``.
    - Converts valid numeric menu choices into the real column names.
    - Prints a warning for any invalid menu number entered.

    Notes
    -----
    - Invalid selections are ignored individually rather than terminating the
    whole selection process.
    - If no column mapping is available, the function returns ``None`` immediately.
    - This function only handles selection logic and does not modify the dataset.
    """
    logger.info("_select_target_columns() started")
    col_map = column_list(data)

    if not col_map:
        logger.warning("No column mapping available for selection")
        return None

    selected_col_num = input_list("🔎 Enter column numbers")

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
            print(f"⚠️ Invalid column number: {item} ‼️")

    logger.info("Selected target columns: %s", target_columns)
    return target_columns


# -------------------- Helper: select dropna how --------------------
def _select_dropna_how() -> str | None:
    """
    Select the missing-value dropping mode for ``dropna``.

    This helper function presents a small menu that allows the user to choose how
    missing-value rows should be removed.

    Returns
    -------
    str | None
        - ``"any"``
        Drop rows if any inspected cell is missing.
        - ``"all"``
        Drop rows only if all inspected cells are missing.
        - ``None``
        Returned when the user goes back, cancels the prompt, or enters an
        invalid choice.

    Behavior
    --------
    - Displays a fixed menu for the supported ``dropna`` modes.
    - Uses ``input_int()`` to collect the user's choice.
    - Converts the menu number into the corresponding mode string.
    - Prints a warning when the entered choice is invalid.

    Notes
    -----
    - The default menu choice is ``1``, which corresponds to ``"any"``.
    - The returned value is intended to be passed into data-cleaning methods that
    support the pandas ``dropna(how=...)`` pattern.
    """
    logger.info("_select_dropna_how() started")
    how_menu = {
        1: "any",
        2: "all",
    }

    for i, val in how_menu.items():
        print(f"🍁 {i}. {val}")

    how_choice = input_int("🕯️ Select how", default=1)

    if how_choice is None:
        logger.info("_select_dropna_how() cancelled")
        return None

    how = how_menu.get(how_choice)
    if how is None:
        logger.warning("Invalid dropna how choice: %s", how_choice)
        print("⚠️ Invalid how choice ‼️")
        return None

    logger.info("dropna how selected: %s", how)
    return how


# -------------------- Helper: select duplicate keep mode --------------------
def _select_keep_mode() -> str | None:
    """
    Select the duplicate-retention mode for duplicate removal.

    This helper function presents a menu that allows the user to choose which
    duplicate row occurrence should be kept during duplicate removal.

    Returns
    -------
    str | None
        - ``"first"``
        Keep the first occurrence of each duplicate group.
        - ``"last"``
        Keep the last occurrence of each duplicate group.
        - ``"false"``
        Remove all duplicated rows.
        - ``None``
        Returned when the user goes back, cancels the prompt, or enters an
        invalid choice.

    Behavior
    --------
    - Displays a fixed menu of supported keep modes.
    - Uses ``input_int()`` to collect the user's choice.
    - Converts the menu number into the corresponding keep-mode string.
    - Prints a warning when the entered choice is invalid.

    Notes
    -----
    - The default menu choice is ``1``, which corresponds to ``"first"``.
    - The returned value is a string and may later be converted by downstream
    cleaning logic into the boolean ``False`` if needed.
    """
    logger.info("_select_keep_mode() started")
    keep_menu = {
        1: "first",
        2: "last",
        3: "false",
    }

    for i, val in keep_menu.items():
        print(f"🍁 {i}. {val}")

    keep_choice = input_int("🕯️ Select keep mode", default=1)

    if keep_choice is None:
        logger.info("_select_keep_mode() cancelled")
        return None

    keep = keep_menu.get(keep_choice)
    if keep is None:
        logger.warning("Invalid keep mode choice: %s", keep_choice)
        print("⚠️ Invalid keep choice ‼️")
        return None

    logger.info("Duplicate keep mode selected: %s", keep)
    return keep


# -------------------- Clarity data menu --------------------
@menu_wrapper("Clarity Data Menu")
def clarity_data_menu(cornus: CornusEngine):
    """
    Interactive menu controller for ClarityCore-related cleaning operations.

    This menu provides a terminal-based interface for inspecting pre-cleaning report
    information and executing the main cleaning services exposed through
    ``CornusEngine``. The user can choose a cleaning action, optionally select
    target rows or columns, configure action-specific parameters, and decide whether
    the result should be applied inplace or returned as a preview only.

    Menu Options
    ------------
    1. ``view_data_before_cleaning``
        Display available pre-cleaning report information, such as the null-related
        report prepared upstream by the inspection layer.
    2. ``drop_rows``
        Remove selected rows by index label.
    3. ``drop_columns``
        Remove selected columns by column name.
    4. ``drop_missing_values``
        Remove rows containing missing values, optionally limited to selected
        columns and a chosen ``how`` mode.
    5. ``drop_duplicates``
        Remove duplicate rows, optionally using selected subset columns and a chosen
        keep mode.
    6. ``fill_values``
        Fill missing values with a user-provided fixed value, either across all
        columns or within selected columns.
    7. ``replace_values``
        Replace specified values with a new value, either across all columns or
        within selected columns.
    8. ``strip_string_values``
        Strip surrounding whitespace from string-like values, either across
        automatically selected string columns or within selected columns.
    0. ``Back to Main Menu``
        Exit the clarity menu and return to the main menu.

    Parameters
    ----------
    cornus : CornusEngine
        Main engine instance used to access cleaning-related features through
        methods such as ``cornus.view_data_before_cleaning()`` and
        ``cornus.clarity_data(...)``.

    Returns
    -------
    None
        This function acts as an interactive menu loop and does not return cleaned
        data directly. Cleaning results and previews are handled by the downstream
        engine/core methods that are called from the selected menu branch.

    Workflow
    --------
    1. Display the available clarity-related operations.
    2. Read and validate the user's menu choice.
    3. Resolve the selected action name from the menu mapping.
    4. For actions that require additional input, collect parameters through helper
    functions such as:

    - ``_select_target_index()``
    - ``_select_target_columns()``
    - ``_select_inplace()``
    - ``_select_dropna_how()``
    - ``_select_keep_mode()``
    - ``_input_text_value()``

    5. Call the corresponding ``CornusEngine`` method:

    - ``cornus.view_data_before_cleaning()`` for report viewing
    - ``cornus.clarity_data(...)`` for cleaning actions

    6. Continue looping until the user chooses to go back to the main menu.

    Behavior by Action
    ------------------
    - ``view_data_before_cleaning``
    Calls ``cornus.view_data_before_cleaning()`` to display any available
    pre-cleaning report information.
    - ``drop_rows``
    Requests target index labels and inplace mode.
    - ``drop_columns``
    Requests target columns and inplace mode.
    - ``drop_missing_values``
    Optionally requests target columns, then requests a missing-value dropping
    mode and inplace mode.
    - ``drop_duplicates``
    Optionally requests subset columns, then requests a duplicate keep mode and
    inplace mode.
    - ``fill_values``
    Optionally requests target columns, then requests a fill value and inplace
    mode.
    - ``replace_values``
    Optionally requests target columns, then requests the value to replace, the
    replacement value, and inplace mode.
    - ``strip_string_values``
    Optionally requests target columns, then requests inplace mode.

    Error Handling
    --------------
    - Invalid menu choices are rejected and the menu is shown again.
    - Unsupported action names are reported explicitly.
    - Any exception raised during report viewing or cleaning execution is caught and
    printed without terminating the overall menu loop.

    Notes
    -----
    - This menu assumes the relevant engine/core objects have already been
    initialized, typically after data upload.
    - For actions that inspect or clean the current working dataset, the menu uses
    ``cornus.cleaned_data`` as the current data source for index/column selection.
    - The decorator ``@menu_wrapper("Clarity Data Menu")`` is used to provide a
    consistent menu-style user interface.
    """
    logger.info("Entered clarity_data_menu")
    while True:
        clarity_op = {
            1: "view_data_before_cleaning",
            2: "drop_rows",
            3: "drop_columns",
            4: "drop_missing_values",
            5: "drop_duplicates",
            6: "fill_values",
            7: "replace_values",
            8: "strip_string_values",
            0: "↩️ Back to Main Menu",
        }

        for i, operation in clarity_op.items():
            print(f"🍁 {i}. {operation}")

        choice = input_int("🕯️ Please enter clarity services", default=None)
        logger.info("Clarity menu choice=%s", choice)

        if choice is None or choice == 0:
            logger.info("Leaving clarity_data_menu")
            print("↩️ Back to Main Menu.")
            return

        if choice not in clarity_op:
            logger.warning("Invalid clarity menu choice: %s", choice)
            print("⚠️ Invalid choice ‼️")
            continue

        action = clarity_op[choice]
        logger.info("Clarity menu action selected: %s", action)

        try:
            # ---------- View pre-cleaning report ----------
            if action == "view_data_before_cleaning":
                logger.info("Dispatching view_data_before_cleaning()")
                cornus.view_data_before_cleaning()

            # ---------- Drop rows ----------
            elif action == "drop_rows":
                target_index = _select_target_index(cornus.cleaned_data)
                if target_index == "__BACK__":
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching clarity_data: action=%s, target_index=%s, inplace=%s",
                    action,
                    target_index,
                    inplace,
                )
                cornus.clarity_data(
                    action=action,
                    target_index=target_index,
                    inplace=inplace,
                )

            # ---------- Drop columns ----------
            elif action == "drop_columns":
                target_columns = _select_target_columns(cornus.cleaned_data)
                if target_columns == "__BACK__":
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching clarity_data: action=%s, target_columns=%s, inplace=%s",
                    action,
                    target_columns,
                    inplace,
                )
                cornus.clarity_data(
                    action=action,
                    target_columns=target_columns,
                    inplace=inplace,
                )

            # ---------- Drop missing values ----------
            elif action == "drop_missing_values":
                target_columns = None

                select_columns = input_yesno(
                    "🕯️ Select specific columns", default=False
                )
                if select_columns is None:
                    continue

                if select_columns:
                    target_columns = _select_target_columns(cornus.cleaned_data)
                    if target_columns == "__BACK__":
                        continue

                how = _select_dropna_how()
                if how is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching clarity_data: action=%s, target_columns=%s, how=%s, inplace=%s",
                    action,
                    target_columns,
                    how,
                    inplace,
                )
                cornus.clarity_data(
                    action=action,
                    target_columns=target_columns,
                    how=how,
                    inplace=inplace,
                )

            # ---------- Drop duplicates ----------
            elif action == "drop_duplicates":
                subset = None

                select_subset = input_yesno("🕯️ Select subset columns", default=False)
                if select_subset is None:
                    continue

                if select_subset:
                    subset = _select_target_columns(cornus.cleaned_data)
                    if subset == "__BACK__":
                        continue

                keep = _select_keep_mode()
                if keep is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching clarity_data: action=%s, subset=%s, keep=%s, inplace=%s",
                    action,
                    subset,
                    keep,
                    inplace,
                )
                cornus.clarity_data(
                    action=action,
                    subset=subset,
                    keep=keep,
                    inplace=inplace,
                )

            # ---------- Fill values ----------
            elif action == "fill_values":
                target_columns = None

                select_columns = input_yesno(
                    "🕯️ Select specific columns", default=False
                )
                if select_columns is None:
                    continue

                if select_columns:
                    target_columns = _select_target_columns(cornus.cleaned_data)
                    if target_columns == "__BACK__":
                        continue

                fill_value = input_text_value("🕯️ Enter fill value")
                if fill_value is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching clarity_data: action=%s, target_columns=%s, fill_value=%s, inplace=%s",
                    action,
                    target_columns,
                    fill_value,
                    inplace,
                )
                cornus.clarity_data(
                    action=action,
                    fill_value=fill_value,
                    target_columns=target_columns,
                    inplace=inplace,
                )

            # ---------- Replace values ----------
            elif action == "replace_values":
                target_columns = None

                select_columns = input_yesno(
                    "🕯️ Select specific columns", default=False
                )
                if select_columns is None:
                    continue

                if select_columns:
                    target_columns = _select_target_columns(cornus.cleaned_data)
                    if target_columns == "__BACK__":
                        continue

                to_replace = input_text_value("🕯️ Enter value to replace")
                if to_replace is None:
                    continue

                new_value = input_text_value("🕯️ Enter new value")
                if new_value is None:
                    continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching clarity_data: action=%s, target_columns=%s, to_replace=%s, new_value=%s, inplace=%s",
                    action,
                    target_columns,
                    to_replace,
                    new_value,
                    inplace,
                )
                cornus.clarity_data(
                    action=action,
                    to_replace=to_replace,
                    value=new_value,
                    target_columns=target_columns,
                    inplace=inplace,
                )

            # ---------- Strip string values ----------
            elif action == "strip_string_values":
                target_columns = None

                select_columns = input_yesno(
                    "🕯️ Select specific columns", default=False
                )
                if select_columns is None:
                    continue

                if select_columns:
                    target_columns = _select_target_columns(cornus.cleaned_data)
                    if target_columns == "__BACK__":
                        continue

                inplace = select_inplace()
                if inplace is None:
                    continue

                logger.info(
                    "Dispatching clarity_data: action=%s, target_columns=%s, inplace=%s",
                    action,
                    target_columns,
                    inplace,
                )
                cornus.clarity_data(
                    action=action,
                    target_columns=target_columns,
                    inplace=inplace,
                )

            else:
                logger.warning("Unsupported clarity action: %s", action)
                print(f"⚠️ Unsupported clarity action: {action} ‼️")

        except Exception as e:
            logger.exception("clarity_data_menu failed unexpectedly")
            print(f"⚠️ Clarity data failed: {e} ‼️")


# =================================================

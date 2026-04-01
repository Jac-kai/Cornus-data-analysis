# -------------------- Modules Import --------------------
from functools import wraps


# -------------------- Menu Wrapper --------------------
def menu_wrapper(menu_name: str):
    """
    Create a menu-style decorator for terminal-based interactive functions.

    This decorator factory wraps a target function with a styled menu header and
    basic exception handling. It is mainly intended for command-line menu
    functions, where each menu entry should display a visible title before
    execution and report a friendly error message if execution fails.

    Parameters
    ----------
    menu_name : str
        Display name of the menu shown before and after the wrapped function runs.

    Returns
    -------
    callable
        A decorator that wraps the target function with:

        - a formatted menu title,
        - execution status output,
        - exception catching with a user-friendly error message.

    Behavior
    --------
    When applied to a function, the wrapper:

    1. Prints a styled menu header using ``menu_name``.
    2. Calls the original function with all received positional and keyword
    arguments.
    3. Prints a completion-style execution message after the function returns.
    4. Catches any exception raised by the wrapped function, prints an error
    message, and returns ``None``.

    Notes
    -----
    - This decorator is intended for terminal-based interactive menu workflows.
    - The wrapper uses ``functools.wraps`` so that the wrapped function keeps its
    original metadata such as name and docstring.
    - Exceptions are suppressed and converted into a printed message plus a
    ``None`` return value.

    Examples
    --------
    Typical usage::

        @menu_wrapper("Main Menu")
        def main_menu():
            ...

    The decorated function will display a menu-style title before execution.
    """

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            print(f"---------- 🔥  {menu_name} 🔥  ----------")
            try:
                result = func(*args, **kwargs)
                print(f"🕯️ 🕯️ 🕯️  Executing... {menu_name} 🕯️ 🕯️ 🕯️\n")
                return result
            except Exception as e:
                print(f"⚠️ [ERROR] {menu_name} failed: {e} ‼️")
                return None

        return wrapped

    return decorator


# -------------------- input_int --------------------
def input_int(prompt: str, default: int | None = None) -> int | None:
    """
    Read one integer value from user input.

    This helper prompts the user for an integer input and returns the parsed
    integer result. It supports a default value when the user presses ENTER and
    uses ``"0"`` as a back/cancel signal.

    Parameters
    ----------
    prompt : str
        Prompt text displayed before reading the input.
    default : int | None, optional
        Default value returned when the user presses ENTER without typing any
        value. The default is ``None``.

    Returns
    -------
    int | None
        - ``int``
        The parsed integer value entered by the user.
        - ``None``
        Returned when the user enters ``"0"`` to go back, or when ``default`` is
        ``None`` and the input is empty.

    Behavior
    --------
    - Reads raw terminal input.
    - Treats ``"0"`` as a back/cancel action.
    - Returns ``default`` when the user presses ENTER without typing anything.
    - Attempts to parse the input as ``int``.
    - If parsing fails, prints a warning and returns ``default``.

    Notes
    -----
    - This helper is intended for menu numbers, counts, rotation angles, bin
    counts, and other integer-based settings.
    - Invalid integer input does not raise an exception to the caller; instead,
    the helper falls back to the provided default value.

    Examples
    --------
    If the user enters ``5``, the function returns::

        5

    If the user presses ENTER and ``default=10``, the function returns::

        10
    """
    try:
        value = input(prompt + " (Number only | 0 to ↩️  BACK) ⚡ ").strip()

        if value == "0":
            return None

        return int(value) if value else default

    except ValueError:
        print(f"⚠️ Invalid input, using default {default} ‼️")
        return default


# -------------------- input_yesno --------------------
def input_yesno(prompt: str, default: bool = False) -> bool | None:
    """
    Read a yes/no decision from user input.

    This helper repeatedly prompts the user until a valid yes/no answer is given,
    unless the user chooses to go back. It supports a default Boolean value when
    the user presses ENTER without typing anything.

    Parameters
    ----------
    prompt : str
        Prompt text displayed before reading the input.
    default : bool, default=False
        Default Boolean value returned when the user presses ENTER without typing
        a value.

    Returns
    -------
    bool | None
        - ``True``
        Returned when the user enters ``"y"`` or ``"yes"``.
        - ``False``
        Returned when the user enters ``"n"`` or ``"no"``.
        - ``None``
        Returned when the user enters ``"0"`` to go back.

    Behavior
    --------
    - Accepts ``y`` or ``yes`` as affirmative input.
    - Accepts ``n`` or ``no`` as negative input.
    - Treats ``"0"`` as a back/cancel action and returns ``None``.
    - Returns ``default`` when the input is empty.
    - Uses a loop to keep asking until valid input is provided or back is chosen.

    Notes
    -----
    - This helper is useful for menu decisions such as whether to save output,
    apply changes inplace, show a figure, or continue a workflow.
    - Invalid input does not terminate the caller; the helper simply asks again.

    Examples
    --------
    If the user enters ``yes``, the function returns::

        True

    If the user presses ENTER and ``default=False``, the function returns::

        False
    """
    while True:
        value = (
            input(prompt + " (y or yes/n or no | 0 to ↩️  BACK) ⚡ ").strip().lower()
        )

        if value == "0":
            return None
        if value == "":
            return default
        if value in ["y", "yes"]:
            return True
        if value in ["n", "no"]:
            return False

        print("⚠️ Invalid input, please enter y/yes or n/no ‼️")


# -------------------- input_list --------------------
def input_list(prompt: str) -> list[str] | str | None:
    """
    Read a comma-separated list of values from user input.

    This helper reads one line of input, splits it by commas, strips surrounding
    whitespace from each item, and returns the resulting list of non-empty string
    values. It is intended for menu-driven selection of multiple items such as
    columns, indexes, or aggregation options.

    Parameters
    ----------
    prompt : str
        Prompt text displayed before reading the input.

    Returns
    -------
    list[str] | str | None
        - ``list[str]``
        List of comma-separated input items after whitespace stripping.
        - ``"__BACK__"``
        Returned when the user enters ``"0"`` to go back.
        - ``None``
        Returned when the user presses ENTER without typing any value or when
        input handling fails.

    Behavior
    --------
    - Reads one line of terminal input.
    - Treats ``"0"`` as a back action.
    - Treats empty input as skip and returns ``None``.
    - Splits non-empty input by commas.
    - Removes surrounding whitespace from each item.
    - Filters out empty items after splitting.

    Notes
    -----
    - Returned values remain strings; numeric conversion is handled by downstream
    logic if needed.
    - This helper is commonly used for multi-selection workflows.

    Examples
    --------
    If the user enters::

        1, 3, 5

    the function returns::

        ["1", "3", "5"]
    """
    try:
        value = input(
            f"{prompt} (comma-separated) (ENTER to skip | 0 to ↩️  BACK) ⚡ "
        ).strip()

        if value == "0":
            return "__BACK__"

        return [v.strip() for v in value.split(",") if v.strip()] if value else None

    except Exception:
        print("⚠️ Failed to read list input, returning None ‼️")
        return None


# -------------------- index_list --------------------
def index_list(data: object) -> dict[int, object]:
    """
    Display dataset index labels as a numbered selection list.

    This helper builds and prints a one-based mapping between menu numbers and the
    actual index labels of the provided dataset. It is mainly intended for
    interactive menu workflows where the user needs to select rows by displayed
    number rather than by raw index label.

    Parameters
    ----------
    data : object
        Target object expected to provide an ``index`` attribute, typically a
        pandas DataFrame or Series.

    Returns
    -------
    dict[int, object]
        A dictionary mapping one-based integer menu numbers to actual index
        labels. An empty dictionary is returned when no usable index is available.

    Behavior
    --------
    - Validates that ``data`` is not ``None``.
    - Validates that ``data`` has an ``index`` attribute.
    - Validates that the index is not empty.
    - Prints a numbered index list to the console.
    - Returns the generated mapping dictionary.

    Side Effects
    ------------
    Prints index information or warning messages to the console.

    Notes
    -----
    - This helper is display-oriented and does not modify the dataset.
    - It is commonly used together with input helpers that let the user select
    row positions by menu number.
    - The actual index labels may be integers, strings, timestamps, tuples, or
    other hashable objects.

    Examples
    --------
    If the dataset index is::

        ["A", "B", "C"]

    the returned mapping will be::

        {1: "A", 2: "B", 3: "C"}
    """
    try:
        if data is None:
            print("⚠️ No data available ‼️")
            return {}

        if not hasattr(data, "index"):
            print("⚠️ Target data has no index attribute ‼️")
            return {}

        if len(data.index) == 0:
            print("⚠️ No index found in target data ‼️")
            return {}

        idx_map = {i: idx for i, idx in enumerate(data.index, 1)}

        print("🍁----- Index List -----🍁")
        for i, idx in idx_map.items():
            print(f"🐝 {i}. {idx}")
        print("-" * 40)

        return idx_map

    except Exception as e:
        print(f"⚠️ Failed to display index list: {e} ‼️")
        return {}


# -------------------- column_list --------------------
def column_list(data: object) -> dict[int, str]:
    """
    Display dataset columns as a numbered selection list with data types.

    This helper builds and prints a one-based mapping between menu numbers and the
    actual column names of the provided dataset. It also shows each column's data
    type to help the user make informed selections during menu-driven workflows.

    Parameters
    ----------
    data : object
        Target object expected to provide ``columns`` and ``dtypes`` attributes,
        typically a pandas DataFrame.

    Returns
    -------
    dict[int, str]
        A dictionary mapping one-based integer menu numbers to actual column
        names. An empty dictionary is returned when no usable columns are
        available.

    Behavior
    --------
    - Validates that ``data`` is not ``None``.
    - Validates that ``data`` has a ``columns`` attribute.
    - Validates that the dataset contains at least one column.
    - Builds a numbered column mapping.
    - Builds a column-to-dtype display mapping.
    - Prints the numbered column list with data types.
    - Returns the generated mapping dictionary.

    Side Effects
    ------------
    Prints column information or warning messages to the console.

    Notes
    -----
    - This helper is intended for interactive column selection in cleaning,
    computation, transformation, and plotting menus.
    - The returned mapping dictionary can be used to convert menu numbers back
    into real column names.

    Examples
    --------
    If the dataset columns are::

        Age (int64), Salary (float64), Department (object)

    the returned mapping may be::

        {1: "Age", 2: "Salary", 3: "Department"}
    """
    try:
        if data is None:
            print("⚠️ No data available ‼️")
            return {}

        if not hasattr(data, "columns"):
            print("⚠️ Target data has no columns attribute ‼️")
            return {}

        if len(data.columns) == 0:
            print("⚠️ No columns found in target data ‼️")
            return {}

        col_map = {i: col for i, col in enumerate(data.columns, 1)}
        col_type_map = {col: str(dtype) for col, dtype in data.dtypes.items()}

        print(f"🍁----- Column List -----🍁")
        for i, col in col_map.items():
            print(f"🐝 {i}. {col} ({col_type_map[col]})")
        print("-" * 40)

        return col_map

    except Exception as e:
        print(f"⚠️ Failed to display column list: {e} ‼️")
        return {}


# -------------------- Helper: input text --------------------
def input_text_value(prompt: str) -> str | None:
    """
    Read one text value from user input.

    This helper prompts the user to enter a single text value and returns the
    stripped result as a plain string. It is intended for menu-driven workflows
    that require simple textual parameters such as labels, names, replacement
    values, or custom titles.

    Parameters
    ----------
    prompt : str
        Prompt text displayed before reading the input.

    Returns
    -------
    str | None
        - ``str``
        The entered text after surrounding whitespace has been stripped.
        An empty string may be returned if the user presses ENTER without typing
        anything.
        - ``None``
        Returned when the user enters ``"0"`` to go back.

    Behavior
    --------
    - Reads one line of terminal input.
    - Treats ``"0"`` as a back/cancel action.
    - Strips surrounding whitespace from the entered text.
    - Returns all non-back input as a plain string.

    Notes
    -----
    - This helper does not perform type conversion or validation beyond whitespace
    stripping.
    - It is suitable for prompts such as custom column names, labels, grouping
    values, or other free-text settings.

    Examples
    --------
    If the user enters::

        target_label

    the function returns::

        "target_label"
    """
    value = input(f"{prompt} (typing manually) (0 to ↩️  BACK) ⚡ ").strip()

    if value == "0":
        return None

    return value


# -------------------- Helper: input numeric value --------------------
def input_numeric_value(prompt: str) -> float | int | None:
    """
    Read one numeric value from user input.

    This helper prompts the user to enter a numeric value and attempts to parse
    the input as either an integer or a floating-point number. It is intended for
    menu-driven workflows that require numeric scalar input.

    Parameters
    ----------
    prompt : str
        Prompt text displayed before reading the numeric input.

    Returns
    -------
    float | int | None
        - ``int``
        Returned when the entered value is a valid integer string.
        - ``float``
        Returned when the entered value contains a decimal point and can be
        parsed as a floating-point number.
        - ``None``
        Returned when the user enters ``"0"`` to go back or when the input
        cannot be parsed as numeric.

    Behavior
    --------
    - Reads one line of terminal input.
    - Treats ``"0"`` as a back/cancel action.
    - Parses decimal-style input as ``float``.
    - Parses non-decimal numeric input as ``int``.
    - Prints a warning and returns ``None`` if parsing fails.

    Notes
    -----
    - This helper is useful for thresholds, constants, arithmetic values,
    fill-values, and other numeric menu parameters.
    - Scientific notation such as ``1e3`` will not be recognized by the current
    decimal-point check and may require separate handling if you want to support
    it.

    Examples
    --------
    If the user enters ``10``, the function returns::

        10

    If the user enters ``3.5``, the function returns::

        3.5
    """
    value = input(f"{prompt} (Number | 0 to ↩️  BACK) ⚡ ").strip()

    if value == "0":
        return None

    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        print("⚠️ Value must be numeric ‼️")


# -------------------- Helper: input new column name --------------------
def input_new_column_name(allow_empty_default: bool = False) -> str | None:
    """
    Read a new output column name from user input.

    This helper prompts the user to enter a new column name, typically for a
    derived feature created during a computation workflow. If no explicit name is
    provided, the function returns ``None``.

    Parameters
    ----------
    allow_empty_default : bool, default=False
        Whether empty input is allowed as a valid way to skip manual naming. When
        ``True``, pressing ENTER returns ``None`` so that downstream logic may use
        a default generated column name.

    Returns
    -------
    str | None
        - ``str``
        The entered column name after surrounding whitespace is stripped.
        - ``None``
        Returned when no explicit output column name is provided.

    Notes
    -----
    - This helper is mainly intended for naming newly created computed columns.
    - The exact meaning of ``None`` depends on downstream logic.
    - This helper does not validate whether the proposed column name already
    exists in the dataset.
    """
    if allow_empty_default:
        value = input("🕯️ Enter new column name (ENTER for default) ⚡ ").strip()

        return value if value else None

    value = input("🕯️ Enter new column name ⚡ ").strip()

    return value if value else None


# -------------------- Helper: select inplace --------------------
def select_inplace() -> bool | None:
    """
    Ask whether the current result should be applied inplace.

    This helper is a thin wrapper around ``input_yesno()`` and is used to collect
    the user's decision about whether an operation should update the current
    working dataset directly or only return a preview/result without storing it.

    Returns
    -------
    bool | None
        - ``True``
        Apply the result inplace and update the stored working dataset.
        - ``False``
        Do not apply inplace; keep the current stored dataset unchanged.
        - ``None``
        Returned when the user goes back or cancels the prompt.

    Notes
    -----
    - The default selection is ``False``, meaning preview-only behavior.
    - Although the prompt text currently refers to updating current data, this
    helper can be reused for multiple workflows that support inplace behavior.
    - The actual meaning of inplace depends on the downstream method that receives
    the returned value.
    """
    return input_yesno("🕯️ Update it to current data", default=False)


# -------------------- Helper: select save_csv --------------------
def select_save_csv() -> bool | None:
    """
    Ask whether CSV output should be saved.

    This helper is a thin wrapper around ``input_yesno()`` and is used to collect
    the user's preference for saving CSV-based reports, summaries, exported
    results, or history records produced during a workflow.

    Returns
    -------
    bool | None
        - ``True``
        Save CSV output.
        - ``False``
        Do not save CSV output.
        - ``None``
        Returned when the user goes back or cancels the prompt.

    Notes
    -----
    - The default selection is ``True``.
    - This helper is commonly used in computation workflows such as grouped
    aggregation, conditional calculation, result export, and history logging.
    - The exact file content and save behavior are determined by the downstream
    method that receives the returned value.
    """
    return input_yesno("🕯️ Save CSV report/record/history", default=True)


# -----------------------------------------

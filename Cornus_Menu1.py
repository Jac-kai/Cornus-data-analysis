# -------------------- Import Modules --------------------
import logging
import os
import time

from Cornus.Cornus_Engine import CornusEngine
from Cornus.Menu_Helper_Decorator import (
    column_list,
    index_list,
    input_int,
    input_list,
    input_yesno,
    menu_wrapper,
)

logger = logging.getLogger("Cornus")


# Uploading and vision data sections
# -------------------- Helper: select folder and file --------------------
def _select_folder_and_file(
    cornus: CornusEngine,
) -> tuple[int, int] | tuple[None, None]:
    """
    Interactively select a folder and file from the current working place.

    This helper function displays the list of available folders in the current
    working place and prompts the user to choose a folder number. After a valid
    folder is selected, it displays the files inside that folder and prompts the
    user to choose a file number.

    If the user cancels at any step, the function returns ``(None, None)``.
    If a valid folder and file are selected, the function returns the corresponding
    folder number and file number.

    Workflow
    --------
    1. Call ``cornus.hunter_core.working_place_searcher()`` to retrieve folders.
    2. Display the folder list and request a folder number.
    3. Validate that the selected folder number is within range.
    4. Call ``cornus.hunter_core.files_searcher_from_folders()`` to retrieve files
    from the selected folder.
    5. Display the file list and request a file number.
    6. Validate the selected file number and return the result.

    Parameters
    ----------
    cornus : CornusEngine
        The main Cornus engine instance used to access the ``hunter_core``
        folder and file searching utilities.

    Returns
    -------
    tuple[int, int] | tuple[None, None]
        - ``(selected_folder_num, selected_file_num)``
        The selected folder number and file number.
        - ``(None, None)``
        Returned when the user cancels the operation or when no folders are
        available in the current working place.

    Notes
    -----
    - If the user enters an invalid folder or file number, the function prints
    an error message and asks again.
    - If the selected folder contains no files, the function notifies the user
    and returns to the folder-selection step.
    - This function only handles selection logic. It does not load or upload data.
    """
    logger.info("_select_folder_and_file() started")
    while True:
        # ---------- Show folders from working place ----------
        folders = cornus.hunter_core.working_place_searcher()

        if not folders:
            logger.warning("No folders found in current working place")
            print("⚠️ No folders found in current working place ‼️")
            return None, None

        # ---------- List the folders in working place ----------
        print(f"\n----- 🔥 Folder Lists 🔥-----\n{'-'*50}")
        for i, folder in folders.items():
            print(f"🐞 {i}. {folder}")

        selected_folder_num = input_int("🕯️ Select folder number", default=None)

        if selected_folder_num is None:
            logger.info("_select_folder_and_file() cancelled during folder selection")
            return None, None

        # ---------- Check the input number is in the range ----------
        if selected_folder_num < 1 or selected_folder_num > len(folders):
            logger.warning("Invalid folder number selected: %s", selected_folder_num)
            print("⚠️ Invalid folder number ‼️")
            continue

        # ---------- Show files from selected folder ----------
        files = cornus.hunter_core.files_searcher_from_folders(
            selected_folder_num=selected_folder_num,
            selected_file_num=None,
        )
        logger.info("Selected folder number: %s", selected_folder_num)

        if not files:
            logger.warning("No files found in selected folder: %s", selected_folder_num)
            print("⚠️ No files found in selected folder ‼️")
            continue

        while True:
            # ---------- List the files in selected folder ----------
            print(f"\n----- 🔥 File Lists 🔥-----\n{'-'*50}")
            for i, file in files.items():
                print(f"🍒 {i}. {file}")

            selected_file_num = input_int("🕯️ Select file number", default=None)

            if selected_file_num is None:
                logger.info(
                    "_select_folder_and_file() returned to folder selection from file selection"
                )
                break

            # ---------- Check the input number is in the range ----------
            if selected_file_num < 1 or selected_file_num > len(files):
                logger.warning(
                    "Invalid file number selected: %s in folder %s",
                    selected_file_num,
                    selected_folder_num,
                )
                print("⚠️ Invalid file number ‼️")
                continue

            logger.info(
                "Folder and file selected successfully: folder_num=%s, file_num=%s",
                selected_folder_num,
                selected_file_num,
            )
            return selected_folder_num, selected_file_num


# -------------------- Helper: build parameters for opner --------------------
def _build_opener_param_dict(selected_file_name: str) -> dict:
    """
    Interactively build an opener parameter dictionary based on the selected file type.

    This helper collects optional file-opening parameters through interactive
    prompts and organizes them into a dictionary that can be passed directly to
    a data-loading function.

    The helper automatically checks the selected file extension and only asks for
    parameters that are relevant to that file type. For example, ``parse_dates``
    is only prompted for CSV and Excel files.

    Parameters
    ----------
    selected_file_name : str
        The selected file name used to determine the file extension.

    Returns
    -------
    dict
        A dictionary containing the selected opener parameters.
        Parameters that are not chosen by the user are not included in the result.

    Supported Parameters
    --------------------
    - ``nrows``
      Limit the number of rows to read.
    - ``usecols``
      Specify which columns to read.
    - ``index_col``
      Specify one or more columns to use as the index.
    - ``parse_dates``
      Specify one or more columns to parse as datetime.
      This option is only prompted for CSV and Excel files.

    Notes
    -----
    - This helper only builds the parameter dictionary and does not read any data.
    - The returned dictionary can be passed directly into
      ``cornus.upload_data(..., opener_param_dict=...)``.
    """
    logger.info("_build_opener_param_dict() called for file: %s", selected_file_name)
    opener_param_dict = {}
    ext = os.path.splitext(selected_file_name)[1].lower()
    logger.info("Detected file extension for opener params: %s", ext)

    if input_yesno("🕯️ Set nrows"):
        opener_param_dict["nrows"] = input_int(
            "🔎 How many rows to show out",
            default=500,
        )
        logger.info("Opener parameter set: nrows=%s", opener_param_dict.get("nrows"))

    if input_yesno("🕯️ Set usecols"):
        usecols = input_list("🔎 Which columns to setup")
        if usecols:
            opener_param_dict["usecols"] = usecols
            logger.info(
                "Opener parameter set: usecols=%s", opener_param_dict.get("usecols")
            )

    if input_yesno("🕯️ Set index_col"):
        index_col = input_list("🔎 Which columns to set as index")

        if index_col:
            if len(index_col) == 1:
                item = index_col[0]
                opener_param_dict["index_col"] = (
                    int(item) if str(item).isdigit() else item
                )
            else:
                opener_param_dict["index_col"] = [
                    int(item) if str(item).isdigit() else item for item in index_col
                ]
            logger.info(
                "Opener parameter set: index_col=%s", opener_param_dict.get("index_col")
            )

    # ---------- Only for CSV / Excel ----------
    if ext in [".csv", ".xlsx", ".xls", ".xlsm"]:
        if input_yesno("🕯️ Set parse_dates"):
            parse_dates = input_list("🔎 Which columns to parse as dates")
            if parse_dates:
                opener_param_dict["parse_dates"] = parse_dates
                logger.info(
                    "Opener parameter set: parse_dates=%s",
                    opener_param_dict.get("parse_dates"),
                )

    logger.info("Final opener_param_dict built: %s", opener_param_dict)
    return opener_param_dict


# -------------------- Upload data menu --------------------
@menu_wrapper("Upload Data Menu")
def upload_data_menu(cornus: CornusEngine):
    """
    Upload data menu.

    This menu provides an interactive workflow for selecting a folder and file
    and then uploading data. The user may either upload data directly with default
    settings or configure opener parameters before uploading. If the upload is
    successful, the function prints the data shape and current time. If the upload
    fails, it prints an error message.

    Menu Options
    ------------
    1. ``upload_data``
    Upload data using the default loading behavior.
    2. ``upload_data_with_opener_parameters``
    Build opener parameters interactively before uploading data.
    0. ``Back to Main Menu``
    Return to the main menu without performing any upload.

    Parameters
    ----------
    cornus : CornusEngine
        The main Cornus engine instance responsible for uploading data and managing
        downstream core operations.

    Returns
    -------
    None
        This function is designed as an interactive menu controller and does not
        return uploaded data directly. On success, it prints summary information
        and exits the menu.

    Workflow
    --------
    1. Display the upload menu options.
    2. Determine the upload mode based on the user's selection.
    3. Call ``_select_folder_and_file()`` to let the user choose a folder and file.
    4. If parameterized upload is selected, call ``_build_opener_param_dict()``.
    5. Call ``cornus.upload_data()`` to perform the actual upload.
    6. If successful, print the uploaded data shape and a timestamp.

    Error Handling
    --------------
    - If the user enters an invalid menu choice, the function prints an error
    message and shows the menu again.
    - If folder or file selection is not completed, the workflow returns to the menu.
    - If an exception occurs during upload, the function catches it and prints the
    error message instead of terminating the whole program.

    Notes
    -----
    - This function is typically used as a submenu under the main application menu.
    - The decorator ``@menu_wrapper("Upload Data Menu")`` is used to provide a
    consistent menu display format.
    """
    logger.info("Entered upload_data_menu")
    while True:
        upload_op = {
            1: "upload_data",
            2: "upload_data_with_opener_parameters",
            0: "↩️  Back to Main Menu",
        }

        for i, operations in upload_op.items():
            print(f"🍁 {i}. {operations}")

        choice = input_int("🕯️ Please enter upload services ⚡ ", default=None)
        logger.info("Upload menu choice=%s", choice)

        if choice is None or choice == 0:
            logger.info("Leaving upload_data_menu")
            print("↩️  Back to Main Menu.")
            return

        if choice not in upload_op:
            logger.warning("Invalid upload menu choice: %s", choice)
            print("⚠️ Invalid choice ‼️")
            continue

        action = upload_op[choice]
        logger.info("Upload menu action selected: %s", action)

        try:
            selected_folder_num, selected_file_num = _select_folder_and_file(cornus)

            if selected_folder_num is None:
                logger.info("Upload flow cancelled during folder/file selection")
                continue

            if action == "upload_data":
                logger.info("Uploading data with default opener parameters")
                uploaded_data = cornus.upload_data(
                    selected_folder_num=selected_folder_num,
                    selected_file_num=selected_file_num,
                )

            elif action == "upload_data_with_opener_parameters":
                logger.info("Uploading data with custom opener parameters")
                selected_file_name = cornus.hunter_core.file_list[selected_file_num]
                logger.info(
                    "Selected file for parameterized upload: %s", selected_file_name
                )
                opener_param_dict = _build_opener_param_dict(selected_file_name)

                uploaded_data = cornus.upload_data(
                    selected_folder_num=selected_folder_num,
                    selected_file_num=selected_file_num,
                    opener_param_dict=opener_param_dict,
                )

            else:
                print(f"⚠️ Unsupported upload action: {action} ‼️")
                continue

            if uploaded_data is not None:
                logger.info(
                    "Data uploaded successfully with shape=%s", uploaded_data.shape
                )
                print(f"🐞 Target data shape: {uploaded_data.shape}")
                print(f"🔅 {time.asctime()}\n{'-'*50}")
                return

            else:
                logger.warning("Data upload failed and returned None")
                print("⚠️ Data upload failed ‼️")

        except Exception as e:
            print(f"⚠️ Upload failed: {e} ‼️")
            logger.exception("upload_data_menu failed unexpectedly")


# -------------------- Viewing data menu --------------------
@menu_wrapper("Viewing Data Menu")
def viewing_data_menu(cornus: CornusEngine):
    """
    Viewing data menu.

    This menu provides interactive access to multiple data-inspection operations
    for the currently loaded dataset. Available actions include displaying the
    dataset content, summarizing missing values, selecting specific rows or columns,
    saving a data report, and generating a full data report.

    Menu Options
    ------------
    1. ``data_content``
    Display the current dataset content.
    2. ``null_summary``
    Display a summary of missing values in the dataset.
    3. ``selected_column_or_index``
    View a subset of the data based on selected index labels and/or columns.
    4. ``save_data_report``
    Save a data inspection report.
    5. ``full_data_report``
    Generate and display a full data report.
    0. ``Back to Main Menu``
    Return to the main menu.

    Parameters
    ----------
    cornus : CornusEngine
        The main Cornus engine instance used to execute data-viewing operations.

    Returns
    -------
    None
        This function serves as an interactive menu controller and does not return
        data directly. All output is delegated to ``cornus.viewing_data()``.

    Workflow
    --------
    1. Display the viewing menu options.
    2. Validate the user's menu selection.
    3. If ``selected_column_or_index`` is chosen:
    - Ask whether index labels should be selected.
    - If yes, display the index mapping and collect index numbers.
    - Ask whether columns should be selected.
    - If yes, display the column mapping and collect column numbers.
    - Convert the selected numbers into real index labels and column names.
    - Pass the parsed values into
        ``cornus.viewing_data(action=..., index=..., column=...)``.
    4. For all other actions, call ``cornus.viewing_data(action=action)`` directly.
    5. If an exception occurs, print the corresponding error message.

    Selection Logic
    ---------------
    - Index selection:
    ``index_list(cornus.source_data)`` is used to create a mapping between menu
    numbers and actual index labels.
    - Column selection:
    ``column_list(cornus.source_data)`` is used to create a mapping between menu
    numbers and actual column names.
    - Invalid index or column numbers are reported to the user without terminating
    the menu flow.

    Error Handling
    --------------
    - Invalid menu choices are rejected and the user is prompted again.
    - Any exception raised during data viewing is caught and printed.

    Notes
    -----
    - This function assumes that data has already been loaded into the Cornus engine
    before the menu is used.
    - The decorator ``@menu_wrapper("Viewing Data Menu")`` is used to provide a
    consistent menu display format.
    """
    logger.info("Entered viewing_data_menu")
    while True:
        view_op = {
            1: "data_content",
            2: "null_summary",
            3: "selected_column_or_index",
            4: "save_data_report",
            5: "full_data_report",
            0: "↩️  Back to Main Menu",
        }

        for i, operations in view_op.items():
            print(f"🍁 {i}. {operations}")

        choice = input_int("🕯️ Please enter viewing services", default=None)
        logger.info("Viewing menu choice=%s", choice)

        if choice is None or choice == 0:
            logger.info("Leaving viewing_data_menu")
            print("↩️  Back to Main Menu.")
            return

        if choice not in view_op:
            logger.warning("Invalid viewing menu choice: %s", choice)
            print("⚠️ Invalid choice ‼️")
            continue

        action = view_op[choice]
        logger.info("Viewing menu action selected: %s", action)

        try:
            # ---------- Selected column / index ----------
            if action == "selected_column_or_index":
                logger.info("Starting selected_column_or_index workflow")
                selected_index = None
                selected_column = None

                # ---------- Select index ----------
                select_index = input_yesno("🕯️ Select index")
                if select_index is None:
                    logger.info("Index selection prompt cancelled")
                    continue

                if select_index:
                    logger.info("User chose to select indexes")
                    logger.info("Selected indexes: %s", selected_index)
                    idx_map = index_list(cornus.source_data)

                    if idx_map:
                        selected_index_num = input_list("🔎 Enter index numbers")

                        if selected_index_num == "__BACK__":
                            logger.info("Index number selection returned back")
                            continue

                        if selected_index_num:
                            selected_index = []
                            for item in selected_index_num:
                                if str(item).isdigit() and int(item) in idx_map:
                                    selected_index.append(idx_map[int(item)])
                                else:
                                    logger.warning(
                                        "Invalid index number entered: %s", item
                                    )
                                    print(f"⚠️ Invalid index number: {item} ‼️")

                # ---------- Select columns ----------
                select_column = input_yesno("🕯️ Select columns")
                if select_column is None:
                    logger.info("Column selection prompt cancelled")
                    continue

                if select_column:
                    logger.info("User chose to select columns")
                    logger.info("Selected columns: %s", selected_column)
                    col_map = column_list(cornus.source_data)

                    if col_map:
                        selected_column_num = input_list("🔎 Enter column numbers")

                        if selected_column_num == "__BACK__":
                            logger.info("Column number selection returned back")
                            continue

                        if selected_column_num:
                            selected_column = []
                            for item in selected_column_num:
                                if str(item).isdigit() and int(item) in col_map:
                                    selected_column.append(col_map[int(item)])
                                else:
                                    logger.warning(
                                        "Invalid column number entered: %s", item
                                    )
                                    print(f"⚠️ Invalid column number: {item} ‼️")

                logger.info(
                    "Dispatching viewing_data with action=%s, index=%s, column=%s",
                    action,
                    selected_index,
                    selected_column,
                )
                cornus.viewing_data(
                    action=action,
                    index=selected_index,
                    column=selected_column,
                )

            # ---------- Other viewing actions ----------
            else:
                logger.info("Dispatching viewing_data with action=%s", action)
                cornus.viewing_data(action=action)

        except Exception as e:
            logger.exception("viewing_data_menu failed unexpectedly")
            print(f"⚠️ Viewing data failed: {e} ‼️")


# =================================================

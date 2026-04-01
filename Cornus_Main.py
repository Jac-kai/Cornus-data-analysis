"""
Main terminal controller for the Cornus project.

This module provides the top-level interactive entry point for the Cornus
data-processing workflow by connecting the shared ``CornusEngine`` instance
to all submenu controllers.
"""

# -------------------- Modules Import --------------------
import logging

from Cornus.Cornus_Engine import CornusEngine
from Cornus.Cornus_Menu1 import upload_data_menu, viewing_data_menu
from Cornus.Cornus_Menu2 import clarity_data_menu
from Cornus.Cornus_Menu3 import compution_data_menu
from Cornus.Cornus_Menu4 import transviewing_data_menu
from Cornus.Cornus_Menu5 import data_trendency_menu
from Cornus.Curnus_Logging import cornus_init_logging
from Cornus.Menu_Helper_Decorator import input_int

logger = logging.getLogger("Cornus")


# -------------------- cornus_control --------------------
def cornus_control():
    """
    Run the main interactive controller for the Cornus data-processing system.

    This function serves as the top-level terminal menu for the Cornus project.
    It initializes a single ``CornusEngine`` instance and routes user selections
    to the corresponding menu controllers for data upload, inspection, cleaning,
    computation, transformation, and trend visualization.

    The function maintains one shared engine object throughout the session so that
    all menu branches operate on the same loaded dataset and pipeline state.

    Menu Options
    ------------
    1. ``Upload Data``
        Open the upload-data workflow and load a source dataset into the engine.
    2. ``Viewing Data``
        Open the data-inspection workflow for viewing content summaries, selected
        rows/columns, null summaries, and reports.
    3. ``Clarity Data``
        Open the cleaning/preprocessing workflow for modifying the cleaned dataset.
    4. ``Computing Data``
        Open the computation workflow for derived columns, grouped aggregation,
        and conditional calculations.
    5. ``Transviewing Data``
        Open the reshape/transformation workflow for stack, unstack, melt, pivot,
        and pivot-table operations.
    6. ``Data Trendency``
        Open the visualization workflow for plots and trend inspection.
    0. ``Leave``
        Exit the Cornus main controller loop.

    Returns
    -------
    None
        This function runs an interactive menu loop and does not return a
        computation result. Control flow ends only when the user selects the
        leave option.

    Workflow
    --------
    1. Create one ``CornusEngine`` instance for the current session.
    2. Build the top-level menu mapping between numeric options, display labels,
    and menu functions.
    3. Repeatedly display the main menu and read the user's selected service.
    4. Dispatch the shared engine object to the selected menu function.
    5. Continue until the user selects ``0`` to leave.

    Behavior
    --------
    - All submenu functions receive the same ``cornus_engine`` instance.
    - This allows uploaded data and downstream pipeline state to persist across
    menu branches during a single session.
    - Entering ``0`` is treated as the exit command and terminates the controller
    loop.
    - Empty input and invalid numeric input are converted into ``-1`` through the
    ``input_int(..., default=-1)`` fallback and are handled as invalid
    selections.
    - Invalid selections are handled by printing a warning and continuing the
    loop.

    Notes
    -----
    - This function assumes interactive terminal execution.
    - The shared-engine design is important because it ensures that upload,
    cleaning, computation, transformation, and plotting workflows all operate
    on the same current dataset.
    - Main-menu input is collected through ``input_int(..., default=-1)`` so that
    non-numeric input does not terminate the controller unexpectedly.

    Examples
    --------
    Typical usage from a script entry point::

        if __name__ == "__main__":
            cornus_control()

    This starts the Cornus terminal menu system.
    """
    logger.info("Entered cornus_control")
    cornus_engine = CornusEngine()
    logger.info("CornusEngine initialized successfully")

    menu = [
        (1, "📨 Upload Data", upload_data_menu),
        (2, "👓 Viewing Data", viewing_data_menu),
        (3, "🫧 Clarity Data", clarity_data_menu),
        (4, "🧠 Computing Data", compution_data_menu),
        (5, "🔭 Transviewing Data", transviewing_data_menu),
        (6, "📊 Data Trendency", data_trendency_menu),
        (0, "🍂  Leave", None),
    ]
    menu_width = 35

    while True:
        logger.info("Rendering Cornus main menu")
        print("🐝  Cornus Main Menu 🐝 ".center(menu_width, "━"))

        for opt, action, _ in menu:
            print(f"{opt}. {action:<{menu_width-6}}")
        print("━" * menu_width)

        choice = input_int("🕯️  Select Services ⚡ ", default=-1)
        logger.info("Main menu choice=%s", choice)

        if choice is None:
            logger.info("Leaving cornus_control")
            print("👣👣👣 Leaving Cornus Engine... Goodbye 🍁 Zack King")
            break

        if choice == -1:
            logger.warning("Invalid main menu selection: %s", choice)
            print("⚠️ Invalid selection ‼️")
            continue

        for opt, _, func in menu:
            if choice == opt and func:
                logger.info(
                    "Dispatching submenu: option=%s, function=%s", opt, func.__name__
                )
                func(cornus_engine)
                break
        else:
            logger.warning("Invalid main menu selection: %s", choice)
            print("⚠️ Invalid selection ‼️")


# -------------------- Execute --------------------
if __name__ == "__main__":
    logger = cornus_init_logging()
    logger.info("Starting Cornus main entry point")
    cornus_control()


# -----------------------------------------

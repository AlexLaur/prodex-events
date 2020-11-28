import os

from libs.plugin_collection import Plugin


class MakeProjectDirectory(Plugin):
    """Create the directory for the project"""

    def __init__(self, parent=None):
        super(MakeProjectDirectory, self).__init__(parent=parent)

        self.filters = {"New_Project": ["*"]}

    def perform_operation(self, event, prodex, *args, **kwargs):
        """Execute actions when filters correponds to the incomming event.

        :param event: The event on prodex
        :type event: dict
        :param prodex: The prodex client
        :type prodex: Prodex object
        """
        projects_root = "/home/alaurette/Documents/projects"

        project_item = event.get("meta", None)
        if not project_item:
            return

        reference = project_item.get("reference")
        project_path = os.path.join(projects_root, reference)
        os.mkdir(project_path)

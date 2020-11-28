import os
import inspect
import pkgutil


class Plugin(object):
    """Base class that each plugin must inherit from. within this class
    you must define the methods that all of your plugins must implement"""

    def __init__(self, parent=None):
        self.description = "UNKNOWN"
        self.name = None

        self.filters = {}
        self._parent = parent

    def parent(self):
        """Get the parent of the plugin (should be plugin manager)

        :return: object
        :rtype: PluginCollection
        """
        return self._parent

    def perform_operation(self, argument):
        """The method that we expect all plugins to implement. This is the
        method that our framework will call
        """
        raise NotImplementedError


class PluginCollection(object):
    """Upon creation, this class will read the plugins package for modules
    that contain a class definition that is inheriting from the Plugin class
    """

    def __init__(self, plugin_packages):
        """Constructor that initiates the reading of all available plugins
        when an instance of the PluginCollection object is created
        """
        if not isinstance(plugin_packages, (list, tuple)):
            plugin_packages = [plugin_packages]
        self.plugin_packages = plugin_packages
        self.reload_plugins()

        self._disable = False

    def reload_plugins(self):
        """Reset the list of all plugins and initiate the walk over the main
        provided plugin package to load all available plugins
        """
        self.plugins = {}
        self.seen_paths = []
        print(f"Looking for plugins under package {self.plugin_packages}")
        for plugin_package in self.plugin_packages:
            self.walk_package(plugin_package)

    def disable_plugin_manager(self, disable):
        """This method disable/enable the plugin manager

        :param disable: The status of the disable
        :type disable: bool
        """
        if not isinstance(disable, bool):
            print("Disable must be a boolean.")
            return
        self._disable = disable
        if self._disable:
            print("Disable plugin manager")
        else:
            print("Enable plugin manager")
        if not self._disable:
            self.reload_plugins()

    def apply_all_plugins(self, event_type, field_name, *args, **kwargs):
        """Apply all of the plugins on the argument supplied to this function"""
        result = {}
        if self._disable:
            print("Plugin manager is disable")
            return result
        for plugin_name, plugin_attrs in self.plugins.items():
            if not plugin_attrs.get("enable", False):
                print(f"Skipping {plugin_name} : Plugin disabled.")
                result[plugin_name] = None
                continue
            _plugin = plugin_attrs.get("instance")
            if _plugin.filters:
                if not _plugin.filters.get(event_type):
                    continue
                filters = _plugin.filters[event_type]
                if field_name not in filters and "*" not in filters:
                    continue
                print(f"Dispatching to {plugin_name}")
                try:
                    result[plugin_name] = _plugin.perform_operation(
                        *args, **kwargs
                    )
                except Exception as error:
                    print(f"error on {plugin_name}: {error}")
                    self.manage_plugin(plugin_name=plugin_name, enable=False)
        return result

    def manage_plugin(self, plugin_name, enable):
        """Enable or disable a plugin

        :param plugin_name: The name of the plugin
        :type plugin_name: str
        :param enable: The state of the plugin (True to enable, False to disable)
        :type enable: bool
        """
        _plugin = self.plugins.get(plugin_name, None)
        if _plugin:
            if enable:
                print(f"Enabling {plugin_name}")
            else:
                print(f"Disabling {plugin_name}")
            _plugin["enable"] = enable

    def walk_package(self, package):
        """Recursively walk the supplied package to retrieve all plugins"""
        imported_package = __import__(package, fromlist=["blah"])

        for _, pluginname, ispkg in pkgutil.iter_modules(
            imported_package.__path__, imported_package.__name__ + "."
        ):
            if not ispkg:
                plugin_module = __import__(pluginname, fromlist=["blah"])
                clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
                for (_, c) in clsmembers:
                    # Only add classes that are a sub class of Plugin,
                    # but NOT Plugin itself
                    if issubclass(c, Plugin) & (c is not Plugin):
                        print(
                            f"Found plugin class: {c.__module__}.{c.__name__}"
                        )
                        self.plugins[c.__name__] = {
                            "instance": c(parent=self),
                            "enable": True,
                        }

        # Now that we have looked at all the modules in the current package,
        # start looking recursively for additional modules in sub packages
        all_current_paths = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        for pkg_path in all_current_paths:
            if pkg_path not in self.seen_paths:
                self.seen_paths.append(pkg_path)

                # Get all sub directory of the current package path directory
                child_pkgs = [
                    p
                    for p in os.listdir(pkg_path)
                    if os.path.isdir(os.path.join(pkg_path, p))
                ]

                # For each sub directory,
                # apply the walk_package method recursively
                for child_pkg in child_pkgs:
                    self.walk_package(package + "." + child_pkg)

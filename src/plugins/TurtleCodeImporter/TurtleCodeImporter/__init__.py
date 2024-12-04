"""
This is where the implementation of the plugin code goes.
The TurtleCodeImporter-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase
from .parser import PyToTurtle

# Setup a logger
logger = logging.getLogger('TurtleCodeImporter')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class TurtleCodeImporter(PluginBase):
    def main(self):
        core = self.core
        root_node = self.root_node
        active_node = self.active_node
        META = self.META
        config = self.get_current_config()
        input = self.get_file(config['file'])
        parser = PyToTurtle()

        descriptor = parser.getJson(input)
        print("DESCRIPTOR")
        print(descriptor)

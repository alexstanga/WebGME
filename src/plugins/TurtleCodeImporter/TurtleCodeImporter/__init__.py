"""
This is where the implementation of the plugin code goes.
The TurtleCodeImporter-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase
from .parser import pyToTurtle

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

        result = pyToTurtle(input)

        tNode = core.create_child(active_node, META['Turtle'])
        core.set_attribute(tNode, 'name', 'new Turtle')

        # Create and link nodes for commands and loops
        previous_node = None
        for item in result['commands']:
            if item['type'] == 'command':
                node = self.create_command_node(core, tNode, META, item)
            elif item['type'] == 'loop':
                node = self.create_loop_node(core, tNode, META, item)

            # Sequence the current node to the previous node
            if previous_node:
                sequence_node = core.create_child(tNode, META['Sequence'])
                core.set_pointer(sequence_node, 'src', previous_node)
                core.set_pointer(sequence_node, 'dst', node)

            previous_node = node

        # Save the changes to the model
        self.util.save(root_node, self.commit_hash, 'master', 'Imported Sequence from Python file')

    def create_command_node(self, core, parent, META, command):
        """Create a CommandNode with action and arguments."""
        node = core.create_child(parent, META[command['action']])
        #core.set_attribute(node, 'action', command['action'])

        # Map action to attributes
        attribute_mapping = {
            "penup": [],
            "pendown": [],
            "clear": [],
            "color": ["color"],
            "width": ["thickness"],
            "forward": ["steps"],
            "goto": ["x", "y"],
            "left": ["degree"],
            "right": ["degree"]
        }

        # Assign attributes based on action
        expected_attributes = attribute_mapping.get(command['action'], [])
        arguments = command['arguments']

        for i, attr in enumerate(expected_attributes):
            if i < len(arguments):  # Ensure arguments match expected attributes
                core.set_attribute(node, attr, arguments[i])

        return node

    def create_loop_node(self, core, parent, META, loop):
        """Create a LoopNode and recursively add its body."""
        node = core.create_child(parent, META['Function'])
        core.set_attribute(node, 'loopCount', loop['iterations'])

        previous_node = None
        for body_item in loop['body']:
            if body_item['type'] == 'command':
                body_node = self.create_command_node(core, node, META, body_item)
            elif body_item['type'] == 'loop':
                body_node = self.create_loop_node(core, node, META, body_item)

            # Link the body nodes in sequence
            if previous_node:
                sequence_node = core.create_child(node, META['Sequence'])
                core.set_pointer(sequence_node, 'src', previous_node)
                core.set_pointer(sequence_node, 'dst', body_node)

            previous_node = body_node

        return node


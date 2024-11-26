"""
This is where the implementation of the plugin code goes.
The TurtleCodeGenerator-class is imported from both run_plugin.py and run_debug.py
"""
import os
import sys
import logging
import json
import random
import shutil
from webgme_bindings import PluginBase
from mako.template import Template

# Setup a logger
logger = logging.getLogger('TurtleCodeGenerator')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

turtle_code_template = Template(filename=os.path.join(os.path.dirname(__file__), 'tcg_template.txt'))


class TurtleCodeGenerator(PluginBase):
    def main(self):
        active_node = self.active_node
        core = self.core
        root_node = self.active_node
        graph = {}
        nodes = {}
        dag_output = []
        template_parameters = {'sequence_data': []}

        def get_relative_path(absolute_path):
            return absolute_path[len(root_node):]

        def add_node(parent_path, node_path, node):
            """
            Add nodes and their sequence relations to the graph.
            """
            meta_node = core.get_base_type(node)
            meta_type = core.get_attribute(meta_node, 'name')
            name = core.get_attribute(node, 'name')
            src = core.get_pointer_path(node, 'src')
            dst = core.get_pointer_path(node, 'dst')
            print("Meta")
            print(name)
            if meta_type == "Turtle":
                return
            elif name == "Sequence":
                if src not in graph:
                    graph[src] = []
                graph[src].append(dst)

                if dst not in graph:
                    graph[dst] = []
            else:
                if parent_path != root_node['nodePath']:
                    if parent_path not in graph:
                        graph[parent_path] = []
                    graph[parent_path].append(node_path)

                if node_path not in graph:
                    graph[node_path] = []

            logger.info('Adding {0}'.format(name))
            nodes[node_path] = name

        def print_graph():
            """Utility to print the graph for debugging."""
            logger.info('Printing Graph:')

            # Find the starting nodes (nodes with no incoming edges)
            all_nodes = set(graph.keys())
            all_targets = {dst for edges in graph.values() for dst in edges}
            starting_nodes = list(all_nodes - all_targets)
            dag_sequence = []

            visited = set()

            def traverse_and_print(node, visited, output):
                """
                Traverse the graph and print nodes in sequence.
                Ensure subcommands are processed in the correct order.
                """
                if node in visited:
                    return
                visited.add(node)

                node_type = nodes.get(node, "Unknown")
                depth = node.count('/')  # Depth of the current node based on slashes

                if node_type == "Function":
                    dag_sequence.append(f"Function {node}")
                else:
                    dag_sequence.append(node)

                # Separate subcommands and next commands
                subcommands = []
                next_commands = []

                for neighbor in graph.get(node, []):
                    neighbor_depth = neighbor.count('/')
                    if neighbor_depth > depth:
                        # Neighbor is deeper, treat as a subcommand
                        subcommands.append(f"{neighbor}")
                    elif neighbor_depth == depth:
                        # Neighbor is at the same level, treat as a next command
                        next_commands.append(neighbor)

                # Find the starting subcommand
                all_subcommands = set(subcommands)
                subcommand_targets = {dst for sub in subcommands for dst in graph.get(sub, [])}
                starting_subcommands = list(all_subcommands - subcommand_targets)
                # Traverse subcommands in the proper order
                subcommand_queue = starting_subcommands[:]
                while subcommand_queue:
                    current = subcommand_queue.pop(0)
                    traverse_and_print(current, visited, output)

                # Traverse next commands after subcommands
                for next_command in next_commands:
                    traverse_and_print(next_command, visited, output)


            # Traverse starting from all root nodes
            for start_node in starting_nodes:
                traverse_and_print(start_node, visited, dag_sequence)

            print("All Commands in sequence")

            # Add "subcommand" in front of all subcommands
            current_function_depth = None

            for i, item in enumerate(dag_sequence):
                if item.startswith("Function"):
                    # Add the Function to the processed sequence
                    dag_output.append(item)

                    # Calculate the depth of the Function
                    current_function_depth = item.count('/')
                else:
                    # Calculate the depth of the current item
                    item_depth = item.count('/')

                    if current_function_depth is not None and item_depth == current_function_depth + 1:
                        # The item is at the next level, so it's a subcommand
                        dag_output.append(f"subcommand {item}")
                    else:
                        # Reset current_function_depth if item is no longer a subcommand
                        current_function_depth = None
                        dag_output.append(item)

            # Print the final ordered output
            for line in dag_output:
                print(line)


        def get_attributes(node):
            """
            Parses attributes based on the command type.
            """
            command = core.get_attribute(node, 'name')
            if command.startswith("penup"):
                return {}
            elif command.startswith("pendown"):
                return {}
            elif command.startswith("clear"):
                return {}
            elif command.startswith("forward"):
                step_value = core.get_attribute(node, 'steps')
                return {"steps": step_value}
            elif command.startswith("right"):
                degree_value = core.get_attribute(node, 'color')
                return {"degree": degree_value}
            elif command.startswith("left"):
                degree_value = core.get_attribute(node, 'degree')
                return {"degree": degree_value}
            elif command.startswith("width"):
                thickness = core.get_attribute(node, 'thickness')
                return {"thickness": thickness}
            elif command.startswith("color"):
                color_value = core.get_attribute(node, 'color')
                return {"color": color_value}
            elif command.startswith("goto"):
                x_value = core.get_attribute(node, 'x')
                y_value = core.get_attribute(node, 'y')
                return {"x": x_value, "y": y_value}
            else:
                return {}

        def output_template():
            print("Output Template")
            current_function = None
            for entry in dag_output:
                if entry.startswith('Function'):
                    split = entry.split(' ')
                    node_path = split[1]
                    # Get node by looking up using the relative node path (i.e. /g for /4/g)
                    node = core.load_by_path(root_node, get_relative_path(node_path))
                    count = core.get_attribute(node, 'loopCount')
                    current_function = {
                        "type": "function",
                        "path": node_path,
                        "loopCount": count,
                        "subcommands": [],
                    }
                    template_parameters['sequence_data'].append(current_function)
                elif entry.startswith('subcommand'):
                    # Extract subcommand path
                    _, node_path = entry.split(" ")
                    # Get node by looking up using the relative node path (i.e. /g for /4/g)
                    node = core.load_by_path(root_node, get_relative_path(node_path))
                    command = core.get_attribute(node, 'name')
                    attributes = get_attributes(node)
                    if current_function is not None:
                        # Add subcommand to the current function
                        current_function["subcommands"].append(
                            {"type": "subcommand", "path": node_path, "command": command, "attributes": attributes})
                    else:
                        raise ValueError(f"Subcommand {node_path} found outside a function!")
                else:
                    # Regular Command
                    node = core.load_by_path(root_node, get_relative_path(entry))
                    command = core.get_attribute(node, 'name')
                    attributes = get_attributes(node)
                    template_parameters['sequence_data'].append(
                        {"type": "command", "path": entry, "command": command, "attributes": attributes})

            print(template_parameters)

            # render template
            turtle_code = turtle_code_template.render(sequence_data=template_parameters['sequence_data'])

            # put content into temporary directory
            directory_name = 'turtle_sim_'
            for i in range(10):
                directory_name += str(random.randint(0, 9))
            directory = os.path.join(os.path.dirname(__file__), directory_name)
            os.mkdir(directory)
            os.chdir(directory)
            # Write the rendered code to a file
            with open('turtle_sim.py', 'w') as f:
                f.write(turtle_code)

            print("Turtle code generated!")

        def at_node(node):
            """
      Traverse through each node and extract path, parent_path, and sequence then add to graph
      """

            meta_node = core.get_base_type(node)
            path = core.get_path(node)
            parent_node = core.get_parent(node)
            parent_path = core.get_path(parent_node)
            if meta_node:
                meta_type = core.get_attribute(meta_node, 'name')
            add_node(parent_path, path, node)

        self.util.traverse(active_node, at_node)
        logger.info(graph)
        print("Printing Graph")
        print_graph()
        output_template()

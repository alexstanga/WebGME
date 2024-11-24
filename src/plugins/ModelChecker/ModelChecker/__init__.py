"""
This is where the implementation of the plugin code goes.
The ModelChecker-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('ModelChecker')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class ModelChecker(PluginBase):
    def main(self):
        active_node = self.active_node
        core = self.core
        root_node = self.active_node
        graph = {}
        nodes = {}

        def add_node(parent_path, node_path, node):
            """
            Add nodes and their sequence relations to the graph.
            """
            name = core.get_attribute(node, 'name')
            src = core.get_pointer_path(node, 'src')
            dst = core.get_pointer_path(node, 'dst')
            logger.info('Adding {0}'.format(name))

            if name == "Turtle":
                return
            elif name == "Sequence":
                if src not in graph:
                    graph[src] = []
                graph[src].append(dst)

                if dst not in graph:
                    graph[dst] = []
            else:
                if parent_path not in graph:
                    graph[parent_path] = []
                graph[parent_path].append(node_path)

                if node_path not in graph:
                    graph[node_path] = []

            nodes[node_path] = name

        def detect_cycle():
            """
            Detect cycles in the graph using DFS and return the cycle if detected.

            :param graph: Adjacency list representing the graph.
            :return: A tuple (True, cycle_path) if a cycle is detected; otherwise, (False, None).
            """
            visited = set()
            recursion_stack = set()
            parent_map = {}

            def dfs(node):
                if node in recursion_stack:
                    # Cycle detected, reconstruct the cycle path
                    cycle_path = []
                    current = node
                    while current not in cycle_path:
                        cycle_path.append(current)
                        current = parent_map.get(current, None)
                    cycle_path.append(node)  # Complete the cycle
                    cycle_path.reverse()  # Optional: Start from the detected node
                    return True, cycle_path
                if node in visited:
                    return False, None

                visited.add(node)
                recursion_stack.add(node)

                for neighbor in graph.get(node, []):
                    parent_map[neighbor] = node
                    has_cycle, cycle_path = dfs(neighbor)
                    if has_cycle:
                        return True, cycle_path

                recursion_stack.remove(node)
                return False, None

            for node in graph:
                if node not in visited:
                    has_cycle, cycle_path = dfs(node)
                    if has_cycle:
                        return True, cycle_path
            return False, None

        def log_results():
            """
            Logs whether a cycle was detected and prints the cycle path if found.

            :param graph: Adjacency list representing the graph.
            """
            has_cycle, cycle_path = detect_cycle()
            loopDetectedString = ""
            if has_cycle:
                print("Cycle Detected in the program!")
                print("Cycle Path:", " -> ".join(cycle_path))
                loopDetectedString = "Cycle Detected in the program!\n"
                loopDetectedString += "Cycle Path: " + " -> ".join(cycle_path)
            else:
                print("No Cycles Detected.")
                loopDetectedString = "No Cycles Detected."
            print(loopDetectedString)
            print(active_node)
            core.set_attribute(active_node, 'loopDetected', str(loopDetectedString))
            print(core.get_attribute(active_node, 'loopDetected'))

        def print_graph():
            """Utility to print the graph for debugging."""
            logger.info('Printing Graph:')
            for node, edges in graph.items():
                node_type = nodes.get(node, "Unknown")
                logger.info(f"{node} ({node_type}) -> {', '.join(edges) if edges else 'No connections'}")

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
        print_graph()
        log_results()
        self.util.save(root_node, self.commit_hash, self.branch_name, "Model Checker saved into model.")

"""
This is where the implementation of the plugin code goes.
The TurtleSVGCreator-class is imported from both run_plugin.py and run_debug.py
Helpful starting code used from https://github.com/kecso/StateMachineJoint/blob/main/src/plugins/ExportToSVG/ExportToSVG/__init__.py
"""
import os
import shutil
import sys
import subprocess
import logging

from svg_turtle import SvgTurtle
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('TurtleSVGCreator')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class TurtleSVGCreator(PluginBase):
    def main(self):
        core = self.core
        active_node = self.active_node

        # Retrieve the turtle_sim file that was created in TurtleCodeGenerator
        # Hash was saved in the Turtle node attribute "artifact"
        modelfile = self.commit_hash.replace('#','_') + '_' + core.get_path(active_node).replace('/','_')
        artifact = core.get_attribute(active_node, 'artifact')
        retrieved_file = self.get_file(artifact)
        script_path = os.path.join(os.getcwd(), modelfile + '.py')
        with open(script_path, 'w') as f:
            f.write(retrieved_file)
        self.logger.info('File successfully retrieved and written to new_turtle_sim.py')

        # Ensure svg_turtle is installed
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'svg_turtle'], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error installing svg_turtle: {e}")
            return

        # Execute the Python Script
        try:
            subprocess.run(['/Users/alexanderstanga/anaconda3/envs/micproject/bin/python', script_path], check=True)
            self.logger.info('Python script executed successfully.')
        except subprocess.CalledProcessError as e:
            self.logger.error(f'Error executing script: {e}')
            return

        # Check for the generated SVG file
        svg_filename = './src/common/svg/turtle.svg'
        if os.path.exists(svg_filename):
            self.logger.info(f'SVG file generated: {svg_filename}')

            # Define the new file path
            output_directory = './src/common/svg'
            new_svg_path = os.path.join(output_directory, modelfile + '.svg')

            # Copy and rename the SVG file to the new location
            shutil.copy(svg_filename, new_svg_path)
            self.logger.info(f'SVG file copied and renamed to: {new_svg_path}')

            # Read the SVG content
            with open(new_svg_path, 'r') as svg_file:
                svg_content = svg_file.read()

            # Upload SVG back to WebGME blob storage
            svg_metadata_hash = self.add_file(modelfile + '.svg', svg_content)
            self.logger.info(f'SVG added to blob storage with metadata hash: {svg_metadata_hash}')

        else:
            self.logger.error(f'SVG file {svg_filename} not found.')

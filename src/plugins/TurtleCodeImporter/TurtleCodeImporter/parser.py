def pyToTurtle(script):
    lines = script.splitlines()
    stack = []  # Keeps track of nested loops
    result = {"commands": []}  # Final parsed result
    current_block = result["commands"]  # Current block being populated
    indentation_levels = [0]  # Track indentation levels

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("t.save_as"):
            continue  # Skip empty lines or save_as command

        indent_level = len(line) - len(stripped_line)

        # Handle dedentation
        while indent_level < indentation_levels[-1]:
            stack.pop()
            indentation_levels.pop()

        # Handle entering a new block
        if indent_level > indentation_levels[-1]:
            indentation_levels.append(indent_level)

        # Update current block after dedentation
        current_block = stack[-1] if stack else result["commands"]

        # Handle loop
        if stripped_line.startswith("for _ in range("):
            iterations = int(stripped_line.split("(")[1].split(")")[0])  # Extract loop count
            loop_block = {"type": "loop", "iterations": iterations, "body": []}
            current_block.append(loop_block)
            stack.append(loop_block["body"])  # Push the loop body onto the stack
            current_block = loop_block["body"]

        # Handle commands
        elif stripped_line.startswith("t."):
            action, args = parse_command(stripped_line)
            command = {"type": "command", "action": action, "arguments": args}
            current_block.append(command)

    return result


def parse_command(command_line):
    # Extract action and arguments
    action = command_line[2:command_line.index("(")].strip()
    args = command_line[command_line.index("(") + 1 : command_line.rindex(")")].strip()
    # Handle argument parsing
    if args:
        args = [parse_argument(arg.strip()) for arg in args.split(",")]
    else:
        args = []
    return action, args


def parse_argument(arg):
    # Handle different argument types (strings, numbers, None)
    if arg.startswith(("'", '"')) and arg.endswith(("'", '"')):
        return arg[1:-1]  # Strip quotes for strings
    elif arg.isdigit():
        return int(arg)  # Convert numbers
    elif arg.lower() == "none":
        return None
    return arg  # Return raw for unsupported types
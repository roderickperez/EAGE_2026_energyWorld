GRID_SIZE = 10
MAX_Z = 10


def generate_world():
    """Generate a 3D matrix indexed as [z][y][x]."""
    world_map = []
    for z in range(MAX_Z):
        layer = []
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                if z == MAX_Z - 1:
                    row.append(1)  # Top grass block
                else:
                    row.append(2)  # Deeper soil block
            layer.append(row)
        world_map.append(layer)
    return world_map


def calculate_visible_blocks(world_map):
    """Return visible blocks sorted for isometric back-to-front rendering."""
    visible_blocks = []

    for z in range(MAX_Z):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                block_id = world_map[z][y][x]
                if block_id == 0:
                    continue

                is_visible = False

                # Exposed top or front-facing sides are visible in isometric view.
                if z == MAX_Z - 1 or world_map[z + 1][y][x] == 0:
                    is_visible = True
                elif x == 0 or world_map[z][y][x - 1] == 0:
                    is_visible = True
                elif y == 0 or world_map[z][y - 1][x] == 0:
                    is_visible = True

                if is_visible:
                    visible_blocks.append((z, y, x, block_id))

    visible_blocks.sort(key=lambda b: (b[1] + b[2], b[0], b[1], b[2]))
    return visible_blocks

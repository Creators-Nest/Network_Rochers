from core.node import Node
from routing.xy_router import XYRouter

class MeshTopology:
    """
    Generates and holds the 2D Mesh topology and routing tables.
    A mesh topology is a 2D grid WITHOUT wraparound connections.
    Uses XY (dimension-ordered) routing algorithm.
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.nodes = {}  # Key: (x, y) address, Value: Node object
        
        self._generate_nodes()
        self._connect_nodes()
        
        # Initialize XY router for deterministic dimension-ordered routing
        self.router = XYRouter(self)
        self.router.build_routing_tables()
        self.router.apply_to_nodes()
        self.router.print_routing_statistics()
        
        # Store distance tables for easy access
        self.all_pairs_distances = self.router.distance_tables

    def _generate_nodes(self):
        """Creates nodes in a 2D grid."""
        for x in range(self.width):
            for y in range(self.height):
                address = (x, y)
                self.nodes[address] = Node(address)
        print(f"Generated {len(self.nodes)} total nodes in {self.width}x{self.height} mesh.")

    def _connect_nodes(self):
        """Connects nodes in mesh topology WITHOUT wraparound."""
        for x in range(self.width):
            for y in range(self.height):
                current_addr = (x, y)
                current_node = self.nodes[current_addr]
                
                # North neighbor (only if not at top edge)
                if y > 0:
                    north_addr = (x, y - 1)
                    if north_addr not in current_node.interfaces:
                        current_node.add_connection(self.nodes[north_addr])
                
                # South neighbor (only if not at bottom edge)
                if y < self.height - 1:
                    south_addr = (x, y + 1)
                    if south_addr not in current_node.interfaces:
                        current_node.add_connection(self.nodes[south_addr])
                
                # East neighbor (only if not at right edge)
                if x < self.width - 1:
                    east_addr = (x + 1, y)
                    if east_addr not in current_node.interfaces:
                        current_node.add_connection(self.nodes[east_addr])
                
                # West neighbor (only if not at left edge)
                if x > 0:
                    west_addr = (x - 1, y)
                    if west_addr not in current_node.interfaces:
                        current_node.add_connection(self.nodes[west_addr])
        
        print("Finished connecting nodes in mesh topology.")

    def get_all_node_addresses(self):
        return list(self.nodes.keys())
    
    def get_neighbors(self, address):
        """Get the neighbors of a node in mesh topology (no wraparound)."""
        x, y = address
        neighbors = []
        
        # North (only if not at top edge)
        if y > 0:
            neighbors.append((x, y - 1))
        
        # South (only if not at bottom edge)
        if y < self.height - 1:
            neighbors.append((x, y + 1))
        
        # East (only if not at right edge)
        if x < self.width - 1:
            neighbors.append((x + 1, y))
        
        # West (only if not at left edge)
        if x > 0:
            neighbors.append((x - 1, y))
        
        return neighbors
    
    def manhattan_distance(self, addr1, addr2):
        """Calculate Manhattan distance in mesh (simple, no wraparound)."""
        x1, y1 = addr1
        x2, y2 = addr2
        
        # Simple Manhattan distance (no wraparound consideration)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        return dx + dy

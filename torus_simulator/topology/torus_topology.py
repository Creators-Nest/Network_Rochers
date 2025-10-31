from core.node import Node
from routing.xy_router import XYRouter

class TorusTopology:
    """
    Generates and holds the 2D Torus topology and routing tables.
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.nodes = {}  # Key: (x, y) address, Value: Node object
        
        self._generate_nodes()
        self._connect_nodes()
        
        # Initialize XY router
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
        print(f"Generated {len(self.nodes)} total nodes in {self.width}x{self.height} torus.")

    def _connect_nodes(self):
        """Connects nodes in torus topology with wraparound."""
        for x in range(self.width):
            for y in range(self.height):
                current_addr = (x, y)
                current_node = self.nodes[current_addr]
                
                # North neighbor (with wraparound)
                north_y = (y - 1) % self.height
                north_addr = (x, north_y)
                if north_addr not in current_node.interfaces:
                    current_node.add_connection(self.nodes[north_addr])
                
                # South neighbor (with wraparound)
                south_y = (y + 1) % self.height
                south_addr = (x, south_y)
                if south_addr not in current_node.interfaces:
                    current_node.add_connection(self.nodes[south_addr])
                
                # East neighbor (with wraparound)
                east_x = (x + 1) % self.width
                east_addr = (east_x, y)
                if east_addr not in current_node.interfaces:
                    current_node.add_connection(self.nodes[east_addr])
                
                # West neighbor (with wraparound)
                west_x = (x - 1) % self.width
                west_addr = (west_x, y)
                if west_addr not in current_node.interfaces:
                    current_node.add_connection(self.nodes[west_addr])
        
        print("Finished connecting nodes in torus topology.")

    def get_all_node_addresses(self):
        return list(self.nodes.keys())
    
    def get_neighbors(self, address):
        """Get the 4 neighbors of a node in torus topology."""
        x, y = address
        neighbors = []
        
        # North, South, East, West with wraparound
        neighbors.append((x, (y - 1) % self.height))  # North
        neighbors.append((x, (y + 1) % self.height))  # South
        neighbors.append(((x + 1) % self.width, y))   # East
        neighbors.append(((x - 1) % self.width, y))   # West
        
        return neighbors
    
    def manhattan_distance(self, addr1, addr2):
        """Calculate Manhattan distance in torus (considering wraparound)."""
        x1, y1 = addr1
        x2, y2 = addr2
        
        # Calculate distance in X direction (considering wraparound)
        dx = min(abs(x2 - x1), self.width - abs(x2 - x1))
        
        # Calculate distance in Y direction (considering wraparound)
        dy = min(abs(y2 - y1), self.height - abs(y2 - y1))
        
        return dx + dy
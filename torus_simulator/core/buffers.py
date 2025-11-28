from collections import deque

class CircularBuffer:
    """Implements the circular send/receive buffers."""
    def __init__(self, size):
        self.buffer = deque(maxlen=size)
        self.capacity = size  # Store capacity for web UI
    
    def is_full(self):
        return len(self.buffer) == self.buffer.maxlen
    
    def is_empty(self):
        return len(self.buffer) == 0
    
    def size(self):
        """Return current buffer size"""
        return len(self.buffer)
    
    def enqueue(self, packet):
        if not self.is_full():
            self.buffer.append(packet)
            return True
        return False
    
    def dequeue(self):
        if not self.is_empty():
            return self.buffer.popleft()
        return None
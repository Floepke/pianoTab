class IDGenerator:
    def __init__(self, start_id: int = 1):
        self.current_id = start_id
    
    def new(self) -> int:
        '''Get the next available ID.'''
        current = self.current_id
        self.current_id += 1
        return current
    
    def reset(self, start_id: int = 1):
        '''Reset the generator to a new starting ID.'''
        self.current_id = start_id
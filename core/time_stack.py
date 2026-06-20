class TimeStack:
    def __init__(self, max_size=180):
        self.max_size = max_size
        self.history = []

    def push(self, state):
        self.history.append(state.copy())
        if len(self.history) > self.max_size:
            self.history.pop(0)

    def pop(self):
        if len(self.history) > 0:
            return self.history.pop()
        return None

    # ai
    def __len__(self):
        return len(self.history)

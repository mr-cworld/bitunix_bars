class BaseApiClient:
    def fetch_data(self):
        raise NotImplementedError("Subclasses should implement this method")
    
    def process_data(self, data):
        raise NotImplementedError("Subclasses should implement this method")
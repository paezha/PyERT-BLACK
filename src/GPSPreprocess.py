class GPSPreprocess:
    def __init__(self, data=None):
        data = data
        filteredData = self.filterData(data)
        smoothedData = self.smoothData(data)
        self.processedData = smoothedData

    def getData(self):
        return self.processedData

    def filterData(self, data):
        filteredData = None
        return filteredData

    def smoothData(self, data):
        smoothedData = None
        return smoothedData


class Extractor:
    def __init__(self, episodeData = None):
        episodeData = episodeData
        self.tripSegments = self.extractTripSegments(episodeData)
        self.activityLocations = self.extractActivityLocations(episodeData)

    def extractTripSegments(self, episodeData):
        tripSegments = None
        return tripSegments

    def getTripSegments(self):
        return self.tripSegments

    def extractActivityLocations(self, episodeData):
        activityLocations = None
        return activityLocations

    def getActivityLocations(self):
        return self.activityLocations
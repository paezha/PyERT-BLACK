class InvalidInputException(Exception):
    """Raised when there is an invalid input"""
    pass


class InvalidFilePathException(Exception):
    """Invalid file path or file path does not exist"""
    pass


class InvalidFileFormatException(Exception):
    """Invalid file format"""
    pass


class InvalidDataException(Exception):
    """Raised when the read data is missing information"""
    pass


class InvalidGPSDataException(Exception):
    """Raised when the read GPS data is missing information"""
    pass


class NetworkModeError(Exception):
    """Raised when the input mode is one of 'drive', 'walk' or 'all'"""
    pass


class OutofBoundException(Exception):
    """Raised when trip segment is out of the boundary of the extracted network"""
    pass


class NetworkDataExtractionError(Exception):
    """Raised when None is extracted from network dataset"""
    pass

class InvalidInputException(Exception):
    """Raised when there is an invalid input"""
    print("Invalid Input Exception:\n")
    pass


class InvalidFilePathException(Exception):
    """Invalid file path or file path does not exist"""
    print("Invalid/Incorrect File Path Exception:\n")
    pass


class InvalidFileFormatException(Exception):
    """Invalid file format"""
    print("Invalid File Format Exception:\n")
    pass


class InvalidDataException(Exception):
    """Raised when the read data is missing information"""
    print("Invalid Data Exception:\n")
    pass


class InvalidGPSDataException(Exception):
    """Raised when the read GPS data is missing information"""
    print("Invalid GPS Data Exception:\n")
    pass


class NetworkModeError(Exception):
    """Raised when the input mode is one of 'drive', 'walk' or 'all'"""
    print("Network Mode Error Exception:\n")
    pass
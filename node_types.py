from enum import Enum, auto

class NodeType(Enum):
    thematic_break = auto()  # --- *** ___
    insecure_char = auto()  # replacement char -> U+FFFD
    identifier = auto() # \options: {}
    comment = auto()  # //
    entity_char = auto()  # &nbsp
    atx_heading = auto()  # NODE("#")
    newline = auto()  # \n
    string = auto()  # "this is a string" || this is a string
    tab = auto()  # \t perhaps this is a entity_char

    # we do not current support html this could be "unsafe"
    # block = auto()  # <li> <ul> => NODE("-")

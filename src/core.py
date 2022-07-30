#!/usr/bin/env python3

#   \title      core.py
#
#   \author     Nathan Reed <nreed@linux.com>
#
#   \desc       This is a simple markdown page parser for a blog site
#
#   \license    MIT

__author__ = "Nathan Reed <nreed@linux.com>"

from dataclasses import dataclass, field
from enum import Enum
import sys


class DocNodeType(Enum):
    """
        Types for parser primatives 

        list_item_comment   just a list_item nested list 
        code_block          anything wrapped in ```<lang>
        identifier          
    """
    list_item_comment = auto()
    code_block = auto()
    identifier = auto()
    list_item = auto()
    paragraph = auto()  
    comment = auto() 
    heading = auto()  
    newline = auto()  
    _list = auto()
    text = auto()
    tab = auto()  
    root = auto()


class PageLexerError(object):
    """
        A parser error type

    args
        message     Explaining what error the
        position    position of the cursor
        line        line where the error occurred

    """

    def __init__(self, message: str, position: int, line: int):
        self.position = position
        self.message = message
        self.line = line

    def __str__(self):
        return f"PageLexerError(l{self.line}:c{self.position}): " + self.message


@dataclass(init=True)
class DocToken:
    """
    Defining what a parser token looks like

    args
        type        (* enum)DocNodeType
        Value       str representing the lexme
    """

    type: DocNodeType
    value: str

    def as_dict(self):
        return {"type": str(self.type), "value": self.value}


@dataclass(init=True)
class DocNode(object):
    # I dont think that i fucked up the order on this
    type: DocNodeType
    successors: list = field(default=None)
    depth: int = field(default=1)
    ordered: bool = True
    text: str = ""

    def __post_init__(self):
        assert DocNodeType, "DocnodeType not defined"

        # implement defualts
        if not bool(self.successors):
            self.successors = []

        if not bool(self.ordered):
            self.ordered = True

        if not bool(self.text):
            self.text = ""

    def __str__(self):
        return str(self.type)

    def as_dict(self):
        return {
            "type": str(self.type),
            "successors": self.successors,
            "depth": str(self.depth),
            "text": self.text,
            "depth": self.depth,
            "ordered": self.ordered,
        }


class PageFormatTypes(Enum):
    """
    Types for the way that we parse page section colors
    + how we define page format

        .. Page Format: as defined below

    div* class("pure-grid maincolumn")
        div* class("lwn-u-1 pure-u-md-19-24")
            PageHeadline
                Starting feature text has no tag or class

            div* class("ArticleText")

                Paragraphs
                    paragraph tag no class

                Quotes
                    blockquote* class("bq")

    FUTURE: FeatureByLIne
        author
        date
        TODO: description
    """

    # Required
    GridMainColumn = object()
    Start = object()
    PageHeadline = object()  # Div->H2
    ArticleTextDiv = object()  # Div->text
    # Optional


class PageParser(object):
    def __init__(self, doc_nodes):
        self.doc_nodes: list = doc_nodes
        self.page: list = []
        self.tree = DocNode(DocNodeType.root)

    def add_html_block(self, tag):
        self.page.append(tag)

    def create_html_block(self, start, body, end):
        return start + body + end

    def render(self):
        """
        The way we render the page

            .. Page Format: as defined below

        div* class("pure-grid maincolumn")
            div* class("lwn-u-1 pure-u-md-19-24")
                PageHeadline
                    Starting feature text has no tag or class

                div* class("ArticleText")

                    Paragraphs
                        paragraph tag no class

                    Quotes
                        blockquote* class("bq")

        FUTURE: FeatureByLIne
            author
            date
            TODO: description
            Render the page

        attrs
            none    self

        returns
            none

        """

        for idx, token in enumerate(self.doc_nodes):
            # if the node is a list item
            # and the last node is not a list
            # then add a list with the list item as its child
            if token.type is DocNodeType.list_item:
                if self.tree.successors[-1].type is not DocNodeType._list:
                    index = token.value.index(".")
                    d = int(token.value[0])
                    print(d)
                    token.value = token.value[index + 2 :]
                    node = DocNode(
                        DocNodeType._list,
                        [
                            DocNode(
                                DocNodeType.list_item,
                                [DocNode(DocNodeType.text, text=token.value)],
                            )
                        ],
                    )
                    node.depth = d
                    self.tree.successors.append(node)
                    continue

                elif token.type is DocNodeType.list_item:
                    index = token.value.index(".")
                    d = int(token.value[0])
                    token.value = token.value[index + 2 :]

                    node = DocNode(
                        DocNodeType.list_item,
                        [DocNode(type=DocNodeType.text, text=token.value)],
                    )
                    node.depth = d

                    assert (
                        self.tree.successors[-1].type == DocNodeType._list
                    ), f"did not find list instead found {self.tree.successors[-1].type}"

                    self.tree.successors[-1].successors.append(node)

                    continue

                else:
                    # unreachable
                    raise

            elif token.type is DocNodeType.heading:
                depth = token.value.count("#")

                # here like we mentioned later in the file we can strip out the "#"
                # we dont strip it when we translate the header into HTML because
                # that would be a waste of cycles, you would have to do it in multiple places
                node = DocNode(
                    DocNodeType.heading,
                    [
                        DocNode(
                            DocNodeType.text, text=token.value.strip("#"), depth=depth
                        )
                    ],
                )
                self.tree.successors.append(node)
                continue

            elif token.type is DocNodeType.paragraph:
                self.tree.successors.append(
                    DocNode(
                        DocNodeType.paragraph,
                        [DocNode(DocNodeType.text, text=token.value)],
                    )
                )
            elif token.type is DocNodeType.code_block:
                self.tree.successors.append(
                    DocNode(
                        DocNodeType.code_block,
                        [DocNode(DocNodeType.text, text=token.value)],
                    )
                )

            elif token.type is DocNodeType.text:
                self.tree.successors.append(
                    DocNode(
                        DocNodeType.text, [DocNode(DocNodeType.text, text=token.value)]
                    )
                )
            else:
                pass

        headline = False
        for idx, child in enumerate(self.tree.successors):
            print("NEXT_TOP_NODE\t", hex(id(child)), "  ", child.type)

            # Headings
            if child.type is DocNodeType.heading:
                # ensure depth
                assert child.depth, "No Depth found for header"
                # ensure text node
                assert bool(child.successors), "header had no text successors"
                # DocNode
                assert isinstance(
                    child.successors[0], DocNode
                ), f"Could not find successors Text for Header of depth {child.depth}"

                # TODO: fix header depth
                if headline is True and child.depth == 1:
                    # bad fix for subheaders
                    child.depth += 1

                    text = child.successors[0].text

                    line = self.create_html_block(
                        f"<h{child.depth}>",
                        text,
                        f"</h{child.depth}>",
                    )

                    self.add_html_block(line)

                    continue

                if child.depth == 1:
                    PageHeading = "<div class='PageHeadline'>"
                    PageHeadingEnd = "</div>"

                    # uh oh TODO: fix me
                    # closing tag at end of scope
                    ArticleText = "<div style='margin-left: 20px;' class='ArticleText'>"

                    heading = f"<h{child.depth}>"
                    end = f"</h{child.depth}>"

                    # set headline state
                    headline = True

                    text = child.successors[0].text
                    line = (
                        PageHeading
                        + heading
                        + text
                        + end
                        + PageHeadingEnd
                        + ArticleText
                    )

                    self.add_html_block(line)
                    continue

                line = self.create_html_block(
                    f"<h{child.depth}>",
                    child.successors[0].text,
                    f"</h{child.depth}>",
                )

                self.add_html_block(line)
                continue

            elif child.type is DocNodeType._list:
                self.add_html_block("<ol>")

                for list_item in child.successors:

                    # ensure there is a test node avaliable
                    assert bool(list_item.successors), "no list text successor found"

                    if list_item.type is DocNodeType.list_item:
                        assert (
                            list_item.successors[0].type == DocNodeType.text
                        ), f"successors type for list was not text, found {list_item.successors[0].type}"

                        body = list_item.successors[0].text

                        print("depth", list_item.depth)
                        line = self.create_html_block(
                            f"<li value='{list_item.depth}'>", body, "</li>"
                        )

                        self.add_html_block(line)

                self.add_html_block("</ol>")

                continue

            elif child.type is DocNodeType.paragraph:
                block = child.successors[0].text

                line = self.create_html_block("<p>", block, "</p>")

                self.add_html_block(line)
                continue

            elif child.type is DocNodeType.code_block:
                # check string DocNode access
                assert bool(child.successors[0].text)

                # access string once and only once
                block = child.successors[0].text

                # find the first new line to rid ```<lang>
                index = block.find("\n")

                # grab the rest of the block
                string = block[index:]

                # abstract into function
                line = self.create_html_block(
                    "<pre>",
                    string,
                    "</pre>",
                )

                self.add_html_block(line)

                continue

            else:
                raise ValueError(f"unknown type {child.type}")

        start_page = (
            "<head>"
            + "\n<link rel='stylesheet' href='../styles/skeleton.css'>"
            + "\n<link rel='stylesheet' href='../styles/pure.css'>"
            + "\n<link rel='stylesheet' href='../styles/grid.css'>"
            + "\n</head>"
            + "\n<body color='#fff' link='Blue', vlink='Green' alink='Green'>"
            + "\n<div class='pure-grid maincolumn'>"
            + "\n<div class='lwn-u-1 pure-u-md-19-24'>"
        )
        if headline is True:
            end_page = "</div>" + "\n</div>" + "\n</div>" + "\n</div>" + "\n</body>"
        else:
            "</div>" + "\n</div>" + "\n</body>"

        return start_page + "\n".join(self.page) + end_page


class PageLexer(object):
    """
    our global parser object

    lookahead_ptr   a pointer to look ahead of the cursor temporarily
    _has_errors     defining what the parser ran into during scans
    file_buff       text from the source file
    column          what column are we on in a line
    doc_nodes          list of tokens we have collected in scans
    cursor          where we are in the source file
    line            what line are we on, primarily used with column
    fd              a hidden file descriptor for our source file
    """

    def __init__(self, file_buff: TextIOWrapper):
        self.file_buff = file_buff.read()
        self.lookahead_ptr = 0
        self._has_errors = []
        self.fd = file_buff
        self.doc_nodes = []
        self.cursor = 0
        self.column = 0
        self.line = 0

    def __str__(self):
        """creating the final page"""

        # create the page

    def styles(self, path: str) -> None:
        """
            parse the styles option
            this is also to validate whether the stylesheet is valid

        args
            path    a path to the stylesheet

        returns
            a style sheet
        """
        ...

    def create_error(self, msg: str) -> None:
        """
            Create a new PageLexer error

        attrs
            msg message to say what the error is, and if we can continue

        returns
            PageLexerError(class)
        """
        error = None

    def is_char(self, char: str) -> bool:
        """
        attrs
            character to process

        Returns
            whether something is a alpha-character or not
        """
        return (
            True
            if char >= "a" and char <= "z" or char >= "A" and char <= "Z"
            else False
        )

    def grab_string(self) -> str:
        """
            collecting a full string either to a new line or to EOF

        attrs
            in class

        Returns
            str     full string to collect
        """
        # store the current char that is a char
        result: list = []
        result.append(self.file_buff[self.cursor])

        self.lookahead_ptr = 1
        while True:

            # if grab_string happens to touch the edge of the file buffer
            if self.lookahead_ptr + self.cursor >= len(self.file_buff):

                # grab the last char
                result.append(self.file_buff[-1])
                self.line += 1
                self.column = 0

                # give the resulting string back
                self.cursor = (self.lookahead_ptr + self.cursor) - 1
                return "".join(result)

            # if we reached the end of the line then we result the result
            if self.file_buff[self.cursor + self.lookahead_ptr] == "\n":
                self.line += 1
                self.column = 0

                # reset the position cursor
                self.cursor = self.lookahead_ptr + self.cursor

                # we should have the last char at this point
                return "".join(result)

            # get the next char
            result.append(self.file_buff[self.cursor + self.lookahead_ptr])

            # the next char
            self.lookahead_ptr += 1

        # unreachable
        raise

    def add_token(
        self,
        type: DocNodeType,
        value=None,
    ) -> None:
        """
        add a token to the token to the token buffer

        modes:
            insert  slot in a token at an index
            append  stick it at the end of the buffer

        attrs:
            type_       DocNode Type
            text       the string we passed to the token
            size        size of an token-specific identifier
            insert      mode insert
            position    ^ position to insert at

        returns
            Nothing
        """

        self.doc_nodes.append(DocToken(type, value))

    def peek(self) -> str:
        """
            peek at the next character in the file buffer is there is room

        args
            none

        returns
            the next char in the file buffer
        """
        # TODO: add boundary check
        return self.file_buff[self.cursor + 1]

    def peek_width(self, amount=2) -> str:
        """
            peek at the next character in the file buffer is there is room

        args
            amount  to peek with width

        returns
            the next char in the file buffer
        """
        if amount == 0:
            raise Exception("You can't peek nothing")

        if amount + self.cursor >= len(self.file_buff):
            IndexError("Cursor too close to end of file: amount + PageLexer.cursor")

        # TODO: add boundary check
        return self.file_buff[self.cursor : self.cursor + amount]

    def read_block(self) -> str:
        """
            collecting a full string either to a new line or to EOF

        attrs
            in class

        Returns
            str     full string to collect
        """
        # store the current char that is a char
        result: list = []
        result.append(self.file_buff[self.cursor])

        self.lookahead_ptr = 1

        while True:

            tmp_cursor = self.cursor + self.lookahead_ptr

            # if grab_string happens to touch the edge of the file buffer
            if tmp_cursor >= len(self.file_buff):

                # grab the last char
                result.append(self.file_buff[-1])

                # give the resulting string back
                self.cursor = (tmp_cursor) - 1
                return "".join(result)

            try:
                # if we reached the end of the line then we result the result
                if self.file_buff[tmp_cursor] == "`":

                    # reset the position cursor
                    self.cursor = tmp_cursor

                    if self.peek_width() == "``":
                        self.cursor += 2
                        self.column += 2

                        # we should have the last char at this point
                        return "".join(result)

                    else:
                        continue

                # get the next char
                result.append(self.file_buff[tmp_cursor])

                # the next char
                self.lookahead_ptr += 1

            except Exception:
                raise Exception("did not find edege of block")

        # return the level of header
        self.cursor = tmp_cursor

    def lex_page(self) -> list:
        while True:

            # detecting the bounds of the line
            # if our cursor exceeds the bounds of the file_buff we can exit the parser
            if self.cursor >= len(self.file_buff):
                break

            char = self.file_buff[self.cursor]

            # I think it would be nice to honor newlines
            # in theory you could get around this by using comments
            if char == "\n" or char == "\r":
                self.line += 1
                self.column = 0
                # self.add_token(DocNodeType["newline"], "\n")

            # grabbing full headings
            elif char == "#":

                # gives us the entire header back, including the  #
                # later we use this to strip out the #
                heading = self.grab_string()
                assert heading, "grab_string() l659 returned nothing"
                assert heading.__contains__("#"), "heading did not contain #"

                self.add_token(DocNodeType["heading"], heading)

            elif char == "\\":

                if self.peek() == "o":
                    # self.add_option()
                    ...

                # Githug embeds
                elif self.peek() == "c":
                    # self.add_option()
                    ...

                else:
                    raise Exception(f"Unknown Option: {self.peek()}")

            elif char == "`":
                if self.peek_width(2) == "``":
                    # move two more characters forward
                    self.cursor += 3
                    self.column += 3
                    block = self.read_block().replace("<", "&lt;").replace(">", "&gt;")
                    self.add_token(DocNodeType["code_block"], block)

            elif char.isdigit():
                # ordered list
                if self.peek() == ".":
                    item = self.grab_string()
                    assert item, "item returned nothing l690"

                    # here we reuse the size of the node to specify the list item value
                    self.add_token(DocNodeType["list_item"], item)

            elif char == "-":
                if self.peek_width(2) == "//":
                    # grab that comment
                    string = self.grab_string()[1:]
                    assert string, "string l699 returned nothing"

                    # add a list-comment token
                    self.add_token(DocNodeType["list_item_comment"], string)

            # the posibility of a comment
            elif char == "/":
                # make sure that the next char in the line is a comment
                # for actual text we can ignore this later
                if self.peek() == "/":

                    # we have to advance the cursor here because otherwise we would
                    # have an infinite loop
                    self.cursor += 1
                    self.column += 1
                    continue

                # grab the full string any way, so that we don't consider '/' a comment
                string = self.grab_string()
                assert string, "string returned nothing"
                self.add_token(DocNodeType["paragraph"], string)

            # here we can just grab a full string
            elif self.is_char(char) or char == "\t":

                string = self.grab_string()
                assert string, ""

                self.add_token(DocNodeType["paragraph"], string)

            # go to the next char at the top of the scope
            self.cursor += 1
            self.column += 1

        return self.doc_nodes


if __name__ == "__main__":
    with open(sys.argv[1], "r") as fd:
        page = PageLexer(fd)

        with open(sys.argv[2], "w+") as fd:
            print("Compiling Page")
            tokens = page.lex_page()
            parser = PageParser(tokens)
            final = parser.render()
            if "--debug" in sys.argv:
                for node in page.doc_nodes:
                    print(node)
            print("Nodes Processed:", len(page.doc_nodes))
            print("Compliation Complete!\n")
            fd.write(final)  # pyright: ignore

    sys.exit(0)

#!/usr/bin/env python3

#   \title      core.py
#
#   \author     Nathan Reed <nreed@linux.com>
#
#   \dsec       This is a simple markdown page parser for a blog site
#
#   \license    MIT


from dataclasses import dataclass, field
from enum import Enum
import sys


class DocNodeType(Enum):
    list_item_comment = object()
    code_block = object()
    identifier = object()
    paragraph = object()
    list_item = object()
    comment = object()
    heading = object()
    newline = object()
    anchor = object()
    _list = object()
    text = object()
    tab = object()
    root = object()


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

    def as_dict(self) -> dict:
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

    def as_dict(self) -> dict:
        return {
            "type": str(self.type),
            "successors": self.successors,
            "depth": str(self.depth),
            "text": self.text,
            "depth": self.depth,
            "ordered": self.ordered,
        }


class PageParser(object):
    def __init__(self, doc_nodes):
        self.doc_nodes: list = doc_nodes
        self.page: list = []
        self.tree = DocNode(DocNodeType.root)

        # the LIFO queue "defer_queue" is made to close outer-scope tag at the end of render
        # the way this works is, we have a queue (start)div->div->body   |  (end)div,div,body
        # queue div,div,body
        #       and since we want to use pop() we will have to revere the list
        # queue(reversed) body,div,div
        #       when we pop it will be div,div,body
        self.defer_queue = []

    def prepare_lifo(self) -> None:
        self.defer_queue.reverse()

    def get_next_defer(self) -> object:
        item = self.defer_queue.pop()
        return item

    def add_defer_item(self, item: str) -> None:
        assert isinstance(item, str), "defer item was not str"
        self.defer_queue.append(item)

    def add_html_block(self, tag) -> None:
        self.page.append(tag)

    def create_html_block(self, start, body, end) -> None:
        return start + body + end

    def define_list_item(self, text) -> None:
        index_after_depth = text.index(".")
        depth = int(text[0])

        assert depth
        assert index_after_depth

        list_text = text[index_after_depth + 2 :]

        return (depth, list_text)

    def init_page(self):
        start_page = (
            "<head>"
            + "\n <meta name='viewport' content='width=device-width, initial-scale=1'>"
            + "\n<link rel='stylesheet' href='../styles/skeleton.css'>"
            + "\n</head>"
            + "\n<body class='bod'>"
        )

        self.add_html_block(start_page)
        self.add_html_block("<body>")
        self.add_html_block("<div class='page-container'>")

        # make sure we close this at the end of scope
        self.add_defer_item("</body>")
        self.add_defer_item("</div>")

    def create_ir(self) -> None:

        for idx, token in enumerate(self.doc_nodes):
            if token.type is DocNodeType.list_item:

                # if the we don't already have a list in the tree
                # then go ahead and create one
                if self.tree.successors[-1].type is not DocNodeType._list:

                    # grab the depth and the text for the list item
                    depth, text = self.define_list_item(token.value)

                    node = DocNode(
                        DocNodeType._list,
                        [
                            DocNode(
                                DocNodeType.list_item,
                                [DocNode(DocNodeType.text, text=text)],
                            )
                        ],
                    )

                    node.depth = depth
                    self.tree.successors.append(node)

                    continue

                # if we dont need to create the head of the list
                # then we can append to the _list behind it
                elif token.type is DocNodeType.list_item:

                    # grab the depth and the text for the list item
                    depth, text = self.define_list_item(token.value)

                    node = DocNode(
                        DocNodeType.list_item,
                        [DocNode(type=DocNodeType.text, text=text)],
                    )

                    node.depth = depth

                    # append to _list and freak out if there is not one
                    assert (
                        self.tree.successors[-1].type is DocNodeType._list
                    ), f"expected _list found {self.tree.successors[-1].type}"

                    self.tree.successors[-1].successors.append(node)

                    continue

                else:
                    # unreachable
                    raise

            elif token.type is DocNodeType.heading:
                depth = token.value.count("#")
                print("DEPTH", depth, token.value)

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

    def render(self) -> str:
        """
        TODO: redo this
        """

        self.create_ir()
        self.init_page()

        headline = False
        for idx, child in enumerate(self.tree.successors):
            if "-v" in sys.argv:
                print("COMPILING    ", hex(id(child)), "  ", child.type)

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

                text = child.successors[0]

                if text.depth == 1:

                    #TODO: fix text.text naming wat
                    line = self.create_html_block(
                        f"<h{text.depth}>",
                        text.text,
                        f"</h{text.depth}>",
                    )

                    self.add_html_block(line)

                    continue

                if text.depth == 1:
                    PageHeading = "<div class='PageHeadline'>"
                    PageHeadingEnd = "</div>"

                    # closing tag at end of scope
                    self.add_html_block("<div class='ArticleText'>")
                    self.add_defer_item("</div>")

                    heading = f"<h{text.depth}>"
                    end = f"</h{text.depth}>"

                    line = PageHeading + heading + text.text + end + PageHeadingEnd

                    self.add_html_block(line)
                    continue

                line = self.create_html_block(
                    f"<h{text.depth}>",
                    child.successors[0].text,
                    f"</h{text.depth}>",
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
                            list_item.successors[0].type is DocNodeType.text
                        ), f"successors type for list was not text, found {list_item.successors[0].type}"

                        body = list_item.successors[0].text

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

                # create code_block
                line = self.create_html_block(
                    "<pre>",
                    string,
                    "</pre>",
                )

                # wrap code block in div
                line = self.create_html_block(
                    "<div class='code_block'>", line, "</div>"
                )

                self.add_html_block(line)

                continue

            else:
                raise ValueError(f"unknown type {child.type}")

        # reverse lifo
        self.prepare_lifo()

        # finish off page
        for i in range(0, len(self.defer_queue)):
            item = self.get_next_defer()
            self.add_html_block(item)

        return "".join(self.page)


class PageLexer(object):
    """
    our global lexer object
    lookahead_ptr   a pointer to look ahead of the cursor temporarily
    _has_errors     defining what the parser ran into during scans
    file_buff       text from the source file
    column          what column are we on in a line
    doc_nodes          list of tokens we have collected in scans
    cursor          where we are in the source file
    line            what line are we on, primarily used with column
    fd              a hidden file descriptor for our source file
    """

    def __init__(self, file_buff):
        self.file_buff = file_buff.read()
        self.lookahead_ptr = 0
        self._has_errors = []
        self.fd = file_buff
        self.doc_nodes = []
        self.cursor = 0
        self.column = 0
        self.line = 0

    def parse_between_chars(self, string: str, start: str, end: str) -> str:
        """
            I only need to support 1 chacter indexing
        """
        assert isinstance(start), "start is not a string"
        assert isinstance(end), "end is not a string"
        assert isinstance(string), "string is not a string"

        try:
            start_index = string.index(start)
            end_index = string.index(end)

            return string[start_index+1:end_index+1]

        except:
            raise ValueError(f"Char Not Found {start},{end}")

    def check_lookahead_for_newline(self) -> bool:
        return (
            True if self.file_buff[self.cursor + self.lookahead_ptr] == "\n" else False
        )

    def check_lookahead_bounds(self) -> bool:
        return (
            True if (self.lookahead_ptr + self.cursor >= len(self.file_buff)) else False
        )

    def advance_column_counter(self, amount=1) -> None:
        self.column += amount

    def check_bound_with_int(self, control: int) -> bool:
        return True if control >= len(self.file_buff) else False


    def advance_line_counter(self, amount=1) -> None:
        self.line += amount


    def advance_cursor(self, amount=1) -> None:
        assert amount != 0, "cannot move cursor 0"
        assert isinstance(amount, int), f"amount not int, found {type(amount)}"

        self.cursor += amount

    def reset_column_counter(self) -> None:
        self.column = 0

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
            if self.check_lookahead_bounds():

                # grab the last char
                result.append(self.file_buff[-1])

                # advance cursor and reset column counter
                self.advance_line_counter()
                self.column = 0

                # give the resulting string back
                self.cursor = (self.lookahead_ptr + self.cursor) - 1

                return "".join(result)

            # if we reached the end of the line then we result the result
            if self.check_lookahead_for_newline():
                self.advance_line_counter()
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
        return self.file_buff[self.cursor + 1]

    def peek_width(self, amount=2) -> str:
        """
            peek at the next character in the file buffer is there is room
        args
            amount  to peek with width
        returns
            the next char in the file buffer
        """
        assert amount != 0, "you cannot peek ahead 0"

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
        block: list = []
        block.append(self.file_buff[self.cursor])

        self.lookahead_ptr = 1

        while True:

            lookahead_cursor = self.cursor + self.lookahead_ptr

            # if grab_string happens to touch the edge of the file buffer
            if self.check_bound_with_int(lookahead_cursor):

                # grab the last char
                block.append(self.file_buff[-1])

                self.cursor = (lookahead_cursor) - 1

                # give the resulting block back
                return "".join(block)

            try:
                # if we reached the end of the line then we return the result
                if self.file_buff[lookahead_cursor] == "`":

                    # reset the position cursor
                    self.cursor = lookahead_cursor

                    if self.peek_width() == "``":
                        self.advance_cursor(2)
                        self.advance_column_counter(2)

                        # we should have the last char at this point
                        return "".join(block)

                    else:
                        continue

                # get the next char
                block.append(self.file_buff[lookahead_cursor])

                # the next char
                self.lookahead_ptr += 1

            except:
                raise

        # return the level of header
        self.cursor = lookahead_cursor

    def lex_page(self) -> list:
        while True:

            # detecting the bounds of the line
            # if our cursor exceeds the bounds of the file_buff we can exit the parser
            if self.check_bound_with_int(self.cursor):
                break

            char = self.file_buff[self.cursor]

            # I think it would be nice to honor newlines
            # in theory you could get around this by using comments
            if char == "\n" or char == "\r":
                self.advance_line_counter()
                self.reset_column_counter()

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
                    self.advance_cursor(3)
                    self.advance_column_counter(3)
                    block = self.read_block().replace("<", "&lt;").replace(">", "&gt;")
                    self.add_token(DocNodeType["code_block"], block)

            elif char.isdigit():
                # ordered list
                if self.peek() == ".":
                    item = self.grab_string()
                    assert item, "item returned nothing l690"

                    # here we reuse the size of the node to specify the list item value
                    self.add_token(DocNodeType["list_item"], item)

            #elif char == "[":
                # check for ()
                
                # check for next ]

            elif char == "-":
                if self.peek_width(2) == "//":
                    # grab that comment
                    option = self.grab_string()[1:]
                    assert option, "string returned nothing"

                    # add a list-comment token
                    self.add_token(DocNodeType["list_item_comment"], option)

            # grab comment or paragraph
            elif char == "/":
                # make sure that the next char in the line is a comment
                if self.peek() == "/":

                    # we have to advance the cursor here because otherwise we would
                    # have an infinite loop
                    self.advance_cursor()
                    self.advance_column_counter()

                    # throw away string to seek to a good point in the file
                    _ = self.grab_string()

                    continue

                # grab the full string any way, so that we don't consider '/' a comment
                paragraph = self.grab_string()
                assert string, "string returned nothing"
                self.add_token(DocNodeType["paragraph"], paragraph)

            # here we can just grab a full string
            elif self.is_char(char) or char == "\t":

                paragraph = self.grab_string()
                assert paragraph

                self.add_token(DocNodeType["paragraph"], paragraph)

            # go to the next char at the top of the scope
            self.advance_cursor()
            self.advance_column_counter()

        return self.doc_nodes


if __name__ == "__main__":
    # argv[1] because the first arg is the program name I imagine to prevent underflow
    with open(sys.argv[1], "r") as fd:
        page = PageLexer(fd)

        with open(sys.argv[2], "w+") as fd:
            tokens = page.lex_page()
            parser = PageParser(tokens)
            final = parser.render()
            if "--debug" in sys.argv:
                for node in page.doc_nodes:
                    print(node)
            print("Nodes Processed:", len(page.doc_nodes))
            fd.write(final)  # pyright: ignore

    sys.exit(0)

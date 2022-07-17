#!/usr/bin/env python3
import pdb

#   \title      core.py
#
#   \author     Nathan Reed <nreed@linux.com>
#
#   \dsec       This is a simple markdown page parser for a blog site
#
#   \license    MIT

# NOTE: ITEMS
# i'm trying not to just mindless code here, I want this to be somewhat stable
# so here are some markers that I want for the page renderer

# all text related DocNode's should have the strings attached to them
# this is so we can more easily craft the page in the end
# we are not really trying to create a commonmark implementation
# this is just a page renderer based on markdown iteself
# I think that explains it

# comments should be respected as long as they are not apart of a heading
# or really any other DocNode that has text attached to it
# for example we should parse this a comment
# \\ this is a comment t
# and not this
# ### this looks like a header \\ but has a "comment" in it

# I think that there should be some text that represents some form of a "struct"
# in the page to defined things like styles perhaps the following
# options: { style: "<style here>", page_name: "page name here", "favicon"} etc

# I think that it will do nicely like that to have some keyword to tell the renderer
# what to do for global styles and titles, heading data really

# I think we can use like a "link: {/path/to/other/page}" thing to link pages together

# I also think that we should have a way of determining if something is actually a keyword
# like "\options: {}" having a escape char before the keyword so its not parsed wrong

# TODO: Styles plan
# we have a defined set of css classes
# we have a init for the static site generator to make sure all the paths are there
# based on the classes we can define colors
#   the sites should for the most part be in the same format


from enum import Enum, auto
from io import TextIOWrapper
import json
import json
import sys


class DocNodeType(Enum):
    list_item_comment = auto()
    root = auto()

    list_item = auto()
    code_block = auto()
    identifier = auto()  # \options: {}
    comment = auto()  # //
    heading = auto()  # NODE("#")
    newline = auto()  # \n
    paragraph = auto()  # "this is a string" || this is a string
    tab = auto()  # \t perhaps this is a entity_char
    text = auto()
    _list = auto()
    # we do not current support html this could be "unsafe"
    # block = auto()  # <li> <ul> => NODE("-")


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


class DocToken:
    """
    Defining what a parser token looks like

    args
        type        (* enum)DocNodeType
        text        String representing the value of the token
        depth       most how deep an object is ## in depth is 2
        successors  children
        ordered     for lists if they are ordered or not
        text        string value for the node
    """

    def __init__(
        self,
        type: DocNodeType,
        value: str,
    ):
        self.type = type
        self.value = value

    # def __str__(self):
    #     return (
    #         f"{self.type}->"
    #         + f"({repr(self.value[:20]) + '...' if len(self.value) > 20 else repr(self.value)})".replace(
    #             "\n", ""
    #         )
    #     )

    def as_dict(self):
        return {"type": str(self.type), "value": self.value}


class DocNode(object):
    def __init__(
        self,
        _type,
        successors=[],
        depth=1,
        ordered=True,
        text="",
    ):
        self.type = _type
        self.successors = successors
        self.depth = depth
        self.ordered = ordered
        self.text = text

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
        self.page: str = ""
        self.tree = DocNode(DocNodeType.root)

    def add_html_tag(self, tag):
        self.page += tag

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
                if idx != 1 and self.tree.successors[-1].type is not DocNodeType._list:
                    print("LIST ITEM")
                    node = DocNode(
                        DocNodeType._list,
                        [DocNode(_type=DocNodeType.list_item, text=token.value)],
                    )
                    self.tree.successors.append(node)
                    continue
                elif token.type is DocNodeType.list_item:
                    print("LIST ITEM")
                    index = token.value.index(".")
                    d = token.value[: index + 1].strip(".")
                    token.value = token.value[index:]

                    node = DocNode(
                        DocNodeType.list_item,
                        [DocNode(_type=DocNodeType.text, text=token.value, depth=d)],
                    )
                    self.tree.successors[-1].successors.append(node)
                    continue
                else:
                    # unreachable
                    raise
            elif token.type is DocNodeType.heading:
                depth = token.value.count("#")
                self.tree.successors.append(
                    DocNode(
                        DocNodeType.heading,
                        [DocNode(DocNodeType.text, text=token.value, depth=depth)],
                    )
                )
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

        # init page

        # root->(first)node->page

        ptr = 0
        for idx, i in enumerate(self.tree.successors):
            print("NEXT_TOP_NODE\t\t", hex(id(i)), "\t", i.type)
            # pdb.set_trace()
            if i.type is DocNodeType.heading:
                # if i.depth == '1':
                #     PageHeading = "<div class='PageHeadline'>"
                #     PageHeadingEnd = "</div>"
                #     heading = f"<h{i.depth}>"
                #     text = i.successors[0].text
                #     end = f"</h{i.depth}>"
                #     line = PageHeading + heading + text + end +PageHeadingEnd
                #     self.add_html_tag(line)
                #     continue

                heading = f"<h{i.depth}>"
                text = i.successors[0].text
                end = f"</h{i.depth}>"
                line = heading + text + end
                self.add_html_tag(line)

            elif i.type is DocNodeType._list:
                list_start = "<ol>"
                self.add_html_tag(list_start)
                for j in i.successors:
                    if (
                        j.type is DocNodeType.list_item
                        and j.successors[0].type is DocNodeType.text
                    ):
                        body = j.successors[0].text
                        li = f"<li value='{j.depth}'>" + body + "</li>"
                        self.add_html_tag(li)

                list_end = "</ol>"
                self.add_html_tag(list_end)

            elif i.type is DocNodeType.paragraph:
                block_start = "<p>"
                block = i.successors[0].text
                block_end = "</p>"
                line = block_start + block + block_end
                self.add_html_tag(line)

            elif i.type is DocNodeType.code_block:
                block_start = "<pre>"
                block = i.successors[0].text
                block_end = "</pre>"
                line = block_start + block + block_end
                self.add_html_tag(line)

            else:
                raise ValueError(f"unknown type {i.type}")

        # build the rest of the page
        #     div* class("pure-grid maincolumn")
        # div* class("lwn-u-1 pure-u-md-19-24")
        #     PageHeadline
        #         Starting feature text has no tag or class

        #     div* class("ArticleText")
        start_page = (
            "<head>"
            + "\n<link rel='stylesheet' href='../styles/skeleton.css'>"
            + "\n</head>"
            + "\n<body>"
            + "\n<div class='pure-grid maincolumn'>"
            + "\n<div class='lwn-u-1 pure-u-md-19-24'"
        )
        end_page = "</div>" + "\n</div>" + "\n</body>"

        for i in self.tree.successors:
            print(i.type)

        return start_page + self.page + end_page


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
        result: str = self.file_buff[self.cursor]

        self.lookahead_ptr = 1
        while True:

            # if grab_string happens to touch the edge of the file buffer
            if self.lookahead_ptr + self.cursor >= len(self.file_buff):

                # grab the last char
                result += self.file_buff[-1]

                # reset the cursor for the so we can exit cleanly
                # in the next scan that the parser makes
                # self.cursor = self.cursor - (

                # )
                # self.cursor = len(self.file_buff)-2

                # give the resulting string back
                self.cursor = (self.lookahead_ptr + self.cursor) - 1
                return result

            # if we reached the end of the line then we result the result
            if self.file_buff[self.cursor + self.lookahead_ptr] == "\n":

                # no need to add a newline token here
                # it will be grab at the end of the next token

                # reset the position cursor
                self.cursor = self.lookahead_ptr + self.cursor

                # we should have the last char at this point
                return result

            # get the next char
            result += self.file_buff[self.cursor + self.lookahead_ptr]

            # the next char
            self.lookahead_ptr += 1

        # unreachable

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
        result: str = self.file_buff[self.cursor]

        self.lookahead_ptr = 1

        while True:

            tmp_cursor = self.cursor + self.lookahead_ptr

            # if grab_string happens to touch the edge of the file buffer
            if tmp_cursor >= len(self.file_buff):

                # grab the last char
                result += self.file_buff[-1]

                # give the resulting string back
                self.cursor = (tmp_cursor) - 1
                return result

            try:
                # if we reached the end of the line then we result the result
                if self.file_buff[tmp_cursor] == "`":

                    # reset the position cursor
                    self.cursor = tmp_cursor

                    if self.peek_width() == "``":
                        self.cursor += 2

                        # we should have the last char at this point
                        return result

                    else:
                        continue

                # get the next char
                result += self.file_buff[tmp_cursor]

                # the next char
                self.lookahead_ptr += 1

            except Exception:
                raise Exception("did not find edege of block")

        # return the level of header
        self.cursor = tmp_cursor

    def lex_page(self) -> object:
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
                # self.add_token(DocNodeType["newline"], "\n")

            # grabbing full headings
            elif char == "#":

                # returns how much of a heading there is
                heading = self.grab_string()

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
                    block = self.read_block().replace("<", "&lt;").replace(">", "&gt;")
                    self.add_token(DocNodeType["code_block"], block)

            elif char.isdigit():
                # ordered list
                if self.peek() == ".":
                    item = self.grab_string()

                    # here we reuse the size of the node to specify the list item value
                    self.add_token(DocNodeType["list_item"], item)

            elif char == "-":
                if self.peek_width(2) == "//":
                    # grab that comment
                    string = self.grab_string()[1:]

                    # add a list-comment token
                    self.add_token(DocNodeType["list_item_comment"], string)

            # the posibility of a comment
            elif char == "/":
                # make sure that the next char in the line is a comment
                # for actual text we can ignore this later
                if self.peek() == "/":

                    # FATAL: IGNORE COMMENTS

                    # add a comment instead of a "full string"
                    # because ultimately we handle these differently

                    # self.add_token("comment", comment)

                    # we have to advance the cursor here because otherwise we would
                    # have an infinite loop
                    self.cursor += 1
                    continue

                # grab the full string any way, so that we don't consider '/' a comment
                string = self.grab_string()
                # print(self.doc_nodes)
                # if self.doc_nodes[-1].type is DocNodeType.paragraph:
                #     self.doc_nodes[-1].value += " " + string
                    # continue
                self.add_token(DocNodeType["paragraph"], string)

            # here we can just grab a full string
            elif self.is_char(char) or char == "\t":

                string = self.grab_string()

                # if self.doc_nodes[-1].type is DocNodeType.paragraph:
                #     self.doc_nodes[-1].value += " " + string
                #     continue
                self.add_token(DocNodeType["paragraph"], string)

            # go to the next char at the top of the scope
            self.cursor += 1

        return self.doc_nodes


if __name__ == "__main__":
    with open("../examples/compiler.md", "r") as fd:
        page = PageLexer(fd)

        with open("index.html", "w+") as fd:
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

#!/usr/bin/env python3

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

# all text related Token's should have the strings attached to them
# this is so we can more easily craft the page in the end
# we are not really trying to create a commonmark implementation
# this is just a page renderer based on markdown iteself
# I think that explains it

# comments should be respected as long as they are not apart of a atx_heading
# or really any other Token that has text attached to it
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


from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Union
import json
import sys


class TokenType(Enum):
    thematic_break = auto()  # --- *** ___
    code_block = auto()
    list_item = auto()
    insecure_char = auto()  # replacement char -> U+FFFD
    identifier = auto()  # \options: {}
    comment = auto()  # //
    entity_char = auto()  # &nbsp
    atx_heading = auto()  # NODE("#")
    newline = auto()  # \n
    string = auto()  # "this is a string" || this is a string
    tab = auto()  # \t perhaps this is a entity_char

    # we do not current support html this could be "unsafe"
    # block = auto()  # <li> <ul> => NODE("-")


class PageParserError(object):
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

    def __str__(self):
        return f"PageParserError(l{self.line}:c{self.position}): " + self.message


class Token(object):
    """
    Defining what a parser token looks like

    args
        type    TokenType
        chars   String representing the value of the token
        size    Mostly used to describe the detail of a token
                for example
                    atx_heading may have a size of 3 (h3)
                    or list_item token might have the value 3
    """

    def __init__(self, _type: TokenType, chars: str, size: int):
        self.type = _type
        self.chars = chars
        self.size = size

    def __str__(self):
        return str({self.type: self.chars})

    def __dict__(self):
        return {"_type": _type, "chars": chars, "size": size}


class PageParser(object):
    """
    our global parser object

    lookahead_ptr   a pointer to look ahead of the cursor temporarily
    _has_errors     defining what the parser ran into during scans
    file_buff       chars from the source file
    column          what column are we on in a line
    tokens          list of tokens we have collected in scans
    cursor          where we are in the source file
    line            what line are we on, primarily used with column
    fd              a hidden file descriptor for our source file
    """

    def __init__(self, file_buff: str):
        self.file_buff = file_buff.read()
        self.lookahead_ptr = 0
        self._has_errors = []
        self.fd = file_buff
        self.tokens = []
        self.cursor = 0
        self.column = 0
        self.line = 0

    def __str__(self):
        """creating the final page"""

        # create the page
        return "\n".join(self.page)

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

    def create_error(self, msg: str) -> PageParserError:
        """
            Create a new PageParser error

        attrs
            msg message to say what the error is, and if we can continue

        returns
            PageParserError(class)
        """
        error = PageParserError()

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

    def add_option(self) -> None:
        """
            To add an option to the begining of the token buffer

        examples
            o   title
            c   a code block (gist embed)

        returns
            nothing
        """
        valid_options = ["title", "code_embed"]
        # grab the options string
        self.cursor += 2

        # get dict options
        _json = self.grab_string()
        option = json.loads(_json)

        # TODO: find a way to have valid and invalid keys
        # if option not in valid_options:
        # raise Exception(f"invalid option: {option.keys()}")

        self.add_token("identifier", option, True, 0)

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
                print("EOF")
                print(self.lookahead_ptr, self.cursor, len(self.file_buff))

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

        # return the level of header
        self.cursor = self.lookahead_ptr + self.cursor
        return result

    def render(self) -> str:
        """
            Render the page

        attrs
            none    self

        returns
            none

        """
        self.parse_page()
        things = {}
        result = ""
        for i, token in enumerate(self.tokens):

            # this is always pushed to the front of "page stack"
            if token.type is TokenType.identifier:
                # assemble title
                title = token.chars.get("title")
                result += f"<title>{title}</title>"
                result += "\n"

                if "favicon" in token.chars:
                    print("FABULOUS")

            # the headings order really don't matter luckily
            elif token.type is TokenType.atx_heading:
                heading_title = token.chars

                if token.size > 6:
                    raise Exception(f"invalid size: {token.size}")

                result += (
                    f'<h{token.size} class="heading{token.size}">'
                    + f"{heading_title}</h{token.size}>"
                )
                result += "\n"

            # we can't assume this is the first item
            elif token.type is TokenType.list_item:

                # TODO: UGLY AF CODE
                if i + 1 >= len(self.tokens):
                    result += (
                        f'<li class="list-item" value="{token.size}">{token.chars}</li>'
                    )
                    result += "\n"
                    result += "</ol>"
                    result += "\n"
                    result = (
                        '<link rel="stylesheet" href="../styles/main.css">'
                        + '\n<body class="bod">\n'
                        + result
                        + "\n</body>"
                    )
                    break

                # TODO: make this agnostic to newlines
                # if its the tail
                elif self.tokens[i + 1].type != TokenType.list_item:
                    result += (
                        f'<li class="list-item" value="{token.size}">{token.chars}</li>'
                    )
                    result += "</ol>"
                    result += "\n"

                # TODO: make this agnostic to newlines
                # if its the head
                elif self.tokens[i - 1].type != TokenType.list_item:
                    result += '<ol class="list-def">\n'
                    result += f'<li value="{token.size}">{token.chars}</li>'
                    result += "\n"

                else:

                    # just append a new list item because we can reasonably assume
                    # (without newlines) that this is the next list item
                    result += f'<li value="{token.size}">{token.chars}</li>'
                    result += "\n"

            elif token.type is TokenType.code_block:
                result += f'<pre><code class=\"block\">{token.chars}</code></pre>'

            elif token.type is TokenType.newline:
                # if we are at EOF, then we don't really care about the newline
                if i + 1 >= len(self.tokens):
                    continue

                # only add a line break if there are 2 newlines for in source
                # formatting. This prevents lack of lines between markdown decs
                if (
                    self.tokens[i + 1].type == TokenType.newline
                    or self.tokens[i - 1] == TokenType.newline
                ):
                    result += "<br>\n\n"

            elif token.type is TokenType.string:
                result += f'<div class="string-body"><span>{token.chars}</span></div>'
                result += "\n"

            # ignore comments
            elif token.type is TokenType.comment:
                continue

            else:
                raise Exception(f"invalid identifier: {token}")

        result = (
            '<link rel="stylesheet" href="../styles/main.css">'
            + '\n<body class="bod">\n'
            + result
            + "\n</body>"
        )

        return result

    def add_token(
        self, type_: str, chars: str, size=0, insert=False, position=None
    ) -> None:
        """
        add a token to the token to the token buffer

        modes:
            insert  slot in a token at an index
            append  stick it at the end of the buffer

        attrs:
            type_       Token Type
            chars       the string we passed to the token
            size        size of an token-specific identifier
            insert      mode insert
            position    ^ position to insert at

        returns
            Nothing
        """
        if isinstance(chars, str):
            chars = chars.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        try:
            type_ = TokenType[type_]
        except Exception:
            # FATAL: tokentype unavaliable
            raise Exception(f"Unavaliable Type: {str(type_)}")

        if insert:
            # we need to know where to stick this element
            if position is None:
                raise Exception("invalid position: None")

            # insert into the position request, instead of at the end of the stack
            self.tokens.insert(
                position,
                Token(
                    type_,
                    chars,
                    size,
                ),
            )

        # append as normal
        self.tokens.append(
            Token(
                type_,
                chars,
                size,
            )
        )

    def peek(self, amount: int) -> str:
        """
            peek at the next character in the file buffer is there is room

        args
            none

        returns
            the next char in the file buffer
        """
        if amount == 0:
            raise Exception("You can't peek nothing")

        if amount + self.cursor >= len(self.file_buff):
            IndexError("Cursor too close to end of file: amount + PageParser.cursor")

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
        print("parsing block")
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

                    if self.peek(2) == "``":
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

    def parse_page(self) -> object:
        while True:

            # detecting the bounds of the line
            # if our cursor exceeds the bounds of the file_buff we can exit the parser
            if self.cursor >= len(self.file_buff):
                return

            char = self.file_buff[self.cursor]

            # I think it would be nice to honor newlines
            # in theory you could get around this by using comments
            if char == "\n" or char == "\r":
                self.line += 1
                self.add_token("newline", "\n")

            # grabbing full headings
            elif char == "#":

                # returns how much of a heading there is
                heading = self.grab_string()
                size = heading.count("#")

                heading = heading[size + 1 :]

                self.add_token("atx_heading", heading, size)

            elif char == "\\":

                if self.peek(1) == "o":
                    self.add_option()

                elif self.peek(1) == "c":
                    self.add_option()

                else:
                    raise Exception(f"Unknown Option: {self.peek()}")

            elif char == "`":
                print("code block start", char)
                print(self.peek(2))
                if self.peek(2) == "``":
                    print("enter block")
                    # move two more characters forward
                    self.cursor += 2
                    block = self.read_block()
                    self.add_token("code_block", block)

            elif char.isdigit():
                # ordered list
                if self.peek(1) == ".":
                    # store the current char before moving the cursor.
                    # this way we now what we can feed as the li value->li_value
                    li_value = char

                    # we now can consume the next char
                    self.cursor += 1

                    item = self.grab_string()[1:].strip(" ")

                    # here we reuse the size of the node to specify the list item value
                    self.add_token("list_item", item, li_value)

            # the posibility of a comment
            elif char == "/":
                # make sure that the next char in the line is a comment
                # for actual text we can ignore this later
                if self.peek(1) == "/":

                    # add a comment instead of a "full string"
                    # because ultimately we handle these differently
                    comment = self.grab_string()
                    self.add_token("comment", comment)

                    # we have to advance the cursor here because otherwise we would
                    # have an infinite loop
                    self.cursor += 1
                    continue

                # grab the full string any way, so that we don't consider '/' a comment
                string = self.grab_string()
                self.add_token("string", string)

            # here we can just grab a full string
            elif self.is_char(char) or char == "\t":

                string = self.grab_string()

                self.add_token("string", string)

            # go to the next char at the top of the scope
            self.cursor += 1


if __name__ == "__main__":
    with open("../examples/compiler.md") as fd:
        page = PageParser(fd)

        with open("index.html", "w+") as fd:
            final = page.render()
            for node in page.tokens:
                print(node)
            print()
            print(final)
            fd.write(final)

    sys.exit(0)

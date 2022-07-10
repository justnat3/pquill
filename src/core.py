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

class TokenType(Enum):
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

class PageParserError(object):
    """_summary_

    Args:
        message -- Explaining what error the
        position -- position of the cursor
        line -- line where the error occurred

    """

    def __init__(self, message: str, position: int, line: int):
        self.position = position
        self.message = message

    def __str__(self):
        return f"PageParserError(l{self.line}:c{self.position}): " + self.message


class Token(object):
    def __init__(self, _type: TokenType, chars: str, size: int):
        self.type = _type
        self.chars = chars
        self.size = size

    def __str__(self):
        return str({self.type: self.chars})

    def __dict__(self):
        return {"_type": _type, "chars": chars, "size": size}


class PageParser(object):
    def __init__(self, file_buff: str):

        # NOTE: not sure if I want to keep these around
        # self.readback_ptr = -1  # a pointer behind of the cursor

        self.file_buff = file_buff.read()  # input file_buff chars
        self.lookahead_ptr = 0  # a pointer ahead of the cursor
        self._has_errors = []  # list of errors
        self.cursor = 0  # ptr to the character in the file_buff
        self.column = 0  # what colum we are on in a line
        self.tokens = []  # list of page tokens
        #self.page = []  # strings that make up the final document
        self.fd = file_buff  # hidden file_buff descriptor
        self.line = 0  # what line we are on, we can use this with column

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
        #if option not in valid_options:
            #raise Exception(f"invalid option: {option.keys()}")

        self.add_token("identifier", option, True, 0)

    def grab_string(self) -> str:
        """
            collecting a ** FULL ** string

        attrs
            in class

        Returns
            str     full string to collect
        """
        # store the current char that is a char
        result: str = self.file_buff[self.cursor]

        self.lookahead_ptr = 1
        while True:

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
        return result.replace("\t", "&#9")

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

            if i+2 > len(self.tokens):
                result = "<link rel=\"stylesheet\" href=\"../styles/main.css\">" + "\n<body class=\"bod\">\n" + result + "\n</body>"

            # this is always pushed to the front of "page stack"
            elif token.type is TokenType.identifier:
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

                result += f"<h{token.size} class=\"heading{token.size}\">{heading_title}</h{token.size}>"
                result += "\n"

            elif token.type is TokenType.newline:
                result += f"<pre>{token.chars}</pre>"
                result += "\n"

            elif token.type is TokenType.string:
                result += f"<div class=\"string-body\"><span>{token.chars}</span></div>"
                result += "\n"

            # ignore comments
            elif token.type is TokenType.comment:
                continue

            else:
                raise Exception(f"invalid identifier: {token}")

        return result

    def add_token(self, type_: str, chars: str, size=0, insert=False, position=None) -> None:
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

    def peek(self) -> str:
        """
            peek at the next character in the file buffer is there is room

        args
            none

        returns
            the next char in the file buffer
        """
        # TODO: add boundary check
        return self.file_buff[self.cursor+1]

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

            # tab characters are really just entity characters
            # this should be respected by the "string" tokentype
            # this is because the string tokentype is formatted into a <pre>
            #elif char == "\t":
                #self.add_token("tab", "\t")


            # grabbing full headings
            elif char == "#":

                # returns how much of a heading there is
                heading = self.grab_string()
                size = heading.count("#")

                heading = heading[size + 1 :]

                self.add_token("atx_heading", heading, size)

            elif char == "\\":

                if self.peek() == "o":
                    self.add_option()

                elif self.peek() == "c":
                    self.add_option()

                else:
                    raise Exception(f"Unknown Option: {self.peek()}")

            # the posibility of a comment
            elif char == "/":
                # make sure that the next char in the line is a comment
                # for actual text we can ignore this later
                if self.peek() == "/":

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
    with open("../examples/page.md") as fd:
        page = PageParser(fd)

        with open("index.html", "w+") as fd:
            final = page.render()
            for node in page.tokens:
                print(node)
            print()
            print(final)
            fd.write(final)

    exit(-1)

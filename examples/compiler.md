# Writing a Compiler for blogs 

## Lexing

If you are familiar to writing tokenizers, you will recognize that we need to have some form of Typing. Something could be a header, a code_block, a list, or even just some text. We use the following Enum to keep track of that.

```python
class DocNodeType(Enum):
	list_item_comment = auto()
	root = auto()
	list_item = auto()
	code_block = auto()
	identifier = auto() # \options: {}
	comment = auto() # //
	heading = auto() # NODE("#")
	paragraph = auto() # "this is a string" || this is a string
	tab = auto() # \t perhaps this is a entity_char	
	text = auto()
	_list = auto()
```

In this compiler I try to write quite a few helper functions to enable me to simplify some of the code. For the most part we need to handle the basic parts of tokenizing. In this case its the following

1. grabbing strings
2. detecting end of file
3. detecting end of line
4. digit matching
5. alpha char matching
6. options
7. comments

lets start with capturing strings in this case we use a lookahead pointer to avoid moving the our active cursor in the file. This really is just a really gnarly version of PageParser.peek() or PageParser.peek_width(). We make sure that we capture the char we selected in the last function scope, we set the lookahead pointer. After that is initialized then we can start advancing our fake cursor checking for EOF and EOL. If we didn't find either of those we append the char to the result, if we did find one then we can set the cursor active cursor to the correct position- for EOF we make sure to grab the last char in the buffer and return the string. This makes sure that the next position lets the lexer return cleanly.

```python
# store the current char that is a char
result: str = self.file_buff[self.cursor]

self.lookahead_ptr = 1
while True:

	# if grab_string happens to touch the edge of the file buffer
	if self.lookahead_ptr + self.cursor >= len(self.file_buff):
	
		# grab the last char
		result += self.file_buff[-1]

		# give the resulting string bac
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
	raise
```

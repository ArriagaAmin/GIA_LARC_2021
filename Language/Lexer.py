import ply.lex as lex
import ply.yacc as yacc
from sys import argv

# Aqui guardamos los errores.
lexerErrors = []
# Texto con el codigo.
text = ""
# Tabla de hash super rudimentaria.
tokensList = [[] for i in range(500)]

# Diccionario de palabras reservadas - Tokens
reserved = {
  "initial": "TkInitial",
  "green": "TkGreen",
  "yellow": "TkYellow",
  "blue": "TkBlue",
  "red": "TkRed",
  "left": "TkLeft",
  "right": "TkRight",
  "if": "TkIf",
  "then": "TkThen",
  "else": "TkElse",
  "repeat": "TkRepeat",
  "times": "TkTimes",
  "while": "TkWhile",
  "do": "TkDo",
  "begin": "TkBegin",
  "end": "TkEnd",
  "define": "TkDefine",
  "as": "TkAs",
  "move": "TkMove",
  "identify": "TkIdentify",
  "take": "TkTake",
  "level": "TkLevel",
  "drop": "TkDrop"
}

# Lista de tokens
tokens = [
  # Oraciones reservadas
  "TkBScenario",
  "TkEScenario",
  "TkPlaceBlock",
  "TkBTask",
  "TkETask",
  "TkTurnL",
  "TkTrunR",
  "TkDetectL",
  "TkDetectR",
  "TkDetectF",

  # Caracteres simples
  "TkSemiColon",
  "TkOpenParent",
  "TkCloseParent",
  "TkSpace",
  "TkTab",
  "TkNewLine",

  # Tokens generales
  "TkNum",
  "TkBNum"
  "TkId",

  # Comentarios
  "TkLineComment",
  "TkBlockComment",
] + list(reserved.values())

# Definicion de las Tokens oraciones reservadas
def t_TkBScenario(t):
  r'begin-scenario'
  return t
def t_TkEScenario(t):
  r'end-scenario'
  return t
def t_TkPlaceBlock(t):
  r'Place(\s)+block'
  t.lexer.lineno += t.value.count("\n")
  return t
def t_TkBTask(t):
  r'begin-task'
  return t
def t_TkETask(t):
  r'end-task'
  return t
def t_TkTurnL(t):
  r'turn-left'
  return t
def t_TkTurnR(t):
  r'turn-right'
  return t
def t_TkDetectL(t):
  r'detect-left'
  return t
def t_TkDetectR(t):
  r'detect-right'
  return t
def t_TkDetectF(t):
  r'detect-front'
  return t

# Definicion de los Tokens caracteres simples
t_TkSemiColon = r'\;'
t_TkOpenParent = r'\('
t_TkCloseParent = r'\)'
t_ignore_TkSpace = r'\ '
def t_TkTab(t):
  r'\t'
def t_TkNewLine(t):
  r'\n+'
  t.lexer.lineno += t.value.count("\n")

# Definicion de los Tokens comentarios
def t_TkLineComment(t):
  r'\-\-.*?\n'
  # Contamos los saltos de linea
  t.lexer.lineno += t.value.count("\n") 
def t_TkBlockComment(t):
  r'(?s)\{\{.*?\}\}'
  # Contamos los saltos de linea
  t.lexer.lineno += t.value.count("\n")

# Definicion de los Tokens generales
def t_TkNum(t):
  r'\d+'
  t.value = int(t.value)
  return t
def t_TkBNum(t):
  r'B\d+'
  t.value = int(t.value[1:])
  return t
def t_TkId(t):
  r'[a-zA-Z_][a-zA-Z0-9_]*'
  t.type = reserved.get(t.value, 'TkId')    # Check for reserved words
  return t

# Tokens de error
def t_error(t):
  lexerErrors.append(t)
  t.lexer.skip(1)

# Funcion para obtener la columna de un Token
def getColumn(text, lexpos):
  last_cr = text.rfind('\n', 0, lexpos)
  if last_cr < 0:
      last_cr = 0
  column = lexpos - last_cr
  return column

def getLine(text, lexpos):
  beginLine = text.rfind('\n', 0, lexpos)
  endLine = text.find('\n', lexpos, len(text))
  text[beginLine+1 : endLine]
  newText = text[beginLine+1 : endLine].replace('\t', " ")
  return newText

# Dada la posicion en los tokens de un token, retorna su linea y columna.
# La razon de esta funcion es que el parser no obtiene correctamente la linea
# ni la columna.
def getPosition(lexpos, tokensList):
  array = tokensList[lexpos % len(tokensList)]
  for i in range(len(array)):
    if array[i][0] == lexpos:
      return [array[i][1], array[i][2]]

lex.lex()

def lexer(text):
  # Output por linea
  output = ""

  # Guardamos los tokens encontrados
  lex.input(text)
  while 1:
    tok = lex.token()
    if not tok: break

    # Agregamos los tokens a la tabla de hash.
    tokensList[ tok.lexpos % len(tokensList) ].append(
        [tok.lexpos, tok.lineno, getColumn(text, tok.lexpos)]
      )

  return lexerErrors
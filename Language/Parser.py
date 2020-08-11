import ply.yacc as yacc
from sys import argv
from Lexer import *

########################### GLOBAL VARIABLES ###########################
# Aqui guardaremos los errores de contexto.
contextErrors = []
# Aqui guardaremos las funciones de los task a ejecutar.
toExec = []
# Variable que indica si la sintaxis es correcta.
syntax = [True]
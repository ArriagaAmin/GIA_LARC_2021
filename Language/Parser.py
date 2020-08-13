import ply.yacc as yacc
from sys import argv
from Lexer import *
from time import sleep

########################### GLOBAL VARIABLES ###########################
# Aqui guardaremos los errores de contexto.
contextErrors = []
# Aqui guardaremos las funciones de los task a ejecutar.
toExec = []
# Variable que indica si la sintaxis es correcta.
syntax = [True]


########################### CLASSES ###########################
class SymbolsTable:
  """ Tabla de simbolos utilizada para guardar los simbolos definidos y para verificar si 
  un simbolo existe. Las tablas de simbolos se manejan dentro de una estructura de pila (stack).
  Cada vez que se entra en un contexto sintactico, una nueva tabla se empila, y cada vez que 
  se sale de un contexto, la tabla actual se desempila."""

  def __init__(self):
    """ Crea una pila vacía. """
    # La pila vacía se representa con una lista vacía.
    self.tables = []
    self.head = -1
    self.scopeId = 0

    # Simbolos desechados al hacer pop.
    self.trash = []

    # Verifica si se debe finalizar la ejecucion de la tarea.
    self.terminate = False

  def find(self, id):
    """ Busca un elemento en la tabla de simbolos. """
    for i in range(self.head, -1, -1):
      for j in range(len(self.tables[i])-1, -1, -1):
        if id == self.tables[i][j].id:
          return self.tables[i][j]

  def findNotGlobal(self, id, level=1):
    """ Busca un elemento en la tabla de simbolos, sin considerar los ultimos
    'level' tablas. """
    for i in range(self.head, level-1, -1):
      for j in range(len(self.tables[i])-1, -1, -1):
        if id == self.tables[i][j].id:
          return self.tables[i][j]

  def insert(self, x):
    """ Inserta un elemento junto a sus datos en la tabla actual """
    self.tables[self.head].append(x)

  def push_empty_table(self):
    """ Empilamos una nueva tabla vacia """
    self.tables.append([])
    self.head += 1

  def pop(self):
    """ Desempilamos una tabla """
    if self.head < 0:
      # Error
      return False
    self.head -= 1
    table = self.tables[self.head + 1]
    self.trash.append(table)
    self.tables.pop(self.head + 1)
    return table

  def empty(self):
    """ Verificamos si la tabla de simbolos esta vacia """
    return (self.head == -1)

  def push(self, table):
    """ Empilamos una tabla """
    self.tables.append(table)
    self.head += 1

# Creamos la tabla de simbolos y agregamos el contexto global.
ST = SymbolsTable()
ST.push_empty_table()

class Variable:
  """ Clase que guarda la informacion de una variable en el
  lenguaje Willy*."""
  def __init__(self, id, elementType, data):
    if elementType != "define":
      self.id = id
    else:
      # Si la variable es del tipo instruccion, entonces originalmente
      # su id sera "define", hasta que su definicion este completa y
      # su id pase a ser el indicado por el usuario.
      self.id = "define"

    # Almacenamos el id en otro parametro.
    self.name = id
    self.scopeId = -1
    # Tipo de elemento y datos de la variable.
    self.elementType = elementType
    self.data = data

    # Si la variable es un Object-type, guardamos un atributo correspondiente
    # a la codificiacion de su color en BASH.
    if self.data == "red": self.color = "31"
    elif self.data == "green": self.color = "32"
    elif self.data == "yellow": self.color = "33"
    elif self.data == "blue": self.color = "34"

class Willy:
  """ Clase que guarda la informacion de Willy en uno de los mundos. """
  def __init__(self):
    self.id = "Willy"
    self.elementType = "Willy"

    # Posicion.
    self.x = 0
    self.y = 0

    # Orientacion.
    self.look = "north"
    # Bloque que contiene.
    self.block = None
    # Bloque identificado.
    self.blockId = None
    self.level = 0

class Scenario:
  """ Clase que guarda la informacion de un scenario en el lenguaje Willy*. """
  def __init__(self):
    self.id = "begin-scenario"
    self.scopeId = -1
    # Mapa
    self.scenarioMap = [[[] for _ in range(22)] for _ in range(19)]
    self.shelves = [[0 for _ in range(5)] for _ in range(3)]
    self.unRegions = [0 for _ in range(7)]
    # Conjunto de symbolos definidos en el scenario.
    self.context = [] 
    # Informacion de Willy del scenario.
    self.willy = Willy() 

  def printData(self):
    """ Imprimimos los datos del mundo. """

    x, y = self.willy.x, self.willy.y
    # Limpiamos el terminal.
    print("\033[H\033[2J")

    text = "\033[00;1m\tSCENARIO \t\t\t\t\t\t\tSHELVES\033[0;0m\n"

    for i in range(19):
      line = "\t"

      for j in range(22):
        # Si existe un objeto en la i-j-esima casilla.
        if len(self.scenarioMap[i][j]) > 0:
          if i%3 == 0 and j%3 != 0: space = "-"
          elif i%3 != 0 and j%3 != 0: space = " "
          else: space = ""

          obj = str(self.scenarioMap[i][j][0])
          if obj == "blue": line += space +  "\033[36;1mB\033[0;0m" + space
          elif obj == "red": line += space +  "\033[31;1mR\033[0;0m" + space
          elif obj == "green": line += space +  "\033[32;1mG\033[0;0m" + space
          elif obj == "yellow": line += space +  "\033[33;1mY\033[0;0m" + space
          elif obj[0] == "B" and len(obj) == 2: line += space +  "\033[1;1m\033[4;1m" +\
             str(obj[1]) + "\033[0;0m" + space
          elif obj[0] == "B": line += space +  "\033[1;1m\033[4;1m" + chr(int(obj[1:])+55) +\
             "\033[0;0m" + space
          elif len(obj) > 1: line += space +  chr(int(obj)+55) + space
          else: line += space + str(obj) + space

        # En cambio, si no hay mas objetos y WILLY se encuentra aqui,
        # agregamos a willy.
        elif x == j and y == i:
          if i%3 == 0 and j%3 != 0: space = "-"
          elif i%3 != 0 and j%3 != 0: space = " "
          else: space = ""

          if self.willy.look == "north": line += space + "\033[1;1m^\033[0;0m" + space
          elif self.willy.look == "east": line += space + "\033[1;1m>\033[0;0m" + space
          elif self.willy.look == "south": line += space + "\033[1;1mv\033[0;0m" + space
          else: line += space + "\033[1;1m<\033[0;0m" + space

        # Esquinas.
        elif i%3 == 0 and j%3 == 0: line += "+"
        # Lineas verticales.
        elif i%3 == 0: line += "---"
        # Lineas horizontales.
        elif j%3 == 0: line += "|"
        else: line += "   "
      line += "\t\t"

      # ESTANTES
      if i%2 == 0 and i < 7:
        for j in range(11):
          if j%2 == 0: line += "+"
          else: line += "---"
      elif i < 7:
        for j in range(5):
          line += "| " + str(self.shelves[2-i][j]) + " "
        line += "|"


      # ZONA DE DESCARGA
      elif i == 8: line += "\033[0;1mUNLOADING REGIONS\033[0;0m"
      elif i == 9 or i == 11:
        for j in range(21):
          if j < 3 or j > 17: color = "32"
          elif j < 6 or j > 14: color = "36"
          elif j < 9 or j > 11: color = "33"
          else: color = "31"

          if j%3 == 0 or (j+1)%3 == 0: line += "\033[" + color + ";1m+\033[0;0m"
          else: line += "\033[" + color + ";1m---\033[0;0m"
      elif i == 10:
        for j in range(7):
          if j==0 or j==6: color = "32"
          elif j==1 or j==5: color = "36"
          elif j==2 or j==4: color = "33"
          else: color = "31"
          line += "\033[" + color + ";1m| " + str(self.unRegions[j]) + " |\033[0;0m"


      # INFORMACION DE WILLY
      elif i == 13: line += "\033[0;1mWILLY\033[0;0m"
      elif i == 14: line += "    Position: [" + str(self.willy.x) + ", " + str(18-self.willy.y) + "]"
      elif i == 15: line += "    Orientation: " + self.willy.look
      elif i == 16: line += "    Block: " + str(self.willy.block)
      elif i == 17: line += "    Last identified block: " + str(self.willy.blockId)
      elif i == 18: line += "    Grua level: " + str(self.willy.level)
      
      # Agregamos la linea al texto.
      text += line + "\n"
      
    print(text)
    sleep(0.5)
  
class Task:
  """ Clase que guarda la informacion de una tarea en el lenguaje Willy*. """
  def __init__(self, scenario):
    self.id = "begin-task"
    self.elementType = "Task"
    self.scopeId = -1

    # Inicialmente se guarda el ID de la tarea en un atributo nombre
    # para que el ID de todas las tareas sea "begin-task" durante se definicion,
    # lo que facilita encontrarlo. Una vez terminada la definicion de la tarea,
    # el ID toma el valor del nombre.
    self.name = id

    # Informacion del scenario sobre el que se aplica la tarea.
    self.scenario = scenario
    
    # Conjunto de simbolos definidos en la tarea. Es un superconjunto del
    # contexto del scenario. 
    self.context = []

    # Conjunto de instrucciones.
    self.instructions = None


########################### FUNCTIONS ###########################
# Funciones comunes que podrian aparecer durante la ejecucion del programa.
def skip():
    pass
def terminate():
    ST.terminate = True
def notTerminate():
    ST.terminate = False
def rFalse():
    return False



########################### SCENARIO AND TASK ###########################
def p_universo(p):
  # Esta produccion se usa unica y exclusivamente para permitir los
  # archivos vacios.
  '''universo : beginScenario beginTask
              | empty
              | ignore'''



########################### SCENARIO ###########################
# SCENARIO DEFINITION
def p_beginScenario(p):
  # Permite definir un escenario. 
  '''beginScenario  : beginS endS'''

def p_beginS(p):
  # Permite crear un nuevo contexto para el scenario actual una vez inicializado. 
  '''beginS : TkBeginScenario'''
  ST.push_empty_table()
  ST.insert(Scenario())

def p_endS(p):
  # Permite actualizar la informacion del escenario dada su definicion, y 
  # agrega el symbolo al contexto global.
  '''endS : scenarioInstructions TkEndScenario
          | TkEndScenario'''

  # El condicional 'if ST.find("begin-scenario")' se usara constantemente en
  # las producciones del scenario, y verifica que se haya creado correctamente
  # el scenario al inicio. Si no se creo correctamente, simplemente ignora todas
  # las definiciones del scenario.
  if ST.find("begin-scenario"):
    table = ST.pop()

    # Como el simbolo del scenario siempre es el que se crea de primero,
    # entonces toda la informacion del scenario esta en la primera posicion
    # de la tabla.
    scenario = table.pop(0)
    # Sacamos a Willy del conexto
    willy = scenario.willy

    # Todos los simbolos de la tabla seran agregadas al contexto del scenario.
    for symbol in table:
      scenario.context.append(symbol)

    # Agregamos los simbolos desechados al trash.
    ST.trash.append(table)
    ST.insert(scenario)

# SCENARIO'S INSTRUCTIONS
def p_scenarioInstructions(p):
  # Permite concatenar instrucciones del escenario.
  '''scenarioInstructions : scenarioInstructions scenarioInstruction
                          | scenarioInstructions TkSemiColon
                          | scenarioInstruction
                          | TkSemiColon'''

def p_scenarioInstruction(p):
  # Instrucciones del escenario.
  '''scenarioInstruction  : placeBlock
                          | startAt
                          | boolean
                          | integer'''

def p_position(p):
  # Verificamos la correctitud de una posicion en el mapa.
  '''position : TkNum TkNum'''

  if ST.find("begin-scenario"):
    # Este parametro se usara constantemente e indica si hubo un error
    # sintactico, en caso de ser asi, se cancelara la ejecucion de la
    # instruccion actual.
    error = False

    # Si la columna se sale del mapa, error.
    if p[1] > 21:
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tSe indico una columna superior a la 21." % \
        (pos[0], pos[1], p[1], 21)
      )
      error = True
    
    # Si la columna es nula, error.
    if p[1] < 0:
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tSe indico la columna %d, recuerde " +\
          "que los indices del mundo comienzan en 0." % \
        (pos[0], pos[1], p[1])
      )
      error = True

    # Si la fila se sale del mapa, error.
    if p[2] > 18:
        pos = getPosition(p.lexpos(2), tokensList)
        contextErrors.append(
          "Linea %d, columna %d:\tSe indico una fila superior a la 18 %d." % \
          (pos[0], pos[1], p[2], 21)
        )
        error = True

    # Si la fila es nula, error.
    if p[2] < 0:
        pos = getPosition(p.lexpos(2), tokensList)
        contextErrors.append(
          "Linea %d, columna %d:\tSe indico la fila %d, recuerde " +\
            "que los indices del mundo comienzan en 1." % \
          (pos[0], pos[1], p[2])
        )
        error = True

    p[0] = [error, p[1], p[2]]

def p_orientation(p):
  # Posibles orientaciones de Willy.
  '''orientation  : TkNorth
                  | TkEast
                  | TkWest
                  | TkSouth'''
  p[0] = p[1]

def p_color(p):
  # Posibles colores de los bloques.
  '''color : TkRed
            | TkBlue
            | TkGreen
            | TkYellow'''
  p[0] = p[1]

def p_placeBlock(p):
    # Permite colocar bloques en ubicaciones especificas del mundo.
    '''placeBlock : TkPlaceBlock TkNum TkAt position TkSemiColon
                  | TkPlaceBlock TkBNum TkAt position TkSemiColon
                  | TkPlaceBlock color TkAt position TkSemiColon'''
    if ST.find("begin-scenario"):
        error = p[4][0]

        # Cantidad a colocar, ID del objeto y posicion donde se desea ubicar.
        block, x, y = str(p[2]), p[4][1], p[4][2]
        # Obtenemos el mapa
        scenarioMap = ST.find("begin-scenario").scenarioMap

        # Si en la ubicacion indicada hay otro bloque, error.
        if not error and len(scenarioMap[18 - y][x]) > 0:
          pos = getPosition(p.lexpos(1), tokensList)
          contextErrors.append(
            "Linea %d, columna %d:\tYa se coloco un bloque en esa posicion." % \
            (pos[0], pos[1])
          )
          error = True

        if not block in ["blue", "red", "green", "yellow"]:
          if block[0] == "B": num = int(block[1:])
          else: num = int(block)

          if num < 1 or num > 15:
            pos = getPosition(p.lexpos(1), tokensList)
            contextErrors.append(
              "Linea %d, columna %d:\tLos bloques numericos solo pueden tener " +\
                "un numero del 1 al 15." % \
              (pos[0], pos[1])
            )
            error = True

        if not error:
          scenarioMap[18 - y][x].append(block)

def p_startAt(p):
  # Permite definir la posicion inicial de Willy.
  '''startAt : TkStartAt position TkHeading orientation TkSemiColon'''

  if ST.find("begin-scenario"):
    error = p[2][0]

    # Fila, columna y orientacion de Willy.
    x, y, look = p[2][1], p[2][2], p[4]
    # Informacion del mapa del scenario.
    scenarioMap = ST.find("begin-scenario").scenarioMap
    # Informacion de Willy.
    willy = ST.find("begin-scenario").willy

    # Si se indica una posicion donde se encuentra un bloque, error.
    if not error and len(scenarioMap[18 - y][x]) > 0:
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tNo se puede colocar a Willy encima de un bloque" % \
        (pos[0], pos[1])
      )
      error = True

    if not error:
      # Actualizamos la informacion de Willy.
      willy.x, willy.y, willy.look = x, 18-y, look

def p_boolean(p):
  # Permite definir una variable booleana.
  '''boolean : TkBoolean TkId TkEqual TkTrue TkSemiColon
              | TkBoolean TkId TkEqual TkFalse TkSemiColon'''

  if ST.find("begin-scenario"):
    # Si ya se definio el ID indicado, error.
    if ST.findNotGlobal(p[2]):
      pos = getPosition(p.lexpos(2), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' ya definido." % \
        (pos[0], pos[1], p[2])
      )

    else:
      # Creamos un nuevo Boolean y actualizamos su informacion.
      if p[4] == "True": boolean = Variable(p[2], "Boolean", True)
      else: boolean = Variable(p[2], "Boolean", False)
      ST.insert(boolean)

def p_integer(p):
  # Permite definir una variable entera
  '''integer : TkInteger TkNId TkEqual TkNum TkSemiColon'''

  if ST.find("begin-scenario"):
    # Si ya se definio el ID indicado, error.
    if ST.findNotGlobal(p[2]):
      pos = getPosition(p.lexpos(2), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' ya definido." % \
        (pos[0], pos[1], p[2])
      )

    else:
      # Creamos un nuevo entero y actualizamos su informacion.
      integer = Variable(p[2], "Integer", int(p[4]))
      ST.insert(integer)



########################### BOOL EXPRESSIONS ###########################
def p_boolExpression(p):
  '''boolExpression : boolExpression TkEquiv boolTerm
                    | boolExpression TkNotEqual boolTerm
                    | boolTerm
  '''
  if (len(p) == 2):
    p[0] = p[1]
  elif len(p) == 4:
    if (p[2] == "=="):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() == term()
      p[0] = equivTerm

    elif (p[2] == "!="):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() != term()
      p[0] = equivTerm

def p_boolTerm(p):
  '''boolTerm : boolTerm TkAnd boolFactor
              | boolTerm TkOr boolFactor
              | boolFactor'''
  if (len(p) == 2):
    p[0] = p[1]
  elif len(p) == 4:
    if (p[2] == "and"):
      term = p[1]
      factor = p[3]
      def andFactor(term = term, factor = factor):
        return factor() and term()
      p[0] = andFactor

    elif (p[2] == "or"):
      term = p[1]
      factor = p[3]
      def orFactor(term = term, factor = factor):
        return term() or factor()
      p[0] = orFactor

def p_boolFactor(p):
  '''boolFactor : TkNot boolElement
                | boolElement'''
  if (len(p) == 2):
    p[0] = p[1]
  elif (len(p) == 3):
    factor = p[2]
    def notFactor(factor = factor):
      return not factor()
    p[0] = notFactor

def p_boolElement(p):
  '''boolElement  : boolId
                  | boolC
                  | detectLeft
                  | detectRight
                  | detectFront
                  | detectLine
                  | detectInters
                  | idBlockIs
                  | boolIntExpression
                  | TkOpenParent boolExpression TkCloseParent'''
  if (len(p) == 2):
    p[0] = p[1]
  else:
    p[0] = p[2]

def p_boolConstant(p):
  '''boolC  : TkTrue
            | TkFalse'''
  if p[1] == "True": 
    def const(): return True
  else: 
    def const(): return False
  p[0] = const

def p_detectLeft(p):
  '''detectLeft : TkDetectL'''
  scenario = ST.find("begin-task").scenario
  def detect(scenario = scenario):
    if not ST.terminate:
      willy = scenario.willy
      scenarioMap = scenario.scenarioMap
      x, y, orientation = willy.x, willy.y, willy.look

      if orientation == "north":
        if x == 0: return False
        elif scenarioMap[y][x-1] == []: return False
        else: return True

      elif orientation == "south":
        if x == len(scenarioMap[0])-1: return False
        elif scenarioMap[y][x+1] == []: return False
        else: return True

      elif orientation == "west":
        if y == len(scenarioMap): return False
        elif scenarioMap[y+1][x] == []: return False
        else: return True

      elif orientation == "east":
        if y == 0: return False
        elif scenarioMap[y-1][x] == []: return False
        else: return True
  p[0] = detect

def p_detectRight(p):
  '''detectRight : TkDetectR'''
  scenario = ST.find("begin-task").scenario
  def detect(scenario = scenario):
    if not ST.terminate:
      willy = scenario.willy
      scenarioMap = scenario.scenarioMap
      x, y, orientation = willy.x, willy.y, willy.look

      if orientation == "south":
        if x == 0: return False
        elif scenarioMap[y][x-1] == []: return False
        else: return True

      elif orientation == "north":
        if x == len(scenarioMap[0])-1: return False
        elif scenarioMap[y][x+1] == []: return False
        else: return True

      elif orientation == "east":
        if y == len(scenarioMap): return False
        elif scenarioMap[y+1][x] == []: return False
        else: return True

      elif orientation == "west":
        if y == 0: return False
        elif scenarioMap[y-1][x] == []: return False
        else: return True
  p[0] = detect

def p_detectFront(p):
  '''detectFront : TkDetectF'''
  scenario = ST.find("begin-task").scenario
  def detect(scenario = scenario):
    if not ST.terminate:
      willy = scenario.willy
      scenarioMap = scenario.scenarioMap
      x, y, orientation = willy.x, willy.y, willy.look

      if orientation == "west":
        if x == 0: return False
        elif scenarioMap[y][x-1] == []: return False
        else: return True

      elif orientation == "east":
        if x == len(scenarioMap[0])-1: return False
        elif scenarioMap[y][x+1] == []: return False
        else: return True

      elif orientation == "south":
        if y == len(scenarioMap)-1: return False
        elif scenarioMap[y+1][x] == []: return False
        else: return True

      elif orientation == "north":
        if y == 0: return False
        elif scenarioMap[y-1][x] == []: return False
        else: return True
  p[0] = detect

def p_detectLine(p):
  '''detectLine : TkDetectLine'''
  scenario = ST.find("begin-task").scenario
  def detect(scenario = scenario):
    if not ST.terminate:
      willy = scenario.willy
      x, y = willy.x, willy.y
      if x%3 == 0 or y%3 == 0: return True
      return False
  p[0] = detect

def p_detectInters(p):
  '''detectInters : TkDetectInters'''
  scenario = ST.find("begin-task").scenario
  def detect(scenario = scenario):
    if not ST.terminate:
      willy = scenario.willy
      x, y = willy.x, willy.y
      if x%3 == 0 and y%3 == 0: return True
      return False
  p[0] = detect

def p_idBlockIs(p):
  '''idBlockIs  : TkLastIdBlockIs TkNum
                | TkLastIdBlockIs TkBNum
                | TkLastIdBlockIs color'''
  willy = ST.find("begin-task").scenario.willy
  def identify(willy = willy, id = p[2]):
    return willy.blockId == id
  p[0] = identify

def p_boolId(p):
  # Verifica que un ID sea booleano.
  '''boolId : TkId'''

  if ST.find("begin-task"):
    error = False

    # Si el ID indicado no existe, error.
    if not ST.findNotGlobal(p[1]):
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' no definido." % \
        (pos[0], pos[1], p[1])
      )
      error = True

    # Si el ID indicado no es booleano, error.
    elif ST.find(p[1]).elementType != "Boolean":
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tSe debe operar con una variable del tipo Boolean." % \
        (pos[0], pos[1])
      )
      error = True

    if not error:
      var = ST.find(p[1])
      def boolean(var = var):
        return var.data
      p[0] = boolean

def p_boolIntExpression(p):
  '''boolIntExpression  : intExpression TkEquiv intExpression
                        | intExpression TkNotEqual intExpression
                        | intExpression TkLessT intExpression
                        | intExpression TkLessEq intExpression
                        | intExpression TkGreatT intExpression
                        | intExpression TkGreatEq intExpression'''

  if (p[2] == "=="):
    expression = p[1]
    term = p[3]
    def equivTerm(expression = expression, term = term):
      return expression() == term()
    p[0] = equivTerm

  elif (p[2] == "!="):
    expression = p[1]
    term = p[3]
    def notEqualTerm(expression = expression, term = term):
      return expression() != term()
    p[0] = notEqualTerm

  elif (p[2] == "<"):
    expression = p[1]
    term = p[3]
    def lessThanTerm(expression = expression, term = term):
      return expression() < term()
    p[0] = lessThanTerm

  elif (p[2] == "<="):
    expression = p[1]
    term = p[3]
    def lessEqualTerm(expression = expression, term = term):
      return expression() <= term()
    p[0] = lessEqualTerm
  
  elif (p[2] == ">"):
    expression = p[1]
    term = p[3]
    def greatThanTerm(expression = expression, term = term):
      return expression() > term()
    p[0] = greatThanTerm

  else:
    expression = p[1]
    term = p[3]
    def greatEqualTerm(expression = expression, term = term):
      return expression() >= term()
    p[0] = greatEqualTerm


########################### INTEGER EXPRESSIONS ###########################
def p_intExpression(p):
  '''intExpression  : intExpression TkPlus intTerm
                    | intExpression TkMinus intTerm
                    | intTerm
  '''
  if (len(p) == 2):
    p[0] = p[1]
  elif len(p) == 4:
    if (p[2] == "+"):
      expression = p[1]
      term = p[3]
      def plusTerm(expression = expression, term = term):
        return expression() + term()
      p[0] = plusTerm

    elif (p[2] == "-"):
      expression = p[1]
      term = p[3]
      def minusTerm(expression = expression, term = term):
        return expression() - term()
      p[0] = minusTerm

def p_intTerm(p):
  '''intTerm  : intTerm TkMult intElement
              | intTerm TkMod intElement
              | intElement'''
  if (len(p) == 2):
    p[0] = p[1]

  elif (len(p) == 4) and p[2] == "*":
    term = p[1]
    element = p[3]
    def multElement(term = term, element = element):
      return term() * element()
    p[0] = multElement

  elif (len(p) == 4):
    term = p[1]
    element = p[3]
    def modElement(term = term, element = element):
      return term() % element()
    p[0] = modElement

def p_intElement(p):
  '''intElement : intId
                | intConst
                | TkOpenParent intExpression TkCloseParent'''
  if (len(p) == 2):
    p[0] = p[1]
  elif (len(p) == 4):
    p[0] = p[2]

def p_intId(p):
  # Verifica que un ID sea entero.
  '''intId : TkNId'''

  if ST.find("begin-task"):
    error = False

    # Si el ID indicado no existe, error.
    if not ST.findNotGlobal(p[1]):
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' no definido." % \
        (pos[0], pos[1], p[1])
      )
      error = True

    # Si el ID indicado no es entero, error.
    elif ST.find(p[1]).elementType != "Integer":
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tSe debe operar con una variable del tipo Integer." % \
        (pos[0], pos[1])
      )
      error = True

    if not error:
      var = ST.find(p[1])
      def integer(var = var):
        return var.data
      p[0] = integer 

def p_intConst(p):
  '''intConst : TkNum'''
  num = p[1]
  def integer(num = int(num)):
    return num
  p[0] = integer



########################### TASKS ###########################
# TASK DEFINITION
def p_beginTask(p):
  # Permite definir una tarea.
  '''beginTask : beginT endT'''

def p_beginT(p):
    # Permite crear un nuevo contexto para la tarea actual una vez inicializada.
    '''beginT : TkBeginTask'''

    # Obtenemos la informacion del scenario.
    scenario = ST.find("begin-scenario")
    # Imprimimos el mapa en su estado original.
    toExec.append(scenario.printData)
    # El nuevo contexto de la tarea sera el contexto del scenario.
    context = scenario.context
    ST.push_empty_table()
    # Creamos un nuevo task.
    newTask = Task(scenario)
    newTask.scopeId = ST.scopeId
    ST.scopeId += 1
    # Insertamos el task en la tabla de simbolos.
    ST.insert(newTask)
    # Agregamos cada simbolo del contexto a la tabla de simbolos.
    for c in context:
        ST.insert(c)

def p_endT(p):
  # Permite actualizar la informacion del mundo dada su definicion, y agrega 
  # el symbolo al contexto global.
  '''endT : taskInstruction TkEndTask
          | TkEndTask'''

  # El condicional 'if ST.find("begin-task")' se usara constantemente en
  # las producciones de la tarea, y verifica que se haya creado correctamente
  # la tarea al inicio. Si no se creo correctamente, simplemente ignora todas
  # las definiciones de la tarea y retornara el error 'ID ya definido'.
  if ST.find("begin-task"):
    table = ST.pop()

    # Como el simbolo de la tarea siempre es el que se crea de primero,
    # entonces toda la informacion de la tarea esta en la primera posicion
    # de la tabla.
    task = table.pop(0)
    scenario = task.scenario
    if len(p) == 3:
      task.instructions = p[1]
      toExec.append(p[1])

    toExec.append(notTerminate)

    # Imprimimos el mapa en su estado final.
    def printMap(scenario = scenario):
      scenario.printData()
    toExec.append(printMap)
    ST.insert(task)

  else: ST.pop()

# TASK'S INSTRUCTIONS
def p_taskInstruction(p):
  # Permite concatenar instrucciones de la tarea.
  '''taskInstruction  : taskInstruction instruction
                      | taskInstruction TkSemiColon
                      | instruction
                      | TkSemiColon'''
  if len(p) == 2 and p[1] != ";":
    p[0] = p[1]
  elif len(p) == 2 and p[1] == ";":
    p[0] = skip
  elif p[2] == ";":
    p[0] = p[1]
  else:
    task = p[1]
    instruction = p[2]
    def conc(task = task, instruction = instruction):
      task();  instruction()
    p[0] = conc

def p_instruction(p):
  # Conjunto de instrucciones. Las reglas del tipo 'willyInstructionN'
  # indican las istrucciones basicas con N tokens.
  '''instruction  : assignBool
                  | assignInt
                  | if
                  | repeat
                  | while
                  | beginInstruction
                  | defineInstruction
                  | willyInstruction'''
  p[0] = p[1]

# ASSIGNMENTS
def p_assignBool(p):
  '''assignBool : TkId TkEqual boolExpression'''
  if ST.find("begin-task"):
    error = False

    # Si el ID indicado no existe, error.
    if not ST.findNotGlobal(p[1]):
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' no definido." % \
        (pos[0], pos[1], p[1])
      )
      error = True

    # Si el ID indicado no es booleano, error.
    elif ST.find(p[1]).elementType != "Boolean":
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tSe debe operar con una variable del tipo Boolean." % \
        (pos[0], pos[1])
      )
      error = True

    if not error:
      var = ST.find(p[1])
      def assingBoolean(var = var, expression = p[3]):
        var.data = expression()
      p[0] = assingBoolean

def p_assignInt(p):
  '''assignInt : TkNId TkEqual intExpression'''
  if ST.find("begin-task"):
    error = False

    # Si el ID indicado no existe, error.
    if not ST.findNotGlobal(p[1]):
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' no definido." % \
        (pos[0], pos[1], p[1])
      )
      error = True

    # Si el ID indicado no es entero, error.
    elif ST.find(p[1]).elementType != "Integer":
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tSe debe operar con una variable del tipo Integer." % \
        (pos[0], pos[1])
      )
      error = True

    if not error:
      var = ST.find(p[1])
      def assingInt(var = var, expression = p[3]):\
        var.data = expression()
      p[0] = assingInt

# BLOCKS
def p_if(p):
  # Define el condicional if.
  '''if   : TkIf boolExpression TkThen instruction
          | TkIf boolExpression TkThen instruction TkElse instruction'''
  if ST.find("begin-task"):
    expression = p[2]
    inst = p[4]

    if len(p) == 5:
      def cond(expression = expression, inst = inst):
        if expression() and not ST.terminate: inst()
    else:
      inst2 = p[6]
      def cond(expression = expression, inst = inst, inst2 = inst2):
        if expression() and not ST.terminate: inst()
        elif not ST.terminate: inst2()
    p[0] = cond
    
def p_repeat(p):
  # Define el ciclo repeat.
  '''repeat : TkRepeat TkNum TkTimes instruction'''
  
  if ST.find("begin-task"):
    # Obtenemos la identacion correcta.
    num = int(p[2])
    func = p[4]
    def repeat(num = num, func = func):
      if not ST.terminate:
        for i in range(num): func()
    p[0] = repeat

def p_while(p):
  # Define el ciclo repeat.
  '''while : TkWhile boolExpression TkDo instruction'''
  
  if ST.find("begin-task"):
    expression = p[2]
    instruction = p[4]
    def loop(expression = expression, instruction = instruction):
      while expression() and not ST.terminate: instruction()
    p[0] = loop

def p_beginInstruction(p):
  # Permite colocar bloques de instrucciones.
  '''beginInstruction : TkBegin taskInstruction TkEnd 
                      | TkBegin TkEnd'''

  if ST.find("begin-task"):
    if len(p) == 3: p[0] = skip
    else: p[0] = p[2]

# DEFINE
def p_defineInstruction(p):
  # Permiter definir instrucciones dado un ID.
  '''defineInstruction : startDefine instDefine'''
  p[0] = skip

def p_startDefine(p):
  # Permite entrar en un nuevo contexto al definir una instruccion.
  '''startDefine : TkDefine TkId'''

  if ST.find("begin-task"):
    error = False

    if ST.findNotGlobal(p[2], ST.head):
      pos = getPosition(p.lexpos(2), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' ya definido." % \
        (pos[0], pos[1], p[2])
      )
      error = True

    # Si el head de la tabla de simbolos es mayor que 1, significa que
    # estamos dentro de un define, por lo que va a haber una variable
    # falsa foo, asi que momentaneamente hacemos que el ID de esa variable
    # sea vacia.
    elif ST.head > 1:
      fooId = ST.tables[ST.head][0].id
      ST.tables[ST.head][0].id = ""
      if ST.findNotGlobal(p[2], ST.head):
        pos = getPosition(p.lexpos(2), tokensList)
        contextErrors.append(
          "Linea %d, columna %d:\tID '%s' ya definido." % \
          (pos[0], pos[1], p[2])
        )
        error = True
      ST.tables[ST.head][0].id = fooId


    if not error:
      # Creamos una nueva variable del tipo Instruction y actualizamos sus datos.
      newInstruction = Variable("define", "define", "", "Instructions")
      newInstruction.scopeId = ST.scopeId
      newInstruction.name = p[2]
      newInstruction.declarationBlock = ST.declarationBlock

      # Actualizamos el scopeId/declarationBlock.
      ST.declarationBlock = ST.scopeId
      ST.scopeId += 1

      # Insertamos la instruction a la tabla de simbolos.
      ST.insert(newInstruction)
      task = ST.find("begin-task")
      task.context.append(newInstruction)
      ST.push_empty_table()

      # Insertamos una variable falsa para que esta instruccion pueda ser llamada
      # desde dentro de su definicion
      foo = Variable(p[2], "define", skip, "Instructions")
      foo.id = foo.name
      foo.scopeId = ST.scopeId-1
      ST.insert(foo)

def p_instDefine(p):
  # Permite definir una instruccion y luego regresar al contexto anterior.
  '''instDefine : TkAs instruction'''

  if ST.find("begin-task") and ST.findNotGlobal("define", level=ST.head-1):
    # Obtenemos las instrucciones definidas dentro del define.
    instructions = ST.pop()
    # Removemos la variable falsa
    instructions.pop(0)

    # Actualizamos la informacion de la instruccion definida.
    newInstruction = ST.findNotGlobal("define", level=ST.head)
    newInstruction.data = p[2]
    newInstruction.id = newInstruction.name

    # Actualizamos el declarationBlock.
    ST.declarationBlock = newInstruction.declarationBlock

# BASIC INSTRUCTIONS
def p_willyInstruction(p):
  # Instrucciones basicas.
  '''willyInstruction : TkMove TkSemiColon
                      | TkTurnL TkSemiColon
                      | TkTurnR TkSemiColon
                      | TkTake TkSemiColon
                      | TkDrop TkSemiColon
                      | TkLevel TkNum TkSemiColon
                      | TkIdentify TkSemiColon
                      | TkTerminate TkSemiColon
                      | willyInstructionId TkSemiColon'''
  
  if ST.find("begin-task"):
    scenario = ST.find("begin-task").scenario
    pos = getPosition(p.lexpos(1), tokensList)

    if p[1] == "move":
      def move(scenario = scenario, errX = pos[0], errY = pos[1]):
        if not ST.terminate:
          willy = scenario.willy
          scenarioMap = scenario.scenarioMap
          x, y, orientation = willy.x, willy.y, willy.look
          block = False

          if orientation == "north" and y > 0:
            if len(scenarioMap[y-1][x]) > 0: block = True
            else: willy.y -= 1

          elif orientation == "south" and y < len(scenarioMap)-1:
            if len(scenarioMap[y+1][x]) > 0: block = True
            else: willy.y += 1

          elif orientation == "east" and x < len(scenarioMap[0])-1:
            if len(scenarioMap[y][x+1]) > 0: block = True
            elif y == 0 and 3 <= x <= 18:
              contextErrors.append(
                ("Linea %d, columna %d:\tNo se puede mover a Willy de " +\
                  "orma horizontal en la zona frente a los estantes.") % \
                (errX, errY)
              )
              ST.terminate = True
            else: willy.x += 1

          elif orientation == "west" and x > 0:
            if len(scenarioMap[y][x-1]) > 0: block = True
            elif y == 0 and 3 <= x <= 18:
              contextErrors.append(
                ("Linea %d, columna %d:\tNo se puede mover a Willy de " +\
                  "orma horizontal en la zona frente a los estantes.") % \
                (errX, errY)
              )
              ST.terminate = True
            else: willy.x -= 1

          else:
            contextErrors.append(
              ("Linea %d, columna %d:\tNo se puede mover a Willy fuera " +\
                "del mapa.") % \
              (errX, errY)
            )
            ST.terminate = True
          
          if block:
            contextErrors.append(
              ("Linea %d, columna %d:\tNo se puede mover a Willy hacia " +\
                "un bloque.") % \
              (errX, errY)
            )
            ST.terminate = True

          scenario.printData()
      p[0] = move

    elif p[1] == "turn-left":
      willy = scenario.willy
      def turn(willy = willy):
        if not ST.terminate:
          orientation = willy.look
          if orientation == "north": willy.look = "west"
          elif orientation == "south": willy.look = "east"
          elif orientation == "east": willy.look = "north"
          elif orientation == "west": willy.look = "south"
          scenario.printData()
      p[0] = turn

    elif p[1] == "turn-right":
      willy = scenario.willy
      def turn(willy = willy):
        if not ST.terminate:
          orientation = willy.look
          if orientation == "north": willy.look = "east"
          elif orientation == "south": willy.look = "west"
          elif orientation == "east": willy.look = "south"
          elif orientation == "west": willy.look = "north"
          scenario.printData()
      p[0] = turn

    elif p[1] == "take":
      def take(scenario = scenario, errX = pos[0], errY = pos[1]):
        if not ST.terminate:
          willy = scenario.willy
          scenarioMap = scenario.scenarioMap
          x, y, orientation = willy.x, willy.y, willy.look
          block = True

          if willy.level != 0:
            contextErrors.append(
              ("Linea %d, columna %d:\tWilly debe tener la grua en el nivel " +\
                "0 para poder tomar un bloque.") % \
              (errX, errY)
            )
            ST.terminate = True

          elif orientation == "north" and y > 0:
            if len(scenarioMap[y-1][x]) == 0: block = False
            else: willy.block = scenarioMap[y-1][x].pop()

          elif orientation == "south" and y < len(scenarioMap)-1:
            if len(scenarioMap[y+1][x]) == 0: block = False
            else: willy.block = scenarioMap[y+1][x].pop()

          elif orientation == "east" and x < len(scenarioMap[0])-1:
            if len(scenarioMap[y][x+1]) == 0: block = False
            else: willy.block = scenarioMap[y][x+1].pop()

          elif orientation == "west" and x > 0:
            if len(scenarioMap[y][x-1]) == 0: block = False
            else: willy.block = scenarioMap[y][x-1].pop()

          else:
            contextErrors.append(
              ("Linea %d, columna %d:\tNo hay ningun bloque frente a Willy.") % \
              (errX, errY)
            )
            ST.terminate = True
          
          if not block:
            contextErrors.append(
              ("Linea %d, columna %d:\tNo hay ningun bloque frente a Willy.") % \
              (errX, errY)
            )
            ST.terminate = True
      p[0] = take

    elif p[1] == "drop":
      def drop(scenario = scenario, errX = pos[0], errY = pos[1]):
        if not ST.terminate:
          willy = scenario.willy
          scenarioMap = scenario.scenarioMap
          x, y, orientation = willy.x, willy.y, willy.look

          if willy.block == None:
            contextErrors.append(
              ("Linea %d, columna %d:\tWilly debe tener un bloque.") % \
              (errX, errY)
            )
            ST.terminate = True

          elif not (y == 0 and 3 <= x <= 18 and orientation == "north") and \
            not (y == 18 and orientation == "south"):
            contextErrors.append(
              ("Linea %d, columna %d:\tWilly debe estar en frente del estante o " +\
                "de la zona de descarga para poder soltar un bloque.") % \
              (errX, errY)
            )
            ST.terminate = True

          elif y == 18 and orientation == "south":
            if willy.level != 0:
              contextErrors.append(
                ("Linea %d, columna %d:\tWilly debe tener la grua en el nivel " +\
                  "0 para poder soltar un bloque en la zona de descarga.") % \
                (errX, errY)
              )
              ST.terminate = True
            elif x%3 == 0:
              contextErrors.append(
                ("Linea %d, columna %d:\tNo se puede colocar un bloque en el " +\
                  "borde entre dos zonas de descarga") % \
                (errX, errY)
              )
              ST.terminate = True
            else:
              scenario.unRegions[int(x/3)] += 1
              willy.block = None

          else:
            block = willy.block
            if block[0] == "B": num = int(block[1:])
            else: num = int(block)
            
            if x%3 == 0:
              contextErrors.append(
                ("Linea %d, columna %d:\tNo se puede colocar un bloque en el " +\
                  "borde entre casillas") % \
                (errX, errY)
              )
              ST.terminate = True
            if num != 5*willy.level + int(x/3):
              contextErrors.append(
                ("Linea %d, columna %d:\tSe coloco un bloque de numero " +\
                  "%d en la casilla de numero %d") % \
                (errX, errY, num, 5*willy.level + int(x/3))
              )
              ST.terminate = True

            scenario.shelves[willy.level][int(x/3)-1] += 1
            willy.block = None
      p[0] = drop
      
    elif p[1] == "identify":
      def identify(scenario = scenario, errX = pos[0], errY = pos[1]):
        willy = scenario.willy
        scenarioMap = scenario.scenarioMap
        x, y, orientation = willy.x, willy.y, willy.look

        if not (orientation == "north" and y == 0) and\
          not (orientation == "south" and y == len(scenarioMap)) and\
          not (orientation == "east" and x == len(scenarioMap[0])) and\
          not (orientation == "west" and x == 0):

          if orientation == "north" and len(scenarioMap[y-1][x]) > 0:
            willy.blockId = scenarioMap[y-1][x][0]
          elif orientation == "south" and len(scenarioMap[y+1][x]) > 0:
            willy.blockId = scenarioMap[y+1][x][0]
          elif orientation == "east" and len(scenarioMap[y][x+1]) > 0:
            willy.blockId = scenarioMap[y][x+1][0]
          elif orientation == "west" and len(scenarioMap[y][x-1]) > 0:
            willy.blockId = scenarioMap[y][x-1][0]
      p[0] = identify

    elif p[1] == "terminate":
        p[0] = terminate
    
    elif p[1] == "level":
      willy = scenario.willy
      def level(willy = willy, level = p[2]):
        if level < 0 or level > 2:
          contextErrors.append(
            ("Linea %d, columna %d:\tWilly solo tiene los niveles 0-2 " +\
              "para la grua.") % \
            (errX, errY)
          )
          ST.terminate = True
        else: willy.level = level
      p[0] = level

    else: p[0] = p[1]

def p_willyInstructionId(p):
  # Verifica que el ID indicado sea una instruccion.
  '''willyInstructionId : TkId'''

  if ST.find("begin-task"):
    error = False

    instruction = ST.findNotGlobal(p[1])
    # Si el ID indicado no existe, error.
    if not instruction:
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tID '%s' no definido." % \
        (pos[0], pos[1], p[1])
      )
      error = True

    # En cambio si no es una instruccion, error.
    elif instruction.elementType != "define":
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tSe debe colocar un elemento del tipo Instruction." % \
        (pos[0], pos[1])
      )
      error = True

    if not error:
      task = ST.find("begin-task")
      def execId(task = task, ID = p[1], scopeID = instruction.scopeId):
        for e in task.context:
          if e.id == ID and scopeID == e.scopeId: e.data()
      p[0] = execId 



########################### IGNORED TOKENS ###########################
def p_empty(p):
  'empty :  '

def p_ignore(p):
  '''ignore : TkTab
            | TkNewLine
            | TkLineComment
            | TkBlockComment
            | TkSpace'''

def p_error(p):
  """ Token de error. """
  if p != None:
    pos = getPosition(p.lexpos, tokensList)
    syntax.append(
      "Linea %d, columna %d:\tError de sintaxis." % (pos[0], pos[1]) + "\n" +
      "\t> " + getLine(text, p.lexpos) + "\n"
      "\t" + " "*(pos[1] + 1) + "^"
    )
    p.lexer.skip(1)
    
    syntax[0] = False
  else:
    syntax.append(
      "Error de sintaxis."
    )
    syntax[0] = False



########################### PRECEDENCE ###########################
precedence = (
    # Precedencia de los if/else.
    ('left', 'TkThen'),
    ('left', 'TkElse'),

    # Precedencia de los operadores booleanos.
    ('left', 'TkEquiv'),
    ('left', 'TkNotEqual'),
    ('left', 'TkOr'),
    ('left', 'TkAnd'),
    ('left', 'TkNot'),

    # Precedencia de los operadores numericos enteros.
    ('left', 'TkPlus'),
    ('left', 'TkMinus'),
    ('left', 'TkMult'),
)

# Build the parser
yacc.yacc()


if __name__ == "__main__":
  # Obtenemos el texto
  file = open(argv[1], 'r')
  text = file.read()
  file.close()

  # Ejecutamos el lexer. Agregamos un salto de linea al final para que se puedan
  # reconocer los comentarios de linea en la ultima linea.
  lexerErrors = lexer(text + "\n")

  # Verificamos si hay errores en el lexer.
  if len(lexerErrors) < 1:
    result = yacc.parse(text)

    # Verificamos si hay errores de sintaxis.
    if not syntax[0]:
      # Imprimimos errores de contexto.
      print("\033[1mErrores encontrados:\033[0m")
      print(syntax[1])

    # Verificamos si hay errores de conexto.
    elif len(contextErrors) > 0:
      # Imprimimos errores de contexto.
      print("\033[1mErrores encontrados:\033[0m")
      for e in contextErrors:
        print(e)

    # No hay errores, asi que ejecutamos el programa.
    else:
      for e in toExec:
        # Verificamos si despues de ejecutar cada instruccion ocurren errores.
        if len(contextErrors) < 1: e()
        else: break

      # Si hay errores durante la ejecucion, se imprimen.
      if len(contextErrors) > 0:
        # Imprimimos errores de contexto.
        print("\033[1mErrores encontrados:\033[0m")
        for e in contextErrors:
          print(e)

  else:
    # Imprimimos los errores del lexer.
    print("\033[1mErrores encontrados:\033[0m")
    for e in lexerErrors:
      print(
        "Linea %d, columna %d:\tCaracter ilegal %s" % \
        (e.lineno, getColumn(text, e.lexpos), e.value[0])
      )

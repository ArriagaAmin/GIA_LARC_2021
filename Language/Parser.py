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

class Scenario:
  """ Clase que guarda la informacion de un scenario en el lenguaje Willy*. """
  def __init__(self):
    self.id = "begin-scenario"
    # Mapa
    self.scenarioMap = [[[] for _ in range(22)] for _ in range(22)]
    # Conjunto de symbolos definidos en el scenario.
    self.context = [] 
    # Informacion de Willy del scenario.
    self.willy = Willy() 
  
class Task:
  """ Clase que guarda la informacion de una tarea en el lenguaje Willy*. """
  def __init__(self, scenario):
    self.id = "begin-task"
    self.elementType = "Task"

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
  '''beginScenario  : beginS scenarioInstructions endS
                    | beginS endS'''

def p_beginS(p):
  # Permite crear un nuevo contexto para el scenario actual una vez inicializado. 
  '''beginS : TkBeginScenario'''
  ST.push_empty_table()
  ST.insert( Scenario() )

def p_endS(p):
  # Permite actualizar la informacion del escenario dada su definicion, y 
  # agrega el symbolo al contexto global.
  '''endS : TkEndScenario'''

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
                          | scenarioInstruction'''

def p_scenarioInstruction(p):
  # Instrucciones del escenario.
  '''scenarioInstruction  : placeBlock
                          | startAt
                          | boolean
                          | integer
                          | TkSemiColon'''

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
    if p[2] > 21:
        pos = getPosition(p.lexpos(2), tokensList)
        contextErrors.append(
          "Linea %d, columna %d:\tSe indico una fila superior a la 21 %d." % \
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
    '''placeBlock : TkPlaceBlock TkNum position TkSemiColon
                  | TkPlaceBlock TkBNum position TkSemiColon
                  | TkPlaceBlock color position TkSemiColon'''

    if ST.find("begin-scenario"):
        error = p[3][0]

        # Cantidad a colocar, ID del objeto y posicion donde se desea ubicar.
        block, x, y = p[2], p[3][1], p[3][2]
        # Obtenemos el mapa
        scenarioMap = ST.find("begin-scenario").scenarioMap

        # Si en la ubicacion indicada hay otro bloque, error.
        if not error and len(scenarioMap[rows - y - 1][x]) > 0:
          pos = getPosition(p.lexpos(1), tokensList)
          contextErrors.append(
            "Linea %d, columna %d:\tYa se coloco un bloque en esa posicion." % \
            (pos[0], pos[1])
          )
          error = True

        if not error:
          scenarioMap[rows - y - 1][x].append(block)

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
    if not error and len(scenarioMap[rows - y - 1][x]) > 0:
      pos = getPosition(p.lexpos(1), tokensList)
      contextErrors.append(
        "Linea %d, columna %d:\tNo se puede colocar a Willy encima de un bloque" % \
        (pos[0], pos[1])
      )
      error = True

    if not error:
      # Actualizamos la informacion de Willy.
      willy.x, willy.y, willy.look = x, rows-y-1, look

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
  '''integer : TkInteger TkId TkEqual TkNum TkSemiColon'''

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
  if (len(p) == 2) and (p[1] != None):
    p[0] = p[1]
  elif len(p) == 4:
    if (p[2] == "==") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() == term()
      p[0] = equivTerm

    elif (p[2] == "!=") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() != term()
      p[0] = equivTerm

def p_boolTerm(p):
  '''boolTerm : boolTerm TkAnd boolFactor
              | boolTerm TkOr boolFactor
              | boolFactor'''
  if (len(p) == 2) and (p[1] != None):
    p[0] = p[1]
  elif len(p) == 4:
    if (p[2] == "and") and (p[1] != None) and (p[3] != None):
      term = p[1]
      factor = p[3]
      def andFactor(term = term, factor = factor):
        return factor() and term()
      p[0] = andFactor

    elif (p[2] == "or") and (p[1] != None) and (p[3] != None):
      term = p[1]
      factor = p[3]
      def orFactor(term = term, factor = factor):
        return term() or factor()
      p[0] = orFactor

def p_boolFactor(p):
  '''boolFactor : TkNot boolElement
                | boolElement'''
  if (len(p) == 2) and p[1] != None:
    p[0] = p[1]
  elif (len(p) == 3):
    if p[2] != None:
      factor = p[2]
      def notFactor(factor = factor):
        return not factor()
      p[0] = notFactor

def p_boolElement(p):
  '''boolElement  : boolId
                  | boolIntExpression
                  | TkOpenParent boolExpression TkCloseParent'''
  if (len(p) == 2) and p[1] != None:
    p[0] = p[1]
  elif (len(p) == 4):
    if p[2] != None:
      p[0] = p[2]

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
  '''boolExpression : intExpression TkEquiv intExpression
                    | intExpression TkNotEqual intExpression
                    | intExpression TkLessT intExpression
                    | intExpression TkLessEq intExpression
                    | intExpression TkGreatT intExpression
                    | intExpression TkGreatEq intExpression'''

  if (len(p) == 2) and (p[1] != None):
    p[0] = p[1]
  elif len(p) == 4:
    if (p[2] == "==") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() == term()
      p[0] = equivTerm

    elif (p[2] == "!=") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() != term()
      p[0] = equivTerm

    elif (p[2] == "<") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() < term()
      p[0] = equivTerm

    elif (p[2] == "<=") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() <= term()
      p[0] = equivTerm
    
    elif (p[2] == ">") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() > term()
      p[0] = equivTerm

    elif (p[2] == ">=") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() >= term()
      p[0] = equivTerm



########################### INTEGER EXPRESSIONS ###########################
def p_intExpression(p):
  '''intExpression  : intExpression TkPlus intTerm
                    | intExpression TkMinus intTerm
                    | intTerm
  '''
  if (len(p) == 2) and (p[1] != None):
    p[0] = p[1]
  elif len(p) == 4:
    if (p[2] == "+") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() + term()
      p[0] = equivTerm

    elif (p[2] == "-") and (p[1] != None) and (p[3] != None):
      expression = p[1]
      term = p[3]
      def equivTerm(expression = expression, term = term):
        return expression() - term()
      p[0] = equivTerm

def p_intTerm(p):
  '''intTerm  : intTerm TkMult intElement
              | intElement'''
  if (len(p) == 2) and p[1] != None:
    p[0] = p[1]
  elif (len(p) == 3):
    if p[2] != None:
      element = p[2]
      def multElement(term = term, element = element):
        return term() * element()
      p[0] = multElement

def p_intElement(p):
  '''intElement : intId
                | intConst
                | TkOpenParent intExpression TkCloseParent'''
  if (len(p) == 2) and p[1] != None:
    p[0] = p[1]
  elif (len(p) == 4):
    if p[2] != None:
      p[0] = p[2]

def p_intId(p):
  # Verifica que un ID sea entero.
  '''intId : TkId'''

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
  '''instruction  : if
                  | repeat
                  | while
                  | defineInstruction
                  | beginInstruction
                  | willyInstruction'''
  p[0] = p[1]

# BASIC INSTRUCTIONS
def p_willyInstruction(p):
  # Instrucciones basicas.
  '''willyInstruction : TkMove TkSemiColon
                      | TkTurnLeft TkSemiColon
                      | TkTurnRight TkSemiColon
                      | TkDetectLeft TkSemiColon
                      | TkDetectRight TkSemiColon
                      | TkDetectFront TkSemiColon
                      | TkIdentify TkSemiColon
                      | TkTake TkSemiColon
                      | TkDrop TkSemiColon
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

          if orientation == "north" and y > 0:
            if len(scenarioMap[y-1][x]) > 0: block = True
            else: willy.y -= 1

          elif orientation == "south" and y < len(scenarioMap)-1:
            if len(scenarioMap[y+1][x]) > 0: block = True
            else: willy.y += 1

          elif orientation == "east" and x < len(scenarioMap[0])-1:
            if len(scenarioMap[y][x+1]) > 0: block = True
            else: willy.x += 1

          elif orientation == "west" and x > 0:
            if len(scenarioMap[y][x-1]) > 0: block = True
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
          world.printData()
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
          world.printData()
      p[0] = turn

    elif p[1] == "detect-left":
      def move(scenario = scenario, errX = pos[0], errY = pos[1]):
        if not ST.terminate:
          willy = scenario.willy
          scenarioMap = scenario.scenarioMap
          x, y, orientation = willy.x, willy.y, willy.look

          if orientation == "north":
            if x == 0: p[0] = False
            elif scenarioMap[y][x-1] == []: p[0] = False
            else: p[0] = True

          elif orientation == "south":
            if len(scenarioMap[y+1][x]) > 0: block = True
            else: willy.y += 1

          elif orientation == "east":
            if len(scenarioMap[y][x+1]) > 0: block = True
            else: willy.x += 1

          elif orientation == "west":
            if len(scenarioMap[y][x-1]) > 0: block = True
            else: willy.x -= 1
      p[0] = detect

    elif p[1] == "terminate":
        p[0] = terminate
    
    else:
        p[0] = p[1]

def p_willyInstruction3(p):
    # Instrucciones basicas con 3 tokens.
    '''willyInstruction3    : TkPick TkId TkSemiColon
                            | TkDrop TkId TkSemiColon
                            | TkSet TkId TkSemiColon
                            | TkClear TkId TkSemiColon
                            | TkFlip TkId TkSemiColon'''
    if ST.find("begin-task"):
        error = False

        if ST.findNotGlobal(p[2]):
            # Si la accion es pick o drop, verificamos que el ID sea un Object-type.
            if p[1] in ["pick", "drop"]:
                if ST.find(p[2]).elementType != "Object-type":
                    pos = getPosition(p.lexpos(2), tokensList)
                    contextErrors.append(
                        "Linea %d, columna %d:\tSe debe colocar un elemento del tipo Object-type." % \
                        (pos[0], pos[1])
                    )
                    error = True

            # En cambio, verificamos que el ID sea un booleano.
            else:
                if ST.find(p[2]).elementType != "Boolean":
                    pos = getPosition(p.lexpos(2), tokensList)
                    contextErrors.append(
                        "Linea %d, columna %d:\tSe debe colocar un elemento del tipo Boolean." % \
                        (pos[0], pos[1])
                    )
                    error = True

        # Si el ID definido no existe, error.
        else:
            pos = getPosition(p.lexpos(2), tokensList)
            contextErrors.append(
                "Linea %d, columna %d:\tID '%s' no definido." % \
                (pos[0], pos[1], p[2])
            )
            error = True

        if not error:
            world = ST.find("begin-task").world
            objectId = p[2]
            var = ST.find(p[2])
            pos = getPosition(p.lexpos(1), tokensList)

            if p[1] == "pick":
                def pick(world = world, objectId = objectId, var = var, errX = pos[0], errY = pos[1]):
                    if not ST.terminate:
                        willy = world.willy
                        worldMap = world.worldMap
                        x, y = willy.x, willy.y
                        num = 0

                        if willy.basketObjects < willy.basketCapacity:
                            for i in range(len(worldMap[y][x])):
                                # Verificamos si el objeto ya se encuentran en la posicion indicada
                                # del mapa. En caso afirmativo, solo sumamos las cantidades.
                                if worldMap[y][x][i][0] == objectId:
                                    worldMap[y][x][i][1] -= 1
                                    if worldMap[y][x][i][1] == 0:
                                        worldMap[y][x].pop(i)

                                    num = 1
                                    break
                                

                            if num == 1:
                                willy.basketObjects += 1

                                for i in range(len(willy.basketContent)):
                                    # Verificamos si el objeto ya  se encuentran en la cesta. 
                                    # En caso afirmativo, solo sumamos las cantidades.
                                    if willy.basketContent[i][0].id == objectId:
                                        willy.basketContent[i][1] += 1
                                        num = 0

                                # Si no se encuentra, agregamos a la cesta el objeto
                                # y la cantidad que se desea colocar.
                                if num != 0:
                                    willy.basketContent.append([var, 1])

                            else:
                                contextErrors.append(
                                    ("Linea %d, columna %d:\tNo se puede agarrar un objeto que " +\
                                        "no se encuentra en la casilla actual.") % \
                                    (errX, errY)
                                )
                                ST.seconds = 0.01
                                ST.terminate = True

                        else:
                            contextErrors.append(
                                ("Linea %d, columna %d:\tSe supero la capacidad de la cesta " +\
                                    "de Willy.") % \
                                (errX, errY)
                            )
                            ST.seconds = 0.01
                            ST.terminate = True

                        world.printData()
                p[0] = pick
                
            elif p[1] == "drop":
                def drop(world = world, objectId = objectId, var = var, errX = pos[0], errY = pos[1]):
                    if not ST.terminate:
                        willy = world.willy
                        worldMap = world.worldMap
                        x, y = willy.x, willy.y
                        num = 0
                        for i in range(len(willy.basketContent)):
                            # Verificamos si el objeto ya  se encuentran en la cesta. 
                            # En caso afirmativo, solo sumamos las cantidades.
                            if willy.basketContent[i][0].id == objectId:
                                willy.basketContent[i][1] -= 1
                                if willy.basketContent[i][1] == 0:
                                    willy.basketContent.pop(i)
                                num = 1
                                break

                        if num == 1:
                            willy.basketObjects -= 1

                            for i in range(len(worldMap[y][x])):
                                # Verificamos si el objeto ya se encuentran en la posicion indicada
                                # del mapa. En caso afirmativo, solo sumamos las cantidades.
                                if worldMap[y][x][i][0] == objectId:
                                    worldMap[y][x][i][1] += 1
                                    num = 0

                            # Si no se encuentra, agregamos a la ubicacion en el mapa el objeto
                            # y la cantidad que se desea colocar.
                            if num != 0:
                                worldMap[y][x].append([objectId, 1])
                        else:
                            contextErrors.append(
                                ("Linea %d, columna %d:\tNo se puede soltar un objeto que " +\
                                    "no se encuentra en la cesta de Willy.") % \
                                (errX, errY)
                            )
                            ST.seconds = 0.01
                            ST.terminate = True

                        world.printData()
                p[0] = drop

            elif p[1] == "set":
                def setBool(var = var):
                    if not ST.terminate:
                        var.data = True
                p[0] = setBool

            elif p[1] == "clear":
                def clear(var = var):
                    if not ST.terminate:
                        var.data = False
                p[0] = clear

            else:
                def flip(var = var):
                    if not ST.terminate:
                        var.data = not var.data
                p[0] = flip

def p_willyInstruction5(p):
    # Instruccion basica con 5 tokens.
    '''willyInstruction5    : TkSet TkId TkTo testExpression TkSemiColon
                            | TkSet TkId TkTo TkTrue TkSemiColon
                            | TkSet TkId TkTo TkFalse TkSemiColon'''

    if ST.find("begin-task"):
        error = False

        if not (p[4] in ["true", "false"]):
            # Si el ID definido no existe, error.
            if not ST.findNotGlobal(p[2]):
                pos = getPosition(p.lexpos(2), tokensList)
                contextErrors.append(
                    "Linea %d, columna %d:\tID '%s' no definido." % \
                    (pos[0], pos[1], p[2])
                )
                error = True

            # En cambio si el ID no es booleano, error.
            elif ST.findNotGlobal(p[2]).elementType != "Boolean":
                pos = getPosition(p.lexpos(2), tokensList)
                contextErrors.append(
                    "Linea %d, columna %d:\tSe debe colocar un elemento del tipo Boolean." % \
                    (pos[0], pos[1])
                )
                error = True

            if not error:
                var = ST.findNotGlobal(p[2])
                expression = p[4]

                def setTo(var = var, expression = expression):
                    if not ST.terminate:
                        var.data = expression()

                p[0] = setTo
        
        else:
            var = ST.findNotGlobal(p[2])
            expression = (p[4] == "true")

            def setTo(var = var, expression = expression):
                if not ST.terminate:
                    var.data = expression

            p[0] = setTo

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
                    if e.id == ID and scopeID == e.scopeId:
                        e.data()
            p[0] = execId 


# BLOCKS
def p_if(p):
    # Define el condicional if.
    '''if   : TkIf testExpression TkThen instruction
            | TkIf testExpression TkThen instruction TkElse instruction'''
    if ST.find("begin-task"):
        expression = p[2]
        inst = p[4]

        if len(p) == 5:
            def cond(expression = expression, inst = inst):
                if expression() and not ST.terminate:
                    inst()
        else:
            inst2 = p[6]
            def cond(expression = expression, inst = inst, inst2 = inst2):
                if expression() and not ST.terminate:
                    inst()
                elif not ST.terminate:
                    inst2()

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
                for i in range(num):
                    func()

        p[0] = repeat

def p_while(p):
    # Define el ciclo repeat.
    '''while : TkWhile testExpression TkDo instruction'''
    
    if ST.find("begin-task"):
        expression = p[2]
        instruction = p[4]
        def loop(expression = expression, instruction = instruction):
            while expression() and not ST.terminate:
                instruction()

        p[0] = loop

def p_beginInstruction(p):
    # Permite colocar bloques de instrucciones.
    '''beginInstruction : TkBegin taskInstruction TkEnd TkSemiColon
                        | TkBegin taskInstruction TkEnd
                        | TkBegin TkEnd'''

    if ST.find("begin-task"):
        if len(p) == 3:
            p[0] = skip
        else:
            p[0] = p[2]


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

        # Si el head de la tabla de simbolos es mayor que 1, significa que
        # estamos dentro de un define, por lo que va a haber una variable
        # falsa foo, asi que momentaneamente hacemos que el ID de esa variable
        # sea vacia.
        if ST.head > 1:
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

        elif ST.findNotGlobal(p[2], ST.head):
            pos = getPosition(p.lexpos(2), tokensList)
            contextErrors.append(
                "Linea %d, columna %d:\tID '%s' ya definido." % \
                (pos[0], pos[1], p[2])
            )
            error = True


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


# TESTS EXPRESSIONS
def p_testExpression(p):
    '''testExpression   : testExpression TkAnd testTerm
                        | testExpression TkOr testTerm
                        | testTerm'''
    if len(p) == 2:
        p[0] = p[1]
    elif p[2] == "and":
        expression = p[1]
        term = p[3]
        def andTerm(expression = expression, term = term):
            return expression() and term()
        p[0] = andTerm
    else:
        expression = p[1]
        term = p[3]
        def orTerm(expression = expression, term = term):
            return expression() or term()
        p[0] = orTerm

def p_testTerm(p):
    '''testTerm : TkNot testFactor
                | testFactor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        factor = p[2]
        def notFactor(factor = factor):
            return not factor()
        p[0] = notFactor

def p_testFactor(p):
    '''testFactor   : frontClear
                    | leftClear
                    | rightClear
                    | lookingNorth
                    | lookingEast
                    | lookingSouth
                    | lookingWest
                    | foundCarrying
                    | TkOpenParent testExpression TkCloseParent
                    | boolId'''

    if ST.find("begin-task"):
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]

def p_frontClear(p):
    '''frontClear : TkFrontClear'''
    if ST.find("begin-task"):
        willy = ST.find("begin-task").world.willy
        worldMap = ST.find("begin-task").world.worldMap

        def frontClear(willy = willy, worldMap = worldMap):
            x, y, orientation = willy.x, willy.y, willy.look

            if orientation == "north" and y > 0:
                if not ["Wall"] in worldMap[y-1][x]:
                    return True 
                else:
                    return False

            elif orientation == "south" and y < len(worldMap)-1:
                if not ["Wall"] in worldMap[y+1][x]:
                    return True 
                else:
                    return False

            elif orientation == "east" and x < len(worldMap[0])-1:
                if not ["Wall"] in worldMap[y][x+1]:
                    return True 
                else:
                    return False

            elif orientation == "west" and x > 0:
                if not ["Wall"] in worldMap[y][x-1]:
                    return True 
                else:
                    return False
            
            else:
                return False
        p[0] = frontClear

def p_leftClear(p):
    '''leftClear : TkLeftClear'''
    if ST.find("begin-task"):
        willy = ST.find("begin-task").world.willy
        worldMap = ST.find("begin-task").world.worldMap

        def leftClear(willy = willy, worldMap = worldMap):
            x, y, orientation = willy.x, willy.y, willy.look
            if orientation == "east" and y > 0:
                if not ["Wall"] in worldMap[y-1][x]:
                    return True 
                else:
                    return False

            elif orientation == "west" and y < len(worldMap)-1:
                if not ["Wall"] in worldMap[y+1][x]:
                    return True 
                else:
                    return False

            elif orientation == "south" and x < len(worldMap[0])-1:
                if not ["Wall"] in worldMap[y][x+1]:
                    return True 
                else:
                    return False

            elif orientation == "north" and x > 0:
                if not ["Wall"] in worldMap[y][x-1]:
                    return True 
                else:
                    return False
            
            else:
                return False
        p[0] = leftClear

def p_rightClear(p):
    '''rightClear : TkRightClear'''
    if ST.find("begin-task"):
        willy = ST.find("begin-task").world.willy
        worldMap = ST.find("begin-task").world.worldMap

        def rigthClear(willy = willy, worldMap = worldMap):
            x, y, orientation = willy.x, willy.y, willy.look
            if orientation == "west" and y > 0:
                if not ["Wall"] in worldMap[y-1][x]:
                    return True 
                else:
                    return False

            elif orientation == "east" and y < len(worldMap)-1:
                if not ["Wall"] in worldMap[y+1][x]:
                    return True 
                else:
                    return False

            elif orientation == "north" and x < len(worldMap[0])-1:
                if not ["Wall"] in worldMap[y][x+1]:
                    return True 
                else:
                    return False

            elif orientation == "south" and x > 0:
                if not ["Wall"] in worldMap[y][x-1]:
                    return True 
                else:
                    return False
            
            else:
                return False
        p[0] = rigthClear

def p_lookingNorth(p):
    '''lookingNorth : TkLookingNorth'''
    if ST.find("begin-task"):
        willy = ST.find("begin-task").world.willy

        def looking(willy = willy):
            return (willy.look == "north")
        p[0] = looking

def p_lookingSouth(p):
    '''lookingSouth : TkLookingSouth'''
    if ST.find("begin-task"):
        willy = ST.find("begin-task").world.willy

        def looking(willy = willy):
            return (willy.look == "south") 
        p[0] = looking

def p_lookingEast(p):
    '''lookingEast : TkLookingEast'''
    if ST.find("begin-task"):
        willy = ST.find("begin-task").world.willy

        def looking(willy = willy):
            return (willy.look == "east")
        p[0] = looking

def p_lookingWest(p):
    '''lookingWest : TkLookingWest'''
    if ST.find("begin-task"):
        willy = ST.find("begin-task").world.willy

        def looking(willy = willy):
            return (willy.look == "west")
        p[0] = looking

def p_foundCarrying(p):
    '''foundCarrying    : TkFound TkOpenParent TkId TkCloseParent
                        | TkCarrying TkOpenParent TkId TkCloseParent'''

    if ST.find("begin-task"):
        error = False

        # Si el ID indicado no existe, error.
        if not ST.findNotGlobal(p[3]):
            pos = getPosition(p.lexpos(3), tokensList)
            contextErrors.append(
                "Linea %d, columna %d:\tID '%s' no definido." % \
                (pos[0], pos[1], p[3])
            )
            error = True

        # En cambio si no es un Object-type, error.
        elif ST.findNotGlobal(p[3]).elementType != "Object-type":
            pos = getPosition(p.lexpos(3), tokensList)
            contextErrors.append(
                "Linea %d, columna %d:\tSe debe colocar un elemento del tipo Object-type." % \
                (pos[0], pos[1])
            )
            error = True

        if (not error) and (p[1] == "found"):
            willy = ST.find("begin-task").world.willy
            worldMap = ST.find("begin-task").world.worldMap
            objectId = p[3]

            def found(willy = willy, worldMap = worldMap, objectId = objectId):
                x, y = willy.x, willy.y

                for m in worldMap[y][x]:
                    if m[0] == objectId:
                        return True

                return False
            p[0] = found

        elif (not error) and (p[1] == "carrying"):
            willy = ST.find("begin-task").world.willy
            objectId = p[3]

            def carrying(willy = willy, objectId = objectId):
                for i in range(len(willy.basketContent)):
                    if willy.basketContent[i][0].id == objectId:
                        return True

                return False
            p[0] = carrying

        elif error:
            p[0] = rFalse
# GIA_LARC_2021
Language to control the support robot for warehouse operations. LARC - OPEN Category 2021

## Rules
### Goal of robot
The robot can move freely in the scenario, but cannot collide or push a package out of the package's area. To reach the challenges of the competition, the robot has to take each package and take it to its destination. The objective is to take packages from a specific location and take them to predefined locations, so that, at the end, the packages are in a desired arrangement in the proposed scenario. The specific objectives are:
1. Take colored packages (yellow, red, green, blue) and take them to the unloading regions with equivalent colors.
2. Pick up packages containing bar codes and take them to their respective positions on the shelves.
3. Take the packages with numerical values and take them to their respective positions on the shelves.

### Package
Packages can be marked by color, barcode or numeric. The possible colors for the packages are: green, yellow, blue and red. The barcode is a simple representation containing only 16 possible combinations, in binary, from zero (0000) to 15 (1111). There is a specific region in the scenario where the packages are initially positioned, called the loading region. The numerical packages are white and the barcode packages are black.

### Scenario
Each package has a tag that identifies it and, consequently, its destination or destination region. The scenario basically contains three types of regions: transit region, package loading region and package unloading region. The scenario is formed by 49 (7x7) squares for free circulation of the robot, for loading and unloading packages. The package loading region consists in two areas centralized in the scenario. Each area consists of four squares: {(3,2), (3,3), (4,2), (4,3)} and {(3,5), (3,6), (4,5), (4,6)}.

## Language
A program in the language consists of instructions of two different types. The first type of instructions define the scenario. A scenario indicates the initial conditions on which the control programs run. The second type of instructions define a main program and, if necessary, additional procedures that can be invoked from the main program.

### Defining a Scenario
A scenario is described with a block of the form

```begin-scenario <instructions>∗ end-scenario```

A containing zero or more instructions ending in ';'. Each square occupies a space of 4x4 coordinates (including the edges), so in total there are 22x22 coordinates of the shape (X, Y) with 0 <= X, Y <= 21. The instructions that define the scenario are the following:

  * ```Start at <M> <N> heading <direction>``` 

    Define Willy's initial position and orientation with 0 <= ```<M>```, ```<N>``` <= 21. The direction is one in north, east, south, or west. If this instruction is not specified, Willy will initially be located at position 0, 0 facing north.

  * ```Place block <type> at <M> <N>```
  
    Place a block of type ```<type>``` in the cell corresponding to ```<M>```, ```<N>```. ```<type>``` is one in red, green, blue, yellow, [0..15] or B[0..15] (representing the barcodes), p ex. B10. Two blocks cannot be placed on the same coordinate.

  * ```bool <ID> = <True|False>``` 
  
    Defines a variable of the boolean type, where the identifier must not have been previously defined
  
  * ```int #<ID> = <n>``` 
  
    Defines a variable of the integer type, where the identifier must start with # and must not have been previously defined.


### Defining a Task
Within the main block and procedure definitions, only the instructions that operate on Willy can be used; that is, the instructions that define the scenario cannot be used within the main program or auxiliary procedures. A task is described with a block of the form

```begin-task <instructions>∗ end-task```

which contains zero or more instructions separated by ';' that define it. These instructions are

  * ```<ID> = <bool_expression>```

    Assigns a Boolean variable the value of a Boolean expression.

  * ```#<ID> = <int_expression>```

    Assigns a Integer variable the value of a Integer expression.

  * ```if <boolean_expression> then <instruction>``` 
  
    If ```<boolean_expression>``` evaluates to true, ```<instruction>``` is executed.

  * ```if <boolean_expression> then <instruction1> else <instruction2>``` 
  
    If ```<boolean_expression>``` evaluates to true, ```<instruction1>``` is executed. Otherwise, run ```<instruction2>```.

  * ```repeat <n> times <instruction>``` 
  
    Defines a bounded iteration that executes ```<instruction>``` ```<n>``` times. The parameter ```<n>``` is a non-negative decimal integer.

  * ```while <boolean_expression> do <instruction>``` 
  
    Defines an open iteration that executes ```<instruction>``` while ```<boolean_expression>``` evaluates to true.

  * ```begin <instruction>∗ end``` 
  
    Allows you to define a compound instruction that consists of zero or more instructions, separated by ';'.

  * ```define <ID> as <instrucción>``` 
  
    It allows associating an instruction with a new name that can then be used like any other instruction. It is a mistake to define the same instruction twice, as well as to define primitive language instructions.

  * Primitive instructions that instruct Willy to perform specific actions:

    * ```move``` 
    
        Move one step in the current direction. An error will occur if:
        * The square in front of it goes off scenario.
        * The square in front has a block.
        * Willy moves across the edge of the scenario.
        * The crane is at level 0 and willy carries a block.

    * ```follow-line```

        It works the same as move. It will be used to differentiate the robot's move and follow-line functions, which will be different.

    * ```turn-left```

        Turn to the left and thus change orientation. An error will occur if the crane is at level 0 and willy carries a block.

    * ```turn-right```

        Turn to the right and thus change orientation. An error will occur if the crane is at level 0 and willy carries a block.

    * ```take``` 

        Take a block from the square in front. An error will occur if: 
        * The crane is not at level 0.
        * There is no block in front of Willy.

    * ```drop``` 

        Drop a block. An error will occur if: 
        * Willy doesn't have a block.
        * Willy is not in front of the unloading area or the shelves.
        * Willy stands on the edge between two unloading zones or two shelves.
        * The level of the crane and the position of Willy are not indicated to put the block where it belongs.

    * ```identify``` 

        Identify the type of block in front of Willy.

    * ```level <int_expression>``` 

        Move the crane ```<int_expression>```  levels. If ```<int_expression>``` is positive, the movement is upwards, otherwise it will be downwards. If the new level is outside the range [0..2], it will give an error.

    * ```terminate```

        Program execution ends


  * Boolean expressions are constructed from primitive or scenario-defined Booleans, and expressions that can be constructed with standard Boolean connectors:

    * ```<ID>``` 

        Boolean identifier that can be one of those defined on the scenario, or one of the primitive Boolean ones:
        * ```detect-left <int_expression>``` Returns True if there is a block ```<int_expression>``` squares away to Willy's left.
        * ```detect-right <int_expression>``` Returns True if there is a block ```<int_expression>``` squares away to Willy's right.
        * ```detect-front <int_expression>``` Returns True if there is a block ```<int_expression>``` squares away to Willy's front.
        * ```detect-line``` Returns True if Willy is on a line.
        * ```detect-intersection``` Returns True if Willy is on a intersection.
        * ```last identified block is <type>``` Returns True if the last block identified by willy is of type ```<type>```.

    * Operators: ```==, !=, and, or, not```.
    * Parentization ```( . )```.
    * Constants ```True, False```.
    * Integer comparison ```==, !=, <, <=, >, >=```.

  * Integer expressions are constructed from scenario-defined Integers or constants, and expressions that can be constructed with operators: ```+, -, *, %, ( . )```.
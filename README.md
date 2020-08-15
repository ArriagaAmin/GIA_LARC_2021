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

 * ```Start at <M> <N> heading <direction>``` Define Willy's initial position and orientation with 0 <= M, N <= 21. The direction is one in north, east, south, or west. If this instruction is not specified, Willy will initially be located at position 0, 0 facing north.

 * ```Place block <ID> at <M> <N>``` Place a block of type ID in the cell corresponding to M, N. ID is one in red, green, blue, yellow, [0..15] or B[0..15] (representing the barcodes), p ex. B10. Two blocks cannot be placed on the same coordinate.

 * ```int #<ID> = <NUM>``` Defines a variable of the integer type, where the identifier must start with # and must not have been previously defined.

 * ```bool <ID> = <True|False>``` Defines a variable of the boolean type, where the identifier must not have been previously defined
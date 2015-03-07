# Quick tutorial
#### Indec
* [Syntax reference](#syntax-reference)
* [More about functions]

#### Syntax reference
* Literals
  * Number: `10` or `5.3` or `.7`
  * Character: `'a`
  * String: `"a \"feather\""`
  * Lists: `1 2 3` - can contain any of the preceding literals and any expressions surrounded by braces.
* Function calls
  * Functions are referenced by `[A-W][a-z]*`
  * Functions always take two parameters, in the syntax `xFy`, where x is a literal immediately preceding the function and y is everything following it. The left and right argument are always referenced as X and Y, respectively.
  * Modifiers take functions as their arguments and return new functions. They're referenced as A for adverb and C for conjunction.
    * `AF`
    * `vCF`, `FCF` (v is a literal argument to the conjunction)
* Assignment
  * `name:value`
  * If the name is `[X-Z][a-z]*`, the value is treated as an atom.
  * If the name is `[A-W][a-z]*`, the value is treated as a tacit expression, without curly braces.
* Function definitions
  * Functions are defined in so called tacit form.
  * `x{FGH}y` is run as `(xFy) G (xHy)`
  * The tacit expression can contain more than three functions, in which case the functions are read right-to-left and paired to tacit-expressions.
    * Example: `{ABCDE}` -> `{AB{CDE}}`
  * If a literal immediately precedes a function, it is bound as the left argument of the function.
    * Example:

       ```
           F:1+
           F3
       4
       ```




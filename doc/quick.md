# Quick tutorial
## Absolutely not finished yet.
Read the syntax reference and jump to [function reference](reference.md) or [examples](../examples.md)
### Index
* [Syntax reference](#syntax-reference)
* [More about functions](#more-about-functions)

### Syntax reference
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

### More about functions
#### Modifiers
Functions would be pretty boring by themselves. That's why we have modifiers. They appear before a function and can be chained for hilarious effects. Let's glance at a few of them.
#### Rank
Functions behave a bit differently than usually. They operate on a specific rank. Rank of a list is it's depth. For example, `[[1, 2], [3, 4]]` has rank of 2. Rank of a function consists of three numbers though. 

# Quick tutorial
### Absolutely not finished yet.
Read the syntax reference and jump to [function reference](reference.md) or [examples](../examples.md)
## Index
* [Syntax reference](#syntax-reference)
* [More about functions](#more-about-functions)

## Syntax reference
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

## More about functions
#### Monadic or dyadic?
Most functions can be called with one or two arguments. Never zero and never more than two. And no, it really isn't restricting. Function used with one argument is called the monadic form of the function and, like you could guess, function used with two arguments is called the dyadic form of the function. The difference between the two is usually quite obvious and often can be used interchangeably, resulting in more flexible derived functions. Here's a couple of examples:

* Table-function

    ```
       T5 3
     0  1  2  3  4 
     5  6  7  8  9 
    10 11 12 13 14 
       5 3T0 1
    0 1 0 1 0 
    1 0 1 0 1 
    0 1 0 1 0 
    ```

* Minus-function

    ```
       3-5
    2
       -5
    -5
    ```

#### Modifiers
Functions would be pretty boring by themselves. That's why we have modifiers. They appear before a function and can be chained for hilarious effects. Let's glance at a few of them.

* `/F` is the table-adverb
  Table has two behaviours, depending on if it's used monadically or dyadically. If you use it monadically, it applies the function between the items of it's argument, just like foldr.

    ```
       /+1 2 3 4 5
    15
       1+2+3+4+5
    15
    ```

  If it's used dyadically, it applies the whole left argument to the items of the right argument.

    ```
       1 2 3/*1 2 3
    1 2 3 
    2 4 6 
    3 6 9 
       (1 2 3*1)(1 2 3*2)(1 2 3*3)
    1 2 3 
    2 4 6 
    3 6 9 
    ```

* `~F` is flip-adverb
  Flip also has different behaviours when used monadically and dyadically, but they resemble each other a lot more. If used monadically, it applies the argument as both arguments to the function.

    ```
       ~*5
    25
       5*5
    25
    ```
  
  If used dyadically, it swaps the arguments.

    ```
       2~%5
    2.5
       5%2
    2.5
    ```

#### Rank
Functions behave a bit differently than usually. They operate on a specific rank. Rank of a list is it's depth. For example, `[[1, 2], [3, 4]]` has rank of 2. Rank of a function consists of three numbers though. 

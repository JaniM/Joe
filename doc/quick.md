# Quick tutorial
## Index
* [Syntax reference](#syntax-reference)
* [More about functions](#more-about-functions)
  * [Monadic or dyadic?](#monadic-or-dyadic)
  * [Modifiers](#modifiers)
  * [Rank](#rank)
  * [Padding](#padding)

You should also look at [Function reference](reference.txt) and [examples](../examples.md)

## Syntax reference
* Literals
  * Number: `10` or `_7` or `5.3` or `.7` (use _ instead of -, because - is a function)
  * Character: `'a`
  * String: `"a \"feather\""`
  * Lists: `1 2 3` - can contain any of the preceding literals and any expressions surrounded by braces.
* Function calls
  * Functions are referenced by `[A-W][a-z]*`
  * Functions always take one or two parameters, in the syntax `Fy` or `xFy`, where x is a literal immediately preceding the function and y is everything following it. The left and right argument are always referenced as X and Y, respectively.
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
Most functions can be called with one or two arguments. Never zero and never more than two. And no, it really isn't restricting. Function used with one argument is called the monadic form of the function and, like you could guess, function used with two arguments is called the dyadic form of the function. The difference between the two is usually quite obvious and often can be used interchangeably, resulting in more flexible derived functions. As a rule of thumb, you often can think of the left argument as control data. Here's a couple of examples:

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
Functions behave a bit different than usually. They operate on a specific rank. Rank of a list is it's depth. For example, `[[1, 2], [3, 4]]` has rank of 2. Rank of a function consists of three numbers though. Let's look at what each one of them means and what the rank of a function actually does.

I'll take the function Ld ("list drop") as an example. It has rank of `M 0 M` (not intended). The first value, which in this case is "maximum", means that if the function is used monadically, it applies to the whole argument, dropping the first item. The more interesting case is when it's used monadically.

The second and third values mean the rank of left and right argument, respectively. In the case of `M 0 M`, it applies each individual cell (rank 0 item, or atom) of the left argument to the whole right argument. It's hard to explain, but you can think of it as implicit mapping. I'll demonstrate with an example:

```

   2Ld0 1 2 3 4 5
2 3 4 5 
   2 1 3Ld0 1 2 3 4 5
2 3 4 5 
1 2 3 4 5 
3 4 5 
```

You can always create a function with different rank by using the `^` conjunction. Note that you can use comma to separate the rank from a preceding argument if necessary. It has three possible forms:

* `M L R^F`, which gives the rank `M L R` to F. For example: `1 0 1^+`
* `L R^F`, which gives the rank `R L R` to F. For example: `0 1^+` is `1 0 1^+`
* `N^F`, which gives the rank `N N N` to F. For example: `1^+` is `1 1 1^+^

Note: Rank can be negative, in which case ... hard to explain, have an example. If the function's rank is `_1`, and the argument's rank is 3, it maps to the rank 2 items of the argument.

#### Padding
Padding is a more subtle technique, It ensures that the function's arguments have at least the required rank to operate correctly. For example, monadic `;` flattens a list by one level. For this to work, the argument must have at least a rank of 2. Padding ensures that it is. In effect, `;10` gives `[10]`. Padding can't be affected by code.


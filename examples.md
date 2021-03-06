# Examples

## Random examples

* Mean of a list

    ```
       F:{/+%N
       F1 2 3 4
    2.5
       F1 2 3 4 5
    3.0
    ```
  
  Explanation: `{/+%N)` defines a fork. The superfluous ending brace can be dropped. Let's denote the argument as Y. When we call the function, it gets interpreted as `(/+Y)%(NY)`.
    * `/+` gives the sum of a list
    * `%` divides the left argument by the right argument
    * `N` gives the length of a list

* Factorial

    ```
       Fac:/*-,1R
       MFacR10
    [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880]
    ```

  Explanation: Fac is a chain. When you call `FacY`, it gets evaluated as `/*-,1RY`.
    * `/*` gives the product of the given list
    * `-,` removes the items of the left argument from the right argument. Because no left argument was given, it removes zeroes.
    * `1R` gives a list from 1 to the argument, inclusive
    * `R10` gives a list from 0 to 9
    * `MFac` maps Fac to them

* Fibonacci sequence

    ```
       F:2Lr0 1/v;$l/+@2ER
       F10
    [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    ```

    Explanation: Here we see a lot of new features. Let's look at what each function does from right-to-left
      * `R` gives a range from 0 to x.
      * `;$l/+@2E` takes a list as it's right argument and appends the sum of the two last elements to it.
        * `2E` takes the last two elements
        * `/+` sums them
        * `;` concats two values
        * `x F$lG y` gets evaluated as `y F x G y`
      * `0 1/v` right-folds the list, starting with the value of `[0, 1]`. This is the magic.
      * `2Lr` drops the last two elements. Without it, two extra numbers would be returned.

* Count letters in a word

    ```
       F:VO$rME{M;C)$r-u
       F"this is a sentence"
    e 3
      3
    s 3
    n 2
    i 2
    t 2
    c 1
    a 1
    h 1
    ```

    Explanation coming soon.

## Code golf examples

* [Home on the Range of Lists](http://codegolf.stackexchange.com/q/47351/20356)

    ```
       F:/+lM]R
       F10
    [0, [1, [2, [3, [4, [5, [6, [7, [8, [9]]]]]]]]]]
       F3
    [0, [1, [2]]]
       F2
    [0, [1]]
       F1
    [0]
       F0
    []
    ```

  Explanation: Function definition initiates a chain of functions. The function is evaluated as `/+,(M](RY))` or `X/+,(XM](XRY))`, depending on if it's called monadically or dyadically.
    * `R` gives the range from 0 to Y.
    * `M]` wraps every element to a list.
    * `/+l` gives the fold of `+l`, which returns `x + [y]`



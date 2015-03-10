# Examples

## Random examples

* Mean of a list

    ```
       F:{/+%L
       F1 2 3 4
    2.5
       F1 2 3 4 5
    3.0
    ```
  
  Explanation: `{/+%L)` defines a fork. The superfluous ending brace can be dropped. Let's denote the argument as Y. When we call the function, it gets interpreted as `(/+Y)%(LY)`.
    * `/+` gives the sum of a list
    * `%` divides the left argument by the right argument
    * `L` gives the length of a list

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
       F:0 1/,{A;/+@2E)R
       F10
    [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    ```

    Explanation coming

## Code golf examples

* [Home on the Range of Lists](http://codegolf.stackexchange.com/q/47351/20356)

    ```
       F:/+,R
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

  Explanation: Function definition initiates a chain of functions. The function is evaluated as `/+,(RY)` or `X/+,(XRY)`, depending on if it's called monadically or dyadically.
    * `/+,` gives the fold of `+,`, which returns `x + [y]`
    * `R` gives the range from 0 to Y.



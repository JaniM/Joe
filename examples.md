# Examples

## Random examples

* Mean of a list

    ```
       F:/+%L
       F1 2 3 4
    2.5
       F1 2 3 4 5
    3.0
    ```
  
  Explanation: `/+%L` defines a fork. Let's denote the argument as Y. When we call the function, it gets interpreted as `(/+Y)%(LY)`.
    * `/+` gives the sum of a list
    * `%` divides the left argument by the right argument
    * `L` gives the length of a list

## Code golf examples

* [Home on the Range of Lists](http://codegolf.stackexchange.com/q/47351/20356)

    ```
       F:/;,@{Lr;Lt@E}@R
       F10
    [0, [1, [2, [3, [4, [5, [6, [7, [8, [9]]]]]]]]]]
       _3F7
    [-3, [-2, [-1, [0, [1, [2, [3, [4, [5, [6, [7]]]]]]]]]]]
    ```


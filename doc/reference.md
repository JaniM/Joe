# Function reference
### Adverbs
Adverbs take only one argument, which is an immediately following function, and return a new function.

* `~F` flips the arguments of the function. Informally: `x ~F y` is `y F x`
* `/F` has two meanings, depending if it's called monadically or dyadically.
  * `/F y` applies F between all items of y. For example: `/+1 2 3` is `1+2+3`
  * `x /F y` maps `x /F` to all items of y. For example: `1 2/+1 2 3` is `(1 2+1) (1 2+2) (1 2+3)`

### Conjunctions
Conjunctions always take two arguments, where left argument either a literal or a function, and right argument is a function. They all return a function.

* `r^F` gives a function, which calls F with rank r.
* `F@G` gives a function, which passes the result of G to F. Informally: `x F@G y` is `F x G y`

### Functions
* `x+y` gives the atomic sum of x and y.
  * X defaults to 0.
  * Rank 0 0 0
* `x-y` gives the atomic difference of y from x. `2-5` is 3.
  * X defaults to 0.
  * Rank 0 0 0
* `x*y` gives the product of x and y.
  * `*y` gives the sign of y, which is -1, 0 or 1.
  * Rank 0 0 0
* `x%y` gives the dividend of x and y.
  * X defaults to 1.
  * Rank 0 0 0
* `x|y` gives the module of x and y.
  * '|y` gives the absolute value of y.
  * Rank 0 0 0
* `x;y` concatenates x and y.
  * `;y` flattens y by one level
  * Rank M M M
  * Padding 2 1 1
* `x;,y` gives list [x, y]
  * `;,y` flattens y completely
  * Rank M M M
  * Padding 1 0 0

* `xAy` returns x
  * `Ay` returns y
* `xBy` return y
  * `By` return y
* `xRy` gives numbers from x to y, inclusive. Y can be less than x.
  * `Ry` gives numbers from 0 to y, exclusive.
  * Rank 0 0 0
* `xTy` gives a table of shape x, using items of y cyclically.
  * Example (in table mode):

        ```
           5 3T1 0
        1 0 1 0 1
        0 1 0 1 0
        1 0 1 0 1
        ```

  * `Ty` gives a table of shape y, where each item has successive value, starting from 0.
  * Rank 1 1 1
  * Padding 1 1 1
* `Dy` gives the depth of y.
* `Ly` gives the length of y.
* `xSy` splits y by x.
  * x defaults to `" "`
  * Rank 1 1 1
* `x Ld y` drops the first x items of y.
  * x defaults to 1
  * Rank M 0 M
  * Padding 1 0 1
* `x Lr y` drops the last x items of y.
  * x defaults to 1
  * Rank M 0 M
  * Padding 1 0 1
* `xHy` returns the first x items of y.
  * `Hy` returns the first item of y.
  * Rank M 0 M
  * Padding 1 0 1
* `xEy` returns the last x items of y.
  * `Ey` returns the last item of y.
  * Rank M 0 M
  * Padding 1 0 1
* `xNy` returns the xth item of y.
  * Rank 1 0 M
  * Padding 1 0 1
* `xPy` print y formatted with x (uses Python's format).
  * `Py` prints y.
  * Both return 0.
  * Rank M 1 M
  * Padding 0 0 1


# Joe
Joe is a concise language derived from J and is designed for code golfing. So, if you're familiar with J, you can easily grasp Joe. Othwerwise, let me run through the most important points:

* Joe is not a von Neumann -language
* Functions can usually implicitly handle arbitrarily nested lists (arrays).
  * `1+1 2 3` is `2 3 4`
  * `1 2 3+1 2 3` is `2 4 6`
* Functions are usually defined in tacit-style, which is closely related to pointless style.

Note: The interpreter used the [Arpeggio module](https://github.com/igordejanovic/Arpeggio) to parse code. You can install it by executing `pip install arpeggio`.

#### Links
* [Quick tutorial](doc/quick.md)


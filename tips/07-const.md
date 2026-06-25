🦀 Tip of the day 07: `const` -- Values the Compiler Knows Before Your Program Even Starts

You already know from tip [5](05-immutable-variables.md) that `let` variables are immutable by default. But `const` is a different beast entirely.

```rust
let max_players = 8;         // Decided at runtime, when this line runs
const MAX_PLAYERS: u32 = 8;  // Decided at compile time, baked into the binary
```

The compiler does not reserve memory for `const`. It replaces every use of `MAX_PLAYERS` with the literal `8` before your program even runs.

Rules that come with it:

Since the value must be known at compile time, you are limited to literals, math on other constants, and a few built-in operations. You cannot call non-const functions to initialize a const (more on that later).

```rust
const TIMEOUT: u64 = 30;       // Type annotation is required, no inference allowed
const PI: f64 = 3.14159;       // Can live at global scope, unlike `let` which can only exist inside functions
const ROWS: usize = 8;
const COLS: usize = 8;
const TOTAL: usize = ROWS * COLS; // Math on other consts works

const NAME: String = String::from("hello"); // ERROR: String::from is not a const function

fn main() {
    const SIZE: usize = 10;
    let numbers = [0; SIZE]; // Array sizes must be compile-time, so const works here but let does not
}
```

Naming convention: `ALL_CAPS_SNAKE_CASE`. The compiler will not enforce it, but every Rustacean will judge you.

How other languages handle it:

Go and Kotlin also have true compile-time constants. Go's is interesting: constants are untyped by default and pick up their type at the point of use. Kotlin's `const val` is stricter, only primitives and `String`, and it must live at the top level or inside a `companion object`. C++ has `constexpr`/`consteval`, which are the closest cousins to Rust's `const` and the original inspiration for compile-time evaluation.

Then there are the pretenders. JavaScript's `const` just means "can't reassign", the value is still computed at runtime, and you can freely mutate the object it points to. Java's `static final` looks like a constant but the language makes no compile-time guarantee. Python does not have constants at all. `ALL_CAPS` is just a polite suggestion that everyone ignores.

*Think of `const` as a fact about your program that is true before it even starts, like the number of cards in a deck, or the value of pi. `let` is for things you figure out while running. `const` is for things you already know.*

🔇 JavaScript really named their "you can't reassign this but go ahead and mutate whatever is inside" feature `const`. Brave naming choice.

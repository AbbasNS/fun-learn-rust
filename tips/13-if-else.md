🦀 Tip of the day 13: `if/else` Returns a Value, So Ternary Can Retire

If you are coming from Java, C++, or JavaScript, you have two separate tools: `if/else` for control flow, and the ternary operator (`? :`) for inline value selection. Rust merged them. In Rust, `if` is an expression. It evaluates to a value, just like `match`, just like the blocks you saw back in tip [4](04-no-return.md). That makes the ternary operator redundant, so Rust simply doesn't have one.

The basics look familiar, minus the parentheses. Rust does not require parentheses around the condition, but the braces are mandatory, even for one-liners:
```rust
let temperature = 35;

if temperature > 30 {
    println!("it's hot");
} else if temperature > 20 {
    println!("nice out");
} else {
    println!("bring a jacket");
}
```
Coming from C-style languages, you will forget the braces and add unnecessary parentheses for the first week. The compiler will gently nudge you on both.

Because `if` returns a value, you can bind the result directly to a variable:
```rust
let weather = if temperature > 30 { "hot" } else { "fine" };
```
In Java or C++ you would write `temperature > 30 ? "hot" : "fine"`. In Rust, that syntax does not exist. You already have `if`. Both branches must return the same type, same rule as `match` arms.

No implicit truthiness. Unlike C++, Python, or JavaScript, Rust requires the condition to be `bool`. There is no `if (0)`, `if ("")`, or `if (null)`. If you want to check whether a collection is empty, you write `if list.is_empty()`, not `if !list`. This removes an entire class of bugs where a value is accidentally falsy.

`let else` is the inverse of `if let` (tip [12](12-match.md)). Instead of "if it matches, run this block," it means "this must match, otherwise bail out":
```rust
let Ok(config) = load_config() else {
    return default_config();
};
// config is available here, no nesting
```
The `else` branch must diverge (return, break, continue, or panic). This keeps the happy path unindented.

Skipping `else` means the block returns `()`, Rust's unit type. That is fine for side effects, but you cannot assign it to anything useful.

The takeaway: Rust's `if` is an expression that returns a value, requires real `bool` conditions, and pairs with `let else` for clean early exits.

🔇 The ternary operator spent 50 years being the clever shortcut. Rust just made every `if` clever by default and quietly showed it the door.

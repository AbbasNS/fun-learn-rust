🦀 Tip of the day 06: Shadowing, Reusing Variable Names on Purpose!

If you are coming from Java, Python, or C++, you were probably taught that reusing a variable name in the same scope is sloppy, confusing, and a guaranteed source of bugs. Your linter screams at you. Your code reviewer leaves a passive-aggressive comment. Your professor deducts points. In Rust, shadowing is not only legal, it is idiomatic and actively encouraged.

How it works in practice:
When you write let x = ...; a second time in the same scope, you are not mutating the old variable. You are creating an entirely new variable that happens to have the same name. The old value is effectively dead. The compiler knows it is unreachable and can drop it.

What you write:
```rust
let input = "  42  ";                      // A string
let input = input.trim();                  // Still a string, but trimmed
let input = input.parse::<i32>().unwrap(); // Now it's an integer!
println!("{}", input + 1); // 43, works perfectly, it's an i32 now
```
We just changed the type of input from &str to i32, using the same name. Try doing that with mut and the compiler will slap you:
```rust
let mut input = "  42  ";
input = input.trim();          // OK: &str → &str, same type
input = input.parse().unwrap(); // ERROR: expected `&str`, found `i32`
// `mut` lets you change the VALUE, not the TYPE.
```
Why it is NOT a code smell in Rust: No silent mutation. In Python, reusing a name silently overwrites the old value with zero safety checks:
```python
connection = open_database()
connection = "oops, I'm a string now"
connection.execute("SELECT * FROM users")  # Runtime crash at 3 AM. Good luck.
```
In Rust, shadowing creates a completely new binding, the old variable is not mutated, it is replaced. The compiler audits this: if the old value was never used before being shadowed, you get a warning. And if you accidentally call .execute() on a &str, the type system catches it at compile time. The bug that would have been a 3 AM production incident is a squiggle in your editor before you even hit save.
Type transformations are explicit: Shadowing is the idiomatic way to progressively refine a value through a pipeline. Without it, you end up with input_raw, input_trimmed, input_parsed: a graveyard of throwaway names that clutter your function and make you play a naming game instead of writing logic.
Where we actually use it:
```rust
// Narrowing Option/Result types:
let config = load_config();              // Returns Option<Config>
let config = config.unwrap_or_default(); // Now it's just Config, same name, no confusion

// Immutable "freeze" after setup:
let mut buffer = Vec::new();
buffer.push(1);
buffer.push(2);
buffer.push(3);

let buffer = buffer; // Shadow with an immutable binding, buffer is now locked
// buffer.push(4);   // ERROR: cannot borrow as mutable, the setup phase is over
```
You get a mutable setup phase, then freeze the variable by shadowing it with an immutable let. The compiler guarantees no code below this line can accidentally modify it.

The takeaway: In most languages, variable shadowing is an accidental footgun that hides bugs. In Rust, it is a deliberate, compiler-checked tool for transforming data through a clean pipeline, without inventing throwaway names or resorting to mutation.

🔇 In Python, you can shadow a database connection with a 🥪 and nobody will know until the pager goes off.

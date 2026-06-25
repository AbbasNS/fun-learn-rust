🦀 Tip of the day 05: Variables That... Don't Vary

If you are coming from Python, JavaScript, or C++, you are used to declaring a variable and changing its value whenever you need to. It is right there in the name: a variable is supposed to vary. In Rust, variables are immutable by default. Once you bind a value to a name, it is locked in.

How it works in practice:
Rust assumes that once you set a value, you probably don't want it changing behind your back. If you do actually need to modify it later, you have to formally request permission from the compiler using the mut (mutable) keyword.

What you write:
```rust
// The Python/JS way (The Rust compiler will respectfully reject this)
let score = 10;
// score = 20; // ERROR: cannot assign twice to immutable variable `score`

// The idiomatic Rust way
let mut score = 10; // `mut` flags that this value will change
score = 20;         // All good!
```

Why do we do this?
It is all about trust and readability. When you are reading a massive function and see let config = load_settings();, you have a compiler-backed guarantee that config won't be secretly modified by a random if statement 50 lines down. Conversely, when you see let mut, it acts as a polite heads-up: "Pay attention, this data is going to change over time." It makes debugging much faster. If you are ever tracking down an unintended state change, you only have to suspect the variables explicitly marked as mutable.
The takeaway: By making you opt-in to mutation, Rust forces you to be intentional about state changes, eliminating a whole category of accidental overwrite bugs.

🔇 Yes, we still call them "variables" even though 90% of them will never vary. Just think of it as a historical naming quirk, exactly like how we still click a picture of a floppy disk every time we want to save a file!

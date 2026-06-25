🦀 Tip of the day 04: Reaching the Point of No return!

If you are coming from Java, Python, or C++, you are deeply conditioned to type return whenever you want a function to hand data back. You might be surprised to learn that in idiomatic Rust, we rarely use the return keyword at all. In Rust, you don't formally declare you are returning a value; you just... stop typing.

How it works in practice: Rust is an expression-based language. This means almost every block of code evaluates to a value, even things like if blocks, loops, and match statements. The core rule of Rust functions is wonderfully simple: The last expression in a block is automatically returned, provided it doesn't end with a semicolon.

What you write:
```rust
// The C/Java/Python way (Valid in Rust, but your linter will judge you)
fn add_boring(a: i32, b: i32) -> i32 {
    return a + b;
}

// The Idiomatic Rust way
fn add_idiomatic(a: i32, b: i32) -> i32 {
    a + b // Look ma, no `return`! And no semicolon!
}
```
Expressions vs. Statements (The Semicolon Trap): This is where new Rustaceans usually trip up.
Expression (No Semicolon): Evaluates to a value and passes it outward. a + b hands back an integer.
Statement (With Semicolon): Performs an action, suppresses the value, and evaluates to the empty unit type (), which is Rust's safe version of void. a + b; calculates the math, immediately throws the integer in the trash, and returns ().

Wait, so do I ever use the return keyword? Yes! The return keyword is still alive and well, but it is strictly reserved for early returns. If you need to bail out of a function prematurely, maybe because of an error or a guard clause, you explicitly return.
```rust
fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        return 0; // Early return requires the keyword AND a semicolon
    }

    a / b // The implicit return at the very end of the function
}
```
The takeaway: By treating blocks of code as expressions, Rust allows your logic to flow naturally into its output, cutting down on visual clutter and letting the structural boundaries of your code dictate what gets returned.

🔇 I was going to leave you with a clever joke about semicolons to wrap this up, but sorry, I have no pun to return;. I guess I'll just have to punt this one to tomorrow!

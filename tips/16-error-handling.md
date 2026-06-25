🦀 Tip of the day 16: Exceptions, the Feature You'll Wish Your Language Didn't Have

If you are coming from Java, Python, C++, or JavaScript, you are used to throwing and catching exceptions. Something goes wrong, you `throw`, and somewhere up the call stack a `try/catch` block deals with it. Maybe. Hopefully. Rust does not have exceptions. No throwing, no catching, no exception to the rule. Errors are just values you return.

`Result` is just an enum. You already know enums from tip [11](11-enums.md):

```rust
enum Result<T, E> {
    Ok(T),   // Success, here's the value
    Err(E),  // Failure, here's what went wrong
}
```

Just like `Option` wraps "value or nothing," `Result` wraps "value or error." The compiler forces you to handle both cases.

The verbose way (you already know this from tip [12](12-match.md)):

```rust
fn read_config() -> Result<String, std::io::Error> {
    let content = std::fs::read_to_string("config.toml");
    match content {
        Ok(text) => Ok(text),
        Err(e) => Err(e),
    }
}
```

That works, but you are just receiving a `Result` and forwarding it. If you have three operations that can fail, you end up with three nested match blocks. This is basically Go's `if err != nil { return err }` pattern, except even more verbose.

The `?` operator fixes this. Placing `?` after an expression that returns `Result` does exactly what the match above does: if it is `Ok`, unwrap the value and continue. If it is `Err`, return the error from the current function immediately.

```rust
fn read_config() -> Result<String, std::io::Error> {
    let content = std::fs::read_to_string("config.toml")?;
    // If we get here, content is a String, not a Result
    Ok(content)
}
```

Chain multiple fallible operations and the code stays flat:

```rust
fn load_user(path: &str) -> Result<User, std::io::Error> {
    let text = std::fs::read_to_string(path)?;  // fails? return early
    let user = parse_user(&text)?;               // fails? return early
    Ok(user)
}
```

`?` only works in functions that return `Result` (or `Option`). This is not a limitation, it is the whole point. If your function signature returns `Result`, anyone calling it can see that it might fail. The error path is right there in the type. No surprises.

When you just want the value: `unwrap()` and `expect()`.

Sometimes you know a `Result` should be `Ok`, or you are prototyping and don't want to handle errors properly yet. `unwrap()` extracts the value, but if the `Result` is `Err`, your program panics and crashes:

```rust
let text = std::fs::read_to_string("config.toml").unwrap();
// If the file is missing:
// thread 'main' panicked at src/main.rs:2:51:
// called `Result::unwrap()` on an `Err` value: Os { code: 2, ... }
```

That tells you what went wrong and, since Rust 1.65, the file and line it happened on, but not *why* you expected the value to be there. `expect()` lets you add that context:

```rust
let text = std::fs::read_to_string("config.toml")
    .expect("failed to read config file");
// If the file is missing:
// thread 'main' panicked at src/main.rs:2:6:
// failed to read config file: Os { code: 2, ... }
```

Both are fine in tests, examples, and throwaway scripts. In production code, propagate with `?` instead.

If you want a fallback instead of crashing, `unwrap_or` provides a default value:

```rust
let port: u16 = port_string.parse().unwrap_or(8080); // bad input? use 8080
```

How other languages compare:

- Java checked exceptions put errors in the signature, which is the right idea. In practice, the boilerplate pushed many libraries and most modern frameworks toward unchecked exceptions, which weakens the guarantee.
- C++ tried exception specifications (`throw(Type)` in C++98) and removed them in C++17 because they were broken in practice. C++11 added `noexcept`, which only tells you a function *won't* throw, not what it *might* throw. So C++ can mark the safe path but not the error path.
- Python and JS/TS use unchecked exceptions only. You cannot tell from a function signature whether it might throw. You just have to know, or read the docs, or find out in production.
- C# deliberately rejected checked exceptions. Anders Hejlsberg, C#'s lead designer, [identified two problems with Java's design](https://www.artima.com/intv/handcuffs.html): "scalability and versionability." So C# kept only unchecked exceptions, with the same signature blindness as Python and JS, but by design rather than default.
- TypeScript later named the deeper reason. Ryan Cavanaugh, TypeScript's lead, [closing the proposal for a throws keyword in 2023](https://github.com/microsoft/TypeScript/issues/13219#issuecomment-1515037604), put it bluntly: "Effectively, exceptions (and *checked* exceptions doubly so) are a *workaround* for a lack of union return types in a language." Twenty years after Hejlsberg rejected checked exceptions in C#, his own team articulated why: exceptions exist because older languages could not express `T | E` in a return type. Which is to say, the feature you wish your language didn't have.
- Go gets the explicitness right with `if err != nil { return err }`, but you write that boilerplate on nearly every line. Rust's `?` gives you the same visibility with far less noise.

The takeaway: Rust replaces invisible exception-based control flow with `Result`, a simple enum that makes errors part of the type system, and `?`, a one-character shorthand that keeps the code clean. No exceptions, no exception-makers, just values.

🔇 Other languages: "Errors should be exceptional!" Also other languages: *throws an exception because a file didn't exist, which is arguably the most expected thing a file can do.*

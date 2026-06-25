🦀 Tip of the day 39: From and Into, the Conversion Pair

You have written all of these without thinking about it:

```rust
let s = String::from("hello");      // tip 23
let s = "hello".to_string();
let s: String = "hello".into();
```

All three produce a `String` from a `&str`, but they do not share one mechanism. `String::from("hello")` and `"hello".into()` are the two halves of the pair this tip is about: `From` and `Into`. The middle one, `"hello".to_string()`, comes from a different trait, `ToString` (which is built on `Display`), not from `From` at all. So really there are two syntaxes for one idea, plus a lookalike.

`From` defines a conversion *from* one type *into* the type implementing it:

```rust
trait From<T> {
    fn from(value: T) -> Self;
}
```

`String` implements `From<&str>`, which is what `String::from("hello")` calls. Implementing `From` for your own type is straightforward:

```rust
struct Email(String);

impl From<String> for Email {
    fn from(s: String) -> Self {
        Email(s)
    }
}

impl From<&str> for Email {
    fn from(s: &str) -> Self {
        Email(s.to_string())
    }
}

let e1: Email = String::from("a@b.com").into();
let e2: Email = "c@d.com".into();
```

The `Into` trait is the inverse direction. If `T: From<U>`, then `U: Into<T>` automatically. The standard library provides the matching `Into` impl through a blanket implementation, so you only ever write `impl From`. The `into()` form lets the *caller* pick the conversion target; `From::from` lets you write the target type explicitly.

So which trait do you use? Implement `From`; you never implement `Into`. Reach for `Into` only as a bound, as in `fn send(to: impl Into<Email>)`, which lets a function accept anything convertible into what it needs. The two are just spellings of the same conversion, so the choice is ergonomics: `where Email: From<T>` and `impl Into<Email>` express the same requirement, and the `Into` form only reads in the direction the value flows.

When should you implement `From`? Whenever a conversion is total, infallible, and obvious. The `Email` above is a thin wrapper that stores whatever string it is handed, so wrapping never fails. The moment a conversion can reject its input it does not belong in `From`: validating that a string is actually a well-formed email address can fail, and so can parsing a string into an integer. Those use a different trait, `TryFrom`, which returns `Result`.

Now the part that explains a piece of magic from tip [16](16-error-handling.md). The `?` operator does more than early-return on `Err`. It also calls `From::from` on the error value. So when one function returns `Result<T, ErrorA>` and another returns `Result<T, ErrorB>`, you can chain them with `?` if `ErrorA: From<ErrorB>`:

```rust
struct AppError;

impl From<std::io::Error> for AppError {
    fn from(_: std::io::Error) -> Self {
        AppError
    }
}

fn read_config() -> Result<String, AppError> {
    let text = std::fs::read_to_string("config.toml")?;  // io::Error -> AppError automatically
    Ok(text)
}
```

Each `?` checks for `Err`. If found, it converts the inner error using the `From` impl and returns. This is how a single application error type can absorb errors from across the standard library and other crates without explicit conversion code at every call site.

Comparison:

- C++: implicit conversion constructors do something similar, and are notoriously easy to abuse, which is why modern style guides push `explicit` on single-argument constructors (C++20 even added `explicit(bool)` for conditionally explicit ones).
- C#: the closest analog. A `public static implicit operator Email(string s)` is a safe conversion the compiler applies on its own; `explicit operator` needs a cast and is for lossy ones. For conversions that can fail, C# 11 added `IParsable<T>` with `TryParse`, the real parallel to `TryFrom`.
- Java: no user-defined conversions at all. You write factory methods or constructors and call them by name.
- Python: explicit constructors plus conversion dunders like `__int__` and `__str__`, invoked through `int(x)` or `str(x)`. No implicit user conversions.
- Kotlin: no implicit conversions either, not even `Int` to `Long`; you call `.toLong()`. Construction goes through `companion object` factories.
- Rust: `From` plus a blanket `Into` impl, with `?` integration for error types. Conversions are explicit at the call site (someone wrote `into()` or `from()` or used `?`), but the rest is plumbing the compiler handles.

The takeaway: implement `From<U>` to define how to convert `U` into your type, and you get `Into<YourType>` for free. The same machinery powers `?`'s automatic error conversion. Reach for `From` whenever a conversion is total and obvious; reach for `TryFrom` when it can fail.

🔇 Python: explicit is better than implicit. C++: needs a keyword named explicit just to turn the implicit ones off. Rust: nods along, then has a single ? quietly do three things you never wrote, check for Err, convert it via From::from, and return.
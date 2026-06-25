🦀 Tip of the day 22: Lifetimes, or Why a Reference Cannot Outlive Its Referent

Borrowing (tips [20](20-borrowing.md) and [21](21-mutable-borrowing.md)) lets you read or mutate a value without owning it. But what if the borrow outlives the data it points to? In C++, this is the classic dangling reference: a function returns a pointer to a local, the function exits, the local is destroyed, and the caller now holds a pointer into freed memory. Compiles fine. Crashes later, somewhere unrelated.

Rust refuses to let this happen. For every reference, the compiler tracks how long the data it points to is actually alive, and refuses to let the reference escape past it. The mechanism for expressing this is *lifetimes*.

A lifetime is a label, written `'a` (read "tick a"), that names a region during which a reference is valid. The name `'a` is convention, not syntax. Any identifier works (`'src`, `'input`). Two reserved names: `'static` (lives the whole program) and `'_` (placeholder, "infer this one").

Most code never writes lifetimes. Take a real string-parsing function, extracting the first word:

```rust
fn first_word(s: &str) -> &str {
    let end = s.find(' ').unwrap_or(s.len());
    &s[..end]
}
```

The output is a slice into the input. The compiler knows the result borrows from `s`, so it cannot outlive `s`. You wrote no annotations because the relationship is unambiguous: one input reference, one output reference. This automatic inference is called *lifetime elision*, and it covers the vast majority of code.

The realistic case where you do write lifetimes is structs that hold references. Picture parsing a CSV line into a view that does not allocate any of its columns:

```rust
struct Row<'a> {
    name: &'a str,
    email: &'a str,
}

fn parse(line: &str) -> Row<'_> {
    let mut parts = line.split(',');
    Row {
        name: parts.next().unwrap(),
        email: parts.next().unwrap(),
    }
}
```

`Row<'a>` says: a `Row` borrows from a string with lifetime `'a`, and the `Row` cannot outlive that string. You get a parsed view with zero allocation, and the compiler ensures the original line stays alive as long as the `Row` is used. Drop `line` while a `Row` still points into it, and your code does not compile. This pattern is everywhere in real Rust: parsers, log readers, cursor types, anything that wants to inspect a buffer without copying. Without lifetimes on the struct, the language could not safely allow it.

Both fields share `'a` here because both columns come from the same `line`. If the two fields came from different sources, you would declare two parameters and name them separately:

```rust
struct Row<'a, 'b> {
    name: &'a str,
    email: &'b str,
}
```

Most of the time one lifetime is enough. Reach for two only when the fields really do borrow from different places and you don't want the intersection.

The other place you sometimes write lifetimes is functions that return one of several input references:

```rust
fn longer<'a>(a: &'a str, b: &'a str) -> &'a str {
    if a.len() > b.len() { a } else { b }
}
```

The `<'a>` ties all three references to a common region, the intersection of the actual input lifetimes. At the call site the compiler picks `'a` to be the window during which every input is alive; the result cannot be used past that window. Without `<'a>`, the compiler refuses. From the signature alone, it cannot tell whether the output borrows from `a`, `b`, or either.

Inputs share a lifetime only when they need to. If only one input is the source of the output, only that input needs an explicit name:

```rust
fn first_part<'a>(input: &'a str, separator: &str) -> &'a str {
    let idx = input.find(separator).unwrap_or(input.len());
    &input[..idx]
}
```

The output borrows from `input`, so `input` gets `'a`. The `separator` is just `&str` because elision gives it its own anonymous lifetime, independent of `'a`. Nothing ties them together, so the separator can live a much shorter window than `input`. Picking the same `'a` for both inputs, like in `longer`, is a deliberate constraint, used only when either input could become the output.

The distinction shows up in real code. The compiler catches a dangling reference through `input`:

```rust
let part;
{
    let s = String::from("hello,world");
    part = first_part(&s, ",");
}                          // s dropped here
println!("{}", part);      // ERROR: `s` does not live long enough
```

But it does not care about `separator` dying early, because `part` does not borrow from it:

```rust
let s = String::from("hello,world");
let part;
{
    let sep = String::from(",");
    part = first_part(&s, &sep);
}                          // sep dropped, but part does not borrow from sep
println!("{}", part);      // OK
```

If we had used the same `'a` for both inputs (like `longer`), the second snippet would also fail: the compiler would require `sep` to outlive `part`. Naming only `input`'s lifetime is what frees the separator from that constraint.

Why doesn't the compiler just look inside the body and figure all this out? Two reasons. First, the signature is the public contract: if lifetimes came from the body, a one-line change inside the function could silently tighten or loosen what callers are allowed to do, breaking them with no warning. Second, the compiler and the reader often only have the signature. Across crates, through trait objects, or just when reviewing code, the body is not available. Putting the borrowing relationship in the signature keeps it visible, stable, and independent of implementation.

What does any of this defend against? The dangling reference:

```rust
fn dangling() -> &i32 {
    let x = 42;
    &x         // ERROR: returns reference to local
}
```

`x` lives only inside `dangling`. The returned reference would point into a stack frame that has already been popped.

When are lifetimes inferred and when do you write them?

- Function parameters and returns: usually inferred (lifetime elision). You write `<'a>` mainly when the function returns a reference and elision can't figure out which input it borrows from.
- Struct fields that are references: the struct must declare a lifetime parameter. There is no elision here. `struct Row<'a> { ... }` is mandatory the moment a field is `&str` or any other reference.
- Local variables (`let`): never. The compiler infers them entirely from how the binding is used.

Lifetimes have a reputation as the hardest part of Rust, but in everyday code you rarely write them. The compiler usually tells you exactly which annotation it wants.

The takeaway: lifetimes track how long each reference is valid, so references can never outlive their data. Most are inferred. The ones you write usually appear on parser-style structs and on functions returning one of several input references.

🔇 No, that is not a stuck pixel. The cat didn't walk on your keyboard. That is `'a`, and the compiler will make sure you remember it for a lifetime.


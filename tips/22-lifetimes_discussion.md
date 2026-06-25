🦀 Tip of the day 22 follow-up

Follow-up questions from the discussion on [Tip 22: Lifetimes, or Why a Reference Cannot Outlive Its Referent](22-lifetimes.md).

## Does `'_` only work when the function has a single reference parameter, or can it handle multiple?

In `fn parse(line: &str) -> Row<'_>`, you could equally have written `fn parse<'a>(line: &'a str) -> Row<'a>`. The `'_` is shorthand that asks the compiler to infer the output lifetime using the elision rules. So the real question is: when can elision figure it out on its own?

The rules are a small priority list.

If the function takes `&self` or `&mut self`, the receiver wins. Its lifetime is assigned to every elided output lifetime, no matter how many other reference parameters there are. This is why methods rarely need explicit annotations even when they take extra borrowed arguments.

Otherwise, elision fills in the output only when the inputs contribute exactly one lifetime position. Each `&` and each lifetime slot of a generic input counts as a position; plain value arguments like `i32` do not count. Two references are two positions even if you happen to give them the same name, so `fn build(a: &str, b: &str) -> Row<'_>` does not compile:

```rust
fn build(a: &str, b: &str) -> Row<'_> {  // ERROR
    Row { name: a, email: b }
}
```

```
error[E0106]: missing lifetime specifier
  = help: this function's return type contains a borrowed value, but the
    signature does not say whether it is borrowed from `a` or `b`
```

The compiler cannot guess whether the result borrows from `a` or `b`, so it makes you spell it out:

```rust
fn build<'a>(a: &'a str, b: &'a str) -> Row<'a> {
    Row { name: a, email: b }
}
```

A practical note: `'a` is no harder to type than `'_`, and it states the relationship explicitly. When in doubt, write the name. The elision rules are convenient, not something you need to memorize.

## Does declaring a lifetime guarantee the function is written correctly, or could the code still compile if the lifetime were omitted from `Row`?

These are two different guarantees, and it helps to keep them apart.

A struct that holds references cannot omit the lifetime parameter at all. This does not compile:

```rust
struct Row { name: &str, email: &str }
```

```
error[E0106]: missing lifetime specifier
```

There is no elision for struct fields. The lifetime parameter is the type's contract for how long its borrowed contents must stay valid, and the compiler demands it at the definition. A malformed `Row` that secretly holds a dangling reference cannot exist in the first place, because you cannot even name the type without committing to that contract.

So the annotation is not optional documentation that a careful author remembers to add. It is required, and once it is there the compiler enforces it everywhere the type is used: construct a `Row` from a string and the `Row` is held to the string's lifetime, drop the string early and your code stops compiling. The annotation does not certify the function body is good logic; it certifies the borrowing relationship is sound, which is the part that causes use-after-free bugs in other languages.

## Can a `Row` be built in two different contexts, one where both fields share a string and one where each field borrows from a different string? Do `Row<'a>` and `Row<'a, 'b>` need to be different types?

You usually do not need two lifetime parameters for this. A single-lifetime `Row<'a>` already accepts references from different scopes, because the compiler picks `'a` to be the intersection (the shorter) of the actual lifetimes involved:

```rust
struct Row<'a> {
    name: &'a str,
    email: &'a str,
}

let long = String::from("alice");
{
    let short = String::from("bob");
    let r = Row { name: &long, email: &short };
    println!("{} / {}", r.name, r.email);  // prints: alice / bob
}
```

This compiles. The compiler shrinks `&long` to fit the shorter window of `short`, so both fields share one valid region and the `Row` is sound for the duration of the inner scope.

`Row<'a>` and `Row<'a, 'b>` are indeed distinct types, and they can coexist in the same program:

```rust
struct Row<'a> {
    name: &'a str,
    email: &'a str,
}

struct RowSplit<'a, 'b> {
    name: &'a str,
    email: &'b str,
}
```

You reach for the two-parameter version only when callers genuinely need the two lifetimes tracked independently, for example when each field is produced and consumed under separate constraints and you do not want one to be shrunk to match the other. That is rare. The intersection behavior of a single lifetime is what makes `Row<'a>` cover almost every case without extra ceremony.

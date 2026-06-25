🦀 Tip of the day 36: Generics and Trait Bounds, Writing Code for All Types

In tip [27](27-traits.md) we said `fn f(x: impl Trait)` accepts any type implementing the trait. That syntax is shorthand for the generic form, which is more flexible and what you reach for when the function needs more than one type parameter or has multiple constraints.

The full generic form uses angle brackets to declare type parameters:

```rust
fn first<T>(v: Vec<T>) -> Option<T> {
    v.into_iter().next()
}

let n = first(vec![1, 2, 3]);          // T inferred as i32
let s = first(vec!["a", "b", "c"]);    // T inferred as &str
```

`T` is a type parameter. The function works for any `T` because it only does things that work for any type (move it around, hand it back).

When the function actually needs `T` to support specific operations, you constrain it with trait bounds:

```rust
use std::fmt::Display;

fn announce<T: Display>(item: T) {
    println!("here it is: {}", item);
}

announce(42);
announce("hello");
```

`T: Display` reads as "I will accept any type as long as it implements `Display`." The body is type-checked against the bounds alone, and at each call site the compiler verifies that the supplied type satisfies them. If you pass a type that doesn't implement `Display`, the error points to your call rather than somewhere inside `announce`.

You can require multiple bounds with `+`:

```rust
fn copy_and_print<T: Display + Clone>(item: T) {
    let copy = item.clone();
    println!("{} and {}", item, copy);
}
```

When the bounds get long, a `where` clause keeps the signature readable:

```rust
fn process<T, U>(t: T, u: U) -> String
where
    T: Display + Clone,
    U: Display + Default,
{
    let copy = t.clone();
    let fallback = U::default();
    format!("{}/{} (copy: {}, fallback: {})", t, u, copy, fallback)
}
```

Functionally identical to inline bounds, just easier to read once there are several.

Two small extras. When the compiler can't infer `T` from context, you write it explicitly with the turbofish (tip [15](15-iterators.md)):

```rust
let parsed = "42".parse::<u32>().unwrap();
let empty = Vec::<i32>::new();
```

And type parameters can have defaults. `HashMap<K, V>` is actually `HashMap<K, V, S = RandomState>` in the standard library, with the hasher defaulted. You can do the same on your own types:

```rust
struct Buffer<T = u8> {
    data: Vec<T>,
}

let b: Buffer = Buffer { data: vec![0, 1, 2] };   // T defaults to u8
let s: Buffer<String> = Buffer { data: vec![] };
```

Defaults work on type definitions (`struct`, `enum`, `trait`, type aliases), not on free functions.

What does the compiler do with all this? *Monomorphization*. For each combination of concrete types you call the generic function with, the compiler generates a specialized copy tailored to those types. `announce(42)` and `announce("hello")` produce two separately compiled versions of `announce`. This makes generic code as fast as hand-written specialized code, with zero runtime cost.

The price is in compile time and binary size: a heavily generic function that gets used with many types takes longer to build and produces more machine code. For most code the trade is invisible.

Comparison:

- Java: type erasure. Generics are checked at compile time then discarded; at runtime `List<String>` and `List<Integer>` are the same `List`. Reflection cannot recover the original type parameter.
- C#: reified generics. The CLR keeps type parameters at runtime; the JIT specializes value-type instantiations and shares one implementation across reference types. `typeof(T)` works inside generic methods. Closer in spirit to Rust, just done at JIT time rather than AOT.
- C++: templates are the closest analogue. One copy per concrete type, no runtime cost, and a Turing-complete compile-time language on top (template metaprogramming, SFINAE, concepts). The big difference is timing: Rust checks generics against the bounds before instantiation, so errors are local to your code; classic C++ templates are checked after instantiation, producing the famously long template error messages. C++20 concepts narrow that gap by checking the constraints at the instantiation point, so a violated `concept` reports at the call site, though the body is still free to use operations the concept never promised.
- Go: generics arrived in 1.18 (2022). Type parameters with constraints expressed as interfaces. Runtime cost varies by implementation strategy.
- Python: dynamic at runtime, but static generics have existed since 3.5 (`typing.Generic`, `TypeVar`) and got native syntax in 3.12 (`def first[T](v: list[T]) -> T | None`). Static checkers like mypy and pyright enforce them; the runtime ignores them, closer to Java's erasure model than to JavaScript.
- JavaScript: no static generics. TypeScript adds them as a separate type-system layer that erases to plain JS at runtime.
- Rust: monomorphization plus trait bounds checked before instantiation. As fast as C++ templates, with friendlier errors. Not as cool for metaprogramming, though: that role goes to `const fn` and macros.

The takeaway: `<T>` declares a type parameter, `<T: Trait>` constrains it, multiple bounds combine with `+`, and `where` clauses keep complex signatures readable. The compiler generates a specialized copy of your function for each concrete type, so generic code costs nothing extra at runtime.

🔇 C++ generic errors: a thousand lines of template instantiation, and somewhere in there is the actual problem. Rust generic errors: the bound on line 3 was not satisfied; here is the call.

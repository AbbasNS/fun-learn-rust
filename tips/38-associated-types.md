🦀 Tip of the day 38: Associated Types and Default Methods, or How Iterator Really Works

You have been using iterators since tip [15](15-iterators.md). `.map()`, `.filter()`, `.collect()`, `.sum()`, dozens of others. They all come from the `Iterator` trait, but tip [27](27-traits.md) only showed you traits with required methods. So how does one trait give you a hundred methods?

Two trait features we have not yet shown: *default methods* and *associated types*. They are how `Iterator` actually works.

The simplified definition of `Iterator` looks roughly like this (real signatures have a few more details):

```rust
trait Iterator {
    type Item;                                  // associated type
    fn next(&mut self) -> Option<Self::Item>;   // required method

    // many default methods, including:
    fn count(self) -> usize { /* default body uses next() */ }
    fn map<B, F>(self, f: F) -> /* ... */ { /* default body */ }
    // ... and many more
}
```

Two new features in there.

First, `type Item;`. This is an *associated type*: a type that the trait carries with it, supplied by the implementor. When you implement `Iterator` for your own type, you also pick what `Item` is. This is different from a generic parameter: a generic parameter is supplied by the *caller*, an associated type is supplied by the *implementor*. Each iterator type has exactly one `Item`.

Second, the `count` and `map` definitions in the trait body. These are *default methods*: the trait provides an implementation, and types that implement the trait get those methods for free unless they choose to override. `Iterator` ships dozens of these. You implement `next()`, and you get `map`, `filter`, `take`, `collect`, `sum`, and friends without writing a single one.

Implement `Iterator` once and the payoff is clear:

```rust
struct CountUpTo {
    current: u32,
    max: u32,
}

impl Iterator for CountUpTo {
    type Item = u32;

    fn next(&mut self) -> Option<u32> {
        if self.current < self.max {
            let n = self.current;
            self.current += 1;
            Some(n)
        } else {
            None
        }
    }
}

let counter = CountUpTo { current: 1, max: 5 };
let sum: u32 = counter.map(|n| n * 2).sum();   // 2 + 4 + 6 + 8 = 20
```

We wrote `next`, the only required method. The trait gave us `map` and `sum` (and `filter`, `take`, `collect`, dozens more) automatically. As a bonus, `for x in counter { ... }` works too: a `for` loop calls `.into_iter()` first (tip [15](15-iterators.md)), and every `Iterator` already counts as an `IntoIterator` that returns itself, so the loop just keeps calling `next()`.

Why associated types instead of a generic parameter (`trait Iterator<T>`, the way you would reach for a C++ template parameter or a Java generic)? Because each iterator yields exactly one element type, and fixing it is what makes type inference work.

With a generic `Iterator<T>`, one type could have many impls: `impl Iterator<i32> for CountUpTo` and `impl Iterator<String> for CountUpTo` would both be legal. Now when you write `counter.next()`, which one did you mean? The compiler cannot tell, so you would have to annotate the element type at every call, and a chain like `.map(...).filter(...).collect()` would need a hint at each step.

An associated type removes the choice. Given the iterator type, `Item` is uniquely determined, so the compiler infers it for free and the chain just flows. The implementor picks `Item` once; everyone else gets it for nothing.

You will see associated types throughout the standard library: `Iterator::Item`, `IntoIterator::Item`, `Add::Output`, `Index::Output`, `Future::Output`. Every one of them is "the type that comes out," fixed per implementor.

Comparison:

- Java: interfaces had only abstract methods until Java 8 added `default` methods. Generic interfaces use type parameters (`Iterable<T>`), so the element type lives in the interface's name; there is nothing equivalent to associated types. Java still fixes that type per implementor: you cannot implement `Iterable<String>` and `Iterable<Integer>` on one class.
- C#: same default-method story (C# 8), but C# does let one class implement `IEnumerable<int>` and `IEnumerable<string>` at once. That is exactly the ambiguity associated types forbid: with `Item`, each implementor has one element type and no more.
- Haskell: type classes have associated types (with the `TypeFamilies` extension) and default method implementations. This is where Rust borrowed both ideas.
- C++: you can get close. A type carries a nested alias (`using value_type = int;`), and a concept (C++20) can require it (`requires { typename It::value_type; }`). The difference is ownership: that alias belongs to the type, not the concept, so every concept mentioning `value_type` shares the same one. A Rust associated type belongs to the trait, so one type can carry an independent `Iterator::Item`, `Add::Output`, and `Future::Output` at once, each fixed by its own impl.
- Rust: both built into traits from the start, used heavily across the standard library.

The takeaway: traits can carry associated types (one per implementor) and default method implementations. `Iterator` uses both. You implement `next()` and pick `Item`, and the standard library hands you the rest of the toolkit.

🔇 The trait saves you fifty functions of typing. Don't get excited: you will pay every minute back fighting the borrow checker.

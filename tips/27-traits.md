🦀 Tip of the day 27: Traits, the Shape Your Types Can Promise

Tip [26](26-derive-macros.md) kept saying "implement the `Debug` trait." What is a trait? In one sentence: a trait is a set of method signatures that types can promise to provide. Other languages call this an interface (Java, C#, Go), a protocol (Python, Swift), or a type class (Haskell). Rust borrowed the idea most directly from Haskell.

You define a trait by listing the methods it requires:

```rust
trait Greet {
    fn hello(&self) -> String;
}
```

Any type can implement `Greet` by providing that method:

```rust
struct English;
struct French;

impl Greet for English {
    fn hello(&self) -> String {
        String::from("Hello!")
    }
}

impl Greet for French {
    fn hello(&self) -> String {
        String::from("Bonjour!")
    }
}
```

Now both `English` and `French` are `Greet` types. You can write a function that accepts anything implementing `Greet`:

```rust
fn greet_someone(g: impl Greet) {
    println!("{}", g.hello());
}

greet_someone(English);   // "Hello!"
greet_someone(French);    // "Bonjour!"
```

The `impl Greet` parameter is shorthand for "any type that implements `Greet`." The compiler generates a specialized version of `greet_someone` for each concrete type that calls it, a process called *monomorphization*. No virtual dispatch, no runtime cost.

A small but important detail: you can implement a trait for a type you did not write. `impl MyTrait for Vec<T>` is allowed. This is unusual coming from Java or C#, where a class's interfaces are fixed at the moment the class is declared. In Rust, you can extend existing types with new behavior, as long as either the trait or the type is local to your *crate*. A crate is a Rust library or binary built as a single piece by the compiler; a later tip covers crates properly. This restriction has a name: the *orphan rule*. It stops two unrelated crates from independently writing conflicting impls for the same trait and type pair.

Standard library traits are how you opt into language behavior. `impl Display for MyType` makes `println!("{}", x)` work. `impl Iterator for MyType` makes it work in `for` loops. `impl PartialEq for MyType` enables `==`. The trait system *is* how Rust does polymorphism.

Each `impl Trait for Type { ... }` block implements exactly one trait. You cannot bundle multiple traits into a single block; three traits means three blocks. `#[derive(Debug, Clone, PartialEq)]` generates three such blocks too, one per trait, sitting alongside the struct rather than modifying it.

Two more shapes worth knowing now. A trait method can ship with a *default body*; implementors override it only when they need something different. This is why related traits compose cleanly: `Ord` requires only `cmp`, and gets `min`, `max`, and `clamp` for free from defaults built on top. And a trait can have no methods at all. *Marker traits* like `Copy` (tip [19](19-moves.md)), `Eq` (tip [26](26-derive-macros.md)), and the concurrency markers `Send` and `Sync` carry no code, only a promise the type makes to the compiler.

Traits versus other languages:

- Java, C#: classes declare which interfaces they implement at definition time. Default methods (Java 8+, C# 8+) and C# extension methods soften this, but you cannot retroactively make an existing class satisfy a new interface. Dispatch through an interface is dynamic by default (vtable lookup).
- Python: two analogues, not one. ABCs are nominal: you inherit explicitly, and forgetting an abstract method raises `TypeError` at construction. Protocols (PEP 544) are structural and statically checked by mypy or pyright, closer to Go interfaces than Rust traits.
- Go: interfaces are structurally typed; any type with the right methods satisfies them, no `impl` needed. Both languages catch typos at compile time. The real difference is that Rust's explicit `impl Trait for Type` records intent (one canonical, grep-able declaration), enforces coherence via the orphan rule, and makes semantic opt-ins like `Eq`'s reflexivity a conscious promise rather than an accident of method shape.
- Haskell: type classes. Same idea, different syntax. Rust borrowed heavily here.

Trait bounds with generics (`fn f<T: Trait>(x: T)`), associated types, and `dyn Trait` for runtime polymorphism are topics for later tips. For now, the basics: define a trait, implement it for a type, accept `impl Trait` as a parameter.

The takeaway: a trait is a set of method signatures. Types implement traits by providing those methods. Functions accept `impl Trait` to take any matching type, with the compiler checking the contract at compile time and no runtime cost.

🔇 Java interfaces describe what a class can do at the moment of birth. Rust traits describe what a type can do, possibly after the type was written, possibly by someone else, possibly with capabilities its original author never imagined.

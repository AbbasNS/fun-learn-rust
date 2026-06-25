🦀 Tip of the day 37: dyn Trait, Runtime Polymorphism

Generics from tip [36](36-generics.md) give you static polymorphism: each call-site type produces a separately compiled version of the function. Fast, but limited. Two limits show up quickly:

- A `Vec<T>` holds one type. You cannot put `Cat`, `Dog`, and `Cow` together in one collection through generics alone.
- A struct field of type `T` makes the whole struct generic (`S<T>`), and that type is fixed when the value is built. When you want a single, non-generic struct whose field holds a type chosen at runtime, generics cannot express that.

For these cases, Rust offers the second flavor: `dyn Trait`, runtime polymorphism through *trait objects*.

```rust
trait Animal {
    fn sound(&self) -> &'static str;
}

struct Cat;
struct Dog;
impl Animal for Cat { fn sound(&self) -> &'static str { "meow" } }
impl Animal for Dog { fn sound(&self) -> &'static str { "woof" } }

let zoo: Vec<Box<dyn Animal>> = vec![
    Box::new(Cat),
    Box::new(Dog),
];

for a in &zoo {
    println!("{}", a.sound());
}
```

The second case is the struct field, and it is the clearer reason to choose `dyn` over a generic:

```rust
struct Exhibit {
    featured: Box<dyn Animal>,   // which species is featured is decided at runtime
}
```

Written as `struct Exhibit<A: Animal> { featured: A }`, the species would be fixed when the `Exhibit` is built, and every type holding an `Exhibit` would have to name `A` (or become generic itself). The trait object keeps `Exhibit` a single plain type and defers the choice to runtime, which is exactly what you want when the species comes from config or user input rather than the source.

A bare `dyn Animal` has no size known at compile time (a `Cat` and a `Dog` can differ in size), so you always reach it through a pointer: `Box<dyn Animal>`, `&dyn Animal`, and so on. That is why you never see a plain `dyn Animal` by value.

`Box<dyn Animal>` is a trait object, and it is two pointers wide: one to the value, one to a *vtable*, a small lookup table of that type's method implementations. Calling `a.sound()` becomes a vtable lookup followed by an indirect call.

Java and C++ do the same thing with one layout difference. There the vtable pointer lives inside the object, so every instance carries it whether or not you ever dispatch on it. In Rust the vtable pointer rides in the trait object instead, and the payoff is concrete: a `Cat` used by its own type stays exactly as big as its fields and dispatches statically, paying nothing. The extra pointer word and the indirection appear only where you erase it to `dyn`, and only while you hold it that way.

You can also borrow a trait object with `&dyn Trait` (or `&mut dyn Trait`):

```rust
fn announce(a: &dyn Animal) {
    println!("an animal says: {}", a.sound());
}

announce(&Cat);
announce(&Dog);
```

Compare with the generic `fn announce<T: Animal>(a: &T)`. The generic version produces a specialized copy per type. The `dyn` version produces one copy that serves all of them through the vtable. The trade-off:

- Generics / `impl Trait`: no indirection, and the compiler can inline the call. But the function exists in multiple compiled forms, and you cannot store mixed types in one collection.
- `dyn Trait`: one indirect call the compiler usually cannot inline (the lost inlining often costs more than the indirection itself), in exchange for a single compiled form and heterogeneous values held together.

For most code the per-call cost is invisible. Default to generics when each call site has one type; reach for `dyn Trait` when you genuinely need a heterogeneous collection or runtime polymorphism. The same `dyn` works behind `Rc` and `Arc`, not just `Box`: `Rc<dyn Animal>`, or `Arc<dyn Animal + Send + Sync>` when the object crosses threads.

A constraint worth knowing: not every trait can become a trait object. The trait must be *dyn compatible* (these rules were called *object safety* until they were renamed around Rust 1.84, so you will see both terms). The common disqualifiers are generic methods and methods that take or return `Self` by value, because the vtable would need one entry per concrete type, or a return size it cannot know at the call site. `Clone` is the classic example: `fn clone(&self) -> Self` returns `Self`, so there is no `Box<dyn Clone>`. Everyday traits like `Display`, `Debug`, and `Iterator` are fine, and the compiler tells you plainly when you hit one that is not.

Comparison:

- Java: interface calls dispatch through a vtable, with no static-dispatch alternative in the language, though the JIT often devirtualizes hot calls at runtime.
- C#: interface calls are virtual too, but generics over value types are specialized by the JIT, so a generic constrained to an interface gets static dispatch when the type is a struct. Two paths, like Rust.
- C++: `virtual` methods give dynamic dispatch, templates give static. The choice mirrors Rust's `dyn` versus generics.
- Python, JavaScript: every method call is dynamic, with no static-dispatch option in the language itself.
- Go: interface calls go through a method table, the same idea as a vtable. Generics (since 1.18) only partly monomorphize: the compiler groups types by memory shape and shares one copy across all pointer types, reaching methods through a dictionary, so a call on a type parameter is often still indirect rather than the zero-cost static dispatch Rust gets.
- Rust: both options exist as separate constructs, and the trade-off is visible in the syntax you write.

The takeaway: `dyn Trait` is runtime polymorphism through a vtable. Use `Box<dyn Trait>`, `&dyn Trait`, or `Rc`/`Arc<dyn Trait>` when you need to hold values of different types in one place, and accept one indirect, un-inlinable call per method in exchange.

🔇 `dyn` is one vowel from "dine," which fits. You place your order, the vtable fetches it, dispatch serves it. Never instant, always one table away.

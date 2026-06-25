🦀 Tip of the day 15: Iterators, Part 1

In tip [14](14-loops.md), you saw `for item in collection` as Rust's way of looping. But that is only the surface. Under the hood, Rust has a full iterator system that will feel familiar if you have used Java Streams, Python list comprehensions, C# LINQ, or JavaScript's `.map().filter()` chain. The difference: Rust iterators are lazy and zero-cost.

Quick detour: closures.

Iterator methods take closures as arguments. A closure is an inline function, what other languages call lambdas or arrow functions. Where Python writes `lambda x: x * 2`, JavaScript writes `(x) => x * 2`, and Java writes `x -> x * 2`, Rust writes:

```rust
|x| x * 2
|x, y| x + y
|name| name.len() > 3
```

Pipes instead of arrows or keywords. Closures can capture variables from their surroundings, but that is a topic for another tip. For now, just read `|n| n % 2 == 0` as "a function that takes n and returns whether n is even."

Lazy means nothing happens until you consume.

When you write `.filter().map()`, Rust builds a recipe. No elements are processed yet. Work only starts when you consume the iterator with `collect()`, `sum()`, `count()`, or a `for` loop. Java Streams and C# LINQ are lazy the same way. JavaScript is not: `array.map().filter()` creates a brand new array at every step in the chain, even if you only need the first match.

The chaining pattern:

```rust
let evens: Vec<i32> = (1..=10)
    .filter(|n| n % 2 == 0)
    .collect();
// [2, 4, 6, 8, 10]
```

In Python, this is `[n for n in range(1, 11) if n % 2 == 0]`. In Java, `IntStream.rangeClosed(1, 10).filter(n -> n % 2 == 0).boxed().collect(Collectors.toList())`. Same idea, different verbosity.

`collect()` and the turbofish.

`collect()` is how you materialize an iterator into a real collection. It can produce a `Vec`, a `HashSet`, a `String`, and more, so the compiler needs to know which one. You can annotate the variable:

```rust
let evens: Vec<i32> = (1..=10).filter(|n| n % 2 == 0).collect();
```

Or use the turbofish:

```rust
let evens = (1..=10).filter(|n| n % 2 == 0).collect::<Vec<_>>();
```

See the `::<>`? That is the turbofish. It is how you pass a type argument to a function or method call. The `_` tells the compiler "figure out the element type yourself, just give me a Vec." You will see `::<>` in other contexts too, whenever Rust needs a type hint on a generic call.

Three ways to iterate a collection.

You have a collection and you want to loop over it. Rust offers three choices depending on what you need:

- `.iter()` reads each element. The collection is still there afterwards.
- `.iter_mut()` lets you modify each element in place. The collection survives, but contents may change.
- `.into_iter()` takes each element out. The collection is consumed and gone.

```rust
let names = vec!["Alice", "Bob", "Carol"];

// .iter(): read, collection survives
for name in names.iter() {
    println!("{name}");
}
println!("still have {} names", names.len()); // works fine

// .into_iter(): consume, collection is gone
for name in names.into_iter() {
    println!("{name}");
}
// names.len(); // ERROR: names has been consumed
```

```rust
let mut words = vec![String::from("hello"), String::from("world")];

// .iter_mut(): modify in place
for word in words.iter_mut() {
    word.push_str("!");
}
// words is now ["hello!", "world!"]
```

Shorthand you already know: `for name in &names` borrows, `for name in names` consumes. Under the hood, the `for` loop always calls `.into_iter()`. The difference is what you pass it: `&names` passes a reference, so `.into_iter()` on a reference just reads. `names` passes the collection itself, so it gets consumed. This is consistent with how the rest of the language works: passing a value moves it, passing `&` does not. The loop follows the same rules.

When chaining methods like `.filter()` and `.map()`, you call `.iter()` or `.into_iter()` explicitly.

The takeaway: Rust iterators are lazy pipelines built from closures. Choose `.iter()`, `.iter_mut()`, or `.into_iter()` based on whether you want to read, modify, or consume your collection. There are dozens of useful iterator methods (`enumerate`, `zip`, `find`, `sum`, and more), but you can discover those as you need them.

🔇 Rust lets you write elegant iterator chains and then compiles them into the same tight loop a C programmer would write after three cups of coffee and a debugging session. You get the readability. The CPU gets the performance. Everyone wins except the C programmer.

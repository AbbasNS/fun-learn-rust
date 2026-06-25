🦀 Tip of the day 17: Iterators, Part 2

Part 1 gave you the engine. Part 2 hands you the toolbox. The standard library ships dozens of iterator methods, and the ones below cover most of what you will ever reach for. Skim them once. Future-you will remember "there was a method for that" and grep for it.

`map` and `filter`, with a useful guest.

You met these in part 1. Here they are working together, with `inspect` joining the chain:

```rust
let names = vec!["Alice", "Bob", "Carol", "Dave"];
let short_upper: Vec<String> = names
    .iter()
    .inspect(|n| println!("checking {n}"))   // peek without disturbing the chain
    .filter(|n| n.len() <= 4)
    .map(|n| n.to_uppercase())
    .collect();
// ["BOB", "DAVE"]
```

`inspect` is the debugging escape hatch: it lets you print or log values mid-pipeline without changing them. Drop it in, find your bug, delete it. Order matters too: filter before map, otherwise you transform elements you are about to throw away.

`enumerate`: index plus value.

```rust
let colors = vec!["red", "green", "blue"];
for (i, color) in colors.iter().enumerate() {
    println!("{i}: {color}");
}
```

Python: `for i, c in enumerate(colors)`. Java: no direct equivalent, you reach for a manual counter or `IntStream.range()`. Small detail with a reason: `i` is a `usize`, the type Rust requires for indexing. If it were `u32` you would need `vec[i as usize]`. With `enumerate`, no cast needed.

`find`, `any`, `all`: searching and testing.

```rust
let names = vec!["Alice", "Bob", "Carol"];

let found = names.iter().find(|n| n.starts_with("C")); // Some("Carol")
let has_short = names.iter().any(|n| n.len() <= 3);    // true
let all_short = names.iter().all(|n| n.len() <= 5);    // true
```

All three short-circuit. `any` stops at the first match, `all` stops at the first failure, `find` returns as soon as it has something. The lazy pipeline means you get this for free, no `break` needed.

`zip`: pair two iterators.

```rust
let names = vec!["Alice", "Bob", "Carol"];
let scores = vec![85, 92, 78];

for (name, score) in names.iter().zip(scores.iter()) {
    println!("{name}: {score}");
}
```

Python: `for name, score in zip(names, scores)`. Nearly identical. If the iterators have different lengths, `zip` quietly stops at the shorter one. No panic, no error. The reason: iterators describe what they *can* produce, not what they *must*. If one runs dry, the chain just ends.

Infinite iterators are real, and useful.

```rust
let first_five_evens: Vec<i32> = (1..)            // 1, 2, 3, ... no upper bound
    .filter(|n| n % 2 == 0)
    .take(5)
    .collect();
// [2, 4, 6, 8, 10]
```

`(1..)` is a range with no upper bound. Eagerly walking it would run until the integer type overflows (over two billion steps for `i32`), so in practice you'd be waiting longer than the program would tolerate. But iterators are lazy: nothing runs until something consumes. `take(5)` says "give me five and stop," and the pipeline stops at the fifth value, never asking the range for a sixth. Python's `itertools.count`, Java's `Stream.iterate`, and JavaScript generators can all express the same idea, but each is a dedicated API you call into. In Rust, `(1..)` is just a value: the same `..` syntax you already use, minus the upper bound.

`take`, `skip`, `chain`, `step_by`: slice and combine.

```rust
let first_two: Vec<i32> = (1..=10).take(2).collect();      // [1, 2]
let every_third: Vec<i32> = (1..=10).step_by(3).collect(); // [1, 4, 7, 10]
let glued: Vec<i32> = (1..=3).chain(7..=9).collect();      // [1, 2, 3, 7, 8, 9]
```

`sum`, `count`, `min`, `max`, and the godfather: `fold`.

```rust
let total: i32 = (1..=10).sum();                          // 55
let evens = (1..=10).filter(|n| n % 2 == 0).count();      // 5
let product: i32 = (1..=5).fold(1, |acc, n| acc * n);     // 120
```

`fold` is the parent of every reducer. `sum` is `fold(0, +)`. `count` is `fold(0, |a, _| a + 1)`. When no built-in does quite what you want, `fold` is the universal fallback. Note the `: i32` on `total`: `sum` works for any numeric type, so the compiler insists you pick one. Mildly annoying, then forgettable.

Putting it together:

```rust
let sum: i32 = (1..=10)
    .filter(|n| n % 2 == 0)
    .map(|n| n * n)
    .sum();
// 220 (4 + 16 + 36 + 64 + 100)
```

Reads like English: take 1 through 10, keep the evens, square them, add them up. No mutable state, no off-by-one risk, no temporary `Vec` allocated between each step.

The takeaway: Rust's iterator toolkit covers transforming, filtering, searching, combining, and reducing. Most of what you used to write as a `for` loop with mutable state has a method named after it, the chain reads top-to-bottom like a sentence, and the compiler turns it into the same machine code anyway.

🔇 You write `(1..).filter(...).take(5)` and briefly feel like a functional wizard. Enjoy the spell, it is on borrowed time. Seventeen tips of dodging ownership, and next week the borrow checker comes to collect. Unlike our iterators, it is not lazy.

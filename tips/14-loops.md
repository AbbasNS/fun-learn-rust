🦀 Tip of the day 14: Loops, Three Ways

If you are coming from C++, Java, or JavaScript, you are used to `for`, `while`, and maybe `do-while`. Rust gives you three loop constructs too, but the lineup is different: `loop`, `while`, and `for`. No `do-while`, no C-style `for(int i = 0; i < n; i++)`.

`loop`: the infinite loop that knows it is infinite.

Most languages spell this `while(true)`. Rust has a dedicated keyword, and the real payoff is that `loop` can return a value through `break`:

```rust
let answer = loop {
    let guess = get_input();
    if guess == secret {
        break guess; // this value becomes `answer`
    }
};
```

You saw in tip [4](04-no-return.md) that Rust is expression-based. `loop` with `break value` fits right in. A `while` loop cannot do this because the compiler cannot guarantee the body ever runs, so the value might never be produced.

`while` and `while let`: conditional loops.

`while` works exactly as you expect. The interesting variant is `while let`, which loops as long as a pattern matches. Think of it as `if let` (tip [12](12-match.md)) on repeat:

```rust
let mut stack = vec![1, 2, 3]; // vec! creates a growable list, like ArrayList or std::vector
while let Some(top) = stack.pop() {
    println!("{top}"); // prints 3, 2, 1
}
```

Cleaner than a `loop` with a `match` inside and a `break` on `None`.

`for`: ranges and iterators.

There is no C-style `for(init; cond; step)`. Rust uses ranges and iterators instead, which eliminate off-by-one errors and out-of-bounds access:

```rust
for i in 0..5 {
    print!("{i} "); // 0 1 2 3 4 (use 0..=5 for inclusive)
}

let names = vec!["Alice", "Bob", "Carol"];
for name in &names { // & to borrow; No, we aren't ready to have this talk yet...
    println!("{name}");
}
```

Python's `for x in range(5)` is the closest equivalent. Java and C++ developers will miss the classic three-part `for`, but range-based loops turn out to be harder to get wrong. We will dig into iterators in the next tip.

Loop labels let you control nested loops.

`break` and `continue` work as expected, but in nested loops they only affect the innermost one. Labels let you target the outer loop:

```rust
'outer: for x in 0..5 {
    for y in 0..5 {
        if x + y == 6 {
            break 'outer;
        }
    }
}
```

Labels work with all three loop types, and with `continue` too:

```rust
'rows: for row in &matrix {
    for cell in row {
        if *cell < 0 {
            continue 'rows; // skip the rest of this row, move to the next
        }
        process(cell);
    }
}
```

You can also combine labels with `break value` in a `loop`:

```rust
let result = 'search: loop {
    for item in &candidates {
        if item.is_valid() {
            break 'search item.clone(); // return a value from the labeled loop
        }
    }
    refresh_candidates();
};
```

Java, Kotlin, and Go have labeled breaks as well. In Python, you need a flag variable or a helper function to break out of nested loops.

The takeaway: Rust gives you `loop` for intentional infinite loops (with the bonus of returning values), `while let` for pattern-based repetition, and iterator-based `for` that replaces C-style counting with something safer.

🔇 C++ has `goto` for when you need to jump anywhere, and no labeled `break` for when you need to jump somewhere specific. One can only [dream](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2025/p3568r0.html).

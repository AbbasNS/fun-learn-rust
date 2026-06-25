🦀 Tip of the day 12: `match` -- The Switch Statement That Actually Works

You saw `match` in tip [11](11-enums.md) destructuring enum variants. But `match` goes much further than enums.

It works on any value with a known structure. Integers, tuples, strings, ranges:
```rust
let point = (3, -5);
match point {
    (0, 0)  => println!("origin"),
    (x, 0)  => println!("{x} on the x-axis"),
    (0, y)  => println!("{y} on the y-axis"),
    (x, y)  => println!("({x}, {y})"),
}
```

Patterns are checked top to bottom, first match wins. No fall-through. The compiler also rejects any `match` that does not cover every possible value. This means adding a new enum variant turns every unhandled `match` into a compile error, giving you a checklist of what needs updating.

Combine patterns with `|`, refine them with `if` guards, name values with `@`:

These three tools let you express complex conditions inside patterns without nesting `if` statements:
```rust
match status_code {
    200 | 201 => println!("success"),
    301 | 302 => println!("redirect"),
    code if code >= 500 => println!("server error: {code}"),
    _ => println!("other"),
}
```
`code` binds the value so you can use it in both the guard and the body. If you also need to test against a pattern, `@` does both at once:
```rust
match score {
    perfect @ 100 => println!("perfect score: {perfect}!"),
    good @ 80..=99 => println!("{good} is solid"),
    _ => println!("keep going"),
}
```

`if let` for when you only care about one case. Writing a full `match` with a `_ => {}` arm just to handle one variant is noisy. `if let` is the shorthand:
```rust
if let Some(value) = maybe_result {
    println!("got {value}");
}
```

Quick boolean check with `matches!`. Sometimes you do not need the inner value, just whether something matches a pattern:
```rust
let is_success = matches!(status_code, 200 | 201);
let has_value = matches!(maybe_result, Some(_));
```

The takeaway: `match` checks patterns top to bottom, forces you to handle every case, and works on far more than enums. `if let` handles the single-pattern case, and `matches!` gives you a quick true/false.

🔇 Other languages let you add a new enum variant and find out you missed a case in production. Rust lets you find out before lunch. Bon app!

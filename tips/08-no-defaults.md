🦀 Tip of the day 08: No Free Lunches, No Free Defaults

In most languages, you can declare a variable and use it without ever giving it a value. What happens next depends on the language, and none of the options are great.

In C++, an uninitialized `int` contains whatever garbage was sitting in memory. Your program compiles, runs, and produces different results each time. This is undefined behavior; the compiler is not required to warn you, and debuggers will not always catch it.

In Python, you get a `NameError` at runtime. Maybe better than garbage 🤔? But you only find out when that exact line of code executes. If it is behind a rare `if` branch, it might not blow up until production.

In Rust, nothing has a default value unless you explicitly ask for one. If you try to use a variable before assigning it, the compiler rejects your code.

```rust
let x: i32;
println!("{}", x); // ERROR: used binding `x` isn't initialized
```

This is not a runtime crash. This is a compile-time error. Your program will not build until every variable has a value before it is used. Every code path, every branch, is checked before your code ever runs.

Late initialization is fine, as long as every path sets the value:
```rust
let temperature;

if sensor_available {
    temperature = read_sensor();
} else {
    temperature = 0; // Explicit fallback, your choice
}

println!("Temp: {}", temperature); // Works, both branches set it
```

The compiler tracks every possible code path. If even one branch leaves the variable unset, it will not compile.

What if I actually want a default?

Rust has the `Default` trait. But you have to opt in. Nothing gets it for free.
```rust
let x: i32 = Default::default();  // 0, but you asked for it explicitly
let s: String = Default::default(); // "", same idea
```

The key difference: in Rust, you wrote `Default::default()`, so anyone reading the code knows the default was intentional, not an accident.

The takeaway: Rust does not assume you want zero, false, or empty. If a value matters enough to exist, it matters enough to be set on purpose.

🔇 C++ lets you read uninitialized memory and calls it "performance." Python waits until your code is running in production to tell you a variable does not exist. Rust just says no at compile time. Boring, but you sleep better.

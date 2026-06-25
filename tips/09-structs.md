🦀 Tip of the day 09: Structs, or "Classes Without the Drama"

If you are coming from Java, Python, or C#, you are used to classes. A class bundles your data and your methods together, usually with inheritance, constructors, access modifiers, and a 200-line file before you even get to the interesting part.

Rust has structs. They hold your data. That's it.

```rust
struct Player {
    name: String,
    score: u32,
    online: bool,
}
```

No constructors. No inheritance. No `public`/`private` on each field (yet). Just: here is the shape of my data.

Creating one:
```rust
let alice = Player {
    name: String::from("Alice"),
    score: 0,
    online: true,
};

println!("{} has {} points", alice.name, alice.score);
```

Every field must be set. Just like you learned in tip [8](08-no-defaults.md), Rust has no implicit defaults. The compiler will reject your struct if you forget even one field.

Quick shorthand: If your variable names match the field names, Rust lets you skip the repetition:
```rust
let name = String::from("Bob");
let score = 100;
let online = false;

let bob = Player { name, score, online }; // No need for `name: name`
```

The struct update syntax (`..`):

Remember the `Default` trait from tip [8](08-no-defaults.md)? Here is where it really shines. If all your fields already implement `Default`, just derive it:

```rust
#[derive(Default)]
struct Point3D {
    x: f64,  // defaults to 0.0
    y: f64,  // defaults to 0.0
    z: f64,  // defaults to 0.0
}

let p = Point3D { y: 1.0, ..Default::default() }; // x = 0.0, y = 1.0, z = 0.0
```

When the standard defaults are not what you want, implement it manually:

```rust
struct ServerConfig {
    host: String,
    port: u16,
    max_connections: u32,
}

impl Default for ServerConfig { // more on this later
    fn default() -> Self {
        Self {
            host: String::from("localhost"),
            port: 8080,
            max_connections: 100,
        }
    }
}

let config = ServerConfig { port: 3000, ..Default::default() };
// host = "localhost", port = 3000, max_connections = 100
```

The `..` syntax fills in all the fields you did not specify from another instance. It also works for copying from an existing struct:

```rust
let base = Point3D { x: 1.0, y: 2.0, z: 3.0 };
let moved = Point3D { z: 10.0, ..base }; // x = 1.0, y = 2.0, z = 10.0
```

You set the fields you care about, everything else comes from the source. No builders, no optional parameters, no 10-argument constructor.

Tuple structs: When naming every field feels like overkill, you can use positional fields instead:
```rust
struct Color(u8, u8, u8);

let red = Color(255, 0, 0);
println!("R: {}", red.0); // Access by position
```

Printing structs with `#[derive(Debug)]`:

If you try to `println!` a struct, the compiler will tell you it does not know how to display it. `#[derive(Debug)]` is a macro (everything is a macro) that auto-generates a `Debug` trait implementation for your struct, so Rust knows how to print it.

Why `{:?}` and not `{}`? Rust has two formatting traits. `{}` uses `Display`, which is for user-facing output. Rust will not auto-generate that because it cannot guess how you want to present data to users. `{:?}` uses `Debug`, which is for developer-facing output. Since the format is mechanical (dump the struct name and all fields), it can be derived automatically.

```rust
#[derive(Debug)]
struct Player {
    name: String,
    score: u32,
}

let alice = Player { name: String::from("Alice"), score: 42 };
println!("{:?}", alice); // Player { name: "Alice", score: 42 }
```

The takeaway: Structs are Rust's way of saying "define your data, nothing more." Methods, behavior, and all the fun stuff come separately (tomorrow!).

🔇 Rust looked at the 100-line Java class with one `name` field, a constructor, a getter, a setter, a `toString`, an `equals`, a `hashCode`, and said: "What if we just... didn't?" Though you will still end up putting `#[derive(Debug)]` on almost every struct, so the boilerplate found a way back in.

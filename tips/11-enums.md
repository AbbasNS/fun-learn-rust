🦀 Tip of the day 11: Enums -- More Than Just a List of Labels

If you are coming from Java, C++, or C#, you know enums as a fixed list of named constants. Red, Green, Blue. They are just labels with integers hiding underneath. If you are coming from TypeScript, discriminated unions are closer to what Rust does, but Rust bakes the concept deeper into the type system. Rust enums can carry data.

The simple version (looks familiar):
```rust
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

let move_dir = Direction::Up;
```

The interesting version (each variant holds different data):
```rust
enum Message {
    Quit,                        // No data
    Text(String),                // Holds a String
    Move { x: i32, y: i32 },    // Holds named fields
    Color(u8, u8, u8),           // Holds a tuple
}

let msg = Message::Text(String::from("hello"));
let pos = Message::Move { x: 10, y: 20 };
```

You have already seen this. `Option<T>` from tip [3](03-banning-null.md) is just an enum:
```rust
enum Option<T> {
    Some(T),
    None,
}
```
No compiler magic. No special syntax. Just a regular enum with a generic type. `Result<T, E>` works the same way.

Enums can have methods, just like structs. You use `match` (think `switch`, but it also extracts the data inside each variant. Tomorrow: `match` in depth) to handle them:
```rust
impl Message {
    fn to_json(&self) -> String {
        match self {
            Message::Quit => String::from(r#"{"type":"quit"}"#),
            Message::Text(s) => format!(r#"{{"type":"text","body":"{s}"}}"#),
            Message::Move { x, y } => format!(r#"{{"type":"move","x":{x},"y":{y}}}"#),
            Message::Color(r, g, b) => format!(r#"{{"type":"color","rgb":[{r},{g},{b}]}}"#),
        }
    }
}
```

In Java, you would reach for a sealed interface. In C#, an abstract class. Either way, one subclass per variant.

One thing to watch: Rust stores enums inline, not behind a pointer. The layout is a small discriminant tag (which variant?) plus enough space for the largest variant's data. Think C++ `std::variant`: one contiguous block sized for the biggest case.

```rust
enum Data {
    Small(u8),           // 1 byte of data
    Large([u8; 1024]),   // 1024 bytes of data
}
// sizeof Data == 1025 bytes, 1 byte discriminant + 1024 for the largest variant, even when it holds Small(42)
```

The takeaway: Rust enums are not just labels. They are full tagged unions that can hold different data in each variant, and the compiler tracks which variant you have.

🔇 In most languages, if you want a type that can be "a string, a pair of coordinates, or nothing," you reach for inheritance, interfaces, and a class per variant. In Rust, that is four lines inside an `enum`.

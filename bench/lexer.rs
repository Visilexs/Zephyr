// String-processing benchmark: Rust reference for bench/lexer.zeph. Tokens
// are (kind, &str) slices into the generated source. Same LCG, same checksum.
// Build: rustc -O lexer.rs
// Usage: lexer [tokens]
use std::env;

struct Rng {
    state: u64,
}

impl Rng {
    fn next_random(&mut self) -> i64 {
        self.state = self.state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.state >> 33) & 2147483647) as i64
    }

    fn below(&mut self, limit: i64) -> usize {
        (self.next_random() % limit) as usize
    }
}

#[derive(Clone, Copy, PartialEq)]
enum TokenKind {
    Identifier,
    Keyword,
    Number,
    StringLiteral,
    Operator,
}

struct Token<'a> {
    kind: TokenKind,
    text: &'a str,
}

const IDENTIFIER_CHARACTERS: &[u8] = b"abcdefghijklmnopqrstuvwxyz0123456789_";
const COMMENT_CHARACTERS: &[u8] = b"abcdefghijklmnopqrstuvwxyz ";
const KEYWORDS: [&str; 8] = ["if", "else", "while", "fn", "return", "let", "var", "for"];
const OPERATORS: [&str; 17] = ["+", "-", "*", "/", "=", "==", "<", "<=", ">", ">=", "->", "(", ")", "{", "}", ",", "."];

fn generate_source(rng: &mut Rng, token_count: usize) -> String {
    let mut buffer: Vec<u8> = Vec::new();
    for _ in 0..token_count {
        let choice = rng.next_random() % 10;
        if choice < 3 {
            let length = rng.below(8) + 1;
            buffer.push(b'a' + rng.below(26) as u8);
            for _ in 1..length {
                buffer.push(IDENTIFIER_CHARACTERS[rng.below(37)]);
            }
        } else if choice == 3 {
            buffer.extend_from_slice(KEYWORDS[rng.below(8)].as_bytes());
        } else if choice < 6 {
            let length = rng.below(6) + 1;
            for _ in 0..length {
                buffer.push(b'0' + rng.below(10) as u8);
            }
        } else if choice < 8 {
            buffer.extend_from_slice(OPERATORS[rng.below(17)].as_bytes());
        } else if choice == 8 {
            let length = rng.below(10);
            buffer.push(b'"');
            for _ in 0..length {
                buffer.push(IDENTIFIER_CHARACTERS[rng.below(37)]);
            }
            buffer.push(b'"');
        } else {
            let length = rng.below(12);
            buffer.extend_from_slice(b"//");
            for _ in 0..length {
                buffer.push(COMMENT_CHARACTERS[rng.below(27)]);
            }
            buffer.push(b'\n');
        }
        match rng.next_random() % 8 {
            0 => buffer.push(b'\n'),
            1 => buffer.extend_from_slice(b"  "),
            2 => {}
            _ => buffer.push(b' '),
        }
    }
    String::from_utf8(buffer).unwrap()
}

fn is_letter(character: u8) -> bool {
    character.is_ascii_alphabetic() || character == b'_'
}

fn tokenize<'a>(source: &'a str, line_count: &mut i64, comment_count: &mut i64) -> Vec<Token<'a>> {
    let bytes = source.as_bytes();
    let length = bytes.len();
    let mut tokens = Vec::new();
    let mut position = 0;
    while position < length {
        let character = bytes[position];
        if character == b' ' || character == b'\t' || character == b'\r' {
            position += 1;
            continue;
        }
        if character == b'\n' {
            *line_count += 1;
            position += 1;
            continue;
        }
        let start = position;
        let mut kind = TokenKind::Operator;
        if is_letter(character) {
            while position < length && (is_letter(bytes[position]) || bytes[position].is_ascii_digit()) {
                position += 1;
            }
            kind = TokenKind::Identifier;
        } else if character.is_ascii_digit() {
            while position < length && bytes[position].is_ascii_digit() {
                position += 1;
            }
            kind = TokenKind::Number;
        } else if character == b'"' {
            position += 1;
            while position < length && bytes[position] != b'"' {
                position += 1;
            }
            if position < length {
                position += 1;
            }
            kind = TokenKind::StringLiteral;
        } else if character == b'/' && position + 1 < length && bytes[position + 1] == b'/' {
            while position < length && bytes[position] != b'\n' {
                position += 1;
            }
            *comment_count += 1;
            continue;
        } else {
            position += 1;
            if position < length {
                let next = bytes[position];
                if (next == b'=' && (character == b'=' || character == b'<' || character == b'>')) || (character == b'-' && next == b'>') {
                    position += 1;
                }
            }
        }
        let text = &source[start..position];
        if kind == TokenKind::Identifier && KEYWORDS.contains(&text) {
            kind = TokenKind::Keyword;
        }
        tokens.push(Token { kind, text });
    }
    tokens
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let token_count: usize = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 1000000 };
    let passes = 3;
    let mut rng = Rng { state: 12345 };

    let source = generate_source(&mut rng, token_count);
    let mut checksum: i64 = 0;
    for _ in 0..passes {
        let mut line_count: i64 = 0;
        let mut comment_count: i64 = 0;
        let tokens = tokenize(&source, &mut line_count, &mut comment_count);
        let mut kind_counts = [0i64; 5];
        let mut hash: i64 = 0;
        for token in &tokens {
            let kind_index = token.kind as i64;
            kind_counts[kind_index as usize] += 1;
            hash = hash.wrapping_mul(31).wrapping_add(kind_index);
            for &character in token.text.as_bytes() {
                hash = hash.wrapping_mul(131).wrapping_add(character as i64);
            }
        }
        checksum = checksum.wrapping_mul(31).wrapping_add(tokens.len() as i64);
        for kind_total in kind_counts {
            checksum = checksum.wrapping_mul(31).wrapping_add(kind_total);
        }
        checksum = checksum.wrapping_mul(31).wrapping_add(line_count);
        checksum = checksum.wrapping_mul(31).wrapping_add(comment_count);
        checksum = checksum.wrapping_mul(31).wrapping_add(hash);
    }
    println!("{} {}", source.len(), checksum);
}

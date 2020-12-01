use wasmparser::Parser;
use wasmparser::Payload::DataSection;

use std::collections::HashMap;
use std::collections::HashSet;
use std::path::Path;

use regex::bytes::Regex;

use indicatif::ProgressIterator;

/// Input: Filenames of Wasm binaries.
/// Output: JSON of all files with their strings (UTF-8 characters, longer than 3, after trimming whitespace)
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let (_, filenames) = args.split_at(1);

    // see https://en.wikipedia.org/wiki/Unicode_character_property#General_Category
    // let strings_regex = Regex::new(r"[\p{Letter}\p{Mark}\p{Number}\p{Punctuation}\p{Symbol}\p{Separator}]+").unwrap();

    // Alternative: only ASCII printable characters (more recall than below)
    let strings_regex = Regex::new(r"(?-u)[\x20-\x7E]+").unwrap();

    let mut strings_db = HashMap::new();

    for filename in filenames.iter().progress() {
        let bytes = std::fs::read(filename).unwrap();

        let mut strings = HashSet::new();

        let parser = Parser::new(0);
        for payload in parser.parse_all(&bytes) {
            // Ignore binaries that cannot be parsed or other errors...
            if payload.is_err() {
                break;
            }
            let payload = payload.unwrap();
            match payload {
                DataSection(mut reader) => {
                    for _ in 0..reader.get_count() {
                        if let Ok(data) = reader.read() {
                            for match_ in strings_regex.find_iter(data.data) {
                                let bytes = match_.as_bytes();
                                let string = std::str::from_utf8(bytes)
                                    .expect("should be valid UTF-8 due to the splitting!?");
                                let string = string.trim();
                                if string.len() > 3 {
                                    strings.insert(string.to_string());
                                }
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        let filestem = Path::new(filename).file_stem().unwrap().to_str().unwrap();
        strings_db.insert(filestem, strings);
    }

    println!("{}", serde_json::to_string(&strings_db).unwrap());
    // println!("{}", serde_json::to_string_pretty(&strings_db).unwrap());
}

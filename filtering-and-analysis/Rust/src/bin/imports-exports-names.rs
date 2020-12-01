use wasmparser::Name;
use wasmparser::NameSectionReader;
use wasmparser::Parser;
use wasmparser::Payload::CustomSection;
use wasmparser::Payload::ExportSection;
use wasmparser::Payload::ImportSection;

use std::collections::HashMap;
use std::collections::HashSet;
use std::path::Path;

use indicatif::ProgressIterator;

use serde::Serialize;

#[derive(Serialize, Default)]
struct Names {
    imports: HashSet<String>,
    exports: HashSet<String>,
    // Names in the custom 'name' section.
    module_name: Option<String>,
    function_names: HashSet<String>,
}

// Turns off filtering short names and demangling.
const SHORT_NAMES: bool = true;

/// Input: Filenames of Wasm binaries.
/// Output: JSON of all files with their names information.
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let (_, filenames) = args.split_at(1);

    let mut names_db = HashMap::new();

    for filename in filenames.iter().progress() {
        let bytes = std::fs::read(filename).unwrap();

        let mut names = Names::default();

        let parser = Parser::new(0);
        for payload in parser.parse_all(&bytes) {
            // Ignore binaries that cannot be parsed or other errors...
            if payload.is_err() {
                break;
            }
            let payload = payload.unwrap();
            match payload {
                ImportSection(mut reader) => {
                    for _ in 0..reader.get_count() {
                        if let Ok(import) = reader.read() {
                            let field = import.field.expect("Can imports have no field name?");
                            // Take only names if they have a minimum length
                            if SHORT_NAMES || field.len() > 2 {
                                let import = format!(
                                    "{}.{}",
                                    import.module,
                                    field
                                );
                                names.imports.insert(import);
                            }
                        }
                    }
                }
                ExportSection(mut reader) => {
                    for _ in 0..reader.get_count() {
                        if let Ok(export) = reader.read() {
                            // Take only names if they have a minimum length
                            if SHORT_NAMES || export.field.len() > 2 {
                                names.exports.insert(export.field.to_string());
                            }
                        }
                    }
                }
                CustomSection { name: "name", data_offset, data } => {
                    let mut reader = NameSectionReader::new(data, data_offset).unwrap();
                    while !reader.eof() {
                        if let Ok(name) = reader.read() {
                            match name {
                                Name::Module(module_name) => {
                                    if let Ok(module_name) = module_name.get_name() {
                                        names.module_name = Some(module_name.to_string());
                                    }
                                }
                                Name::Function(function_names) => {
                                    if let Ok(mut function_names) = function_names.get_map() {
                                        for _ in 0..function_names.get_count() {
                                            if let Ok(name) = function_names.read() {
                                                let name = match demangle(name.name) {
                                                    // If it can be demangled to Rust AND C++, take the shorter one
                                                    // (which is more likely being correct, since it has less special characters etc.)
                                                    (Some(cpp), Some(rust)) => if cpp.len() > rust.len() {
                                                        rust
                                                    } else {
                                                        cpp
                                                    },
                                                    (None, Some(rust)) => rust,
                                                    (Some(cpp), None) => cpp,
                                                    (None, None) => name.name.to_string(),
                                                };
                                                names.function_names.insert(name);
                                            }
                                        }
                                    }
                                }
                                Name::Local(_local_names) => {
                                    // ignore for now...
                                }
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        let filestem = Path::new(filename).file_stem().unwrap().to_str().unwrap();
        names_db.insert(filestem, names);
    }

    println!("{}", serde_json::to_string(&names_db).unwrap());
}

/// First is C++, second Rust, if any.
fn demangle(raw: &str) -> (Option<String>, Option<String>) {
    let cpp = cpp_demangle::Symbol::new(raw).ok().and_then(|sym| {
        sym.demangle(&cpp_demangle::DemangleOptions::default()).ok()
    });
    let rust = rustc_demangle::try_demangle(raw).as_ref().map(ToString::to_string).ok();
    (cpp, rust)
}
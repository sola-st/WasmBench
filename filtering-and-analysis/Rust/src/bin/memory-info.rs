use wasmparser::ImportSectionEntryType;
use wasmparser::MemoryType;
use wasmparser::Operator::{MemoryGrow, MemorySize};
use wasmparser::Parser;
use wasmparser::Payload::CodeSectionEntry;
use wasmparser::Payload::ImportSection;
use wasmparser::Payload::MemorySection;

use indicatif::ProgressIterator;

use std::collections::HashMap;
use std::collections::HashSet;
use std::path::Path;

use serde::Serialize;

#[derive(Serialize, Default)]
struct MemoryInfo {
    memory_count: usize,
    memories_upper_limit: Vec<bool>,
    memories_initial_size: Vec<u64>,
    // load_count: usize,
    // store_count: usize,
    memory_grow_size_functions: HashSet<usize>,
    memory_ops_count: usize,
    memory_grow_count: usize,
    memory_size_count: usize,
}

fn has_upper_limit(ty: MemoryType) -> bool {
    match ty {
        MemoryType::M32 { limits, .. } => limits.maximum.is_some(),
        MemoryType::M64 { limits } => limits.maximum.is_some(),
    }
}

fn initial_size(ty: MemoryType) -> u64 {
    match ty {
        MemoryType::M32 { limits, .. } => limits.initial as u64,
        MemoryType::M64 { limits } => limits.initial,
    }
}

// Input: filenames of Wasm binaries
// Output: JSON of all files with their stack pointer info
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let (_, filenames) = args.split_at(1);

    let mut memory_info_db = HashMap::new();

    for filename in filenames.iter().progress() {
        let bytes = std::fs::read(filename).unwrap();

        let mut info = MemoryInfo::default();

        let mut function_imports = 0;
        let mut code_section_entry_i = 0;

        let parser = Parser::new(0);
        for payload in parser.parse_all(&bytes) {
            let payload = payload.unwrap();
            match payload {
                ImportSection(mut reader) => {
                    for _ in 0..reader.get_count() {
                        let import = reader.read().unwrap();
                        if let ImportSectionEntryType::Function(..) = import.ty {
                            function_imports += 1;
                        }
                        if let ImportSectionEntryType::Memory(memory_ty) = import.ty {
                            info.memory_count += 1;
                            info.memories_upper_limit.push(has_upper_limit(memory_ty));
                            info.memories_initial_size.push(initial_size(memory_ty));
                        }
                    }
                }
                MemorySection(mut reader) => {
                    info.memory_count += reader.get_count() as usize;
                    for _ in 0..reader.get_count() {
                        let memory_ty = reader.read().unwrap();
                        info.memories_upper_limit.push(has_upper_limit(memory_ty));
                        info.memories_initial_size.push(initial_size(memory_ty));
                    }
                }
                CodeSectionEntry(function_body) => {
                    let function_idx = function_imports + code_section_entry_i;

                    let mut operators_reader = function_body.get_operators_reader().unwrap();
                    while !operators_reader.eof() {
                        // Ignore unknown/invalid opcodes
                        if let Ok(operator) = operators_reader.read() {
                            match operator {
                                MemorySize { .. } => {
                                    info.memory_size_count += 1;
                                    info.memory_grow_size_functions.insert(function_idx);
                                }
                                MemoryGrow { .. } => {
                                    info.memory_grow_count += 1;
                                    info.memory_grow_size_functions.insert(function_idx);
                                }
                                _ => {
                                    // Use string representation instead of pattern match on many instructions...
                                    let operator_string = format!("{:?}", operator);
                                    if operator_string.contains("MemoryImmediate") {
                                        info.memory_ops_count += 1;
                                    }

                                    // The following is a bit too slow, but you can do it to discern reads from writes.
                                    // if operator_string.contains("Load") {
                                    //     info.load_count += 1;
                                    //     info.ops_count += 1;
                                    // } else if operator_string.contains("Store") {
                                    //     info.store_count += 1;
                                    //     info.ops_count += 1;
                                    // } else if operator_string.contains("Rmw") {
                                    //     info.load_count += 1;
                                    //     info.store_count += 1;
                                    //     info.ops_count += 1;
                                    // } else if operator_string.contains("Notify") || operator_string.contains("Wait") {
                                    //     // Not a load or store, not sure what to do with it...
                                    //     info.ops_count += 1;
                                    // } else {
                                    //     assert!(
                                    //         !operator_string.contains("MemoryImmediate"),
                                    //         "memory operation that is not load, store, or atomic rmw: {}",
                                    //         operator_string
                                    //     );
                                    // }
                                }
                            };
                        }
                    }

                    code_section_entry_i += 1;
                }
                _ => {}
            }
        }

        let filestem = Path::new(filename).file_stem().unwrap().to_str().unwrap();
        memory_info_db.insert(filestem, info);
    }

    println!("{}", serde_json::to_string_pretty(&memory_info_db).unwrap());
}

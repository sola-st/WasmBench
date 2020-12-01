use wasmparser::Parser;
use wasmparser::Payload::CodeSectionEntry;
use wasmparser::Payload::GlobalSection;
use wasmparser::Payload::MemorySection;
use wasmparser::Payload::ImportSection;
use wasmparser::ImportSectionEntryType;
use wasmparser::Operator::{GlobalSet, GlobalGet};

use indicatif::ProgressIterator;

use std::collections::HashMap;
use std::collections::HashSet;
use std::path::Path;

use serde::{Serialize, Serializer};

#[derive(Serialize)]
struct StackPointerInfo {
    #[serde(serialize_with = "serialize_result")]
    stack_pointer_inferred: Result<u32, &'static str>,
    stack_pointer_reads: Option<usize>,
    stack_pointer_writes: Option<usize>,
    stack_pointer_area: Option<usize>,
    functions_using_stack_pointer: usize,
    functions_all_local: usize
}

fn serialize_result<S>(x: &Result<u32, &'static str>, s: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    match x {
        Ok(u) => s.serialize_u32(*u),
        Err(st) => s.serialize_str(st)
    }
}

// Input: filenames of Wasm binaries
// Output: JSON of all files with their stack pointer info
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let (_, filenames) = args.split_at(1);

    let mut stack_info_db = HashMap::new();

    for filename in filenames.iter()
    .progress() 
    {
        let bytes = std::fs::read(filename).unwrap();

        // Step 1: Infer the stack pointer.

        let mut globals_mut_i32 = HashSet::new();
        let mut globals_get_counts = HashMap::new();
        let mut globals_set_counts = HashMap::new();
        
        let mut imports_global_count = 0;
        let mut imports_global_i32 = HashMap::new();
        
        let mut functions_all_local = 0;
        let mut functions_using_stack_pointer = 0;
        
        let mut memory_count = 0;

        let parser = Parser::new(0);
        for payload in parser.parse_all(&bytes) {
            let payload = payload.unwrap();
            match payload {
                ImportSection(mut reader) => {
                    for _ in 0..reader.get_count() {
                        let import = reader.read().unwrap();
                        let import_field_name = import.field.unwrap_or("");

                        if let ImportSectionEntryType::Global(global_type) = import.ty {
                            // Remove this, if we want to extract all functions, regardless of import name.
                            if global_type.content_type == wasmparser::Type::I32 {
                                if import_field_name.to_ascii_lowercase().contains("stack") {
                                    imports_global_i32.insert(
                                        import_field_name.to_string(),
                                        imports_global_count,
                                    );
                                }
                            }

                            imports_global_count += 1;
                        }
                        if let ImportSectionEntryType::Memory(_) = import.ty {
                            memory_count += 1;
                        }
                    }
                }
                GlobalSection(mut reader) => {
                    for i in 0..reader.get_count() {
                        let global = reader.read().unwrap();
                        if global.ty.mutable && global.ty.content_type == wasmparser::Type::I32 {
                            globals_mut_i32.insert(i + imports_global_count);
                        }
                    }
                }
                MemorySection(reader) => {
                    memory_count += reader.get_count();
                }
                CodeSectionEntry(function_body) => {
                    functions_all_local += 1;

                    // If there are no globals with even a stack pointer type, 
                    // no need to inspect the instructions
                    if globals_mut_i32.is_empty() {
                        continue;
                    }

                    // // Collect all instructions.
                    let mut operators_reader = function_body.get_operators_reader().unwrap();
                    while !operators_reader.eof() {
                        // Ignore unknown/invalid opcodes
                        if let Ok(operator) = operators_reader.read() {
                            match operator {
                                GlobalGet { global_index } 
                                if globals_mut_i32.contains(&global_index) => 
                                    *globals_get_counts.entry(global_index).or_insert(0) += 1,
                                GlobalSet { global_index } 
                                if globals_mut_i32.contains(&global_index) => 
                                    *globals_set_counts.entry(global_index).or_insert(0) += 1,
                                _ => {}
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        let mut stack_pointer_reads = None;
        let mut stack_pointer_writes = None;
        let mut stack_pointer_area = None;

        let stack_pointer_inferred = if memory_count == 0 {
            Err("no local or imported memory")
        } else if globals_mut_i32.is_empty() {
            Err("no mutable i32 global")
        } else {
            let global_uses = globals_mut_i32
                .iter()
                .filter_map(|i| {
                    if let Some(set_count) = globals_set_counts.get(&i) {
                        if let Some(get_count) = globals_get_counts.get(&i) {
                            let area = *set_count * *get_count;
                            if *set_count > 3 && *get_count > 3 {
                                return Some((i, area, *get_count, *set_count));
                            }
                        }
                    }
                    None
                });

            let global_max_uses = global_uses.max_by_key(|(_i, area, _, _)| *area);
            if let Some((i, area, get, set)) = global_max_uses {
                stack_pointer_area = Some(area);
                stack_pointer_reads = Some(get);
                stack_pointer_writes = Some(set);
                Ok(*i)
            } else {
                Err("not enough uses of all candidate pointers")
            }
        };

        // Step 2: count how many functions use it.

        if let Ok(stack_pointer) = stack_pointer_inferred {
            let parser = Parser::new(0);
            for payload in parser.parse_all(&bytes) {
                let payload = payload.unwrap();
                match payload {
                    CodeSectionEntry(function_body) => {
                        let mut operators_reader = function_body.get_operators_reader().unwrap();
                        while !operators_reader.eof() {
                            // Ignore unknown/invalid opcodes
                            if let Ok(operator) = operators_reader.read() {
                                match operator {
                                    | GlobalGet { global_index }
                                    | GlobalSet { global_index }
                                    if stack_pointer == global_index => {
                                        functions_using_stack_pointer += 1;
                                        break;
                                    }
                                    _ => {}
                                }
                            }
                        }
                    }
                    _ => {}
                }
            }
        }

        let filestem = Path::new(filename).file_stem().unwrap().to_str().unwrap();
        
        stack_info_db.insert(filestem, StackPointerInfo {
            stack_pointer_inferred,
            stack_pointer_reads,
            stack_pointer_writes,
            stack_pointer_area,
            functions_using_stack_pointer,
            functions_all_local
        });
    }

    println!("{}", serde_json::to_string_pretty(&stack_info_db).unwrap());
}

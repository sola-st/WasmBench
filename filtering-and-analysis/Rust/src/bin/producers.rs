use wasmparser::Parser;
use wasmparser::Payload::CustomSection;
use wasmparser::ProducersSectionReader;

// Input: filename of Wasm binary
// Output: JSON of all producer sections in binary
fn main() {
    let args: Vec<String> = std::env::args().collect();

    let filename = &args[1];
    let bytes = std::fs::read(filename).unwrap();

    let parser = Parser::new(0);
    for payload in parser.parse_all(&bytes) {
        if let Ok(CustomSection { name: "producers", data_offset, data }) = payload {
            let mut reader = ProducersSectionReader::new(data, data_offset).unwrap();
            // NOTE / Simplification: assumes that there is only a single producer section, 
            // otherwise the output is not valid JSON.
            print!("{{");
            for i in 0..reader.get_count() {
                let field = reader.read().unwrap();
                // NOTE / Simplification: assumes there is only a single field of each name, 
                // otherwise the output is not valid JSON
                print!("{:?}:{{", field.name);
                let mut field_reader = field.get_producer_field_values_reader().unwrap();
                for j in 0..field_reader.get_count() {
                    let field_value = field_reader.read().unwrap();
                    print!("{:?}:{:?}", field_value.name, field_value.version);
                    if j < field_reader.get_count() - 1 {
                        print!(",")
                    }
                }
                print!("}}");
                if i < reader.get_count() - 1 {
                    print!(",")
                }
            }
            print!("}}");
        }
    }
}

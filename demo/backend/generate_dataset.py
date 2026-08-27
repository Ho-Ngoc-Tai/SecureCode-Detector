import json
import random

def inject_noise(code):
    # Data Augmentation: Randomly insert comments and spaces to prevent overfitting
    lines = code.split('\n')
    noisy_lines = []
    for line in lines:
        if line.strip() and random.random() < 0.2:
            comments = ["// check bounds", "// TODO: refactor", "// init memory", "// process buffer", "// debug print"]
            noisy_lines.append(f"    {random.choice(comments)}")
        noisy_lines.append(line + (' ' * random.randint(0, 3)))
    return '\n'.join(noisy_lines)

def generate_safe():
    vars = ['buf', 'data', 'str', 'text', 'temp', 'arr', 'block', 'cache']
    v = random.choice(vars)
    size = random.choice([16, 32, 64, 128, 256])
    code = f"""
void process_{v}() {{
    char {v}[{size}];
    const char *src = "safe_input_data_stream";
    strncpy({v}, src, sizeof({v}) - 1);
    {v}[sizeof({v}) - 1] = '\\0';
    printf("Processed: %s\\n", {v});
}}
"""
    return inject_noise(code)

def generate_cwe119():
    vars = ['buffer', 'input', 'payload', 'msg', 'packet', 'stream']
    v = random.choice(vars)
    size = random.choice([8, 16, 24, 32])
    bad_func = random.choice([
        f"strcpy({v}, external_input);",
        f"sprintf({v}, \"%s\", external_input);",
        f"gets({v});"
    ])
    code = f"""
void handle_{v}(char *external_input) {{
    char {v}[{size}];
    // CWE-119: Buffer Copy without Checking Size of Input
    {bad_func}
    process({v});
}}
"""
    return inject_noise(code)

def generate_cwe399():
    vars = ['ptr', 'mem', 'chunk', 'obj', 'node', 'buffer_ptr']
    v = random.choice(vars)
    scenario = random.choice(['leak', 'double_free', 'use_after_free'])
    
    if scenario == 'leak':
        code = f"""
void allocate_{v}() {{
    char *{v} = (char *)malloc(1024);
    if (!{v}) return;
    // CWE-399: Memory Leak (missing free)
    load_data({v});
    return; 
}}
"""
    elif scenario == 'double_free':
        code = f"""
void cleanup_{v}(char *{v}) {{
    if ({v}) {{
        free({v});
    }}
    // CWE-399: Double Free
    free({v});
}}
"""
    else:
        code = f"""
void use_{v}() {{
    char *{v} = (char *)malloc(128);
    free({v});
    // CWE-399: Use After Free
    {v}[0] = 'A';
}}
"""
    return inject_noise(code)

dataset = []
# 0 = Safe, 1 = CWE-119, 2 = CWE-399
# Generate 3000 of each to make 9000 total samples
for _ in range(3000):
    dataset.append({"code": generate_safe(), "label": 0})
    dataset.append({"code": generate_cwe119(), "label": 1})
    dataset.append({"code": generate_cwe399(), "label": 2})

random.shuffle(dataset)

with open('mini_dataset.json', 'w') as f:
    json.dump(dataset, f, indent=2)

print(f"Generated {len(dataset)} samples in mini_dataset.json")

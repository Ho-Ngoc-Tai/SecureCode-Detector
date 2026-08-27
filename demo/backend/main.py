from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import torch.nn.functional as F
from model import DefectScannerCNN, get_tokenizer
import os
import zipfile
import io

app = FastAPI(title="Defect-Scanner API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    code: str

# Global variables for model and tokenizer
model = None
tokenizer = None
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

@app.on_event("startup")
async def startup_event():
    global model, tokenizer
    print("Loading tokenizer...")
    tokenizer = get_tokenizer()
    print("Loading model...")
    model = DefectScannerCNN().to(device)
    
    weight_path = "weights/model.pth"
    if os.path.exists(weight_path):
        model.load_state_dict(torch.load(weight_path, map_location=device))
        print(f"Loaded weights from {weight_path}")
    else:
        print("WARNING: Model weights not found. Using untrained model.")
    model.eval()

def predict_chunk(code_chunk: str):
    # Tokenize the input code
    encoding = tokenizer(
        code_chunk,
        truncation=True,
        padding='max_length',
        max_length=128,
        return_tensors='pt'
    )
    
    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)
    
    # Run model
    with torch.no_grad():
        logits = model(input_ids, attention_mask)
        probs = F.softmax(logits, dim=1)
        
        predicted_class_id = torch.argmax(probs, dim=1).item()
        confidence = probs[0][predicted_class_id].item()
        
    return predicted_class_id, confidence

def analyze_code(code: str):
    # Split code into chunks (e.g. by double newline or chunks of lines)
    # For PoC, we will split into chunks of ~20 lines
    lines = code.split('\n')
    chunk_size = 20
    
    worst_class = 0 # 0=Safe, 1=CWE-119, 2=CWE-399
    highest_confidence = 0.0
    
    if not lines:
        return 0, 1.0 # Safe
        
    for i in range(0, len(lines), chunk_size):
        chunk = '\n'.join(lines[i:i+chunk_size])
        if not chunk.strip():
            continue
            
        pred_class, conf = predict_chunk(chunk)
        # Prioritize vulnerable over safe, and higher confidence
        if pred_class != 0:
            if worst_class == 0 or conf > highest_confidence:
                worst_class = pred_class
                highest_confidence = conf
        else:
            if worst_class == 0 and conf > highest_confidence:
                highest_confidence = conf
                
    return worst_class, highest_confidence

def format_result(pred_class, conf):
    is_vulnerable = pred_class != 0
    if pred_class == 1:
        cwe_id = "CWE-119"
        details = "Buffer Copy without Checking Size of Input / Out-of-bounds Write"
    elif pred_class == 2:
        cwe_id = "CWE-399"
        details = "Resource Management Error (Memory Leak / Double Free / Use After Free)"
    else:
        cwe_id = "SAFE"
        details = "Code conforms to security patterns."
        
    return {
        "status": "success",
        "is_vulnerable": is_vulnerable,
        "cwe_id": cwe_id,
        "vulnerability_score": conf,
        "details": details
    }

@app.post("/api/scan")
async def scan_code(request: ScanRequest):
    code = request.code
    if not code.strip():
        return {"status": "error", "message": "Empty code provided"}
        
    pred_class, conf = analyze_code(code)
    return format_result(pred_class, conf)

@app.post("/api/scan_file")
async def scan_file(file: UploadFile = File(...)):
    content = await file.read()
    results = []
    
    if file.filename.endswith('.zip'):
        # Parse zip file
        with zipfile.ZipFile(io.BytesIO(content)) as zip_ref:
            for zip_info in zip_ref.infolist():
                if zip_info.is_dir() or not zip_info.filename.endswith(('.c', '.cpp', '.h')):
                    continue
                file_content = zip_ref.read(zip_info.filename).decode('utf-8', errors='ignore')
                pred_class, conf = analyze_code(file_content)
                res = format_result(pred_class, conf)
                res["filename"] = zip_info.filename
                results.append(res)
    else:
        # Parse single file
        file_content = content.decode('utf-8', errors='ignore')
        pred_class, conf = analyze_code(file_content)
        res = format_result(pred_class, conf)
        res["filename"] = file.filename
        results.append(res)
        
    return {"status": "success", "results": results}

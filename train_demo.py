import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from model import DefectScannerCNN, get_tokenizer
import os

# Toy dataset for demonstration
code_samples = [
    # Vulnerable samples (CWE-119 Buffer Overflow, etc.)
    {"code": "void func(char *str) { char buffer[10]; strcpy(buffer, str); }", "label": 1},
    {"code": "int main() { char buf[50]; gets(buf); return 0; }", "label": 1},
    {"code": "void copy_data(char *src) { char dest[128]; sprintf(dest, \"%s\", src); }", "label": 1},
    # Safe samples
    {"code": "void func(char *str) { char buffer[10]; strncpy(buffer, str, sizeof(buffer)-1); buffer[9] = '\\0'; }", "label": 0},
    {"code": "int main() { char buf[50]; fgets(buf, sizeof(buf), stdin); return 0; }", "label": 0},
    {"code": "void copy_data(char *src) { char dest[128]; snprintf(dest, sizeof(dest), \"%s\", src); }", "label": 0},
]

class CodeDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=128):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        encoding = self.tokenizer(
            item["code"],
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'label': torch.tensor(item["label"], dtype=torch.long)
        }

def train():
    print("Initializing tokenizer and dataset...")
    tokenizer = get_tokenizer()
    dataset = CodeDataset(code_samples * 10, tokenizer) # duplicate data to have enough batches
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    print("Initializing model CodeBERT + CNN...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DefectScannerCNN().to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    
    epochs = 3
    print(f"Starting training on {device} for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")
        
    os.makedirs('weights', exist_ok=True)
    torch.save(model.state_dict(), 'weights/model.pth')
    print("Training complete. Model saved to weights/model.pth")

if __name__ == "__main__":
    train()

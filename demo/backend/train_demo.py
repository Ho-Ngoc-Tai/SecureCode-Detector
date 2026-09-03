import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from model import DefectScannerCNN, get_tokenizer
import os

import json

# Load dataset generated previously
with open(r"d:\Master's Thesis\Defect-Scanner\demo\backend\mini_dataset.json", 'r') as f:
    code_samples = json.load(f)

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
    dataset = CodeDataset(code_samples, tokenizer)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    print("Initializing model CodeBERT + CNN...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DefectScannerCNN().to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4, weight_decay=1e-4) # Added Weight Decay to prevent overfitting
    
    epochs = 3
    epoch_losses = []
    
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
            
        avg_loss = total_loss / len(dataloader)
        epoch_losses.append(avg_loss)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
    os.makedirs('weights', exist_ok=True)
    torch.save(model.state_dict(), 'weights/model.pth')
    print("Training complete. Model saved to weights/model.pth")
    
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 5))
        plt.plot(range(1, epochs + 1), epoch_losses, marker='o', linestyle='-', color='b', label='Training Loss')
        plt.title('Training Loss per Epoch (9000 samples)')
        plt.xlabel('Epoch')
        plt.ylabel('Cross-Entropy Loss')
        plt.grid(True)
        plt.legend()
        plt.savefig('loss_chart.png')
        print("Loss chart saved to loss_chart.png")
    except ImportError:
        print("matplotlib not installed. Skipping loss chart generation.")

if __name__ == "__main__":
    train()

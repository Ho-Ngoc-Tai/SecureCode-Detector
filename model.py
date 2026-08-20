import torch
import torch.nn as nn
from transformers import RobertaModel, RobertaTokenizer

class DefectScannerCNN(nn.Module):
    def __init__(self, codebert_model_name='microsoft/codebert-base', hidden_size=768, num_filters=128, kernel_sizes=[3, 4, 5], num_classes=2):
        super(DefectScannerCNN, self).__init__()
        # Load pre-trained CodeBERT
        self.codebert = RobertaModel.from_pretrained(codebert_model_name)
        
        # CNN layers
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=hidden_size, out_channels=num_filters, kernel_size=k)
            for k in kernel_sizes
        ])
        
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(len(kernel_sizes) * num_filters, num_classes)
        
    def forward(self, input_ids, attention_mask):
        # Get embeddings from CodeBERT
        # outputs[0] is the last hidden state of shape (batch_size, sequence_length, hidden_size)
        outputs = self.codebert(input_ids=input_ids, attention_mask=attention_mask)
        x = outputs[0]
        
        # Conv1d expects (batch_size, channels, sequence_length)
        x = x.permute(0, 2, 1)
        
        # Apply convolution and max pooling
        conv_outs = []
        for conv in self.convs:
            # conv(x): (batch_size, num_filters, L_out)
            c = torch.relu(conv(x))
            # Max pooling over the sequence dimension
            p = torch.max(c, dim=2)[0] # (batch_size, num_filters)
            conv_outs.append(p)
            
        # Concatenate features from different kernel sizes
        x = torch.cat(conv_outs, dim=1) # (batch_size, len(kernel_sizes) * num_filters)
        
        x = self.dropout(x)
        logits = self.fc(x)
        return logits

def get_tokenizer(model_name='microsoft/codebert-base'):
    return RobertaTokenizer.from_pretrained(model_name)

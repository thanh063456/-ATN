#!/usr/bin/env python3
import torch
import sys
import numpy as np
if not hasattr(np, 'sctypes'):
    np.sctypes = {
        'float': [np.float16, np.float32, np.float64],
        'int': [np.int8, np.int16, np.int32, np.int64],
        'uint': [np.uint8, np.uint16, np.uint32, np.uint64],
        'complex': [np.complex64, np.complex128],
        'others': [bool, object, bytes, str, np.void]
    }
from vietocr.tool.config import Cfg

def main():
    config = Cfg.load_config_from_name('vgg_transformer')
    old_vocab = config['vocab']
    
    new_chars = '–“”…+‘’'
    # Add only chars not in old_vocab
    to_add = [c for c in new_chars if c not in old_vocab]
    if not to_add:
        print("All characters already in vocab.")
        return
        
    print(f"Adding characters: {to_add}")
    new_vocab = old_vocab + ''.join(to_add)
    print(f"New vocab length: {len(new_vocab)}")
    
    # We must patch the checkpoint. But wait, if we download the pretrained weights,
    # we can load it, change the FC layer, and save it.
    config['vocab'] = old_vocab
    config['device'] = 'cpu'
    
    # Init model with OLD vocab
    try:
        from vietocr.tool.translate import build_model
        model, vocab = build_model(config)
    except Exception as e:
        print(f"Failed to build model: {e}")
        sys.exit(1)
        
    print("Model loaded with old vocab.")
    
    # The last layer is model.transformer.fc (Linear layer) for vgg_transformer
    fc = model.transformer.fc
    in_features = fc.in_features
    out_features = fc.out_features
    
    assert out_features == len(old_vocab) + 4, f"Mismatch: {out_features} vs {len(old_vocab) + 4}"
    
    # Create new FC layer
    new_out_features = len(new_vocab) + 4
    new_fc = torch.nn.Linear(in_features, new_out_features)
    
    # Copy old weights and biases
    new_fc.weight.data[:out_features, :] = fc.weight.data
    new_fc.bias.data[:out_features] = fc.bias.data
    
    # Initialize new weights randomly (e.g. mean=0, std=0.02)
    torch.nn.init.normal_(new_fc.weight.data[out_features:, :], std=0.02)
    torch.nn.init.zeros_(new_fc.bias.data[out_features:])
    
    model.transformer.fc = new_fc
    
    # Save the new weights
    out_path = 'models/vgg_transformer_extended.pth'
    import os
    os.makedirs('models', exist_ok=True)
    torch.save(model.state_dict(), out_path)
    
    print(f"Saved extended model to {out_path}")
    print("Now you can update your config to use the new vocab and this checkpoint!")

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""stable_diff.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CW2PHND4bE2DiZE7XOOpXeNXMsXaRrb6
"""

!pip install datasets

import numpy as np
from PIL import Image
from datasets import load_dataset

dataset = load_dataset('poloclub/diffusiondb', '2m_first_5k')

print(dataset.keys())

my_5k_data = dataset['train']
my_5k_data

random_i = np.random.choice(range(my_5k_data.num_rows))
#Print out the prompt of this image
print(my_5k_data['prompt'][random_i])

# Display this image
imaz = my_5k_data['image'][random_i]
display(imaz)

import pandas as pd
txt = my_5k_data['prompt']
df = pd.DataFrame(txt)
df.rename(columns = {0 : 'Prompts'}, inplace = True)
df.head()

!pip install emoji

import string
regular_punct = list(string.punctuation)
def remove_punctuation(text1,punct_list):
    for punc in punct_list:
        if punc in text1:
            text1 = text1.replace(punc, '')
    return text1.strip()

import emoji
import re
def remove_emojis(txt):
    txt = emoji.demojize(txt)
    txt = re.sub(r':[a-zA-Z_]+:', '', txt)



    return txt

for i in range(len(df)):
  df.loc[i, "Prompts"] = remove_emojis(df.loc[i, "Prompts"])
  df.loc[i, "Prompts"] = remove_punctuation(df.loc[i, "Prompts"],regular_punct)
  df.loc[i, "Prompts"] = ''.join ([i for i in df.loc[i, "Prompts"] if not i.isdigit()])
  df.loc[i, "Prompts"] = " ".join(df.loc[i, "Prompts"].split())
  print(df.loc[i, "Prompts"])

df.head()

images = my_5k_data['image']

import os
from PIL import Image

# List of image objects
image_list = images

directory = '/content/sample_data/image_file'
os.makedirs(directory, exist_ok=True)


for i, image in enumerate(image_list):

    image_filename = f"image_{i}.jpg"
    save_path = os.path.join(directory, image_filename)
    image.save(save_path)

import os
import cv2
import numpy as np


images_path = '/content/sample_data/image_file'
target_size = (256, 256)

preprocessed_images = []


for image_file in os.listdir(images_path):
    image = cv2.imread(os.path.join(images_path, image_file))
    image = cv2.resize(image, target_size)
    image = image.astype('float32') / 255.
    preprocessed_images.append(image)

preprocessed_images = np.array(preprocessed_images)

preprocessed_images

!pip install transformers

import pandas as pd
import torch
import transformers
import numpy as np

prompts = df['Prompts'].tolist()


model_name = 'gpt2'
tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
model = transformers.AutoModelForCausalLM.from_pretrained(model_name)


device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)

embeddings = []
for prompt in prompts:
    inputs = tokenizer(prompt, return_tensors='pt')
    inputs = {key: value.to(device) for key, value in inputs.items()}
    outputs = model(**inputs, output_hidden_states=True)
    embeddings.append(outputs.hidden_states[-1].mean(dim=1).squeeze().detach().cpu().numpy())

embeddings = np.array(embeddings)

embeddings

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torchvision.models import resnet18
from torch.utils.data import DataLoader, Dataset
import numpy as np

class ImageDataset(Dataset):
    def __init__(self, images, embeddings, transform=None):
        self.images = images
        self.embeddings = embeddings
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image = self.images[idx]
        embedding = self.embeddings[idx]

        if self.transform:
            image = self.transform(image)

        return image, embedding

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
    transforms.ToTensor()
])

X = torch.tensor(X_train.transpose(0, 3, 1, 2), dtype=torch.float32)
y = torch.tensor(y_train, dtype=torch.float32)

dataset = ImageDataset(X, y, transform=transform)
data_loader = DataLoader(dataset, batch_size=4, shuffle=True, num_workers=0)

model = resnet18(pretrained=True)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, embeddings.shape[1])
model = model.to(device)


criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)


num_epochs = 100
for epoch in range(num_epochs):
    for images, targets in data_loader:
        images = images.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

    print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}")

# Test the model
def image_to_prompt(image):
    model.eval()
    with torch.no_grad():
        image_tensor = torch.tensor(image.transpose(2, 0, 1)[np.newaxis], dtype=torch.float32).to(device)
        embedding = model(image_tensor).cpu().numpy()

        similarity = np.dot(embeddings, embedding.T).squeeze()
        closest_prompt_index = np.argmax(similarity)
        return prompts[closest_prompt_index]


test_image = preprocessed_images[0]
generated_prompt = image_to_prompt(test_image)
print("Generated prompt:", generated_prompt)

from transformers import AutoTokenizer, AutoModel

def calculate_similarity(new_prompt, actual_prompt, model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    inputs = tokenizer([new_prompt, actual_prompt], padding=True, truncation=True, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    new_prompt_embedding = outputs.last_hidden_state[0]
    actual_prompt_embedding = outputs.last_hidden_state[1]

    similarity = torch.cosine_similarity(new_prompt_embedding, actual_prompt_embedding, dim=0)

    return similarity.item()
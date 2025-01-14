import streamlit as st
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler

dirname = os.path.dirname(__file__)

# Neural Network Model
class EmissionPredictor(nn.Module):
    def __init__(self, input_dim):
        super(EmissionPredictor, self).__init__()
        self.layer1 = nn.Linear(input_dim, 64)
        self.layer2 = nn.Linear(64, 32)
        self.layer3 = nn.Linear(32, 2)  # 2 outputs: CO2 emissions and fuel consumption
        self.relu = nn.ReLU()
        
    def forward(self, x):
        x = self.relu(self.layer1(x))
        x = self.relu(self.layer2(x))
        x = self.layer3(x)
        return x

def preprocess_input(vehicle_class, engine_size, cylinders, transmission, fuel_type):
    # Create mapping dictionaries for categorical variables
    vehicle_class_map = {
        'COMPACT': 0,
        'SUV - SMALL': 11,
        'MID-SIZE': 2,
        'TWO-SEATER': 13,
        'MINICOMPACT': 3,
        'SUBCOMPACT': 10,
        'FULL-SIZE': 1,
        'STATION WAGON - SMALL': 9,
        'SUV - STANDARD': 12,
        'VAN - CARGO': 14,
        'VAN - PASSENGER': 15,
        'PICKUP TRUCK - STANDARD': 6,
        'MINIVAN': 4,
        'SPECIAL PURPOSE VEHICLE': 7,
        'STATION WAGON - MID-SIZE': 8,
        'PICKUP TRUCK - SMALL': 5
    }
    
    transmission_map = {
        'AS5': 14,
        'M6': 25,
        'AV7': 22,
        'AS6': 15,
        'AM6': 8,
        'A6': 3,
        'AM7': 9,
        'AV8': 23,
        'AS8': 17,
        'A7': 4,
        'A8': 5,
        'M7': 26,
        'A4': 1,
        'M5': 24,
        'AV': 19,
        'A5': 2,
        'AS7': 16,
        'A9': 6,
        'AS9': 18,
        'AV6': 21,
        'AS4': 13,
        'AM5': 7,
        'AM8': 10,
        'AM9': 11,
        'AS10': 12,
        'A10': 0,
        'AV10': 20
    }
    
    fuel_type_map = {
        'Z': 4,
        'D': 0,
        'X': 3,
        'E': 1,
        'N': 2
    }
    
    # Convert inputs to numerical values
    vehicle_class_num = vehicle_class_map[vehicle_class]
    transmission_num = transmission_map[transmission]
    fuel_type_num = fuel_type_map[fuel_type]
    
    # Create input array
    input_data = np.array([[
        vehicle_class_num,
        float(engine_size),
        int(cylinders),
        transmission_num,
        fuel_type_num
    ]])
    
    # Scale input data
    scaler = StandardScaler()
    # Note: In production, you should load the same scaler used during training
    scaled_input = scaler.fit_transform(input_data)
    
    return scaled_input

# Load the trained model
def load_model():
    model = EmissionPredictor(input_dim=5)
    model.load_state_dict(torch.load(dirname + '/models/emission_predictor.pth'))
    model.eval()
    return model
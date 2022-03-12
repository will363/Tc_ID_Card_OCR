
from matplotlib import pyplot as plt
import numpy as np
import torch
import cv2
import numpy as np
import segmentation_models_pytorch as smp

import torch
import torch.nn as nn


def double_conv(in_c, out_c):
    conv = nn.Sequential(
        nn.Conv2d(in_c, out_c, kernel_size=3, stride=1, padding=1),
        nn.BatchNorm2d(out_c),
        nn.ReLU(inplace=True),
        nn.Conv2d(out_c, out_c, kernel_size=3, stride=1, padding=1),
        nn.BatchNorm2d(out_c),
        nn.ReLU(inplace=True)
    )
    return conv


def addPadding(srcShapeTensor, tensor_whose_shape_isTobechanged):

    if(srcShapeTensor.shape != tensor_whose_shape_isTobechanged.shape):
        target = torch.zeros(srcShapeTensor.shape)
        target[:, :, :tensor_whose_shape_isTobechanged.shape[2],
               :tensor_whose_shape_isTobechanged.shape[3]] = tensor_whose_shape_isTobechanged
        return target
    return tensor_whose_shape_isTobechanged

class UNet(nn.Module):
    def __init__(self):
        super(UNet, self).__init__()
        self.max_pool_2x2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.down_conv_1 = double_conv(3, 64)
        self.down_conv_2 = double_conv(64, 128)
        self.down_conv_3 = double_conv(128, 256)
        self.down_conv_4 = double_conv(256, 512)
        self.down_conv_5 = double_conv(512, 1024)

        self.up_trans_1 = nn.ConvTranspose2d(
            in_channels=1024,
            out_channels=512,
            kernel_size=2,
            stride=2
        )
        self.up_conv_1 = double_conv(1024, 512)

        self.up_trans_2 = nn.ConvTranspose2d(
            in_channels=512,
            out_channels=256,
            kernel_size=2,
            stride=2
        )
        self.up_conv_2 = double_conv(512, 256)

        self.up_trans_3 = nn.ConvTranspose2d(
            in_channels=256,
            out_channels=128,
            kernel_size=2,
            stride=2
        )
        self.up_conv_3 = double_conv(256, 128)

        self.up_trans_4 = nn.ConvTranspose2d(
            in_channels=128,
            out_channels=64,
            kernel_size=2,
            stride=2
        )
        self.up_conv_4 = double_conv(128, 64)

        self.out = nn.Conv2d(
            in_channels=64,
            out_channels=1,
            kernel_size=1
        )

    def forward(self, image):
        # expected size
        # encoder (Normal convolutions decrease the size)
        x1 = self.down_conv_1(image)
        # print("x1 "+str(x1.shape))
        x2 = self.max_pool_2x2(x1)
        # print("x2 "+str(x2.shape))
        x3 = self.down_conv_2(x2)
        # print("x3 "+str(x3.shape))
        x4 = self.max_pool_2x2(x3)
        # print("x4 "+str(x4.shape))
        x5 = self.down_conv_3(x4)
        # print("x5 "+str(x5.shape))
        x6 = self.max_pool_2x2(x5)
        # print("x6 "+str(x6.shape))
        x7 = self.down_conv_4(x6)
        # print("x7 "+str(x7.shape))
        x8 = self.max_pool_2x2(x7)
        # print("x8 "+str(x8.shape))
        x9 = self.down_conv_5(x8)
        # print("x9 "+str(x9.shape))

        # decoder (transposed convolutions increase the size)
        x = self.up_trans_1(x9)
        x = addPadding(x7, x)
        x = self.up_conv_1(torch.cat([x7, x], 1))

        x = self.up_trans_2(x)
        x = addPadding(x5, x)
        x = self.up_conv_2(torch.cat([x5, x], 1))

        x = self.up_trans_3(x)
        x = addPadding(x3, x)
        x = self.up_conv_3(torch.cat([x3, x], 1))

        x = self.up_trans_4(x)
        x = addPadding(x1, x)
        x = self.up_conv_4(torch.cat([x1, x], 1))

        x = self.out(x)
        # print(x.shape)
        return x


def unet_segment_model(input_image, DEVICE):
    #model = smp.Unet(encoder_name="resnet50", encoder_weights="imagenet", in_channels=3, classes = 1, activation='sigmoid')
    model = smp.Unet(encoder_name="resnet34", encoder_weights="imagenet", in_channels=3, classes = 1)
    model.load_state_dict(torch.load('model/resnet34/UNet.pth'))
    #model = torch.load('model/resnet34/best_model.pth', map_location=DEVICE)
    model = model.to("cuda")

    input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
    
    img = torch.tensor(input_image)
    
    img = img.permute((2, 0, 1))
   
    img = img.unsqueeze(0).float()
    img = img.to(DEVICE)
    output = model(img)
    output= output.squeeze(0)
    output[output>0.0] = 1.0
    output[output<=0.0]=0
    output = output.squeeze(0)
    
    predicted_mask = output.detach().cpu().numpy()
    
    
    return np.uint8(predicted_mask)
    #return predicted_mask

def UnetModel(input_image):

    model = UNet()
    model.load_state_dict(torch.load('model/unetModel_20.pth'))
    model = model.to("cuda")

    input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
    
    img = torch.tensor(input_image)
    img = img.permute((2, 0, 1))
    img = img.unsqueeze(0).float()
    img = img.to("cuda")
    output = model(img)
    output= output.squeeze(0)
    output[output>0.0] = 1.0
    output[output<=0.0]=0
    output = output.squeeze(0)
    
    predicted_mask = output.detach().cpu().numpy()
    
    
    return np.uint8(predicted_mask)

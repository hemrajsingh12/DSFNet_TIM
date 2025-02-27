import torch
from torch.autograd import Variable
import os
import argparse
from datetime import datetime
from lib.DSFNet import DSFNet
from utils.dataloader import get_loader
from utils.utils import clip_gradient, poly_lr, AvgMeter
import torch.nn.functional as F
from utils.AdaX import AdaXW
import torch.nn as nn
import torch.optim as optim
from SEAdam import WAAPSO


def structure_loss(pred, mask):
    weit = 1 + 5*torch.abs(F.avg_pool2d(mask, kernel_size=31, stride=1, padding=15) - mask)
    wbce = F.binary_cross_entropy_with_logits(pred, mask, reduce='none')
    wbce = (weit*wbce).sum(dim=(2, 3)) / weit.sum(dim=(2, 3))

    pred = torch.sigmoid(pred)
    inter = ((pred * mask)*weit).sum(dim=(2, 3))
    union = ((pred + mask)*weit).sum(dim=(2, 3))
    wiou = 1 - (inter + 1)/(union - inter+1)
    return (wbce + wiou).mean()


def train(train_loader, model, optimizer, epoch):
    model.train()
    # ---- multi-scale training ----
    size_rates = [0.75, 1, 1.25]
    loss_record3 = AvgMeter()
    for i, pack in enumerate(train_loader, start=1):
        for rate in size_rates:
            optimizer.zero_grad()
            # ---- data prepare ----
            images, gts = pack
            images = Variable(images).cuda()
            gts = Variable(gts).cuda()
            # ---- rescale ----
            trainsize = int(round(opt.trainsize*rate/32)*32)
            if rate != 1:
                images = F.upsample(images, size=(trainsize, trainsize), mode='bilinear', align_corners=True)
                gts = F.upsample(gts, size=(trainsize, trainsize), mode='bilinear', align_corners=True)
            # ---- forward ----
            lateral_map_3 = model(images)
            # ---- loss function ----
            loss3 = structure_loss(lateral_map_3, gts)
            loss = loss3
            # ---- backward ----
            loss.backward()
            # updating the graident using pso
            #pso.update()
            # For calibrating misalignment gradient via cliping gradient technique
            clip_gradient(optimizer, opt.clip)
            optimizer.step()
            # ---- recording loss ----
            if rate == 1:
                loss_record3.update(loss3.data, opt.batchsize)
        # ---- train visualization ----
        if i % 20 == 0 or i == total_step:
            print('{} Epoch [{:03d}/{:03d}], Step [{:04d}/{:04d}], '
                  '[lateral-3: {:.4f}]'.
                  format(datetime.now(), epoch, opt.epoch, i, total_step,
                         loss_record3.show()))
    save_path = 'checkpoints/{}/'.format(opt.train_save)
    os.makedirs(save_path, exist_ok=True)
    if (epoch+1) % 5 == 0:
        torch.save(model.state_dict(), save_path + 'DSFNet-%d.pth' % epoch)
        print('[Saving Snapshot:]', save_path + 'DSFNet-%d.pth'% epoch)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--epoch', type=int,
                        default=25, help='epoch number')
    parser.add_argument('--lr', type=float,
                        default=1e-4, help='learning rate')
    parser.add_argument('--batchsize', type=int,
                        default=12, help='training batch size')
    parser.add_argument('--trainsize', type=int,
                        default=352, help='training dataset size')
    parser.add_argument('--clip', type=float,
                        default=0.5, help='gradient clipping margin')
    parser.add_argument('--train_path', type=str,
                        default='/content/drive/MyDrive/dataset/DIM', help='path to train dataset')
    parser.add_argument('--train_save', type=str,
                        default='DSFNet')
    opt = parser.parse_args()

    # ---- build models ----
    torch.cuda.set_device(0)  # set your gpu device
    model = DSFNet().cuda()

    params = model.parameters()
    # Initialize the Adam optimizer
    #optimizer = optim.Adam(model.parameters(), lr=opt.lr, betas=(0.9, 0.999), eps=1e-8)
    
    #pso = PSO(model, learning_rate=opt.lr, weight_decay=0.0001, beta1=0.9, beta2=0.999, epsilon=1e-8, swarm_size=10)

    optimizer = WAAPSO(params)

    # print total parameters
    para = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print('Total number of parameter:',para)
    
    # load the dataset
    print('........ Load the dataset ........')
    image_root = '{}/RGB/'.format(opt.train_path)
    gt_root = '{}/GT/'.format(opt.train_path)

    train_loader = get_loader(image_root, gt_root, batchsize=opt.batchsize, trainsize=opt.trainsize)
    total_step = len(train_loader)

    print(".......... Start Training .........")

    for epoch in range(opt.epoch):
        poly_lr(optimizer, opt.lr, epoch, opt.epoch)
        train(train_loader, model, optimizer, epoch)

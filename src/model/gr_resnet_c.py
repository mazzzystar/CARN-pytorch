import torch
import torch.nn as nn
import model.ops as ops

class Block(nn.Module):
    def __init__(self, 
                 in_channels, out_channels,
                 group,
                 act=nn.ReLU(inplace=True)):
        super(Block, self).__init__()

        self.b1 = ops.DWResidualBlock(64, 64, group=group)

        self.combine = ops.BasicBlock(64*4, 64, 1)

    def forward(self, x):
        b0 = x
        b1 = self.b1(b0)
        b2 = self.b1(b1)
        b3 = self.b1(b2)

        out = self.combine(torch.cat([b0, b1, b2, b3], dim=1))
        return out
        

class Net(nn.Module):
    def __init__(self, **kwargs):
        super(Net, self).__init__()
        
        scale = kwargs.get("scale")
        multi_scale = kwargs.get("multi_scale")
        reduce_upsample = kwargs.get("reduce_upsample", False)
        group = kwargs.get("group", 64)
        group = kwargs.get("group", 64)

        self.sub_mean = ops.MeanShift((0.4488, 0.4371, 0.4040), sub=True)
        self.add_mean = ops.MeanShift((0.4488, 0.4371, 0.4040), sub=False)

        self.relu = nn.ReLU()
        self.entry = nn.Conv2d(3, 64, 3, 1, 1)

        self.b1 = Block(64, 64, group=group)
        self.b2 = Block(64, 64, group=group)
        self.b3 = Block(64, 64, group=group)
        self.c1 = ops.BasicBlock(64*2, 64, 1)
        self.c2 = ops.BasicBlock(64*3, 64, 1)
        self.c3 = ops.BasicBlock(64*4, 64, 1)
        
        self.upsample = ops.UpsampleBlock(64, scale=scale, 
                                          multi_scale=multi_scale, 
                                          reduce=reduce_upsample)
        
        self.exit = nn.Sequential(
            nn.Conv2d(64, 3, 3, 1, 1)
        )
                
    def forward(self, x, scale):
        x = self.sub_mean(x)
        x = self.entry(x)
        c0 = o0 = x

        b1 = self.b1(o0)
        c1 = torch.cat([c0, b1], dim=1)
        o1 = self.c1(c1)
        
        b2 = self.b2(o1)
        c2 = torch.cat([c1, b2], dim=1)
        o2 = self.c2(c2)
        
        b3 = self.b3(o2)
        c3 = torch.cat([c2, b3], dim=1)
        o3 = self.c3(c3)

        out = self.upsample(o3, scale=scale)

        out = self.exit(out)
        out = self.add_mean(out)

        return out
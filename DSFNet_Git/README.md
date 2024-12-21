## 1. DSFNet (IEEE Transtions on Instrument and Measurement 2024)
[DSFNet: Video Salient Object Detection Using a Novel Lightweight Deformable Separable Fusion Network](https://ieeexplore.ieee.org/abstract/document/10699367)

## 2. Requirements

 - Python 3.7, Pytorch 1.7, Cuda 10.1
 - Test on Win10 and Ubuntu 16.04

## 3. Data Preparation

 - Upload the dataset and trained model (epoch_100.pth). Then put the dataset under the following directory:
 
        -dataset\ 
          -DAVIS\  
          -FBMS\
          ...
        -pretrain
          -epoch_100.pth
          ...

      
## 4. Testing

    Directly run test.py
    
    The test maps will be saved to './resutls/'.

- Evaluate the result maps:
    
    You can evaluate the result maps using the tool in [Matlab Version](http://dpfan.net/d3netbenchmark/) or [Python_GPU Version](https://github.com/zyjwuyan/SOD_Evaluation_Metrics).
    
 
## 5. Citation

Please cite the following paper if you use this repository in your reseach

@article{
  singh2024dsfnet,
  title={DSFNet: Video Salient Object Detection using A Novel Lightweight Deformable Separable Fusion Network},
  author={Singh, Hemraj and Verma, Mridula and Cheruku, Ramalingaswamy},
  journal={IEEE Transactions on Instrumentation and Measurement},
  year={2024},
  publisher={IEEE}
}

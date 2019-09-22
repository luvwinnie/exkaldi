############# Version Information #############
# GRU sample model based on: PythonKaldi V1.6
# WangYu, University of Yamanashi 
# Sep 17, 2019
###############################################

from __future__ import print_function
import pythonkaldi as PK

import chainer
import chainer.functions as F
import chainer.links as L
from chainer.training import extensions

import random
import numpy as np, cupy as cp
import os, datetime
import argparse
import math
import socket

## ------ Parameter Configure -----
parser = argparse.ArgumentParser(description='GRU Acoustic model on TIMIT corpus')

parser.add_argument('--TIMITpath', '-t', type=str, default='/misc/Work18/wangyu/kaldi/egs/timit/demo', help='Kaldi timit rescipe folder')
parser.add_argument('--randomSeed', '-r', type=int, default=2234, help='Random seed')
parser.add_argument('--batchSize', '-b', type=int, default=8)
parser.add_argument('--gpu', '-g', type=int, default=0, help='GPU id (We defaultly use gpu)')
parser.add_argument('--epoch', '-e', type=int, default=27)
parser.add_argument('--outDir','-o',type=str,default='TIMIT_GRU_fmllr_exp')

parser.add_argument('--layer', '-l', type=int, default=5)
parser.add_argument('--hiddenNode', '-hn', type=int, default=550)
parser.add_argument('--dropout', '-do', type=float, default=0.2)

parser.add_argument('--useCMVN', '-u', type=bool, default=True)
parser.add_argument('--splice', '-s', type=int, default=0)
parser.add_argument('--delta', '-de', type=int, default=0)
parser.add_argument('--normalize', '-n', type=bool, default=True)

args = parser.parse_args()

assert args.gpu >= 0, 'We will use gpu so it is not expected a negative value.'
if args.outDir.endswith('/'):
    args.outDir = args.outDir[0:-1]

print("\n############## Parameters Configure ##############")
print('Start System Time:',datetime.datetime.now().strftime("%Y-%m-%d %X"))
print('Host Name:',socket.gethostname())
print('Fix Random Seed:',args.randomSeed)
print('Mini Batch Size:',args.batchSize)
print('GPU ID:',args.gpu)
print('Train Epochs:',args.epoch)
print('Output Folder:',args.outDir)
print('GRU layers:',args.layer)
print('GRU hidden nodes:',args.hiddenNode)
print('GRU dropout:',args.dropout)
print('Use CMVN:',args.useCMVN)
print('Splice N Frames:',args.splice)
print('Add N Deltas:',args.delta)
print('Normalize Dataset:',args.normalize)

## ------ Fix random seed -----
random.seed(args.randomSeed)
np.random.seed(args.randomSeed)
cp.random.seed(args.randomSeed)
chainer.configuration.config.deterministic = True
chainer.configuration.config.cudnn_deterministic = True

## ------ Define model/updater/evaluator -----
class GRUblock(chainer.Chain):
    def __init__(self,outDim,bi=True,ratio=0.):
        super(GRUblock,self).__init__()
        with self.init_scope():
            
            #Feed-forward connections
            self.wh = L.Linear(None,outDim,nobias=True)
            self.wz = L.Linear(None,outDim,nobias=True)
            self.wr = L.Linear(None,outDim,nobias=True)

            #Recurrent connections
            initializer = chainer.initializers.Orthogonal()
            self.uh = L.Linear(outDim,outDim,nobias=True,initialW=None)
            self.uz = L.Linear(outDim,outDim,nobias=True,initialW=None)
            self.ur = L.Linear(outDim,outDim,nobias=True,initialW=None)
            

            #Batch normarlize
            self.bn_wh = L.BatchNormalization(outDim,0.95)
            self.bn_wz = L.BatchNormalization(outDim,0.95)
            self.bn_wr = L.BatchNormalization(outDim,0.95)

            self.act = F.relu

            self.bi = bi
            self.outDim = outDim
            self.ratio = ratio

    def flip(self,x):
        new = []
        for i in range(len(x)):
            new.append(x[len(x)-i-1])
        return F.stack(new)   

    def __call__(self,x):

        #x:[padding_max_frames, batch_size, feature_dims]
        frames,bSize,inDim = x.shape
        xp = chainer.backend.get_array_module(x)

        if self.bi:
            h_init = xp.zeros([2*bSize,self.outDim],dtype=xp.float32)
            x = F.concat([x,self.flip(x)],1)
            
        else:
            h_init = xp.zeros([bSize,self.outDim],dtype=xp.float32)

        if chainer.training:
            drop_mask = xp.random.binomial(n=1, p=(1-self.ratio), size=h_init.shape)
        else:
            drop_mask = xp.array([1-self.ratio])

        wh_out = self.bn_wh(self.wh(x.reshape([-1,inDim]))).reshape([frames,-1,self.outDim])
        wz_out = self.bn_wz(self.wz(x.reshape([-1,inDim]))).reshape([frames,-1,self.outDim])
        wr_out = self.bn_wr(self.wr(x.reshape([-1,inDim]))).reshape([frames,-1,self.outDim])

        hidden = []
        ht = h_init

        for k in range(x.shape[0]):

            zt = F.sigmoid(wz_out[k] + self.uz(ht))
            rt = F.sigmoid(wr_out[k] + self.ur(ht))
            at = wh_out[k] + self.uh(rt*ht)
            hcand = self.act(at) * drop_mask
            ht = (zt*ht+(1-zt)*hcand)

            hidden.append(ht)
        
        h = F.stack(hidden)

        if self.bi:
            h_f = h[:,0:bSize]
            h_b = self.flip(h[:,bSize:])
            h = F.concat([h_f,h_b],2)

        return h

class GRU2(chainer.Chain):
    def __init__(self):
        super(GRU2,self).__init__()
        with self.init_scope():
            #global args 
            self.ln1 = GRUblock(outDim=550,ratio=0.2)
            self.ln2 = GRUblock(outDim=550,ratio=0.2)
            self.ln3 = GRUblock(outDim=550,ratio=0.2)
            self.ln4 = GRUblock(outDim=550,ratio=0.2)
            self.ln5 = GRUblock(outDim=550,ratio=0.2)

            self.ln6 = L.Linear(None,1968,initialW=chainer.initializers.HeNormal(),initial_bias=chainer.initializers.Zero())
            self.ln7 = L.Linear(None,49,initialW=chainer.initializers.HeNormal(),initial_bias=chainer.initializers.Zero())

    def __call__(self,x):

        x = F.pad_sequence(x,padding=0)
        x = F.transpose(x,[1,0,2])
    
        h = self.ln1(x)
        h = self.ln2(h)
        h = self.ln3(h)
        h = self.ln4(h)
        h = self.ln5(h)

        h = F.transpose(h,[1,0,2])
        
        h1 = self.ln6(h)
        h2 = self.ln7(h)

        return h1 ,h2

class Updater(chainer.training.StandardUpdater):
    def __init__(self,*args,**kwargs):
        self.supporter = kwargs.pop('supporter')
        super(Updater,self).__init__(*args,**kwargs)
        
    def convert(self,batch):
        data = []
        label1 = []
        label2 = []
        for x in batch:
            data.append(cp.array(x[:,0:-2],dtype=cp.float32))
            label1.append(cp.array(x[:,-2],dtype=cp.int32))
            label2.append(cp.array(x[:,-1],dtype=cp.int32))
        return data,cp.concatenate(label1,axis=0),cp.concatenate(label2,axis=0)

    def loss_fun(self,y1,y2,t1,t2):
        L1 = F.softmax_cross_entropy(y1,t1)
        L2 = F.softmax_cross_entropy(y2,t2)
        loss = L1 + L2
        acc = F.accuracy(F.softmax(y1,axis=1),t1)
        self.supporter.send_report({'epoch':self.epoch,'train_loss':loss,'train_acc':acc})
        return loss

    def update_core(self):
        optimizer = self.get_optimizer('main')
        model = optimizer.target

        batch = self.get_iterator('main').next()
        data,label1,label2 = self.convert(batch)

        with chainer.using_config('Train',True):
            h1,h2 = model(data)

        optimizer.update(self.loss_fun,h1,h2,label1,label2)

@chainer.training.make_extension()
class Evaluator(chainer.Chain):
    def __init__(self,data,model,supporter,optimizer,outDir,lr,device=0):
        super(Evaluator,self).__init__()
        with self.init_scope():

            self.model = model
            self.data = data
            self.gpu = device
            self.supporter = supporter
            self.optimizer = optimizer
            self.outDir = outDir
            self.lr = lr

            ## Prepare test feature data.
            global args
            filePath = args.TIMITpath + '/data-fmllr-tri3/test/feats.scp'
            feat = PK.load(filePath)
            if args.useCMVN:
                uttSpk = args.TIMITpath + '/data-fmllr-tri3/test/utt2spk'
                cmvnState = args.TIMITpath + '/data-fmllr-tri3/test/cmvn.ark'
                feat = PK.use_cmvn(feat,cmvnState,uttSpk)
            if args.delta > 0:  
                feat = PK.add_delta(feat,args.delta)
            if args.splice > 0:   
                feat = feat.splice(args.splice)
            feat = feat.array
            if args.normalize:   
                self.feat = feat.normalize()
            else:
                self.feat = feat               

    def convert(self,batch):
        data = []
        label1 = []
        label2 = []
        for x in batch:
            data.append(cp.array(x[:,0:-2],dtype=cp.float32))
            label1.append(cp.array(x[:,-2],dtype=cp.int32))
            label2.append(cp.array(x[:,-1],dtype=cp.int32))
        return data,cp.concatenate(label1,axis=0),cp.concatenate(label2,axis=0)

    def loss_fun(self,y1,y2,t1,t2):
        L1 = F.softmax_cross_entropy(y1,t1)
        L2 = F.softmax_cross_entropy(y2,t2)
        loss = L1 + L2
        acc = F.accuracy(F.softmax(y1,axis=1),t1)
        self.supporter.send_report({'dev_loss':loss,'dev_acc':acc})
        return loss

    def wer_fun(self,model,outDir):

        m,u = self.feat.merge(keepDim=True)

        print('Computing WER for TEST dataset: Forward network...',end=" "*50+'\r')
        l = len(m)
        temp = PK.KaldiDict()
        o = []
        with chainer.using_config('train',False),chainer.no_backprop_mode():
            for j in range(math.ceil(l/8)):
                data = [cp.array(x,dtype=cp.float32) for x in m[j*8:(j+1)*8]]
                out1,out2 = model(data)
                out = F.log_softmax(out1,axis=1)
                out.to_cpu()
                o.append(out.array)

        temp.remerge(np.concatenate(o,axis=0),u)

        print('Computing WER for TEST dataset: Transform network output...',end=" "*50+'\r')
        amp = temp.ark

        global args
        hmm = args.TIMITpath + '/exp/dnn4_pretrain-dbn_dnn_ali_test/final.mdl'
        hclg = args.TIMITpath + '/exp/tri3/graph/HCLG.fst'
        lexicon = args.TIMITpath + '/exp/tri3/graph/words.txt'

        print('Computing WER for TEST dataset: Generate lattice...',end=" "*50+'\r')
        lattice = PK.decode_lattice(amp,hmm,hclg,lexicon,Acwt=0.2)

        print('Computing WER for TEST dataset: Get 1best result...',end=" "*50+'\r')
        outs = lattice.get_1best_words(minLmwt=1,maxLmwt=10,outDir=outDir,asFile='outRaw.txt')

        phonemap = args.TIMITpath + '/conf/phones.60-48-39.map'
        outFilter = args.TIMITpath + '/local/timit_norm_trans.pl -i - -m {} -from 48 -to 39'.format(phonemap)
        if not os.path.isfile(outDir+'/test_filt.txt'):
            refText = args.TIMITpath + '/data/test/text'
            cmd = 'cat {} | {} > {}/test_filt.txt'.format(refText,outFilter,outDir)
            (_,_) = PK.run_shell_cmd(cmd)

        print('Computing WER for TEST dataset: Compute WER...',end=" "*50+'\r')
        minWER = None
        for k in range(1,11,1):
            cmd = 'cat {} | {} > {}/test_prediction_filt.txt'.format(outs[k],outFilter,outDir)
            (_,_) = PK.run_shell_cmd(cmd)
            os.remove(outs[k])
            score = PK.compute_wer('{}/test_filt.txt'.format(outDir),"{}/test_prediction_filt.txt".format(outDir),mode='all')
            if minWER == None or score['WER'] < minWER:
                minWER = score['WER']
        os.remove(outDir+'/test_prediction_filt.txt')
        self.supporter.send_report({'test_WER':minWER})

    def __call__(self,trainer):
        while True:
            batchdata = self.data.next()
            data,label1,label2 = self.convert(batchdata)
            with chainer.using_config('train',False),chainer.no_backprop_mode():
                h1,h2 = self.model(data)
                loss = self.loss_fun(h1,h2,label1,label2)
            if self.data.epochOver:
                break
        self.wer_fun(self.model,self.outDir)

        self.supporter.send_report({'lr':self.optimizer.lr})
        self.supporter.collect_report(plot=True)
        
        self.supporter.save_model(models={'GRU':self.model},iterSymbol=self.data.epoch-1,byKey='test_wer',maxValue=False)

        if len(self.lr) > 0 and self.supporter.judge('epoch','>=',self.lr[0][0]):
            self.optimizer.lr = self.lr[0][1]
            self.lr.pop(0)

## ------ Train model -----
def train_model():

    print("\n############## Train LSTM Acoustic Model ##############")

    global args

    if not os.path.isdir(args.outDir):
        os.mkdir(args.outDir)

    print('Prepare Data Iterator...')
    # Feature data
    trainScpFile = args.TIMITpath + '/data-fmllr-tri3/train/feats.scp'
    devScpFile = args.TIMITpath + '/data-fmllr-tri3/dev/feats.scp'

    # Label
    trainAliFile = args.TIMITpath + '/exp/dnn4_pretrain-dbn_dnn_ali/ali.*.gz'
    trainHmm = args.TIMITpath + '/exp/dnn4_pretrain-dbn_dnn_ali/final.mdl'

    devAliFile = args.TIMITpath + '/exp/dnn4_pretrain-dbn_dnn_ali_dev/ali.*.gz'
    devHmm = args.TIMITpath + '/exp/dnn4_pretrain-dbn_dnn_ali_dev/final.mdl'

    trainLabelPdf = PK.get_ali(trainAliFile,trainHmm)
    trainLabelPho = PK.get_ali(trainAliFile,trainHmm,True) 

    devLabelPdf = PK.get_ali(devAliFile,devHmm)
    devLabelPho = PK.get_ali(devAliFile,devHmm,True) 
    
    # Process function
    def loadTrainChunkData(feat):
        # <feat> is KaldiArk
        global args
        # use CMVN
        if args.useCMVN:
            uttSpk = args.TIMITpath + '/data-fmllr-tri3/train/utt2spk'
            cmvnState = args.TIMITpath + '/data-fmllr-tri3/train/cmvn.ark'
            feat = PK.use_cmvn(feat,cmvnState,uttSpk)
        # Add delta
        if args.delta > 0:  
            feat = PK.add_delta(feat,args.delta)
        # Splice front-back n frames
        if args.splice > 0:   
            feat = feat.splice(args.splice)
        # Transform to KaldiDict
        feat = feat.array
        # Normalize
        if args.normalize:   
            feat = feat.normalize()
        # Concatenate label           
        datas = feat.concat([trainLabelPdf,trainLabelPho],axis=1)
        # Transform trainable numpy data
        datas,_ = datas.merge(keepDim=True)
        return datas

    def loadDevChunkData(feat):
        # <feat> is KaldiArk
        global args
        # use CMVN
        if args.useCMVN:
            uttSpk = args.TIMITpath + '/data-fmllr-tri3/dev/utt2spk'
            cmvnState = args.TIMITpath + '/data-fmllr-tri3/dev/cmvn.ark'
            feat = PK.use_cmvn(feat,cmvnState,uttSpk)
        # Add delta
        if args.delta > 0:  
            feat = PK.add_delta(feat,args.delta)
        # Splice front-back n frames
        if args.splice > 0:   
            feat = feat.splice(args.splice)
        # Transform to KaldiDict
        feat = feat.array
        # Normalize
        if args.normalize:   
            feat = feat.normalize()
        # Concatenate label           
        datas = feat.concat([devLabelPdf,devLabelPho],axis=1)
        # Transform trainable numpy data
        datas,_ = datas.merge(keepDim=True)
        return datas

    # Prepare data iterator
    train = PK.DataIterator(trainScpFile,args.batchSize,chunks=5,processFunc=loadTrainChunkData,validDataRatio=0)
    print('Generate train dataset done. Chunks:{} / Batch size:{}'.format(train.chunks,train.batch_size))
    dev = PK.DataIterator(devScpFile,args.batchSize,chunks='auto',processFunc=loadDevChunkData,validDataRatio=0)
    print('Generate validation dataset done. Chunks:{} / Batch size:{}.'.format(dev.chunks,dev.batch_size))

    print('Prepare Model...')

    featDim = 40
    if args.delta>0:
        featDim *= (args.delta + 1)
    if args.splice > 0:
        featDim *= ( 2 * args.splice + 1 ) 
    model = GRU2()
    #model.to_gpu(args.gpu)

    print('Prepare Chainer Trainer...')
    lr = [(0,0.5),(10,0.25),(15,0.125),(17,0.07),(19,0.035),(22,0.02),(25,0.01)]
    #lr = [(0,0.0004)]
    print('Learning Rate:',lr)
    optimizer = chainer.optimizers.MomentumSGD(lr[0][1],momentum=0.0)
    #optimizer = chainer.optimizers.RMSprop(lr[0][1],0.95,1e-8)
    lr.pop(0)
    optimizer.setup(model)
    optimizer.add_hook(chainer.optimizer_hooks.WeightDecay(0.0))

    supporter = PK.Supporter(args.outDir)

    updater = Updater(train, optimizer, supporter=supporter,device=args.gpu)

    trainer = chainer.training.Trainer(updater, (args.epoch,'epoch'), out=args.outDir)

    trainer.extend(Evaluator(dev,model,supporter,optimizer,args.outDir,lr,args.gpu),trigger=(1,'epoch'))

    trainer.extend(extensions.ProgressBar(update_interval=5))
    # While first epoch, the epoch size is computed gradually, so the prograss information will be inaccurate. 

    print('Now Start to Train')
    print('Note that: The first epoch will be doing the statistics of total data size gradually.')
    print('           So the information is not reliable.')
    print('Note that: We will evaluate the WER of test dataset every epoch that will cost a few minutes.')
    trainer.run()

    print("DNN Acoustic Model training done.")
    print("The final model has been saved as:",supporter.finalModel["LSTM"])
    print('Over System Time:',datetime.datetime.now().strftime("%Y-%m-%d %X"))

    return supporter.finalModel["LSTM"]

pretrainedModel = train_model()

## ------ Decode testing -----
def decode_test(pretrainedModel):

    print("\n############## Now do the decode test ##############")

    global args

    print('Load pretrained acoustic model')
    featDim = 40
    if args.delta>0:
        featDim *= (args.delta + 1)
    if args.splice > 0:
        featDim *= ( 2 * args.splice + 1 ) 
    model = LSTM(featDim)

    chainer.serializers.load_npz(pretrainedModel,model)
    print(pretrainedModel)

    print('Process mfcc feat to recognized result')
    filePath = args.TIMITpath + '/data-fmllr-tri3/test/feats.scp'
    feat = PK.load(filePath)
    if args.useCMVN:
        print('Apply CMVN')
        uttSpk = args.TIMITpath + '/data-fmllr-tri3/test/utt2spk'
        cmvnState = args.TIMITpath + '/data-fmllr-tri3/test/cmvn.ark'
        feat = PK.use_cmvn(feat,cmvnState,uttSpk)
    if args.delta > 0:  
        print('Add {} orders delta to feat'.format(args.delta))
        feat = PK.add_delta(feat,args.delta)
    if args.splice > 0:
        print('Splice front-back {} frames'.format(args.splice))   
        feat = feat.splice(args.splice)
    print('Transform to KaldiDict data')      
    feat = feat.array
    if args.normalize:
        print('Normalize with Mean and STD')   
        feat = feat.normalize()

    temp = PK.KaldiDict()
    with chainer.using_config('train',False),chainer.no_backprop_mode():
        for j,utt in enumerate(feat.keys(),start=1):
            print("Forward nework: {}/{}".format(j,len(feat.keys())),end='\r')
            data = np.array(feat[utt],dtype=np.float32)
            out1,out2 = model(data)
            out = F.log_softmax(out1,axis=1)
            temp[utt] = out.array
    print()

    print('Transform model output to KaldiArk data')
    amp = temp.ark

    hmm = args.TIMITpath + '/exp/dnn4_pretrain-dbn_dnn_ali_test/final.mdl'
    hclg = args.TIMITpath + '/exp/tri3/graph/HCLG.fst'
    lexicon = args.TIMITpath + '/exp/tri3/graph/words.txt'

    print('Gennerate lattice')
    lattice = PK.decode_lattice(amp,hmm,hclg,lexicon,Acwt=0.2)

    print('Get 1-bests words from lattice')
    outs = lattice.get_1best_words(minLmwt=1,maxLmwt=10,outDir=args.outDir,asFile='1best_LMWT')

    print('Score by different language model scales') 
    phonemap = args.TIMITpath + '/conf/phones.60-48-39.map'
    outFilter = args.TIMITpath + '/local/timit_norm_trans.pl -i - -m {} -from 48 -to 39'.format(phonemap)
    if not os.path.isfile(args.outDir+'/test_filt.txt'):
        refText = args.TIMITpath + '/data/test/text'
        cmd = 'cat {} | {} > {}/test_filt.txt'.format(refText,outFilter,args.outDir)
        (_,_) = PK.run_shell_cmd(cmd)

    for k in range(1,11,1):
        cmd = 'cat {} | {} > {}/test_prediction_filt.txt'.format(outs[k],outFilter,args.outDir)
        (_,_) = PK.run_shell_cmd(cmd)
        score = PK.compute_wer('{}/test_filt.txt'.format(args.outDir),"{}/test_prediction_filt.txt".format(args.outDir),mode='all')
        print('LMWT:%2d WER:%.2f'%(k,score['WER']))

#decode_test(pretrainedModel)





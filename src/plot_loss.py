import matplotlib.pyplot as plt
loss = open('../data/run_data/loss.txt','r').readlines()
loss = [float(l.strip().split('\t')[2]) for l in loss]
plt.plot(loss)
plt.xlabel('batch')
plt.ylabel('loss')
plt.savefig('../data/run_data/loss.png')
import numpy as np
import pandas as pd
import time, datetime
import matplotlib.pyplot as plt
from surprise.prediction_algorithms.knns import KNNWithMeans
from surprise.prediction_algorithms.matrix_factorization import SVD, NMF
from surprise.model_selection import cross_validate
from surprise import Dataset, Reader
from surprise.model_selection import KFold
import math

#
# !!!!!!!!!!!!!!!!!!!!!!!!!
#
# Jupyter Notebook for a better view only, you can edit/run code
# on your local Jupyter Notebook, but please push/sync code through
# this Project3.py only!!!
#
# (You can upload your own Jupyter Notebook if you want, just name
#  as Project3_yourname.ipynb)
#
# This is because we have not found a tool (like ShareLatex) to
# share/edit/run upyter Notebook simultaneously. Although
# Jupyter Notebook is really intuitive and convenient to use
#
# !!!!!!!!!!!!!!!!!!!!!!!!!
#


"""
This function should not be called during multi-threading!!
"""
def saveDfToPickle():
    data = np.loadtxt('ml-latest-small/ratings.csv',
                      delimiter=',', skiprows=1, usecols=(0, 1, 2))

    # tranform data type (from float to int for first 2 rows)
    # 'userId', 'movieId', 'rating'
    row_userId = data[:, :1].astype(int)
    row_movieId = data[:, 1:2].astype(int)
    row_rating = data[:, 2:3]
    # map movie ids to remove nonexistent movieId
    sortedId = np.sort(row_movieId.transpose()[0])
    m = {}
    idx = 0
    last = None
    for i in sortedId.tolist():
        if i != last:
            m[i] = idx
            idx += 1
        last = i
    mapped_row_movieId = np.copy(row_movieId)
    for r in mapped_row_movieId:
        r[0] = m[r[0]]

    ratings_dict = {
        'movieID': mapped_row_movieId.transpose().tolist()[0],
        'userID': row_userId.transpose().tolist()[0],
        'rating': (row_rating.transpose()*2).tolist()[0]    # map (0.5, 1, ..., 5) to (1, 2, ..., 10)
    }
    df = pd.DataFrame(ratings_dict)
    df.to_pickle('df.pkl')

#
# Question 1
#

# Sparsity = Total number of available ratings
#           / Total number of possible ratings

# Currentyly, row of R is 671 which corresponds to the 671 users listed
# in the dataset README file.
# However, column of R is 163949 which does not correspond to the 9125
# movies listed in dataset README file. As a result, the sparsity if very
# low.
# This is because the max movieId is 163949 from the rating.csv file. We
# will see if this is the correct choice later. If not, we need to find
# a way to map 9000+ movies (with movieIDs max to 163949) from 163949
# columns to 9000+ columns.

def Q1to6():
    data = np.loadtxt('ml-latest-small/ratings.csv',
                      delimiter=',', skiprows=1, usecols=(0, 1, 2))

    # tranform data type (from float to int for first 2 rows)
    # 'userId', 'movieId', 'rating'
    row_userId = data[:, :1].astype(int)
    row_movieId = data[:, 1:2].astype(int)
    row_rating = data[:, 2:3]
    # map movie ids to remove nonexistent movieId
    sortedId = np.sort(row_movieId.transpose()[0])
    m = {}
    idx = 0
    last = None
    for i in sortedId.tolist():
        if i != last:
            m[i] = idx
            idx += 1
        last = i
    mapped_row_movieId = np.copy(row_movieId)
    for r in mapped_row_movieId:
        r[0] = m[r[0]]

    R_row = np.amax(row_userId)
    R_col = np.amax(mapped_row_movieId)
    print('Matrix has row size (users) %s, and col size (movies) %s'
          % (R_row, R_col))
    R = np.zeros([R_row, R_col])
    for i in range(row_userId.size):
        r = row_userId[i] - 1
        c = mapped_row_movieId[i] - 1
        rating = row_rating[i]
        R[r, c] = rating

    rating_avl = np.count_nonzero(R)
    rating_psb = np.prod(R.shape)
    sparsity = rating_avl/rating_psb
    print(sparsity)

    # Question 2
    # plot a historgram showing frequency of rating values
    ratings_arr = []
    for r in range(R_row):
    	for c in range(R_col):
    		if R[r,c]!=0.0:
    			ratings_arr.append(R[r,c])
    binwidth = 0.5
    print (min(ratings_arr))
    print (max(ratings_arr))

    plt.hist(ratings_arr, bins=np.arange(min(ratings_arr), max(ratings_arr) + binwidth, binwidth))
    plt.show()
    plt.close()

    # Question 3
    l = [0 for x in range(0, R_col)] #R_row

    for r in range(R_row):
    	for c in range(R_col): 
    		if R[r,c]!=0.0:
    			l[c] = l[c] + 1
    l_no_zero = [val for val in l if val!=0]
    l_no_zero.sort(reverse = True)

    plt.plot([i+1 for i in range(0, len(l_no_zero))], l_no_zero)
    plt.show()
    plt.close()

    # Question 4
    l = np.zeros(R_row)
    for r in row_userId:
    	l[r[0]-1] += 1
    l[::-1].sort()
    plt.plot([i for i in range(1, len(l)+1)], l)
    plt.show()
    plt.close()

    # Q6
    var = np.array([])
    for c in range(R_col):
    	var = np.append(var, np.var(R[:,c]))
    var_bin = np.zeros(math.ceil((np.amax(var)-np.amin(var))/0.5))
    for v in var:
    	var_bin[math.floor(v/0.5)] += 1
    plt.hist(var, bins=np.arange(min(var),max(var),0.5))
    plt.show()
    plt.close()


def make_plot(x, ys, xlabel, ylabel, xticks=None, grid=False, title=None):
    for y, label in ys:
        plt.plot(x, y, label=label)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if xticks is not None:
        plt.xticks(x)
    plt.legend()
    if grid == True:
        plt.grid()
    if title is not None:
        plt.title(title)
    plt.show()

def load_data():
    df = pd.read_pickle('df.pkl')
    reader = Reader(rating_scale=(1, 10))
    data = Dataset.load_from_df(df[['userID', 'movieID', 'rating']], reader)
    return data

def Q10():
    data = load_data()

    sim_options = {'name': 'pearson_baseline',
                   'shrinkage': 0  # no shrinkage
                 }

    meanRMSE, meanMAE = [], []
    start = time.time()
    for k in range(2, 102, 2):
        knnWithMeans = KNNWithMeans(k, sim_options=sim_options)
        out = cross_validate(knnWithMeans, data, measures=['RMSE', 'MAE'], cv=10)
        meanRMSE.append(np.mean(out['test_rmse']))
        meanMAE.append(np.mean(out['test_mae']))
    cv_time = str(datetime.timedelta(seconds=int(time.time() - start)))
    print("Total time used for cross validation: " + cv_time)

    k = list(range(2, 102, 2))
    ys = [[meanRMSE, 'mean RMSE'], [meanMAE, 'mean MAE']]
    make_plot(k, ys, 'Number of Neighbors', 'Error')
    return meanRMSE, meanMAE

def popularTrim(testSet):
    colCnt = {}
    for (_, c, _) in testSet:
        if c in colCnt.keys():
            colCnt[c] += 1
        else:
            colCnt[c] = 1
    result = []
    for (r, c, rating) in testSet:
        if colCnt[c] > 2:
            result.append((r, c, rating))
    return result

def unpopularTrim(testSet):
    colCnt = {}
    for (_, c, _) in testSet:
        if c in colCnt.keys():
            colCnt[c] += 1
        else:
            colCnt[c] = 1
    result = []
    for (r, c, rating) in testSet:
        if colCnt[c] <= 2:
            result.append((r, c, rating))
    return result

def highVarTrim(testSet):
    colCnt = {}
    for (_, c, rating) in testSet:
        if c in colCnt.keys():
            colCnt[c].append(rating)
        else:
            colCnt[c] = []
    result = []
    for (r, c, rating) in testSet:
        if len(colCnt[c]) > 5 and np.var(np.array(colCnt[c])) > 2:
            result.append((r, c, rating))
    return result

def Q12To14And19To21And26To28(qNum):
    data = load_data()
    kf = KFold(n_splits=10)
    if 12 <= qNum <= 14:
        maxk = 100
    elif 19 <= qNum <= 21:
        maxk = 50
    else:
        maxk = 50
    sim_options = {'name': 'pearson_baseline',
                   'shrinkage': 0  # no shrinkage
                 }
    filterAndModel = {
        12: (popularTrim, 'KNNWithMeans'),
        13: (unpopularTrim, 'KNNWithMeans'),
        14: (highVarTrim, 'KNNWithMeans'),
        19: (popularTrim, 'NMF'),
        20: (unpopularTrim, 'NMF'),
        21: (highVarTrim, 'NMF'),
        26: (popularTrim, 'SVD'),
        27: (unpopularTrim, 'SVD'),
        28: (highVarTrim, 'SVD')
    }

    RMSE = []   #  RMSE for each k
    for k in range(2, maxk + 1, 2): # inclusive
        trimFun, modelName = filterAndModel[qNum]
        if modelName == 'KNNWithMeans':
            model = KNNWithMeans(k, sim_options=sim_options)
        elif modelName == 'NMF':
            model = NMF()
        else:
            model = SVD(n_factors = k)
        subRMSE = []    # RMSE for each k for each train-test split
        for trainSet, testSet in kf.split(data):
            subsubRMSE = 0
            model.fit(trainSet)
            testSet = trimFun(testSet)
            nTest = len(testSet)
            print("test set size after trimming: %d", nTest)
            predictions = model.test(testSet)
            for p in predictions:
                subsubRMSE += pow(p.est - p.r_ui, 2)
            # calculate RMSE of this train-test split
            subRMSE.append(np.sqrt(subsubRMSE / nTest))
        # average of all train-test splits of k-NN for this k
        RMSE.append(np.mean(subRMSE))
    return RMSE


def Q17():
    data = load_data()

    meanRMSE, meanMAE = [], []
    start = time.time()
    for k in range(2, 102, 2):
        nmf = NMF()
        out = cross_validate(nmf, data, measures=['RMSE', 'MAE'], cv=10)
        meanRMSE.append(np.mean(out['test_rmse']))
        meanMAE.append(np.mean(out['test_mae']))
    cv_time = str(datetime.timedelta(seconds=int(time.time() - start)))
    print("Total time used for cross validation: " + cv_time)

    k = list(range(2, 52, 2))
    ys = [[meanRMSE, 'mean RMSE'], [meanMAE, 'mean MAE']]
    make_plot(k, ys, 'Number of Neighbors', 'Error')
    return meanRMSE, meanMAE


def Q19to21(qNum):
    data = load_data()
    kf = KFold(n_splits=10)

    trimFun = {12: popularTrim,
               13: unpopularTrim,
               14: highVarTrim}
    RMSE = []
    for k in range(2, 20, 2):
        nmf = NMF()
        subRMSE = []
        for trainSet, testSet in kf.split(data):
            subsubRMSE = 0
            nmf.fit(trainSet)
            testSet = trimFun[qNum](testSet)
            nTest = len(testSet)
            print("test set size after trimming: %d", nTest)
            predictions = nmf.test(testSet)
            for p in predictions:
                subsubRMSE += pow(p.est - p.r_ui, 2)
        # average of all train-test splits of k-NN
        RMSE.append(np.mean(subRMSE))
    return RMSE


def Q24():

# so far using same code as Q10, Q12-14 for Q24, Q26-28, can combine code later
# only using SVD for Q24 for now, but the RMSE and MAE don't change much with latent factor
    data = load_data()

    meanRMSE, meanMAE = [], []
    start = time.time()
    for k in range(2, 52, 2):
        MF_svd = SVD(n_factors = k)
        out = cross_validate(MF_svd, data, measures=['RMSE', 'MAE'], cv=10)
        meanRMSE.append(np.mean(out['test_rmse']))
        meanMAE.append(np.mean(out['test_mae']))
    cv_time = str(datetime.timedelta(seconds=int(time.time() - start)))
    print("Total time used for cross validation: " + cv_time)

    k = list(range(2, 52, 2))
    ys = [[meanRMSE, 'mean RMSE'], [meanMAE, 'mean MAE']]
    #currently plot meanRMSE and meanMAE separately because it's hard to see the trend when they are plotted in same graph 
    make_plot(k, [[meanRMSE, 'mean RMSE']], 'Number of Neighbors', 'Error')
    make_plot(k, [[meanMAE, 'mean MAE']], 'Number of Neighbors', 'Error')
    return meanRMSE, meanMAE

def Q26To28(qNum, n_splits=10):
    data = load_data()
    kf = KFold(n_splits=10)

    trimFun = {26: popularTrim,
               27: unpopularTrim,
               28: highVarTrim}
    RMSE = []
    for k in range(2, 52, 2):
        MF_svd = SVD(n_factors = k)
        subRMSE = []
        for trainSet, testSet in kf.split(data):
            subsubRMSE = 0
            MF_svd.fit(trainSet)
            testSet = trimFun[qNum](testSet)
            nTest = len(testSet)
            print("test set size after trimming: %d", nTest)
            for (r, c, rating) in testSet:
                predictedRating = MF_svd.predict(str(r), str(c))
                subsubRMSE += (pow(rating - predictedRating.est, 2))
            # calculate RMSE of this train-test split
            subRMSE.append(np.sqrt(subsubRMSE / nTest))
        # average of all train-test splits of k-NN
        RMSE.append(np.mean(subRMSE))

    return RMSE

if __name__ == '__main__':
    Q1to6()




